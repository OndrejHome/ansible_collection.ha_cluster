## ondrejhome.ha_cluster collection
Ansible collection for deploying and configuring HA clusters based on pacemker.

This Ansible collection is based on code from following standalone roles:

- (role) [ondrejhome.ha-cluster-pacemaker](https://github.com/OndrejHome/ansible.ha-cluster-pacemaker)
- (role) [ondrejhome.ha-cluster-lvm](https://github.com/OndrejHome/ansible.ha-cluster-lvm)
- (modules) [ondrejhome.pcs-modules-2](https://github.com/OndrejHome/ansible.pcs-modules-2)
- (modules) [ondrejhome.crm_wait_for](https://github.com/OndrejHome/ansible.crm_wait_for)

### How to use the roles from this collection
Check the relevant README.md files for given roles that contains both the used parameters as well as example playbooks and inventories.

- [`ondrejhome.ha_cluster.pacemaker` playbook examples](https://github.com/OndrejHome/ansible_collection.ha_cluster/blob/master/roles/pacemaker/README.md#example-playbook)
- [`ondrejhome.ha_cluster.lvm` playbook examples](https://github.com/OndrejHome/ansible_collection.ha_cluster/blob/master/roles/lvm/README.md#example-playbook)

### To use this collection from regular ansible
When connected to Internet (online) use command below (dependencies will be installed automatically):
~~~
# ansible-galaxy collection install ondrejhome.ha_cluster
~~~
When not connected to Internet (offline), first download the tarball of collection and its [dependencies](https://galaxy.ansible.com/ui/repo/published/community/general/dependencies/). Then install tarballs of dependencies and this collection on system:
~~~
# ansible-galaxy collection install ansible-posix-1.5.4.tar.gz
# ansible-galaxy collection install community-general-7.0.1.tar.gz
# ansible-galaxy collection install ondrejhome-ha_cluster-1.0.0.tar.gz
~~~

### To use this collection from AWX
You can either include content of this collection in your project or make sure that your project contains file `collections/requirements.yml` that specifies the `ondrejhome.ha_cluster` collection. Example of `collections/requirements.yml`:
~~~
# cat collections/requirements.yml
---
collections:
- ondrejhome.ha_cluster
~~~

### How to use the modules from this collection
Check the relevant documentation pages for the modules or use `ansible-doc <module_name>` from command line to bring up list of supported attributes and examples of use for all modules.

For example to check information on `ondrejhome.ha_cluster.pcs_resource`:

- from CLI (when collection is installed) - `ansible-doc ondrejhome.ha_cluster.pcs_resource`
- via browser - check the [Contents](https://galaxy.ansible.com/ui/repo/published/ondrejhome/ha_cluster/content/) of this collection and click on [`pcs_resource` module](https://galaxy.ansible.com/ui/repo/published/ondrejhome/ha_cluster/content/module/pcs_resource/).

### Reporting issues
You can report issue via [Github Issues page](https://github.com/OndrejHome/ansible_collection.ha_cluster/issues) or via email `ondrej-xa2iel8u@famera.cz`. When reporting issues please include following information in your report:

- your ansible version - `ansible --version`
- version of installed `ondrejhome.ha_cluster` collection and its dependencies - `ansible-galaxy collection list |grep -E 'ansible.posix|community.general|ondrejhome.ha_cluster'`
- (if possible) playbook that triggered error/issue
- expected outcome and observed outcome - for example "playbook failed with error XYZ when I used option ABC", "playbook finished without errors but service XYZ was not enabled", ...

### Contributing new functionality to collection
At this moment the contributions are accepted only in the standalone roles below and then once  accepted there, they will appear in this collection:

- (role) [`ondrejhome.ha-cluster-pacemaker` Pull requests](https://github.com/OndrejHome/ansible.ha-cluster-pacemaker/pulls)
- (role) [`ondrejhome.ha-cluster-lvm` Pull requests](https://github.com/OndrejHome/ansible.ha-cluster-lvm/pulls)
- (modules) [`ondrejhome.pcs-modules-2` Pull requests](https://github.com/OndrejHome/ansible.pcs-modules-2/pulls)
- (modules) [`ondrejhome.crm_wait_for` Pull requests](https://github.com/OndrejHome/ansible.crm_wait_for/pulls)

If you would like to contribute something that doesn't make sense for standalone roles and only makes sense for collection, then first open the Issue for collection repository.
