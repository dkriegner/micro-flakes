from PIL import Image, ImageDraw
from openpyxl import Workbook
from openpyxl.drawing.image import Image as Xl
import cv2
import os
import shutil
import numpy as np


def photo(photoname):
    cap = cv2.VideoCapture(0, cv2.CAP_MSMF)

    # cap.set(14, 500) # gain
    # Turn off auto exposure
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
    # set exposure time
    cap.set(cv2.CAP_PROP_EXPOSURE, 0)

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
        cv2.imwrite(filename=f'{photoname}.jpg', img=frame)
        # print(frame)

        c = cv2.waitKey(1)
        if c == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    return 0

def checkf(vs):
    while 1:
        try:
            vs = float(vs)
            return vs
        except:
            print("Error! Wrong value.")
        vs = input("Write float number: ")

def gamma_correct(im, gamma):
    gamma1 = gamma
    row = im.size[0]
    col = im.size[1]
    result_img1 = Image.new(mode="RGB", size=(row, col), color=0)
    for x in range(row):
        for y in range(col):
            r = pow(im.getpixel((x, y))[0] / 255, (1 / gamma1)) * 255
            g = pow(im.getpixel((x, y))[1] / 255, (1 / gamma1)) * 255
            b = pow(im.getpixel((x, y))[2] / 255, (1 / gamma1)) * 255
            color = (int(r), int(g), int(b))
            result_img1.putpixel((x, y), color)
    return result_img1

def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))
    def contrast(c):
        return 128 + factor * (c - 128)
    return img.point(contrast)

# clean output folder
if os.path.exists(os.path.abspath(os.getcwd())+"\\output\\objects"):
    shutil.rmtree(os.path.abspath(os.getcwd())+"\\output\\objects")
os.makedirs(os.path.abspath(os.getcwd())+"\\output\\objects")

print("Welcome in software to automatics detect object in microscope.")
print("For default value write \"d\".\n")
print("For take a new photo, write 0. For open a existing photo, write 1.")
settings = checkf(input("Write number: "))

if settings == 0:
    name = input("Write name of the new photo: ")
    photo(name)
    name += ".jpg"
elif settings == 1:
    print("Files in input:")
    print(os.listdir("input/"))
    print("Write name of photo from microscope.")
    name = input("input/")
    while not os.path.exists(f"input/{name}"):  # check if the file exists
        print("Error! The file doesn't exist.")
        name = input("input/")  # ask for a new input
    pim = Image.open(f"input/{name}")  # open the original photo
    print("The photo has been opened.")
else:
    print("Error!")

print('Do you want to get image output after 1st iteration? Default: No')
out1 = input("yes - 1, on - 0: ")
if out1 == "d":
    out1 = 0
else:
    out1 = checkf(out1)

print('Write minimal area of edge of object. Smaller object will be deleted. Default: 42.4 um^2')
min_size = input("size = ")
if min_size == "d":
    min_size = 25
else:
    min_size = checkf(min_size)/1.6952

print("The first iteration:")
print("changing gamma and contrast of the original photo")
#pim = gamma_correct(pim, 1.5)
#pim = change_contrast(pim, 100)
pim.save(f"output/org_gc.png")  # save the original photo with gamma and contrast correction
pro = pim.load()

# create new images for processing (object area in low resolution)
nw = Image.new('RGB', (pim.size[0], pim.size[1]), color = 'white')
new = nw.load()

detect = []  # coordinates of detected object area

print("marking non-black area")
for i in range(pim.size[0]-1):
    for j in range(pim.size[1]-1):
        R, G, B = pro[i, j]
        if R > 40 or G > 40 or B > 40:
            pro[i, j] = (255, 0, 0)

print("finding object area")
for i in range(3, pim.size[0]-4, 6):
    for j in range(3, pim.size[1]-4, 6):
            red = 0  # number of red pixels
            px = 0  # number of all pixels
            for k in range(i-3, i+3):
                for l in range(j-3, j+3):
                    if pro[k, l] == (255, 0, 0):
                        red += 1
                    px += 1
            if px != 0:
                if red/float(px) > 0.6:
                    for k in range(i-3, i+3):
                        for l in range(j-3, j+3):
                            new[k, l] = (255, 0, 0)
                    detect.append((i, j))

print("finding whole objects")

detect = np.array(detect)

anything = []  # detected whole objects

while len(detect) > 0:  # find neighbor marked pixel
    seed = detect[0]
    queue = [seed]
    detect = detect[1:]

    i = 0
    while i < len(queue):
        x, y = queue[i]
        for dx in [-6, 0, 6]:
            for dy in [-6, 0, 6]:
                if (dx == 0 and dy == 0) or (dx != 0 and dy != 0):
                    continue
                neighbor = (x + dx, y + dy)
                mask = np.all(detect == neighbor, axis=1)
                if np.any(mask):
                    queue.append(neighbor)
                    detect = detect[~mask]

        i += 1

    anything.append(queue)

print("deleting too small object")
j = 0
for q in range(len(anything)):
    if len(anything[j]) <= min_size:
        anything.remove(anything[j])
        j -= 1
    j += 1

