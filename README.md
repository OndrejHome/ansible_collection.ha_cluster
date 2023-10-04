## ondrejhome.ha_cluster collection

WARNING: This is a proof-of-concept merge of several roles and modules into one collection.

This Ansible collection is collection of following code that is also available as standalone roles:

- (role) [ondrejhome.ha-cluster-pacemaker](https://github.com/OndrejHome/ansible.ha-cluster-pacemaker)
- (role) [ondrejhome.ha-cluster-lvm](https://github.com/OndrejHome/ansible.ha-cluster-lvm)
- (modules) [ondrejhome.pcs-modules-2](https://github.com/OndrejHome/ansible.pcs-modules-2)
- (modules) [ondrejhome.crm_wait_for](https://github.com/OndrejHome/ansible.crm_wait_for)

### How to use the roles from this collection
Check the relevant README.md files for given roles that contains both the used parameters as well as example playbooks and inventories.

- [`ondrejhome.ha_cluster.pacemaker` playbook examples](roles/pacemaker/README.md#example-playbook)
- [`ondrejhome.ha_cluster.lvm` playbook examples](roles/lvm/README.md#example-playbook)

### How to use the modules from this collection
Check the relevant documentation pages for the modules or use `ansible-doc <module_name>` from command line to bring up list of supported attributes and examples of use for all modules.

~~~
# ansible-doc -l |grep ondrejhome
ondrejhome.ha_cluster.detect_pacemaker_cluster   detect facts about installed pacemaker cluster
ondrejhome.ha_cluster.pcs_auth                   Module for interacting with 'pcs auth'
ondrejhome.ha_cluster.pcs_cluster                wrapper module for 'pcs cluster setup/destroy/node add/node remove'
ondrejhome.ha_cluster.pcs_constraint_colocation  wrapper module for 'pcs constraint colocation'
ondrejhome.ha_cluster.pcs_constraint_location    wrapper module for 'pcs constraint location'
ondrejhome.ha_cluster.pcs_constraint_order       wrapper module for 'pcs constraint order'
ondrejhome.ha_cluster.pcs_property               wrapper module for 'pcs property'
ondrejhome.ha_cluster.pcs_quorum_qdevice         wrapper module for 'pcs quorum setup/destroy/change qdevice setting'
ondrejhome.ha_cluster.pcs_resource               wrapper module for 'pcs resource'
ondrejhome.ha_cluster.pcs_resource_defaults      wrapper module for 'pcs resource defaults' and 'pcs resource op defaults'
ondrejhome.ha_cluster.pcs_stonith_level          wrapper module for 'pcs stonith level'
~~~
