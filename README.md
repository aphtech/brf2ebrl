# brf2ebrf
Tool for converting BRF to eBRF.

## Building and running
To build and run brf2ebrf you will need to install PDM. The PDM website is https://pdm.fming.dev and contains details of the various install methods.

Once PDM is installed you can run the brf2ebrf tests with the following command:
```commandline
pdm test
```
To run the brf2ebrf script, you first need to install brf2ebrf with the following command:
```commandline
pdm install
```
Then you can run:
```commandline
pdm run brf2ebrf <brf> <output_file>
```
For details of uing the brf2ebrf command, do the following:
```commandline
pdm run brf2ebrf --help
```

## Building an installer
It is planned that for users there will be an installable version which will not require python or PDM to be installed on the system. At the moment this is still to be done.
