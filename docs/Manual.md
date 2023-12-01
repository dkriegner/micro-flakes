# Manual

## The erminal version
To start the software, open the executable file "flakes-detector". There is the file in the same path where Python is installed. After starting the script, you will be asked a few questions to set basic filters. You will set the working directory by the first answer. The software remembers the last directory. Then you will use an input photo or you will take a new photo by a webcam. The processing time depends on the resolution of the input photo. For instance, a 5 MPx photo typically takes tens of seconds to process.

The script supports input from the command  line, for example:
```
Python3 script.py -p C:\Users\name\Documents\Test -n image1.png -o False -m 42.4 -s 40
```
`-p` is the path of the input image, `-n` is the name of the input image, `-o` is if you want output images (True or False), `-m` is the minimal area of edges of the object in um^2 and `-s` is the sensitivity of script on objects in dark field. For more information use `--help`.

## Graphical version