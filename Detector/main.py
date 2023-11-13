from openpyxl import Workbook
import cv2
import os
import shutil
from .find_objects import ImageCrawler
from .functions import take_webcam_image, float_question, RGB_question, manage_subfolders, read_cache, yes_no_question
import argparse

def dialog() -> (str, str, bool, float, int):
    '''Ask the user to input parameters'''
    print("Welcome in software to automatics detect object in microscope.")
    print("For default value write \"d\".\n")

    # Load last working directory
    path = read_cache()

    print(f"Working path: {path}")
    out2 = yes_no_question("Do you change the path?", False)
    if out2 == 1:
        # clear cache a write a new path
        path = input("New path: ")
        cache = open(r"CACHE", "w")
        cache.write(path)
        cache.close()
        print(f"Working path has set to {path}.")

    manage_subfolders(path) # Clear old output files or make new folder (input and output)

    print("You can upload existing photo or take a new photo by webcam.")
    settings = yes_no_question("Do you upload existing photo?", True)

    if settings == 0:
        # Take a new photo.
        name = input("Write name of the new photo: ")
        take_webcam_image(path, name)
        name += ".jpg"
    else:
        # Open existing photo in the working directory.
        print("Files in input:")
        print(os.listdir(f"{path}/input/"))
        print("Write name of photo from microscope.")
        name = input("input/")
        while not os.path.exists(f"{path}/input/{name}") or name == "":  # check if the file exists
            print("Error! The file doesn't exist.")
            name = input("input/")  # ask for a new input

    out1 = yes_no_question('Do you want to get image output after 1st iteration?', False)

    min_size = float_question("Write minimal area of edge of object in um^2. Smaller object will be deleted", 42.4)
    min_size /= 1.6952  # convert size from micro meters to pixels

    sensitivity = RGB_question("Write sensitivity of script on objects in dark field. Script will mark all pixels with RGB values bigger than the user\'s input.", 40)

    return path, name, out1, min_size, sensitivity

def line_command() -> (str, str, bool, float, int):
    # Load a set parameters via command line parameters
    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--path",
    nargs='?', const='Nothing',
    help="The path where input and output folder is or will be created.",
    type=str)
    parser.add_argument("-n", "--name",
    nargs='?', const='Nothing',
    help="The name of the input image",
    type=str)
    parser.add_argument("-o", "--out1",
    default=False,
    help="Do you want output images? Yes -> True, No -> False",
    type=bool)
    parser.add_argument("-m", "--min_size",
    default= 42.4/1.6952,
    help="Write minimal area of edge of object in um^2. Smaller object will be deleted. Default is 42.4 um.",
    type=float)
    parser.add_argument("-s", "--sensitivity",
    default=40,
    help="Write sensitivity of script on objects in dark field. Script will mark all pixels with RGB values bigger than the user\'s input. Default is 40",
    type=int)

    args = parser.parse_args()

    return args.path, args.name, args.out1, args.min_size, args.sensitivity

def main():
    # Fixed setting parameters
    calibration = 0.187  # calibration factor to get real size of sample

    path, name, out1, min_size, sensitivity = line_command() # Try to read a line-command input.

    if path == None:
        path, name, out1, min_size, sensitivity = dialog() # Print a welcome screen and ask user's inputs

    figure1 = ImageCrawler(path, name, out1, min_size, sensitivity, calibration)
    #print(figure1[0].size)

    input("\nThe task has been finished. Press some key for close a script.")

