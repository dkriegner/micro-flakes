ABOUT
This software, designed to automatically detect objects under a microscope, is a terminal application developed in Python. It was created by Jiri Zelenka for the Institute of Physics of the Czech Academy of Sciences. The software is optimized for Python 3.11.4 in MS Windows.

INSTALLATION
To run this software, Python 3 and the following libraries are required:
- PIL
- openpyxl
- cv2
- shutil
- numpy
To install, use following command:
pip install -r requirements.txt
It is necessary to have PIP in Python installed. To install, visit this webpage: https://pip.pypa.io/en/stable/installation/.

HOW IT WORKS
The root directory contains two folders. The "input" folder is for storing images to be processed. The software supports jpg and png formats and can also capture new images from a webcam. After processing, the "output" folder will contain the processed files. The most important file is "Index_of_objects.xlsx", an Excel table listing the detected objects along with their parameters.

USAGE
To start the software, open "main.py" in the root directory. You will be asked a few questions to set basic filters. The first question is if you will use an input photo of you will take a new photo by a webcam. The processing time depends on the resolution of the input photo. For instance, a 5 MPx photo typically takes tens of seconds to process.
