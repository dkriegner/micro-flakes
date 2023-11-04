from openpyxl import Workbook
import cv2
import os
import shutil
from find_objects import Flakes


def take_webcam_image(path, filename):
    # This function takes a photo by webcam.
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
    return 0


def check_float(vs):
    # This function checks  input is a float.
    while True:
        try:
            vs = float(vs)
            return vs
        except:
            print("Error! Wrong value.")
        vs = input("Write float number: ")


def check_int(vs, min, max):
    # This function checks  input is an integer.
    vs = check_float(vs)
    while True:
        if vs >= min or vs <= max:
            return int(vs)
        else:
            print("Error! Wrong value.")
            vs = input(f"Write integer between {min} and {max}: ")


def manage_subfolders(path):
    # clean output folder
    path1 = path
    path2 = "output\\objects"
    if not os.path.exists(os.path.join(path1, "input")):
        os.makedirs(os.path.join(path1, "input"))
    if not os.path.exists(os.path.join(path1, "output")):
        os.makedirs(os.path.join(path1, "output"))
    if os.path.exists(os.path.join(path1, path2)):
        shutil.rmtree(os.path.join(path1, path2))
    os.makedirs(os.path.join(path1, path2))

def read_cache():
    # Open existing a cache file or reate a new chache file.
    try:
        cache = open(r"CACHE", "r")
    except:
        cache = open(r"CACHE", "w+")
    path = cache.read()
    cache.close()
    return path

def main():
    # Load last working directory
    path = read_cache()

    # Fixed setting parameters
    calibration = 0.187  # calibration factor to get real size of sample

    # Print a welcome screen and ask user's inputs
    print("Welcome in software to automatics detect object in microscope.")
    print("For default value write \"d\".\n")

    print(f"Working path: {path}")
    print("Do you change the path? ")
    out2 = check_int(input("no - 0, yes - 1: "), 0, 1)
    if out2 == 1:
        path = input("New path: ")
        cache = open(r"CACHE", "w")
        cache.write(path)
        cache.close()
        print(f"Working path has set to {path}.")
    manage_subfolders(path)

    print("For take a new photo, write 0. For open a existing photo, write 1.")
    settings = check_int(input("Write number: "), 0, 1)

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

    print('Do you want to get image output after 1st iteration?')
    out1 = check_int(input("no - 0, yes - 1: "), 0, 1)

    print('Write minimal area of edge of object. Smaller object will be deleted. Default: 42.4 um^2')
    min_size = input("size = ")
    if min_size == "d":
        min_size = 25  # size in pixels
    else:
        min_size = check_float(min_size) / 1.6952  # convert size from micro meters to pixels

    print('Write sensitivity of script on objects in dark field. Script will mark all pixels with RGB values bigger than the user\'s input. Default: 40')
    sensitivity = input("size = ")
    if sensitivity == "d":
        sensitivity = 40
    else:
        sensitivity = check_int(sensitivity, 0, 255)

    print("The first iteration:")
    # Find objects in the photo in low resolution
    figure1 = Flakes(path, name, out1, min_size, sensitivity, calibration)
    figure1.find_objects()  # find all object in the photo

    print("The second iteration:")
    # Now, find objects from the first iteration in the same area in high resolution

    figure1.candidate() # Set area for finding object in high resolution

    figure1.prepareteble() # create MS Excel table

    # Make the same procedure as in the first iteration.
    print(f"processing of {len(figure1.candidates) - 1}")
    print("processed: ", end="")
    for q in range(1, len(figure1.candidates)):
        print(f"{q}, ", end="")
        figure1.process_object(q)
        # Process one object and write the width of the photo of the object for set width of the column in Excel table.

    figure1.finishtable() # Finish and save the table.

    input("\nThe task has been finished. Press some key for close a script.")

main()
