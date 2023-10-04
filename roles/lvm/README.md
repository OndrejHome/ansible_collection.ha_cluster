ondrejhome.ha_cluster.lvm
=========

Role for enabling Highly Available LVM (HA-LVM) configuration in pacemaker cluster.
This role can also create LVs and VGs for both tagging and clvm variant, check the examples to see how.

Requirements
------------

RHEL: It is expected that machines will already be registered and subscribed for access to 'High Availability' or 'Resilient storage' channels.

Role Variables
--------------

  - type of HA-LVM:
     - (EL6, EL7) possible options are 'tagging' or 'clvm'
     - (EL8, EL9) possible options are 'systemid' or 'lvmlockd'
     - default is 'tagging'
  
    ```
    halvmtype: 'tagging'
    ```

  - (optional) - this is applied only when 'tagging' mode is selected. List of VGs that should be included in 'volume_list' additionally to VG on which root filesystem resides. By default this list is empty, below example shows how to specify the list of VGs.
  
    ```
    local_vg_list: [ 'vg1', 'vg2' ]
    ```

  - (RHEL only) enable the repositories containing needed packages:
      - on RHEL6 enable `rhel-rs-for-rhel-6-server-rpms`
      - on RHEL7 enable `rhel-rs-for-rhel-7-server-rpms`
      - on RHEL8 enable `rhel-8-for-x86_64-resilientstorage-rpms`
      - on RHEL9 enable `rhel-9-for-x86_64-resilientstorage-rpms`
    ```
    enable_repos: true
    ```

  - (RHEL only) enable the extended update (EUS) repositories containing needed packages:
      - on RHEL6 enable `rhel-rs-for-rhel-6-server-eus-rpms`
      - on RHEL7 enable `rhel-rs-for-rhel-7-server-eus-rpms`
      - on RHEL8 enable `rhel-8-for-x86_64-resilientstorage-eus-rpms`
      - on RHEL9 enable `rhel-9-for-x86_64-resilientstorage-eus-rpms`
    ```
    enable_eus_repos: false
    ```


Example Playbook
----------------

Example playbook for tagging HA-LVM.

    - hosts: servers
      roles:
         - { role: 'ondrejhome.ha_cluster.lvm' }

Example playbook for tagging HA-LVM with extra local VG names 'vg_local'.

    - hosts: servers
      roles:
         - { role: 'ondrejhome.ha_cluster.lvm', local_vg_list: [ 'vg_local' ] }

Example playbook for clvm variant of HA-LVM.

    - hosts: servers
      roles:
         - { role: 'ondrejhome.ha_cluster.lvm', halvmtype: 'clvm' }

Example playbook for systemid variant of HA-LVM.

    - hosts: servers
      roles:
         - { role: 'ondrejhome.ha_cluster.lvm', halvmtype: 'systemid' }

Example playbook for lvmlockd variant of HA-LVM.

    - hosts: servers
      roles:
         - { role: 'ondrejhome.ha_cluster.lvm', halvmtype: 'lvmlockd' }

Example of playbook for tagged variant with one VG and one LV on whole VG.

    - hosts: servers
      vars:
        tagging_vgs:
          - name: 'vg_shared'
            pvs: '/dev/sdb'
            lvs:
              - name: 'lv_name5'
                size: '200M'
      roles:
         - { role: 'ondrejhome.ha_cluster.lvm' }


Example playbook for clvm variant combined with tagging variant and creation of VGs/LVs for both clustered and tagging VGs.

    - hosts: servers
      vars:
        local_vg_list:
          - 'vg_clvm'
        clvm_vgs:
          - name: 'vg_clvm'
            pvs: '/dev/sdb2'
            lvs:
              - name: 'lv_name1'
                size: '200M'
              - name: 'lv_name2'
                size: '100M'
        tagging_vgs:
          - name: 'vg_shared'
            pvs: '/dev/sdb1'
            lvs:
              - name: 'lv_name3'
                size: '200M'
              - name: 'lv_name4'
                size: '100M'
      roles:
         - { role: 'ondrejhome.ha_cluster.lvm', halvmtype: 'clvm' }

Example of playbook for systemid variant with one VG and one LV on whole VG.

    - hosts: servers
      vars:
        systemid_vgs:
          - name: 'vg_systemid'
            pvs: '/dev/sdb'
            lvs:
              - name: 'lv_name5'
                size: '200M'
      roles:
         - { role: 'ondrejhome.ha_cluster.lvm', halvmtype: 'systemid' }

Example of playbook for systemid variant with one VG and one LV on whole VG.

    - hosts: servers
      vars:
        lvmlockd_vgs:
          - name: 'vg_lvmlockd'
            pvs: '/dev/sdb'
            lvs:
              - name: 'lv_name6'
                size: '200M'
      roles:
         - { role: 'ondrejhome.ha_cluster.lvm', halvmtype: 'lvmlockd' }

License
-------

GPLv3

Author Information
------------------

This role was manually tested on limited number of platforms and may not cover all corner cases.

- 2022-09 tested on: RHEL 8.2/8.6/9.0, AlmaLinux 8.6/9.0 with systemid approach
- 2022-10 tested on: CentOS 6.10, RHEL 6.10 with tagging and clvm approach

To get in touch with author you can use email ondrej-xa2iel8u@famera.cz or create a issue on github when requesting some feature.
