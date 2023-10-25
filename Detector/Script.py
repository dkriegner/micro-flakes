from PIL import Image
from openpyxl import Workbook
from openpyxl.drawing.image import Image as Xl
import cv2
import os
import shutil
import numpy as np
from find_objects import find_objects
from process_object import gamma_correct, change_contrast

def take_webcam_image(filename):
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
        cv2.imwrite(filename=f'{filename}.jpg', img=frame)
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


def clean_output():
    # clean output folder
    path1 = os.path.dirname(__file__)
    path2 = "output\\objects"
    if os.path.exists(os.path.join(path1, path2)):
        shutil.rmtree(os.path.join(path1, path2))
    os.makedirs(os.path.join(path1, path2))


# Fixed setting parameters
calibration = 0.187  # calibration factor to get real size of sample

clean_output()
# Print a welcome screen and ask user's input
print("Welcome in software to automatics detect object in microscope.")
print("For default value write \"d\".\n")
print("For take a new photo, write 0. For open a existing photo, write 1.")
settings = check_bool(input("Write number: "))

if settings == 0:
    name = input("Write name of the new photo: ")
    take_webcam_image(name)
    name += ".jpg"
else:
    print("Files in input:")
    print(os.listdir("input/"))
    print("Write name of photo from microscope.")
    name = input("input/")
    while not os.path.exists(f"input/{name}"):  # check if the file exists
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
anything = find_objects(name, out1, min_size, sensitivity)  # write coordinates of found objects from input

print("The second iteration:")
# Now, find objects from the first iteration in the same area in high resolution

name2 = "object"  # name of photos of found objects

