# The detector of micro flakes

## About
This software, designed to automatically detect objects under a microscope with darkfield objectives, is a terminal application developed in Python. It was created by Jiri Zelenka and Dominik Kriegner for the Institute of Physics of the Czech Academy of Sciences. The software is optimized for Python 3.11.4 in MS Windows.

## How to works
The script creates two folders in the working directory if they do not exist. The "input" folder is for storing images to be processed. The software supports all formats of the image which is supported Pillow library (for example: jpg, png, bmp, and gif) and can also capture new images from a webcam. After processing, the "output" folder will contain the processed files. The most important file is "Catalogue_(name_input_file).xlsx". The Excel table lists the detected objects with their parameters.

## Inastallation
It is available a GUI and terminal version for MS Windows on https://github.com/dkriegner/micro-flakes/tags. There are non-instalable exe-files.

## Manual

## 