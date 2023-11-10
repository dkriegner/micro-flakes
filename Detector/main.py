from openpyxl import Workbook
import cv2
import os
import shutil
from .find_objects import Detect, Proces
import argparse


def take_webcam_image(path: str, filename: str):
    '''This function takes a photo with a webcam. The first parameter is the path of a new photo. The second parameter is the name of a new photo.'''
    cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
    # cap.set(14, 500) # gain
    # Turn off auto exposure
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
    # set exposure time
    cap.set(cv2.CAP_PROP_EXPOSURE, 0)
    # set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 5472)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 3648)
    # Check if the webcam is opened correctly
    if not cap.isOpened():
        raise IOError("Cannot open webcam")
    while True:
        ret, frame = cap.read()
        # cv2.normalize(frame, frame, 100, 255, cv2.NORM_MINMAX)
        # frame = cv2.resize(frame, None, fx=1, fy=1, interpolation=cv2.INTER_AREA)
        cv2.imshow('Input', frame)
        cv2.imwrite(filename=f'{path}/{filename}.jpg', img=frame)
        # print(frame)
        c = cv2.waitKey(1)
        if c == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    return None

def float_question(question: str, default: float | None = None) -> float:
    """get float answer for a question."""
    choices = f' [{default}]: ' if default else ':'
    reply = str(input(question + choices)).lower().strip() or default
    try:
        return float(reply)
    except (ValueError, TypeError):
        print("invalid input! try again")  # optional print message
        return float_question(question, default)

def RGB_question(question: int, default: int | None = None) -> int:
    """get integer answer between 0 and 255 for a question."""
    choices = f' [{default}]: ' if default else ':'
    reply = str(input(question + choices)).lower().strip() or default
    try:
        test = int(reply)
        if 0 <= test <= 255:
            return int(reply)
        else:
            print("invalid input! write integer between 0 and 255")  # optional print message
            return float_question(question, default)
    except (ValueError, TypeError):
        print("invalid input! try again")  # optional print message
        return float_question(question, default)

def manage_subfolders(path: str):
    '''create the output and input subfolder or clean the output subfolder'''
    path1 = path
    path2 = "output\\objects"
    if not os.path.exists(os.path.join(path1, "input")):
        os.makedirs(os.path.join(path1, "input"))
    if not os.path.exists(os.path.join(path1, "output")):
        os.makedirs(os.path.join(path1, "output"))
    if os.path.exists(os.path.join(path1, path2)):
        shutil.rmtree(os.path.join(path1, path2))
    os.makedirs(os.path.join(path1, path2))

def read_cache() -> str:
    '''Open existing a cache file or reate a new chache file.'''
    try:
        cache = open(r"CACHE", "r")
    except:
        cache = open(r"CACHE", "w+")
    path = cache.read()
    cache.close()
    return path

def yes_no_question(question: str, default: bool = True) -> bool:
    """get boolean answer for a question."""
    choices = ' [Y/n]: ' if default else ' [y/N]:'
    default_answer = 'y' if default else 'n'
    reply = str(input(question + choices)).lower().strip() or default_answer
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        print("invalid input! try again")  # optional print message
        return yes_no_question(question, default)


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
        while not os.path.exists(f"{path}/input/{name}"):  # check if the file exists
            print("Error! The file doesn't exist.")
            name = input("input/")  # ask for a new input

    out1 = yes_no_question('Do you want to get image output after 1st iteration?', False)

    min_size = float_question("Write minimal area of edge of object in um^2. Smaller object will be deleted", 42.4)
    min_size /= 1.6952  # convert size from micro meters to pixels

    sensitivity = RGB_question("Write sensitivity of script on objects in dark field. Script will mark all pixels with RGB values bigger than the user\'s input.", 40)

    return path, name, out1, min_size, sensitivity

def main():
    # Fixed setting parameters
    calibration = 0.187  # calibration factor to get real size of sample

    # Load a set parameters via command line parameters
    parser = argparse.ArgumentParser()

    parser.add_argument("path")
    parser.add_argument("name")
    parser.add_argument("out1")
    parser.add_argument("min_size")
    parser.add_argument("sensitivity")

    args = parser.parse_args()

    path, name, out1, min_size, sensitivity = (args.path, args.name, args.out1, args.min_size, args.sensitivity)

    if path == 0:
        path, name, out1, min_size, sensitivity = dialog() # Print a welcome screen and ask user's inputs

    print("The first iteration:")
    # Find objects in the photo in low resolution
    figure1 = Detect(path, name, out1, min_size, sensitivity, calibration)
    figure1.find_objects()  # find all object in the photo

    print("The second iteration:")
    # Now, find objects from the first iteration in the same area in high resolution

    # Set area for finding object in high resolution

    # Set area for finding object in high resolution
    index = 0
    for q in figure1.anything:
        x_min, x_max, y_min, y_max = (int(min(x for (x, y) in q)), int(max(x for (x, y) in q)),
                                      int(min(y for (x, y) in q)), int(max(y for (x, y) in q)))
        if (x_max - x_min) * (y_max - y_min) < 50000:
            globals()[f"flakes{index}"] = Proces(figure1.path, figure1.name, figure1.out1, figure1.min_size, figure1.sensitivity, figure1.calibration, index, (x_min, x_max, y_min, y_max))
        index += 1

    # Make the same procedure as in the first iteration.
    print(f"processing of {len(figure1.anything) - 1}")
    print("processed: ", end="")
    for q in range(1, len(figure1.anything)):
        print(f"{q}, ", end="")
        globals()[f"flakes{q}"].load_image()
        globals()[f"flakes{q}"].mark_object()
        globals()[f"flakes{q}"].measure()
        # Process one object and write the width of the photo of the object for set width of the column in Excel table.
    figure1.maketeble([globals()[f"flakes{index}"].size for index in range(len(figure1.anything))],
                      [globals()[f"flakes{index}"].full_size for index in range(len(figure1.anything))],
                      [globals()[f"flakes{index}"].size2 for index in range(len(figure1.anything))],
                      [globals()[f"flakes{index}"].full_size2 for index in range(len(figure1.anything))],
                      [globals()[f"flakes{index}"].centre for index in range(len(figure1.anything))],
                      [globals()[f"flakes{index}"].bright2 for index in range(len(figure1.anything))],
                      [globals()[f"flakes{index}"].width for index in range(len(figure1.anything))],
                      [globals()[f"flakes{index}"].hight for index in range(len(figure1.anything))]) # Finish and save the table.
    figure1.clean()
    input("\nThe task has been finished. Press some key for close a script.")

