from PIL import Image, ImageDraw
import numpy as np
from openpyxl import Workbook
from openpyxl.drawing.image import Image as Xl
import cv2
import shutil
import os

def gamma_correct(im, gamma1: float):
    '''
    Change the gamma of a picture. The fistr parametr is a photo and second parametr is a gamma parametr.
    The formala of function is?: new_RGB = ((RGB / 255)^(1 / gamma)) * 255.
    '''
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
    '''
    Change the gamma of a picture. The fistr parametr is a photo and second parametr is a contrast parametr.
    The formala of function is?: new_RGB = 128 + (259 * (contrast + 255)) / (255 * (259 - contrast)) * (RGB - 128).
    '''
    factor = (259 * (level + 255)) / (255 * (259 - level))
    def contrast(c):
        return 128 + factor * (c - 128)
    return img.point(contrast)


class Detect:
    '''
    Functions to detecting flakes.
    Longer description is needed!
    '''
    def __init__(self, path: str, name: str, out1: bool, min_size: float, sensitivity: int, calibration: float):
        self.path = path
        self.workbook = 0
        self.name = name
        self.out1 = out1
        self.min_size = min_size
        self.sensitivity = sensitivity
        self.calibration = calibration
        self.anything = []
        self.max_width = 0

    def find_objects(self):
        '''It finds and marks all object in the photo.'''
        pim = Image.open(f"{self.path}/input/{self.name}")  # open the original photo
        print("The photo has been opened.")

        print("changing gamma and contrast of the original photo")
        # pim = gamma_correct(pim, 1.5)
        # pim = change_contrast(pim, 100)
        pim.save(f"{self.path}/output/org_gc.png")  # save the original photo with gamma and contrast correction
        pro = pim.load()

        # create new images for processing (object area in low resolution)
        nw = Image.new('RGB', (pim.size[0], pim.size[1]), color='white')
        new = nw.load()

        detect = []  # coordinates of detected object area

        print("marking non-black area")
        for i in range(pim.size[0] - 1):
            for j in range(pim.size[1] - 1):
                R, G, B = pro[i, j]
                if R > self.sensitivity or G > self.sensitivity or B > self.sensitivity:
                    pro[i, j] = (255, 0, 0)

        print("finding object area")
        for i in range(3, pim.size[0] - 4, 6):
            for j in range(3, pim.size[1] - 4, 6):
                red = 0  # number of red pixels
                px = 0  # number of all pixels
                for k in range(i - 3, i + 3):
                    for l in range(j - 3, j + 3):
                        if pro[k, l] == (255, 0, 0):
                            red += 1
                        px += 1
                if px != 0:
                    if red / float(px) > 0.6:
                        for k in range(i - 3, i + 3):
                            for l in range(j - 3, j + 3):
                                new[k, l] = (255, 0, 0)
                        detect.append((i, j))

        print("finding whole objects")

        detect = np.array(detect)

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

            self.anything.append(queue)

        print("deleting too small object")
        for obj in self.anything.copy():
            if len(obj) <= self.min_size:
                self.anything.remove(obj)

        # create output photo of detected object with centres and area of detected edges
        if self.out1 == 1:

            ts = Image.new('RGB', (pim.size[0], pim.size[1]), color='white')
            test = ts.load()

            for n in self.anything:
                for (i, j) in n:
                    for k in range(i - 3, i + 3):
                        for l in range(j - 3, j + 3):
                            test[k, l] = (256, 0, 0)

            centre = []
            for q in self.anything:
                centre.append((int(sum(x for (x, y) in q) / len(q)),
                               int(sum(y for (x, y) in q) / len(q))))

            p = 0
            for (i, j) in centre:
                ImageDraw.Draw(ts).text((i + 5, j + 5), str(len(self.anything[p])), (0, 0, 0))
                for k in range(i - 5, i + 5):
                    for l in range(j - 5, j + 5):
                        test[k, l] = (0, 0, 0)
                p += 1

            ts.save(f'{self.path}/output/{self.name}_first_step1.png')  # store detected objects with centre and size of edge
            pim.save(f'{self.path}/output/{self.name}_first_step2.png')  # store marked object area
            nw.save(f'{self.path}/output/{self.name}_first_step3.png')  # store object area in low resolution
            ts.close()

        pim.close()
        nw.close()

        return None


    def maketeble(self, size, full_size, size2, full_size2, centre, bright2, widht, hight):
        '''It create a teble with all objects from Process.'''
        self.workbook = Workbook()  # create MS Excel table
        sheet = self.workbook.active
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
        sheet["N1"] = "Bright (RGB)"
        sheet["O1"] = "Height (Å)"
        sheet["P1"] = "Size X (um)"
        sheet["Q1"] = "Size Y (um)"

        for index in range(1, len(self.anything)):
            # fill Excel table
            sheet = self.workbook.active
            img = Xl(f'{self.path}/output/objects/{self.name}_object{index}.png')
            sheet.add_image(img, f'G{index + 1}')
            img2 = Image.open(f'{self.path}/output/objects/{self.name}_object{index}.png')
            sheet.row_dimensions[index + 1].height = img2.height * 0.8

            sheet[f"A{index + 1}"] = index
            sheet[f"B{index + 1}"] = centre[index][0] * self.calibration
            sheet[f"C{index + 1}"] = centre[index][1] * self.calibration
            sheet[f"D{index + 1}"] = full_size2[index] * self.calibration ** 2
            sheet[f"E{index + 1}"] = 1 - size2[index] / full_size2[index]
            sheet[f"F{index + 1}"] = max(((-size2[index] - (size2[index] ** 2
                    - 16 * full_size2[index]) ** 0.5) / 4) / (4 * full_size2[index] /
                    (-size2[index] - (size2[index] ** 2 - 16 * full_size2[index]) ** 0.5)),
                                         (4 * full_size2[index] / (-size2[index]
                                        - (size2[index] ** 2 - 16 * full_size2[index]) ** 0.5)) / (
                                        (-size2[index] - (size2[index] ** 2
                                        - 16 * full_size2[index]) ** 0.5) / 4))
            sheet[f"H{index + 1}"] = size[index]
            sheet[f"I{index + 1}"] = full_size[index]
            if 3.5 < full_size[index] / size[index] < 5:
                sheet[f"J{index + 1}"] = "OK"
                sheet[f"K{index + 1}"] = abs(full_size[index] / size[index] - (3.5 + 5) / 2)
            else:
                sheet[f"J{index + 1}"] = "NO"
            if 0.08 < 1 - size2[index] / full_size2[index]:
                sheet[f"L{index + 1}"] = "OK"
                sheet[f"M{index + 1}"] = abs(1 - size2[index] / full_size2[index]) - 0.08
            else:
                sheet[f"L{index + 1}"] = "NO"

            sheet[f"N{index + 1}"] = bright2[index] / size2[index]
            sheet[f"O{index + 1}"] = 20 * bright2[index] / size2[index] - 6940
            sheet[f"P{index + 1}"] = widht[index] * self.calibration
            sheet[f"Q{index + 1}"] = hight[index] * self.calibration
            if self.max_width < widht[index]:
                self.max_width = widht[index]
        sheet = self.workbook.active
        sheet.column_dimensions['G'].width = self.max_width * 0.15
        self.workbook.save(f"{self.path}/output/Catalogue_{self.name}.xlsx")  # save Excel table
        return None


    def clean(self):
        if self.out1 == 0:
            shutil.rmtree(os.path.join(self.path, "output\\objects"))
        return None


