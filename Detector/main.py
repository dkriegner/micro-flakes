from openpyxl import Workbook
import cv2
import os
import shutil
from .find_objects import find_objects
from .process_object import process_object


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


def check_bool(vs):
    # This function checks  input is an integer.
    vs = check_float(vs)
    while True:
        if vs == 0 or vs == 1:
            return int(vs)
        else:
            print("Error! Wrong value.")
            vs = input("Write 0 or 1: ")


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


def main():
    try:
        cache  = open(r"CACHE", "r")
    except:
        cache = open(r"CACHE", "w+")
    path = cache.read()
    cache.close()

    # Fixed setting parameters
    calibration = 0.187  # calibration factor to get real size of sample

    # Print a welcome screen and ask user's inputs
    print("Welcome in software to automatics detect object in microscope.")
    print("For default value write \"d\".\n")

    print(f"Working path: {path}")
    print("Do you change the path? ")
    out2 = check_bool(input("yes - 1, on - 0: "))
    if out2 == 1:
        path = input("New path: ")
        cache = open(r"CACHE", "w")
        cache.write(path)
        cache.close()
        print(f"Working path has set to {path}.")
    manage_subfolders(path)

    print("For take a new photo, write 0. For open a existing photo, write 1.")
    settings = check_bool(input("Write number: "))

    if settings == 0:
        name = input("Write name of the new photo: ")
        take_webcam_image(path, name)
        name += ".jpg"
    else:
        print("Files in input:")
        print(os.listdir(f"{path}/input/"))
        print("Write name of photo from microscope.")
        name = input("input/")
        while not os.path.exists(f"{path}/input/{name}"):  # check if the file exists
            print("Error! The file doesn't exist.")
            name = input("input/")  # ask for a new input

    print('Do you want to get image output after 1st iteration?')
    out1 = check_bool(input("yes - 1, on - 0: "))

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
        sensitivity = check_float(sensitivity)

    print("The first iteration:")
    anything = find_objects(path, name, out1, min_size, sensitivity)  # write coordinates of found objects from input

    print("The second iteration:")
    # Now, find objects from the first iteration in the same area in high resolution

    # Set area for finding object in high resolution
    candidates = []  # (x_min, x_max, y_min, y_max)
    for q in anything:
        x_min, x_max, y_min, y_max = (int(min(x for (x, y) in q)), int(max(x for (x, y) in q)),
                                      int(min(y for (x, y) in q)), int(max(y for (x, y) in q)))
        if (x_max - x_min) * (y_max - y_min) < 50000:
            candidates.append((x_min, x_max, y_min, y_max))

    workbook = Workbook()  # create MS Excel table

    sheet = workbook.active
    sheet["A1"] = "id"
    sheet["B1"] = "x (um)"
    sheet["C1"] = "y (um)"
    sheet["D1"] = "size (um^2)"
    sheet["E1"] = "transparency (%)"
    sheet["F1"] = "size ratio"
    sheet["G1"] = "photo"
    sheet["H1"] = "contourI"
    sheet["I1"] = "contourII"
    sheet["J1"] = "filter - contour"  # Does the object have a constant contour?  3,5 (3,7) - 5
    sheet["K1"] = "Value - bigger is better"
    sheet["L1"] = "filter - transparency"  # Is the object transparent?  >0,1 (0,08)
    sheet["M1"] = "Value - bigger is better"
    sheet["N1"] = "Bright"
    sheet["O1"] = "Height"

    # Make the same procedure as in the first iteration.
    print(f"processing of {len(candidates) - 1}")
    max_width = 0
    print("processed: ", end="")
    for q in range(1, len(candidates)):
        print(f"{q}, ", end="")
        width = process_object(path, candidates[q], min_size, q, calibration, workbook)
        # Process one object and write the width of the photo of the object for set width of the column in Excel table.
        if max_width < width:
            max_width = width

    sheet.column_dimensions['G'].width = max_width * 0.15
    workbook.save(f"{path}/output/Index_of_objects.xlsx")  # save Excel table

    input("\nThe task has been finished. Press some key for close a script.")
