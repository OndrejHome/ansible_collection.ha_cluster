#!/usr/bin/python
# Copyright: (c) 2020, Ondrej Famera <ondrej-xa2iel8u@famera.cz>
# GNU General Public License v3.0+ (see LICENSE-GPLv3.txt or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
author: "Ondrej Famera (@OndrejHome)"
module: crm_wait_for
short_description: "Wait for resource in pacemaker cluster to get into requested state before continuing."
description:
  - "This module can wait for resource in cluster to become simply present/absent from configuration or"
  - "for resource defined in cluster to get into desired state."
  - "Optionally you can define on which node(s) the state for resource should be achieved."
  - "It is possible to adjust C(timeout) for how long to wait before failing and C(sleep) interval between the checks of cluster state."
  - "If resource is expected to take some time to reach desired state the C(delay) defines how long to wait before first check."

version_added: "2.10"
options:
  state:
    description:
      - "'present' - waits for resource is present/defined in cluster"
      - "'absent' - waits for resource to not exists in cluster configuration"
      - "'Started' - waits for resource to reach 'Started' state"
      - "'Stopped' - waits for resource to reach 'Stopped' state"
      - "'Master' - waits for resource to reach 'Master' state"
      - "'Slave' - waits for resource to reach 'Slave' state"
    required: false
    default: present
    choices: ['present', 'absent', 'Started', 'Stopped', 'Master', 'Slave']
    type: str
  resource:
    description:
      - Name of resource to wait for.
      - For cloned resource use the name of 'primitive resource' (typically name without '-clone'/'-master'/'-promotable' suffix)
    required: true
    type: str
  delay:
    description:
      - Number of seconds to delay first check.
    required: false
    type: int
    default: 0
  timeout:
    description:
      - Number of seconds to wait for condition before failing (after initial C(delay)).
    required: false
    type: int
    default: 60
  sleep:
    description:
      - Number of seconds to sleep/wait between checks.
    required: false
    type: int
    default: 2
  node_list:
    description:
      - "List of nodes on which the desired stated is expected (only for 'Started'/'Stopped'/'Master'/'Slave'/'Promoted'/'Unpromoted' states."
      - "For state 'Stopped' the default is 'all cluster nodes', while for other states the default is 'any node'."
    required: false
    default: []
    type: list
    elements: str
notes:
   - tested on XXX
   - This modules requires the C(crm_mon) binary to be present on target system.
   - "LIMITATION: module gets list of nodes only once it starts."
'''

EXAMPLES = '''
- name: wait for 'resA' resource to get defined in cluster config
  crm_wait_for:
    resource: 'resA'
    state: 'present'

- name: wait for 'resA' resource to get removed from cluster configuration
  crm_wait_for:
    resource: 'resA'
    state: 'absent'

- name: wait for 'resA' resource to get 'Started' anywhere in cluster, wait 2 seconds between checks
  crm_wait_for:
    resource: 'resA'
    state: 'Started'
    sleep: '2'

- name: wait for 'resA' resource to get 'Stopped' on all cluster nodes, delay first check for 3 seconds
  crm_wait_for:
    resource: 'resA'
    state: 'Stopped'
    delay: '3'

- name: wait for 'resA' resource to get 'Stopped' on node 'node-b' (succeeds when 'resA' is not running or when it is running on any other node than 'node-b')
  crm_wait_for:
    resource: 'resA'
    state: 'Stopped'
    node_list: ['node-b']

- name: wait for 'resB' resource to get promoted to 'Master' on node 'node-a'
  crm_wait_for:
    resource: 'resB'
    state: 'Master'
    node_list: ['node-a']

- name: wait up to 20 seconds for 'resC' resource to get started both node 'node-a' and node 'node-b'
  crm_wait_for:
    timeout: '20'
    resource: 'resC'
    state: 'Started'
    node_list: ['node-a', 'node-b']
'''

RETURN = '''
elapsed:
  description: The number of seconds that elapsed while waiting
  returned: always
  type: int
  sample: 23
cluster_nodes:
  description: List of cluster nodes in cluster.
  returned: always
  type: list
  sample: ['node-a', 'node-b']
rsc_active_node_set:
  description: (Only present when state is 'Stopped'/'Started'/'Master'/'Slave'/'Promoted'/'Unpromoted'). List of nodes where resource is in desired state.
  returned: always
  type: list
  sample: ['node-b']
rsc_inactive_node_set:
  description: (Only present when state is 'Stopped'). List of nodes where resource is not running.
  returned: always
  type: list
  sample: ['node-a']