pim = Image.open(f'output/org_gc.png')  # open corrected original photo
org = pim.load()

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
print(f"processing of {len(candidates)}")
max_width = 0
print("processed: ", end="")
for q in range(1, len(candidates)):
    print(f"{q}, ", end="")
    nw = Image.new('RGB', (candidates[q][1] - candidates[q][0] + 8, candidates[q][3] - candidates[q][2] + 8),
                   color='white')  # vytvoreni noveho obrazku
    new = nw.load()
    ts = Image.new('RGB', (candidates[q][1] - candidates[q][0] + 8, candidates[q][3] - candidates[q][2] + 8),
                   color='white')  # vytvoreni noveho obrazku
    test = ts.load()

    detect2 = []
    bright2 = 0

    for i in range(candidates[q][0] - 4, candidates[q][1] + 4):
        for j in range(candidates[q][2] - 4, candidates[q][3] + 4):
            R, G, B = org[i, j]
            new[i - candidates[q][0] - 1 + 5, j - candidates[q][2] - 1 + 5] = org[i, j]
            bright2 += R + G + B
            if R > 80 or G > 80 or B > 80:
                org[i, j] = (256, 0, 0)
    nw.save(f'output/objects/{name2}_{q}.png')  # storage image q-th objects

    for i in range(candidates[q][0] - 4, candidates[q][1] - 1 + 4, 2):
        for j in range(candidates[q][2] - 4, candidates[q][3] - 1 + 4, 2):
            red = 0
            px = 0
            for k in range(i - 1, i + 1):
                for l in range(j - 1, j + 1):
                    if org[k, l] == (255, 0, 0):
                        red += 1
                    px += 1
            if px != 0:
                if red / float(px) > 0.6:
                    detect2.append((i, j))

    detect2 = np.array(detect2)

    anything2 = []

    i = 0
    while len(detect2) > 0:
        seed = detect2[0]
        queue = [seed]
        detect2 = np.delete(detect2, 0, axis=0)

        b = 1
        while b == 1:
            b = 0
            for (x, y) in detect2:
                dx_values = [2, -2, 0, 0, 2, -2, 2, -2]
                dy_values = [0, 0, 2, -2, 2, -2, -2, 2]

                for dx, dy in zip(dx_values, dy_values):
                    neighbor = (x + dx, y + dy)
                    mask = np.all(detect2 == neighbor, axis=1)
                    if np.any(mask):
                        queue.append(neighbor)
                        detect2 = detect2[~mask]
                        b = 1

        anything2.append(queue)
        i += 1

    j = 0
    for a in range(len(anything2)):
        if len(anything2[j]) <= min_size:
            anything2.remove(anything2[j])
            j -= 1
        j += 1

    index = 0
    if len(anything2) == 1:
        for n in range(len(anything2)):
            for (i, j) in anything2[n]:
                for k in range(i - 1, i + 1):
                    for l in range(j - 1, j + 1):
                        test[k - candidates[q][0] - 1 + 5, l - candidates[q][2] - 1 + 5] = (256, 0, 0)
    elif len(anything2) == 0:
        continue
    else:
        mx = max(len(x) for x in anything2)
        for n in range(len(anything2)):
            if len(anything2[n]) == mx:
                index = n
                for (i, j) in anything2[n]:
                    for k in range(i - 1, i + 1):
                        for l in range(j - 1, j + 1):
                            test[k - candidates[q][0] - 1 + 5, l - candidates[q][2] - 1 + 5] = (256, 0, 0)

    centre = ((int(sum(x for (x, y) in anything2[index]) / len(anything2[index])),
               int(sum(y for (x, y) in anything2[index]) / len(anything2[index]))))

    # mark shapes of image
    shape = Image.open(f'output/objects/{name2}_{q}.png')
    shape = gamma_correct(shape, 1.5)
    shape = change_contrast(shape, 100)
    shape.save(f'output/objects/processing0_{q}.png')

    shape = cv2.imread(f'output/objects/processing0_{q}.png')
    shape = cv2.cvtColor(shape, cv2.COLOR_BGR2RGB)
    shape = cv2.addWeighted(shape, 4, shape, 0, 0)
    shape = cv2.cvtColor(shape, cv2.COLOR_BGR2GRAY)
    shape = cv2.Canny(shape, 300, 100)
    cv2.imwrite(f'output/objects/processing_{q}.png', shape)

    prc = Image.open(f'output/objects/processing_{q}.png')  # open corrected original photo
    pc = prc.load()

    # calculate size of the object (new)
    size = 0
    full_size = 0

    x_min = x_max = 0
    for i in range(prc.size[0]):
        white = 0
        for j in range(prc.size[1]):
            W = pc[i, j]
            if W == 255 and white == 0:
                white = 1
                size += 1
                x_min = j
            elif W == 255 and white == 1:
                size += 1
                x_max = j
        full_size += (x_max - x_min)
        x_min = x_max = 0

    # calculate size of the object (old)
    size2 = 0
    full_size2 = 0

    x_min = x_max = 0
    for i in range(ts.size[0] - 3):
        red = 0
        for j in range(ts.size[1] - 3):
            R, G, B = test[i, j]
            if (R, G, B) == (255, 0, 0) and red == 0:
                red = 1
                size2 += 1
                x_min = j
            elif (R, G, B) == (255, 0, 0) and red == 1:
                size2 += 1
                x_max = j
        full_size2 += (x_max - x_min)
        x_min = x_max = 0

    ts.save(f'output/objects/{name2}2_{q}.png')  # store photo of area of detect object

    # fill Excel table
    img = Xl(f'output/objects/{name2}_{q}.png')
    sheet.add_image(img, f'G{q + 1}')
    img2 = Image.open(f'output/objects/{name2}_{q}.png')
    sheet.row_dimensions[q + 1].height = img2.height * 0.8
    if max_width < img2.width:
        max_width = img2.width
    sheet[f"A{q + 1}"] = q
    sheet[f"B{q + 1}"] = centre[0] * calibration
    sheet[f"C{q + 1}"] = centre[1] * calibration
    sheet[f"D{q + 1}"] = full_size2 * calibration ** 2
    sheet[f"E{q + 1}"] = 1 - size2 / full_size2
    sheet[f"F{q + 1}"] = max(((-size2 - (size2 ** 2 - 16 * full_size2) ** 0.5) / 4) / (
                4 * full_size2 / (-size2 - (size2 ** 2 - 16 * full_size2) ** 0.5)),
                             (4 * full_size2 / (-size2 - (size2 ** 2 - 16 * full_size2) ** 0.5)) / (
                                         (-size2 - (size2 ** 2 - 16 * full_size2) ** 0.5) / 4))
    sheet[f"H{q + 1}"] = size
    sheet[f"I{q + 1}"] = full_size
    if 3.5 < full_size / size < 5:
        sheet[f"J{q + 1}"] = "OK"
        sheet[f"K{q + 1}"] = abs(full_size / size - (3.5 + 5) / 2)
    else:
        sheet[f"J{q + 1}"] = "NO"
    if 0.08 < 1 - size2 / full_size2:
        sheet[f"L{q + 1}"] = "OK"
        sheet[f"M{q + 1}"] = abs(1 - size2 / full_size2) - 0.08
    else:
        sheet[f"L{q + 1}"] = "NO"

    sheet[f"N{q + 1}"] = bright2 / size2
    sheet[f"O{q + 1}"] = 20 * bright2 / size2 - 6940

sheet.column_dimensions['G'].width = max_width * 0.15
workbook.save("output/Index_of_objects.xlsx")  # save Excel table
