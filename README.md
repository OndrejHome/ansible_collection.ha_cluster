## crm_wait_for

Ansible module used for waiting on various resource states in pacemaker cluster.

Purpose of this module is to provide ability to wait for resources in pacemaker cluster to reach desired state and/or to determine on which node(s) the selected resource is in desired state.

## ansible-doc crm_wait_for

~~~
# ansible-doc -M library/crm_wait_for
> CRM_WAIT_FOR    (ansible.crm_wait_for/library/crm_wait_for.py)

        This module can wait for resource in cluster to become simply
        present/absent from configuration or for resource defined in
        cluster to get into desired state. Optionally you can define
        on which node(s) the state for resource should be achieved. It
        is possible to adjust `timeout' for how long to wait before
        failing and `sleep' interval between the checks of cluster
        state. If resource is expected to take some time to reach
        desired state the `delay' defines how long to wait before
        first check.

OPTIONS (= is mandatory):

- delay
        Number of seconds to delay first check.
        [Default: 0]
        type: int

- node_list
        List of nodes on which the desired stated is expected (only
        for 'Started'/'Stopped'/'Master'/'Slave' states.
        For state 'Stopped' the default is 'all cluster nodes', while
        for other states the default is 'any node'.
        [Default: []]
        elements: str
        type: list

= resource
        Name of resource to wait for.
        For cloned resource use the name of 'primitive resource'
        (typically name without '-clone'/'-master'/'-promotable'
        suffix)

        type: str

- sleep
        Number of seconds to sleep/wait between checks.
        [Default: 2]
        type: int

- state
        'present' - waits for resource is present/defined in cluster
        'absent' - waits for resource to not exists in cluster
        configuration
        'Started' - waits for resource to reach 'Started' state
        'Stopped' - waits for resource to reach 'Stopped' state
        'Master' - waits for resource to reach 'Master' state
        'Slave' - waits for resource to reach 'Slave' state
        (Choices: present, absent, Started, Stopped, Master,
        Slave)[Default: present]
        type: str

- timeout
        Number of seconds to wait for condition before failing (after
        initial `delay').
        [Default: 60]
        type: int


NOTES:
      * tested on XXX
      * This modules requires the `crm_mon' binary to be present
        on target system.
      * LIMITATION: module gets list of nodes only once it
        starts.


AUTHOR: Ondrej Famera (@OndrejHome)

METADATA:
  metadata_version: '1.1'
  status:
  - preview
  supported_by: community


EXAMPLES:

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


RETURN VALUES:
- cluster_nodes
        List of cluster nodes in cluster.

        returned: always
        sample: node-a, node-b
        type: list

- elapsed
        The number of seconds that elapsed while waiting

        returned: always
        sample: 23
        
        type: int

- rsc_active_node_set
        (Only present when state is
        'Stopped'/'Started'/'Master'/'Slave'). List of nodes where
        resource is in desired state.

        returned: always
        sample: node-b
        type: list

- rsc_inactive_node_set
        (Only present when state is 'Stopped'). List of nodes where
        resource is not running.

        returned: always
        sample: node-a
        type: list
~~~

## License
GPLv3

## Author Information

WARNING: Despite the module is tested only manually and currently in early releases (0.x.x) may not be stable with future updates.

To get in touch with author you can use email ondrej-xa2iel8u@famera.cz or create a issue on github when requesting some feature.