'''

import os.path
import xml.etree.ElementTree as ET
import datetime
import time
from distutils.spawn import find_executable

from ansible.module_utils.basic import AnsibleModule


def get_crm_data(module):
    # get running cluster crm_mon state informantion
    rc, out, err = module.run_command('crm_mon -1r --as-xml')
    if rc == 0:
        return ET.fromstring(out)
    else:
        module.fail_json(msg='Failed to get current cluster state from crm_mon', out=out, error=err)


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default="present", choices=['present', 'absent', 'Started', 'Stopped', 'Master', 'Slave', 'Promoted', 'Unpromoted']),
            resource=dict(required=True),
            delay=dict(type='int', default=0),
            timeout=dict(type='int', default=60),
            sleep=dict(type='int', default=2),
            node_list=dict(required=False, type='list', elements='str', default=[]),
        ),
        supports_check_mode=True
    )

    state = module.params['state']
    resource = module.params['resource']
    node_list = module.params['node_list']
    delay = module.params['delay']
    sleep = module.params['sleep']
    timeout = module.params['timeout']

    result = {'changed': False}  # This module never changes state

    if find_executable('crm_mon') is None:
        module.fail_json(msg="'crm_mon' executable not found. Install package containing 'crm_mon' command.")

    # create a set out of node_list provided to module
    rsc_desired_node_set = set()
    if len(module.params['node_list']) > 0:
        for node in module.params['node_list']:
            rsc_desired_node_set.add(node)

    # delay the initial check if requested
    if delay:
        time.sleep(delay)

    # construct set of cluster nodes
    crm_root = get_crm_data(module)
    cluster_nodes = crm_root.findall(".//nodes/node")
    result['cluster_nodes'] = set()
    for node in cluster_nodes:
        result['cluster_nodes'].add(node.attrib.get('name'))

    if not rsc_desired_node_set.issubset(result['cluster_nodes']):
        result['msg'] = "node_list contains a node that is not present in cluster."
        result['node_list'] = node_list
        module.fail_json(**result)

    # determine the start and end of timeout
    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(seconds=timeout)

    # BEGIN - MAIN WAITING LOOP
    while datetime.datetime.utcnow() < end:
        crm_root = get_crm_data(module)
        crm_resource = crm_root.findall(".//resource[@id='" + resource + "']")
        # additional variables
        result['rsc_active_node_set'] = set()
        elapsed = datetime.datetime.utcnow() - start
        result['elapsed'] = elapsed.seconds

        if state == 'absent' and len(crm_resource) == 0:
            # resource should not be present and is gone, FINISH
            result['state'] = 'absent'
            module.exit_json(**result)
        elif state == 'present' and len(crm_resource) > 0:
            # resource should be present and it is, FINISH
            result['state'] = 'present'
            module.exit_json(**result)
        elif state == 'Stopped' and len(crm_resource) > 0:
            # if resource should be present in Stopped state
            # we need to handle this situation a bit specially
            # element '<node>' is present ONLY when resource is active on given node
            rsc_inactive_node_list = crm_root.findall(".//resource[@id='" + resource + "']/node")
            for node in rsc_inactive_node_list:
                result['rsc_active_node_set'].add(node.attrib.get('name'))
            result['rsc_inactive_node_set'] = result['cluster_nodes'] - result['rsc_active_node_set']

            if len(node_list) == 0 and result['rsc_inactive_node_set'] == result['cluster_nodes']:
                # resource is Stopped everywhere, FINISH
                module.exit_json(**result)
            elif len(node_list) > 0 and rsc_desired_node_set.issubset(result['rsc_inactive_node_set']):
                # resource is stopped where it is desired, FINISH
                module.exit_json(**result)
        elif state not in ['absent', 'present', 'Stopped'] and len(crm_resource) > 0:
            # resource should be present in certain state
            # determine node list where resource is in desired state
            active_node_list = crm_root.findall(".//resource[@id='" + resource + "'][@role='" + state + "']/node")
            for node in active_node_list:
                result['rsc_active_node_set'].add(node.attrib.get('name'))

            # if the node_list is empty we don't care where the state was achieved
            if len(node_list) == 0 and len(active_node_list) >= 1:
                # resource is in desired state somewhere, FINISH
                module.exit_json(**result)
            elif len(node_list) >= 1 and len(active_node_list) >= 1 and result['rsc_active_node_set'] == rsc_desired_node_set:
                # resource is in state on nodes where it is desired to be in such state, FINISH
                module.exit_json(**result)

        # Conditions not yet met, RETRY
        time.sleep(module.params['sleep'])
    # END - MAIN WAITING LOOP

    result['msg'] = "timeout"
    module.fail_json(**result)
    # END of module


def main():
    run_module()


if __name__ == '__main__':
    main()