# create output photo of detected object with centres and area of detected edges
if out1 == 1:

    ts = Image.new('RGB', (pim.size[0], pim.size[1]), color='white')
    test = ts.load()

    for n in range(len(anything)):
        for (i, j) in anything[n]:
            for k in range(i-3, i+3):
                for l in range(j-3, j+3):
                    test[k,l] = (256, 0, 0)


    centre = []
    for q in range(len(anything)):
        centre.append((int(sum(x for (x, y) in anything[q])/len(anything[q])), int(sum(y for (x, y) in anything[q])/len(anything[q]))))

    p=0
    for (i, j) in centre:
        ImageDraw.Draw(ts).text((i+5, j+5), str(len(anything[p])), (0, 0, 0))
        for k in range(i-5, i+5):
            for l in range(j-5, j+5):
                test[k,l] = (0, 0, 0)
        p+=1

    name = "first_step"  # name output files of the first iteration
    ts.save(f'output/{name}_1.png')  # store detected objects with centre and size of edge
    pim.save(f'output/{name}_2.png')  # store marked object area
    nw.save(f'output/{name}_3.png')  # store object area in low resolution
    ts.close()
    pim.close()
    nw.close()

print("The second iteration:")
# Now, find objects from the first iteration in the same area in high resolution

name2 = "object"  # name of photos of found objects

pim = Image.open(f'output/org_gc.png')  # open corrected original photo
org = pim.load()

# Set area for finding object in high resolution
candidates = []  # (x_min, x_max, y_min, y_max)
for q in range(len(anything)):
    x_min, x_max, y_min, y_max = (int(min(x for (x, y) in anything[q])), int(max(x for (x, y) in anything[q])), int(min(y for (x, y) in anything[q])), int(max(y for (x, y) in anything[q])))
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
    nw = Image.new('RGB', (candidates[q][1]-candidates[q][0]+8, candidates[q][3]-candidates[q][2]+8), color = 'white') #vytvoreni noveho obrazku
    new = nw.load()
    ts = Image.new('RGB', (candidates[q][1]-candidates[q][0]+8, candidates[q][3]-candidates[q][2]+8), color = 'white') #vytvoreni noveho obrazku
    test = ts.load()

    detect2 = []
    bright2 = 0

    for i in range(candidates[q][0]-4, candidates[q][1]+4):
        for j in range(candidates[q][2]-4, candidates[q][3]+4):
            R, G, B = org[i, j]
            new[i - candidates[q][0] - 1+5, j - candidates[q][2] - 1+5] = org[i,j]
            bright2 += R + G + B
            if R > 80 or G > 80 or B > 80:
                org[i, j] = (256, 0, 0)
    nw.save(f'output/objects/{name2}_{q}.png')  # storage image q-th objects

    for i in range(candidates[q][0]-4, candidates[q][1]-1+4, 2):
        for j in range(candidates[q][2]-4, candidates[q][3]-1+4, 2):
            red = 0
            px = 0
            for k in range(i - 1, i + 1):
                for l in range(j - 1, j + 1):
                    if org[k, l] == (255,0,0):
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
                    for k in range(i-1, i+1):
                        for l in range(j-1, j+1):
                            test[k-candidates[q][0]-1+5, l-candidates[q][2]-1+5] = (256, 0, 0)



    centre = ((int(sum(x for (x, y) in anything2[index])/len(anything2[index])), int(sum(y for (x, y) in anything2[index])/len(anything2[index]))))

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
        full_size += (x_max-x_min)
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
        full_size2 += (x_max-x_min)
        x_min = x_max = 0

    ts.save(f'output/objects/{name2}2_{q}.png')  # store photo of area of detect object

    # fill Excel table
    img = Xl(f'output/objects/{name2}_{q}.png')
    sheet.add_image(img, f'G{q + 1}')
    img2 = Image.open(f'output/objects/{name2}_{q}.png')
    sheet.row_dimensions[q+1].height = img2.height * 0.8
    if max_width < img2.width:
        max_width = img2.width
    sheet[f"A{q+1}"] = q
    sheet[f"B{q+1}"] = centre[0]*0.187
    sheet[f"C{q + 1}"] = centre[1]*0.187
    sheet[f"D{q+1}"] = full_size2**0.187**2
    sheet[f"E{q+1}"] = 1 - size2/full_size2
    sheet[f"F{q+1}"] = max(((-size2-(size2**2-16*full_size2)**0.5)/4)/(4*full_size2/(-size2-(size2**2-16*full_size2)**0.5)), (4*full_size2/(-size2-(size2**2-16*full_size2)**0.5))/((-size2-(size2**2-16*full_size2)**0.5)/4))
    sheet[f"H{q + 1}"] = size
    sheet[f"I{q + 1}"] = full_size
    if 3.5 < full_size / size < 5:
        sheet[f"J{q + 1}"] = "OK"
        sheet[f"K{q + 1}"] = abs(full_size / size - (3.5 + 5)/2)
    else:
        sheet[f"J{q + 1}"] = "NO"
    if 0.08 < 1 - size2 / full_size2:
        sheet[f"L{q + 1}"] = "OK"
        sheet[f"M{q + 1}"] = abs(1 - size2 / full_size2) - 0.08
    else:
        sheet[f"L{q + 1}"] = "NO"

    sheet[f"N{q+1}"] = bright2/size2
    sheet[f"O{q + 1}"] = 20*bright2 / size2 - 6940

sheet.column_dimensions['G'].width = max_width * 0.15
workbook.save("output/Index_of_objects.xlsx")  # save Excel table
