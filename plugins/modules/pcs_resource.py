#!/usr/bin/python
# Copyright: (c) 2018, Ondrej Famera <ondrej-xa2iel8u@famera.cz>
# GNU General Public License v3.0+ (see LICENSE-GPLv3.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# Apache License v2.0 (see LICENSE-APACHE2.txt or http://www.apache.org/licenses/LICENSE-2.0)

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
module: pcs_resource
short_description: "wrapper module for 'pcs resource' "
description:
     - "Module for creating, deleting and updating clusters resources using 'pcs' utility."
     - "This module should be executed for same resorce only on one of the nodes in cluster at a time."
version_added: "2.4"
options:
  state:
    description:
      - "'present' - ensure that cluster resource exists"
      - "'absent' - ensure cluster resource doesn't exist"
    required: false
    default: present
    choices: ['present', 'absent']
    type: str
  name:
    description:
      - "name of cluster resource - cluster resource identifier"
    required: true
    type: str
  resource_class:
    description:
      - class of cluster resource
    required: false
    default: 'ocf'
    choices: ['ocf', 'systemd', 'stonith', 'master', 'promotable']
    type: str
  resource_type:
    description:
      - cluster resource type
    required: false
    type: str
  options:
    description:
      - "additional options passed to 'pcs' command"
    required: false
    type: str
  force_resource_update:
    description:
      - "When set to 'yes' the pcs will use 'scope=resource' instead of 'scope=all' when creating resources"
      - "For primitive resources the default is 'no' while for multistate resources ('master'/'promotable')
      the default value is 'yes'."
      - "This option is useful in busy clusters where a lot of changes may happen while module is running resulting
      in error like 'Unable to push to the CIB because pushed configuration is older than existing one.' in
      which case this is worth a try to see if that resolves the error.
      However enabling this options may discard other resource config changes made to cluster while module is running."
    required: false
    type: bool
  cib_file:
    description:
      - "Apply changes to specified file containing cluster CIB instead of running cluster."
      - "This module requires the file to already contain cluster configuration."
    required: false
    type: str
  child_name:
    description:
      - "define custom name of child resource when creating multistate resource ('master' or 'promotable' resource_class)."
      - "If not specified then the child resource name will have for of name+'-child'."
    required: false
    type: str
  ignored_meta_attributes:
    description:
      - "list of meta attributes that will be ignored when comparing existing resources"
    required: false
    default: []
    type: list
    elements: str
notes:
   - tested on CentOS 6.8, 7.3
   - module can create and delete clones, groups and master resources indirectly -
     resource can specify --clone, --group, --master option which will cause them to create
     or become part of clone/group/master
'''

EXAMPLES = '''
- name: ensure Dummy('ocf:pacemaker:Dummy') resource with name 'test' is present
  pcs_resource:
    name: 'test'
    resource_type: 'ocf:pacemaker:Dummy'

- name: create 'stonith' class resource 'kdump' of type 'fence_kdump'
  pcs_resource:
    name: 'kdump'
    resource_type: 'fence_kdump'
    resource_class: 'stonith'

- name: ensure that resource with name 'vip' is not present
  pcs_resource:
    name: 'vip'
    state: 'absent'

- name: ensure resource 'test2' of IPaddr2('ocf:heartbeat:IPaddr2') type exists an has 5 second monitor interval
  pcs_resource:
    name: 'test2'
    resource_type: 'ocf:heartbeat:IPaddr2'
    options: 'ip=192.168.1.2 op monitor interval=5'

- name: create resource in group 'testgrp'
  pcs_resource:
    name: 'test3'
    resource_type: 'ocf:pacemaker:Dummy'
    options: '--group testgrp'

- name: create multistate (Master/Slave) resource 'test' of 'ocf:pacemaker:Stateful' type - pcs-0.9
  pcs_resource:
    name: 'test'
    resource_type: 'ocf:pacemaker:Stateful'
    resource_class: 'master'
    options: >
      fake=some_value --master meta master-max=1 master-node-max=1 clone-max=2 clone-node-max=1 notify=true
      op monitor interval=60s meta resource-stickiness=100

