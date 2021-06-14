# AWS Channel Assembly BreakPoint Validator

## Overview
AWS MediaTailor Channel Assembly supports inserting ad content inside program assets in the channel timeline. However, there is a caveat that the value specified by the operator for the desired ad break must align with segment boundaries from all media representations/renditions. The tolerance for the value entered is +/- 100ms. This script is designed to check the manifest against your desired breakpoints, and then return will actual values you can use that are as close as possible to what you intended.

This Python script accepts input from a user for:
* Manifest URL
* Desired BreakPoints (seconds) *comma delimited*

The script then iterates through the manifest to check if the desired breakpoint is suitable across all video, audio, and subtitle renditions.

### Limitations
* This script is intended for MPEG DASH assets only
* Segment Timeline is expected to be a child element of Representations.
* Segment Timescale is expected to be an attribute inside of Representations element.

## Dependencies
You will need Python 3.7 or 3.9 to run this script. Find out how to install/upgrade Python for your platform [here](https://www.python.org/)

This script utilizes the follow Python packages:
* requests
* re (regex)
* json
* logging
* xmltodict

To install REQUESTS module and XMLTODICT module, you'll need to install them via pip. 
* How to [install](https://pip.pypa.io/en/stable/installing/) PIP
* How to install [requests](https://pypi.org/project/requests/) module
* How to install [xmltodict](https://pypi.org/project/xmltodict/) module

It has been validated to run on Python version 3.7 and 3.9

## How to use
Copy the script to your Python environment and make sure the required packages are installed and available.

Run the script from the CLI like so:
``` 
$ python breakpoint_checker.py
```

You will be prompted to enter the manifest URL and desired breakpoints. Each input will need to be confirmed by the operator, then a series of checks are performed to make sure the values received are valid.

The script will attempt to get the DASH Manifest from the location specified, then it will try to align segment boundaries from all renditions to the desired breakpoints.

The script will exit with errors if there are any, otherwise it will print a list of breakpoints in milliseconds that can be used in Channel Assembly.

Here's an example of the prompts and message prints you will see when running the script:
```
Please enter the location of the DASH manifest:https://mediapackage-vod.us-west-2.amazonaws.com/12345/dash.mpd

You entered https://mediapackage-vod.us-west-2.amazonaws.com/12345/dash.mpd for the manifest location, is this correct? [Y,N]y

Enter your desired breakpoints, in seconds. Separated by comma's. IE: 30,60,90,150,240 :15,30,90,120

You entered 15,30,90,120 for the desired breakpoints, is this correct? [Y,N]y

```

A series of INFO messages will then be displayed at the script iterates through the DASH manifest. At the end, if all is well you will see an INFO message similar to the below:

```
2021-06-10 12:58:53,814 - root - INFO - SCRIPT RUN COMPLETE: Please use these breakpoints for your asset : [18108, 30120, 60150, 90180]
```