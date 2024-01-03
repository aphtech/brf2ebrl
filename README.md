# brf2ebrf

Library for converting BRF to eBRF.

## Status of EBRF support

As there is no published version of the EBRF standard, currently this tool is
unable to produce files which are guaranteed to comply with the final EBRF
specification. Once a EBRF specification is published this tool will then
receive updates to produce files to comply with that specification.

## Building and running

To build and run brf2ebrf you will need to install PDM. The PDM web site is https://pdm.fming.dev and contains details of the various install methods.

Once PDM is installed you can run the brf2ebrf tests with the following command:
```command line
pdm test
```
There is a basic command line script for demonstration purposes. To run the brf2ebrf script, you first need to install brf2ebrf with the following command:
```command line
pdm install
```
Then you can run:
```command line
pdm run brf2ebrf <brf> <output_file>
```
For details of using the brf2ebrf command, do the following:
```command line
pdm run brf2ebrf --help
```
