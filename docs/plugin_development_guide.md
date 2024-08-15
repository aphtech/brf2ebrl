# Plugin Development Guide

This document describes the process of developing a plugin for the BRF2EBRL library. A plugin will allow you to create custom parsers and bundlers. This should offer flexibility of the conversion process and the output produced.

## Defining a Plugin

A plugin is a Python module following a required naming convention and containing the correct attributes. As brf2ebrl is primarily a library it is for the application to define where it will look for plugins. The scripts in this project simply use the Python system path.

### Naming Convention

Plugins are Python modules or packages of the form `brf2ebrl_<plugin_name>`. This should be a top level package name. So for a plugin named `my_plugin` the base plugin package name should be `brf2ebrl_my_plugin`.

### The PLUGIN attribute

The main entry point for a plugin is the PLUGIN attribute within the plugin base package. The PLUGIN attribute should be an instance of `brf2ebrl.Plugin`.