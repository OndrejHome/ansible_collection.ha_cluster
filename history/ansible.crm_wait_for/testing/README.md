## Manual testing of crm_wait_for
At present time all the below tests are done by hand after setting up clusters on various systems. 

**IMPORTANT:** It is expected that cluster can run resources when running tests - which means that they either have configure stonith devices or disabled stonith. Tests should not cause any fencing.

### Running tests
1. Prepare target cluster on which tests will run.

2. Install 2 ansible roles for using the tests.

       # ansible-galaxy install -p roles/ ondrejhome.pcs-modules-2 ondrejhome.crm_wait_for

3. Run the tests.

       # ansible -i test-cluster.hosts test_crm_wait_for.yaml; echo $?
       ...
       0

If the tests has finished with `0` exit code then inspect the outputs and compared them with existing tests in this directory to verify that outputs looks "similar" and in accordance to descriptions of tasks.
