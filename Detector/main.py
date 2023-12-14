import argparse
import logging as log
import os

from platformdirs import user_config_dir

from .find_objects import ImageCrawler
from .functions import RGB_question, float_question, manage_subfolders, read_config, take_webcam_image, yes_no_question


def dialog() -> (str, str, bool, float, int):
    """Ask the user to input parameters"""
    print("Welcome in software to automatics detect object in microscope.")
    print("Project webpage: https://github.com/dkriegner/micro-flakes/tree/main/Detector\nVersion: 0.1.1\n")

    # Load last working directory
    path = read_config()

    print(f"Working path: {path}")
    out2 = yes_no_question("Do you change the path?", False)
    if out2 == 1:
        # clear cache and write a new path
        path = input("New path: ")
        cache = open(user_config_dir("config_terminal", "flakes_detector"), 'w')
        cache.write(path)
        cache.close()
        print(f"Working path has set to {path}.")

    manage_subfolders(path)  # Clear old output files or make new folder (output)

    print("You can upload existing photo or take a new photo by webcam.")
    settings = yes_no_question("Do you upload existing photo?", True)

    if settings == 0:
        # Take a new photo by USB webcam.
        name = input("Write name of the new photo (with extension - jpg, bmp, ... ): ")
        take_webcam_image(path, name)
    else:
        # Open existing photo in the working directory.
        print("Files in input:")
        print(os.listdir(f"{path}/"))
        print("Write name of photo from microscope.")
        name = input(".../")
        while not os.path.exists(f"{path}/{name}") or name == "":  # check if the file exists
            log.warning("Error! The file doesn't exist.")
            name = input("input/")  # ask for a new input

    # Make output file after 1st iteration: marked pixel, found flakes and selected flakes with the centre of gravity.
    more_output = yes_no_question('Do you want to get image output after 1st iteration?', False)

    # Parameter to remove trash and noise
    min_size = float_question("Write minimal area of edge of object in um^2. Smaller object will be deleted", 42.4)
    min_size /= 1.6952  # convert size from micro meters to pixels

    # Parameter to mark pixel with a potential object.
    sensitivity = RGB_question("Write sensitivity of script on objects in dark field. Script will mark all"
                               "pixels with RGB values bigger than the user\'s input.", 40)

    return path, name, more_output, min_size, sensitivity


def line_command() -> (str, str, bool, float, int):
    # Load a set parameters via the command line
    parser = argparse.ArgumentParser()

    # add parameters
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
                        default=42.4,
                        help="Write minimal area of edge of object in um^2. Smaller object will be deleted. Default "
                             "is 42.4 um.",
                        type=float)
    parser.add_argument("-s", "--sensitivity",
                        default=40,
                        help="Write sensitivity of script on objects in dark field. Script will mark all pixels with "
                             "RGB values bigger than the user\'s input. Default is 40",
                        type=int)

    args = parser.parse_args()

    return args.path, args.name, args.out1, args.min_size/1.6952, args.sensitivity


def main():
    # Show info messages
    log.getLogger().setLevel(log.INFO)
    log.basicConfig(format='%(message)s')

    # Fixed setting parameters
    calibration = 0.187  # calibration factor to get real size of sample (converting from px to um)

    path, name, more_output, min_size, sensitivity = line_command()  # Try to read a line-command input.

    if path is None:  # If there is no parameter from command line
        # Print a welcome screen and ask user's inputs. This function can make a new image by a USB webcam.
        path, name, more_output, min_size, sensitivity = dialog()

    # Load an image, find all flakes and make a catalogue them.
    ImageCrawler(path, name, more_output, min_size, sensitivity, calibration)

    input("\nThe task has been finished. Press some key for close a script.")