- name: create multistate (Promotable) resource 'test' of 'ocf:pacemaker:Stateful' type - pcs-0.10
  pcs_resource:
    name: 'test'
    resource_type: 'ocf:pacemaker:Stateful'
    resource_class: 'promotable'
    options: >
      fake=some_value promotable meta promotable-max=1 promotable-node-max=1 clone-max=2 clone-node-max=1 notify=true
      op monitor interval=60s meta resource-stickiness=100

- name: ensure Dummy('ocf:pacemaker:Dummy') resource with name 'test' is present, but ignore if it is enabled or disabled (ignore target-role)
  pcs_resource:
    name: 'test'
    resource_type: 'ocf:pacemaker:Dummy'
    ignored_meta_attributes: [ 'target-role' ]
'''

# TODO if group exists and is not part of group, then specifying group won't put it into group
# same problem is with clone and master - it might be better to make this functionality into separate module

import sys
import os.path
import xml.etree.ElementTree as ET
import tempfile
import re
from distutils.spawn import find_executable
from ansible.module_utils.basic import AnsibleModule

# determine if we have 'to_native' function that we can use for 'ansible --diff' output
to_native_support = False
try:
    from ansible.module_utils._text import to_native
    to_native_support = True
except ImportError:
    pass


def replace_element(elem, replacement):
    elem.clear()
    elem.text = replacement.text
    elem.tail = replacement.tail
    elem.tag = replacement.tag
    elem.attrib = replacement.attrib
    elem[:] = replacement[:]


def compare_resources(module, res1, res2):
    # we now have 2 nodes that we can compare, so lets dump them into files for comparring
    n1_file_fd, n1_tmp_path = tempfile.mkstemp()
    n2_file_fd, n2_tmp_path = tempfile.mkstemp()
    n1_file = open(n1_tmp_path, 'w')
    n2_file = open(n2_tmp_path, 'w')
    # dump the XML resource definitions into temporary files
    old_stdout = sys.stdout
    sys.stdout = n1_file
    ET.dump(res1)
    sys.stdout = n2_file
    ET.dump(res2)
    sys.stdout = old_stdout
    # close files
    n1_file.close()
    n2_file.close()
    # normalize the files and store results in new files - this also removes some unimportant spaces and stuff
    n3_file_fd, n3_tmp_path = tempfile.mkstemp()
    n4_file_fd, n4_tmp_path = tempfile.mkstemp()
    rc, out, err = module.run_command('xmllint --format --output ' + n3_tmp_path + ' ' + n1_tmp_path)
    rc, out, err = module.run_command('xmllint --format --output ' + n4_tmp_path + ' ' + n2_tmp_path)

    # add files that should be cleaned up
    module.add_cleanup_file(n1_tmp_path)
    module.add_cleanup_file(n2_tmp_path)
    module.add_cleanup_file(n3_tmp_path)
    module.add_cleanup_file(n4_tmp_path)

    # now compare files
    diff = ''
    rc, out, err = module.run_command('diff ' + n3_tmp_path + ' ' + n4_tmp_path)
    if rc != 0:
        # if there was difference then show the diff
        n3_file = open(n3_tmp_path, 'r+')
        n4_file = open(n4_tmp_path, 'r+')
        if to_native_support:
            # produce diff only where we have to_native function which give sensible output
            # without 'to_native' whole text is wrapped as single line and not diffed
            # seems that to_native was added in ansible-2.2 (commit 57701d7)
            diff = {
                'before_header': '',
                'before': to_native(''.join(n3_file.readlines())),
                'after_header': '',
                'after': to_native(''.join(n4_file.readlines())),
            }
    return rc, diff


def find_resource(cib, resource_id):
    my_resource = None
    tags = ['group', 'clone', 'master', 'primitive']
    for elem in list(cib):
        if elem.attrib.get('id') == resource_id:
            return elem
        elif elem.tag in tags:
            my_resource = find_resource(elem, resource_id)
            if my_resource is not None:
                break
    return my_resource


def rename_multistate_element(multistate_resource, resource_name, child_name, resource_suffix):
    multistate_resource.set('id', resource_name)
    # search for meta_attributes tag
    for elem in list(multistate_resource):
        if elem.tag == 'meta_attributes':
            new_meta_id = re.sub('^' + child_name + resource_suffix, resource_name, elem.attrib.get('id'))
            elem.set('id', new_meta_id)
            # replace ID of all nvpairs inside of this meta_attributes
            for nvpair in list(elem):
                new_nvpair_id = re.sub('^' + child_name + resource_suffix, resource_name, nvpair.attrib.get('id'))
                nvpair.set('id', new_nvpair_id)


def remove_ignored_meta_attributes(resource, ignored_meta_attributes):
    for elem in list(resource):
        if elem.tag == 'meta_attributes' and len(list(elem)) > 0:
            for nvpair in list(elem):
                if nvpair.tag == 'nvpair' and nvpair.attrib.get('name') in ignored_meta_attributes:
                    elem.remove(nvpair)


def remove_empty_meta_attributes_tag(resource):
    # remove the meta_attribute element to make comparison clean - Issue #10
    # some versions of 'pcs' left empty 'meta_attributes' tag after 'pcs resource enable'
    for elem in list(resource):
        if elem.tag == 'meta_attributes' and len(list(elem)) == 0:
            resource.remove(elem)


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default="present", choices=['present', 'absent']),
            name=dict(required=True),
            resource_class=dict(default="ocf", choices=['ocf', 'systemd', 'stonith', 'master', 'promotable']),
            resource_type=dict(required=False),
            options=dict(default="", required=False),
            force_resource_update=dict(type='bool', required=False),
            cib_file=dict(required=False),
            child_name=dict(required=False),
            ignored_meta_attributes=dict(required=False, type='list', elements='str', default=[]),
        ),
        supports_check_mode=True
    )

    state = module.params['state']
    resource_name = module.params['name']
    resource_class = module.params['resource_class']
    cib_file = module.params['cib_file']
    if 'child_name' in module.params and module.params['child_name'] is None:
        module.params['child_name'] = resource_name + '-child'
    child_name = module.params['child_name']
    resource_options = module.params['options']
    ignored_meta_attributes = module.params['ignored_meta_attributes']
    # Issue #39: Use scope=resources when dealing with master/promotable resource as default
    # In many cases these resources needs this option as they quickly create node attributes causing error.
    if module.params['force_resource_update'] is None and resource_class in ['master', 'promotable']:
        module.params['force_resource_update'] = True
    elif module.params['force_resource_update'] is None:
        module.params['force_resource_update'] = False
    # if value was specified we will not override it

    if state == 'present' and (not module.params['resource_type']):
        module.fail_json(msg='When creating cluster resource you must specify the resource_type')
    result = {}

    if find_executable('pcs') is None:
        module.fail_json(msg="'pcs' executable not found. Install 'pcs'.")

    # get the pcs major.minor version
    rc, out, err = module.run_command('pcs --version')
    if rc == 0:
        pcs_version = out.split('.')[0] + '.' + out.split('.')[1]
    else:
        module.fail_json(msg="pcs --version exited with non-zero exit code (" + rc + "): " + out + err)

    # check if 'master' and 'promotable' classes have the needed keyword in options
    if resource_class == 'master' and not ('--master' in resource_options or 'master' in resource_options):
        module.fail_json(msg='When creating Master/Slave resource you must specify keyword "master" or "--master" in "options"')
    if resource_class == 'promotable' and 'promotable' not in resource_options:
        module.fail_json(msg='When creating promotable resource you must specify keyword "promotable" in "options"')

    module.params['cib_file_param'] = ''
    if cib_file is not None:
        # use cib_file if specified
        if os.path.isfile(cib_file):
            try:
                current_cib = ET.parse(cib_file)
            except Exception as e:
                module.fail_json(msg="Error encountered parsing the cib_file - %s" % (e))
            current_cib_root = current_cib.getroot()
            module.params['cib_file_param'] = '-f ' + cib_file
        else:
            module.fail_json(msg="%(cib_file)s is not a file or doesn't exists" % module.params)
    else:
        # get running cluster configuration
        rc, out, err = module.run_command('pcs cluster cib')
        if rc == 0:
            current_cib_root = ET.fromstring(out)
        else:
            module.fail_json(msg='Failed to load cluster configuration', out=out, error=err)

    # try to find the resource that we seek
    resource = None
    cib_resources = current_cib_root.find('./configuration/resources')
    resource = find_resource(cib_resources, resource_name)

    if state == 'present' and resource is None:
        # resource should be present, but we don't see it in configuration - lets create it
        result['changed'] = True
        if not module.check_mode:
            if resource_class == 'stonith':
                cmd = 'pcs %(cib_file_param)s stonith create %(name)s %(resource_type)s %(options)s' % module.params
            elif resource_class == 'master' or resource_class == 'promotable':
                # we first create Master/Slave or Promotable resource with child_name and later rename it
                cmd = 'pcs %(cib_file_param)s resource create %(child_name)s %(resource_type)s %(options)s' % module.params
            else:
                cmd = 'pcs %(cib_file_param)s resource create %(name)s %(resource_type)s %(options)s' % module.params
            rc, out, err = module.run_command(cmd)
            if rc != 0 and "Call cib_replace failed (-62): Timer expired" in err:
                # EL6: special retry when we failed to create resource because of timer waiting on cib expired
                rc, out, err = module.run_command(cmd)
            if rc == 0:
                if resource_class == 'master' or resource_class == 'promotable':
                    # rename the resource to desirable name
                    rc, out, err = module.run_command('pcs cluster cib')
                    if rc == 0:
                        updated_cib_root = ET.fromstring(out)
                        multistate_resource = None
                        updated_cib_resources = updated_cib_root.find('./configuration/resources')
                        resource_suffix = '-master' if pcs_version == '0.9' else '-clone'
                        multistate_resource = find_resource(updated_cib_resources, child_name + resource_suffix)
                        if multistate_resource is not None:
                            rename_multistate_element(multistate_resource, resource_name, child_name, resource_suffix)
                            ##
                            # when not using cib_file then we continue preparing changes for cib-push into running cluster
                            new_cib = ET.ElementTree(updated_cib_root)
                            new_cib_fd, new_cib_path = tempfile.mkstemp()
                            module.add_cleanup_file(new_cib_path)
                            new_cib.write(new_cib_path)
                            push_scope = 'scope=resources' if module.params['force_resource_update'] else ''
                            push_cmd = 'pcs cluster cib-push ' + push_scope + ' ' + new_cib_path
                            rc, out, err = module.run_command(push_cmd)
                            if rc == 0:
                                module.exit_json(changed=True)
                            else:
                                # rollback the failed rename by deleting the multistate resource
                                cmd = 'pcs %(cib_file_param)s resource delete %(child_name)s' % module.params
                                rc2, out2, err2 = module.run_command(cmd)
                                if rc2 == 0:
                                    module.fail_json(msg="Failed to push updated configuration for multistate resource to cluster using command '" + push_cmd +
                                                     "'. Creation of multistate resource was rolled back. You can retry this task with " +
                                                     "'force_resource_update=true' to see if that helps.", output=out, error=err)
                                else:
                                    module.fail_json(msg="Failed to delete resource after unsuccessful multistate resource configuration update using command '"
                                                     + cmd + "'", output=out2, error=err2)
                        else:
                            module.fail_json(msg="Failed to detect multistate resource after creating it with cmd '" + cmd + "'!",
                                             output=out, error=err, previous_cib=current_cib)
                module.exit_json(changed=True)
            else:
                module.fail_json(msg="Failed to create resource using command '" + cmd + "'", output=out, error=err)

    elif state == 'present' and resource is not None:
        # resource should be present and we have find resource with such ID - lets compare it with definition if it needs a change

        # lets simulate how the resource would look like if it was created using command we have
        clean_cib_fd, clean_cib_path = tempfile.mkstemp()
        module.add_cleanup_file(clean_cib_path)
        module.do_cleanup_files()
        # we must be sure that clean_cib_path is empty
        if resource_class == 'stonith':
            cmd = 'pcs -f ' + clean_cib_path + ' stonith create %(name)s %(resource_type)s %(options)s' % module.params
        elif resource_class == 'master' or resource_class == 'promotable':
            # we first create Master/Slave or Promotable resource with child_name and later rename it
            cmd = 'pcs -f ' + clean_cib_path + ' resource create %(child_name)s %(resource_type)s %(options)s' % module.params
        else:
            cmd = 'pcs -f ' + clean_cib_path + ' resource create %(name)s %(resource_type)s %(options)s' % module.params
        rc, out, err = module.run_command(cmd)
        if rc == 0:
            if resource_class == 'master' or resource_class == 'promotable':
                # deal with multistate resources
                clean_cib = ET.parse(clean_cib_path)
                clean_cib_root = clean_cib.getroot()
                multistate_resource = None
                updated_cib_resources = clean_cib_root.find('./configuration/resources')
                resource_suffix = '-master' if pcs_version == '0.9' else '-clone'
                multistate_resource = find_resource(updated_cib_resources, child_name + resource_suffix)
                if multistate_resource is not None:
                    rename_multistate_element(multistate_resource, resource_name, child_name, resource_suffix)
                    # we try to write the changes into temporary cib_file
                    try:
                        clean_cib.write(clean_cib_path)
                    except Exception as e:
                        module.fail_json(msg="Error encountered writing intermediate multistate result to clean_cib_path - %s" % (e))
                else:
                    module.fail_json(msg="Failed to detect intermediate multistate resource after creating it with cmd '" + cmd + "'!",
                                     output=out, error=err, previous_cib=current_cib)

            # we have a comparable resource created in clean cluster, so lets select it and compare it
            clean_cib = ET.parse(clean_cib_path)
            clean_cib_root = clean_cib.getroot()
            clean_resource = None
            cib_clean_resources = clean_cib_root.find('./configuration/resources')
            clean_resource = find_resource(cib_clean_resources, resource_name)

            if clean_resource is not None:
                # cleanup the definition of resource and clean_resource before comparison
                remove_ignored_meta_attributes(resource, ignored_meta_attributes)
                remove_empty_meta_attributes_tag(resource)

                remove_ignored_meta_attributes(clean_resource, ignored_meta_attributes)
                remove_empty_meta_attributes_tag(clean_resource)

                # compare the existing resource in cluster and simulated clean_resource
                rc, diff = compare_resources(module, resource, clean_resource)
                if rc == 0:
                    # if no differnces were find there is no need to update the resource
                    module.exit_json(changed=False)
                else:
                    # otherwise lets replace the resource with new one
                    result['changed'] = True
                    result['diff'] = diff
                    if not module.check_mode:
                        replace_element(resource, clean_resource)
                        # when we use cib_file then we can dump the changed CIB directly into file
                        if cib_file is not None:
                            try:
                                current_cib.write(cib_file)  # FIXME add try/catch for writing into file
                            except Exception as e:
                                module.fail_json(msg="Error encountered writing result to cib_file - %s" % (e))
                            module.exit_json(changed=True)
                        # when not using cib_file then we continue preparing changes for cib-push into running cluster
                        new_cib = ET.ElementTree(current_cib_root)
                        new_cib_fd, new_cib_path = tempfile.mkstemp()
                        module.add_cleanup_file(new_cib_path)
                        new_cib.write(new_cib_path)
                        push_scope = 'scope=resources' if module.params['force_resource_update'] else ''
                        push_cmd = 'pcs cluster cib-push ' + push_scope + ' ' + new_cib_path
                        rc, out, err = module.run_command(push_cmd)
                        if rc == 0:
                            module.exit_json(changed=True)
                        else:
                            module.fail_json(msg="Failed to push updated configuration to cluster using command '" + push_cmd + "'", output=out, error=err)
            else:
                module.fail_json(msg="Unable to find simulated resource, This is most probably a bug.")
        else:
            module.fail_json(msg="Unable to simulate resource with given definition using command '" + cmd + "'", output=out, error=err)

    elif state == 'absent' and resource is not None:
        # resource should not be present but we have found something - lets remove that
        result['changed'] = True
        if not module.check_mode:
            if resource_class == 'stonith':
                cmd = 'pcs %(cib_file_param)s stonith delete %(name)s' % module.params
            else:
                cmd = 'pcs %(cib_file_param)s resource delete %(name)s' % module.params
            rc, out, err = module.run_command(cmd)
            if rc == 0:
                module.exit_json(changed=True)
            else:
                module.fail_json(msg="Failed to delete resource using command '" + cmd + "'", output=out, error=err)

    else:
        # resource should not be present and is nto there, nothing to do
        result['changed'] = False

    # END of module
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
