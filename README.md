# brf2ebrf

Library for converting BRF to eBRF.

## Status of EBRF support

As there is no published version of the EBRF standard, currently this tool is unable to produce files which are guaranteed to comply with the final EBRF specification. Once a EBRF specification is published this tool will then recieve updates to produce files to comply with that specification.

## Building and running

To build and run brf2ebrf you will need to install PDM. The PDM website is https://pdm.fming.dev and contains details of the various install methods.

Once PDM is installed you can run the brf2ebrf tests with the following command:
```commandline
pdm test
```
There is a basic command line script for demonstration purposes. To run the brf2ebrf script, you first need to install brf2ebrf with the following command:
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