class Proces:
    '''It makes the measurment of object which is detected in Detect. You get coordinates, size, images of object.'''
    def __init__(self, path: str, name: str, out1: bool, min_size: float, sensitivity: int, calibration: float, num: int, coordinates: (int, int, int, int)):
        self.path = path
        self.name = name
        self.out1 = out1
        self.min_size = min_size
        self.sensitivity = sensitivity
        self.calibration = calibration
        self.id = num
        self.coordinates = coordinates
        self.pim = 0
        self.org = 0
        self.nw = 0
        self.new = 0
        self.ts = 0
        self.test = 0
        self.bright2 = 0
        self.centre = (0, 0)
        self.size = 0
        self.full_size = 0
        self.size2 = 0
        self.full_size2 = 0
        self.width = 0
        self.hight = 0

    def load_image(self):
        '''Crop original image and make output images.'''
        self.pim = Image.open(f'{self.path}/output/org_gc.png')  # open corrected original photo
        self.org = self.pim.load()

        self.nw = Image.new('RGB', (self.coordinates[1] - self.coordinates[0] + 8,
                               self.coordinates[3] - self.coordinates[2] + 8),
                       color='white')  # vytvoreni noveho obrazku
        self.new = self.nw.load()
        self.ts = Image.new('RGB', (self.coordinates[1] - self.coordinates[0] + 8,
                               self.coordinates[3] - self.coordinates[2] + 8),
                       color='white')  # vytvoreni noveho obrazku
        self.test = self.ts.load()
        return None

    def mark_object(self):
        '''Detect object in higth resolution and delete too small objects.'''
        detect2 = []

        for i in range(self.coordinates[0] - 4, self.coordinates[1] + 4):
            for j in range(self.coordinates[2] - 4, self.coordinates[3] + 4):
                R, G, B = self.org[i, j]
                self.new[i - self.coordinates[0] - 1 + 5, j - self.coordinates[2] - 1 + 5] = self.org[i, j]
                self.bright2 += R + G + B
                if R > self.sensitivity or G > self.sensitivity or B > self.sensitivity:
                    self.org[i, j] = (256, 0, 0)
        self.nw.save(f'{self.path}/output/objects/{self.name}_object{self.id}.png')  # storage image n-th objects

        for i in range(self.coordinates[0] - 4, self.coordinates[1] - 1 + 4, 2):
            for j in range(self.coordinates[2] - 4, self.coordinates[3] - 1 + 4, 2):
                red = 0
                px = 0
                for k in range(i - 1, i + 1):
                    for l in range(j - 1, j + 1):
                        if self.org[k, l] == (255, 0, 0):
                            red += 1
                        px += 1
                if px != 0:
                    if red / float(px) > 0.6:
                        detect2.append((i, j))

        detect2 = np.array(detect2)

        self.anything2 = []

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

            self.anything2.append(queue)
            i += 1

        for obj in self.anything2.copy():
            if len(obj) <= self.min_size:
                self.anything2.remove(obj)

        self.best = 0
        if len(self.anything2) == 1:
            for n in self.anything2:
                for (i, j) in n:
                    for k in range(i - 1, i + 1):
                        for l in range(j - 1, j + 1):
                            self.test[k - self.coordinates[0] - 1 + 5, l - self.coordinates[2] - 1 + 5] = (256, 0, 0)
        elif len(self.anything2) > 1:
            mx = max(len(x) for x in self.anything2)
            for n in self.anything2:
                if len(n) == mx:
                    self.best = n
                    for (i, j) in n:
                        for k in range(i - 1, i + 1):
                            for l in range(j - 1, j + 1):
                                self.test[k - self.coordinates[0] - 1 + 5, l - self.coordinates[2] - 1 + 5] = (
                                256, 0, 0)
        return None

    def measure(self):
        '''Measure coordinates, size, hight of a object.'''
        self.centre = ((int(sum(x for (x, y) in self.anything2[self.best]) / len(self.anything2[self.best])),
                   int(sum(y for (x, y) in self.anything2[self.best]) / len(self.anything2[self.best]))))

        # mark shapes of image
        shape = Image.open(f'{self.path}/output/objects/{self.name}_object{self.id}.png')
        shape = gamma_correct(shape, 1.5)
        shape = change_contrast(shape, 100)
        shape.save(f'{self.path}/output/objects/{self.name}_object{self.id}_proc1.png')

        shape = cv2.imread(f'{self.path}/output/objects/{self.name}_object{self.id}_proc1.png')
        shape = cv2.cvtColor(shape, cv2.COLOR_BGR2RGB)
        shape = cv2.addWeighted(shape, 4, shape, 0, 0)
        shape = cv2.cvtColor(shape, cv2.COLOR_BGR2GRAY)
        shape = cv2.Canny(shape, 300, 100)
        cv2.imwrite(f'{self.path}/output/objects/{self.name}_object{self.id}_proc2.png', shape)

        prc = Image.open(f'{self.path}/output/objects/{self.name}_object{self.id}_proc2.png')  # open corrected original photo
        pc = prc.load()

        # calculate size of the object (new)
        x_min = x_max = 0
        for i in range(prc.size[0]):
            white = 0
            for j in range(prc.size[1]):
                W = pc[i, j]
                if W == 255 and white == 0:
                    white = 1
                    self.size += 1
                    x_min = j
                elif W == 255 and white == 1:
                    self.size += 1
                    x_max = j
            self.full_size += (x_max - x_min)
            x_min = x_max = 0

        # calculate size of the object (old)
        x_min = x_max = 0
        for i in range(self.ts.size[0] - 3):
            red = 0
            for j in range(self.ts.size[1] - 3):
                R, G, B = self.test[i, j]
                if (R, G, B) == (255, 0, 0) and red == 0:
                    red = 1
                    self.size2 += 1
                    x_min = j
                elif (R, G, B) == (255, 0, 0) and red == 1:
                    self.size2 += 1
                    x_max = j
            self.full_size2 += (x_max - x_min)
            x_min = x_max = 0

        if self.out1 == 1:
            self.ts.save(
                f'{self.path}/output/objects/{self.name}_object{self.id}_proc0.png')  # store photo of area of detect object

        self.width = self.nw.width
        self.hight = self.nw.height
        return None
