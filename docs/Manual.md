# Manual

The script creates a folder in the working directory if it does not exist. The software supports all formats of images that are supported by the Pillow library (for example: jpg, png, bmp, and gif) and can also capture new images from a webcam. The new image is stored as jpg. After processing, the "output" folder will contain the processed files. The most important file is "Catalogue_(name_input_file).xlsx". It is an Excel table of lists the detected objects with their parameters.

## The terminal version
To start the software, open the executable file "flakes-detector". There is the file in the same path where Python is installed. After starting the script, you will be asked a few questions to set basic filters. You will set the working directory by the first answer. The software remembers the last directory. Then you will use an input photo or you will take a new photo by a webcam. The default value is in squared brackets. To use the value, press the enter key. If you take a new photo, you must write the name of a new image without extension.  Then a new widget opens with an actual video stream from a webcam. To take an image press the enter key. The next question is if you want to get image output after 1st iteration. It is useful for debugging. A user can see the steps of the process of the image in 1st iteration (marking light pixels, found objects, and area of objects). The processing time depends on the resolution of the input photo. For instance, a 5 MPx photo typically takes tens of seconds to process.

The script supports input from the command  line, for example:
```
Python3 script.py -p C:\Users\name\Documents\Test -n image1.png -o False -m 42.4 -s 40 -q False
```
`-p` is the path of the input image, `-n` is the name of the input image, `-o` is if you want output images (True or False), `-m` is the minimal area of edges of the object in um^2, `-s` is the sensitivity of script on objects in dark field and `-q` deactivates asking users in the end of process (for autotesting). For more information use `--help`.


## Graphical version
The input parameters are the same as in the terminal version. There are tooltips in the widget. It is necessary to select the input image or take a new image. The default values are prewritten. To find flakes in the image, press the "Start" button. The progress of processing and warning and error messages are written in the log box between the "Start" and "Open Catalogue" buttons. To open the output catalog, press the last button. It is active after processing of the image.
