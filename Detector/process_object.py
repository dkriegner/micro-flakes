from PIL import Image
import numpy as np
from openpyxl.drawing.image import Image as Xl
import cv2

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


def process_object(coordinates, min_size, q, calibration, workbook):
    name2 = "object"  # name of photos of found objects

    pim = Image.open(f'output/org_gc.png')  # open corrected original photo
    org = pim.load()

    nw = Image.new('RGB', (coordinates[1] - coordinates[0] + 8, coordinates[3] - coordinates[2] + 8),
                   color='white')  # vytvoreni noveho obrazku
    new = nw.load()
    ts = Image.new('RGB', (coordinates[1] - coordinates[0] + 8, coordinates[3] - coordinates[2] + 8),
                   color='white')  # vytvoreni noveho obrazku
    test = ts.load()

    detect2 = []
    bright2 = 0

    for i in range(coordinates[0] - 4, coordinates[1] + 4):
        for j in range(coordinates[2] - 4, coordinates[3] + 4):
            R, G, B = org[i, j]
            new[i - coordinates[0] - 1 + 5, j - coordinates[2] - 1 + 5] = org[i, j]
            bright2 += R + G + B
            if R > 80 or G > 80 or B > 80:
                org[i, j] = (256, 0, 0)
    nw.save(f'output/objects/{name2}_{q}.png')  # storage image q-th objects

    for i in range(coordinates[0] - 4, coordinates[1] - 1 + 4, 2):
        for j in range(coordinates[2] - 4, coordinates[3] - 1 + 4, 2):
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

    for obj in anything2.copy():
        if len(obj) <= min_size:
            anything2.remove(obj)

    index = 0
    if len(anything2) == 1:
        for n in anything2:
            for (i, j) in n:
                for k in range(i - 1, i + 1):
                    for l in range(j - 1, j + 1):
                        test[k - coordinates[0] - 1 + 5, l - coordinates[2] - 1 + 5] = (256, 0, 0)
    elif len(anything2) > 1:
        mx = max(len(x) for x in anything2)
        for n in anything2:
            if len(n) == mx:
                index = n
                for (i, j) in n:
                    for k in range(i - 1, i + 1):
                        for l in range(j - 1, j + 1):
                            test[k - coordinates[0] - 1 + 5, l - coordinates[2] - 1 + 5] = (256, 0, 0)

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
    sheet = workbook.active
    img = Xl(f'output/objects/{name2}_{q}.png')
    sheet.add_image(img, f'G{q + 1}')
    img2 = Image.open(f'output/objects/{name2}_{q}.png')
    sheet.row_dimensions[q + 1].height = img2.height * 0.8

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

    return img2.width
