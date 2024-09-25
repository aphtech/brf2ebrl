# brf2ebrl

Library for converting BRF to eBraille.

## Status of eBraille support

As there is no published version of the eBraille standard, currently this tool is
unable to produce files which are guaranteed to comply with the final eBraille
specification. Once a eBraille specification is published this tool will then
receive updates to produce files to comply with that specification.

## Building and running

To build and run brf2ebrl you will need to install PDM. The PDM web site is https://pdm.fming.dev and contains details of the various install methods.

Once PDM is installed you can run the brf2ebrl tests with the following command:
```command line
pdm test
```
There is a basic command line script for demonstration purposes. To run the brf2ebrl script, you first need to install brf2ebrl with the following command:
```command line
pdm install
```
Then you can run:
```command line
pdm run brf2ebrl -o  <output_file> <brf>
```
For details of using the brf2ebrl command, do the following:
```command line
pdm run brf2ebrl --help
```
To create a stand alone executable of the command line tool run:
```command line
pdm build_exe
```
You will find a subdirectory named brf2ebrl.dist will be created containing the executable.