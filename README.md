# azcam-bluechan

## Purpose

This repository contains the *azcam-bluechan* *azcam* environment.  It contains the code and data files for the MMTO Spectrograph Blue Channel camera system.

## Installation

Download the code (usually into the *azcam* root folder such as `c:\azcam`) and install.

```shell
cd /azcam
git clone https://github.com/mplesser/azcam-bluechan
cd azcam-bluechan
pip install -e .
```
 
# Notes

## System Setup
- install Windows 10 and do updates

### Install python
- Download and install VS Code with GIT (notpad as editor)
- install python to c:\python3x (e.g. c:\python39)

### Install azcam
- create and cd to c:\azcam
- git clone https://github.com/mplesser/azcam-bluechan
- git clone https://github.com/mplesser/azcam-tool
- git clone https://github.com/mplesser/azcam-ds9-winsupport

- [copy or] git clone https://github.com/mplesser/motoroladsptools

- pip install -e .\azcam-bluechan

- install Labview 2014 runtime for azcam-tool
- install SAO ds9
- install and start xpans and nssm from azcam-ds9-winsupport

### If PC is a controller server
- install ARC Win10 PCI card driver
- install and configure controller server

### update powershell
- winget install --id=Microsoft.PowerShell -e

