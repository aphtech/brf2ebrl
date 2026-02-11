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

## Contributing

If you would like to contribute code to the project, please create an issue on GitHub first explaining what you would like to change and why. This will give an opportunity for your idea to be discussed, for us to get a feeling of how much demand there is for what you propose and to be able to give feedback on how it may be done. Having these discussions prior to pull requests being submitted is likely to increase the chance your contribution will be accepted.