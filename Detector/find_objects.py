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


class ImageCrawler(list):
    """
    something

    Important properties of this object includes the list of all identified objects which is a list of lists of ....

    The final output of identified flakes will be stored in the underlying list.
    """
    def __init__(self, path: str, name: str, out1: bool, min_size: float, sensitivity: int, calibration: float):
        self.path = path
        self.workbook = 0
        self.name = name
        self.out1 = out1
        self.min_size = min_size
        self.sensitivity = sensitivity
        self.calibration = calibration
        self.detected_object = []
        self.max_width = 0

        print("The first iteration:")
        # Find objects in the photo in low resolution
        self.orig_photo, self.output = self._load_image()
        self.marked_objects = self._find_objects_low_resolution()
        # create output photo of detected object with centres and area of detected edges
        if out1 == 1:
            self._output_marked_objects()

        self.orig_photo.close()
        self.output.close()

        print("The second iteration:")
        # Now, find objects from the first iteration in the same area in high resolution
        # Set area for finding object in high resolution
        print(f"processing of {len(self.marked_objects)}")
        for index, q in enumerate(self.marked_objects):
            # identify corners of objects
            x_min, x_max, y_min, y_max = (int(min(x for (x, y) in q)), int(max(x for (x, y) in q)),
                                          int(min(y for (x, y) in q)), int(max(y for (x, y) in q)))
            #if (x_max - x_min) * (y_max - y_min) < 50000:  # work around a bug where too big objects are linked together
            self.append(Flake(self, index,(x_min, x_max, y_min, y_max)))

        #print(self[0].size)
        catalogue = ExcelOutput(self)

        if not out1 == 1:
            self._clean()

    def _load_image(self):
        """Loads the image from the disk into a PIL Image object"""
        '''It finds and marks all object in the photo.'''
        orig_photo = Image.open(f"{self.path}/input/{self.name}")  # open the original photo
        print("The photo has been opened.")

        print("changing gamma and contrast of the original photo")
        # orig_photo = gamma_correct(orig_photo, 1.5)
        # orig_photo = change_contrast(orig_photo, 100)
        orig_photo.save(f"{self.path}/output/org_gc.png")  # save the original photo with gamma and contrast correction
        #pro = orig_photo.load()

        # create new images for processing (object area in low resolution)
        output = Image.new('RGB', (orig_photo.size[0], orig_photo.size[1]), color='white')
        #new = output.load()
        return orig_photo, output

    def _find_objects_low_resolution(self):
        """Identify objects on a artificially lower resolution image."""
        pro = self.orig_photo.load()
        new = self.output.load()
        marked_pixel = []  # coordinates of detected object area
        marked_objects = []

        print("marking non-black area")
        for i in range(self.orig_photo.size[0] - 1):
            for j in range(self.orig_photo.size[1] - 1):
                R, G, B = pro[i, j]
                if R > self.sensitivity or G > self.sensitivity or B > self.sensitivity:
                    pro[i, j] = (255, 0, 0)

        print("finding object area")
        for i in range(3, self.orig_photo.size[0] - 4, 6):
            for j in range(3, self.orig_photo.size[1] - 4, 6):
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
                        marked_pixel.append((i, j))

        print("finding whole objects")

        marked_pixel = np.array(marked_pixel)

        while len(marked_pixel) > 0:  # find neighbor marked pixel
            seed = marked_pixel[0]
            queue = [seed]
            marked_pixel = marked_pixel[1:]

            i = 0
            while i < len(queue):
                x, y = queue[i]
                for dx in [-6, 0, 6]:
                    for dy in [-6, 0, 6]:
                        if (dx == 0 and dy == 0) or (dx != 0 and dy != 0):
                            continue
                        neighbor = (x + dx, y + dy)
                        mask = np.all(marked_pixel == neighbor, axis=1)
                        if np.any(mask):
                            queue.append(neighbor)
                            marked_pixel = marked_pixel[~mask]

                i += 1

            marked_objects.append(queue)

        print("deleting too small object")
        for obj in marked_objects.copy():
            if len(obj) <= self.min_size:
                marked_objects.remove(obj)
        return marked_objects

    def _output_marked_objects(self):
        """Output debug images allowing to judge the identification of objects."""
        # create output photo of detected object with centres and area of detected edges

        ts = Image.new('RGB', (self.orig_photo.size[0], self.orig_photo.size[1]), color='white')
        test = ts.load()

        for n in self.marked_objects:
            for (i, j) in n:
                for k in range(i - 3, i + 3):
                    for l in range(j - 3, j + 3):
                        test[k, l] = (256, 0, 0)

        centre = []
        for q in self.marked_objects:
            centre.append((int(sum(x for (x, y) in q) / len(q)),
                           int(sum(y for (x, y) in q) / len(q))))

        p = 0
        for (i, j) in centre:
            ImageDraw.Draw(ts).text((i + 5, j + 5), str(len(self.marked_objects[p])), (0, 0, 0))
            for k in range(i - 5, i + 5):
                for l in range(j - 5, j + 5):
                    test[k, l] = (0, 0, 0)
            p += 1

        ts.save(f'{self.path}/output/{self.name}_first_step1.png')  # store detected objects with centre and size of edge
        self.orig_photo.save(f'{self.path}/output/{self.name}_first_step2.png')  # store marked object area
        self.output.save(f'{self.path}/output/{self.name}_first_step3.png')  # store object area in low resolution
        ts.close()

        return None

    def _clean(self):
        shutil.rmtree(os.path.join(self.path, "output\\objects"))

        return None

class Flake:
    """Represents and processes an identified object on an image."""
    def __init__(self, parent: ImageCrawler, identifier: int, coordinates: (int, int, int, int)):
        """Process flake in high resolution."""
        # define all needed properties
        self.id = identifier
        self.coordinates = coordinates
        self.bright2 = 0
        self.centre = (0, 0)
        self.size = 0
        self.full_size = 0
        self.size2 = 0
        self.full_size2 = 0
        self.width = 0
        self.hight = 0
        self.calib = parent.calibration

        print(f"{self.id + 1}, ", end="")
        self.edit_orig_photo, self.output, self.output2 = self._load_image2(parent.path)
        self.marked_object2 = self._find_objects_high_resolution(parent.path, parent.name, parent.sensitivity, parent.min_size)
        self._measure(parent.path, parent.name, parent.out1)


    def _load_image2(self, path):
        '''Crop original image and make output images.'''
        edit_orig_photo = Image.open(f'{path}/output/org_gc.png')  # open corrected original photo
        #self.org = self.edit_orig_photo.load()

        output = Image.new('RGB', (self.coordinates[1] - self.coordinates[0] + 8,
                               self.coordinates[3] - self.coordinates[2] + 8),
                       color='white')  # vytvoreni noveho obrazku
        #self.new = self.output.load()
        output2 = Image.new('RGB', (self.coordinates[1] - self.coordinates[0] + 8,
                               self.coordinates[3] - self.coordinates[2] + 8),
                       color='white')  # vytvoreni noveho obrazku
        #self.test = self.output2.load()
        return edit_orig_photo, output, output2

    def _find_objects_high_resolution(self, path, name, sensitivity, min_size):
        '''Detect object in higth resolution and delete too small objects.'''
        self.org = self.edit_orig_photo.load()
        self.new = self.output.load()
        self.test = self.output2.load()

        marked_pixel = []

        for i in range(self.coordinates[0] - 4, self.coordinates[1] + 4):
            for j in range(self.coordinates[2] - 4, self.coordinates[3] + 4):
                R, G, B = self.org[i, j]
                self.new[i - self.coordinates[0] - 1 + 5, j - self.coordinates[2] - 1 + 5] = self.org[i, j]
                self.bright2 += R + G + B
                if R > sensitivity or G > sensitivity or B > sensitivity:
                    self.org[i, j] = (256, 0, 0)
        self.output.save(f'{path}/output/objects/{name}_object{self.id}.png')  # storage image n-th objects

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
                        marked_pixel.append((i, j))

        marked_pixel = np.array(marked_pixel)

        marked_object = []

        i = 0
        while len(marked_pixel) > 0:
            seed = marked_pixel[0]
            queue = [seed]
            marked_pixel = np.delete(marked_pixel, 0, axis=0)

            b = 1
            while b == 1:
                b = 0
                for (x, y) in marked_pixel:
                    dx_values = [2, -2, 0, 0, 2, -2, 2, -2]
                    dy_values = [0, 0, 2, -2, 2, -2, -2, 2]

                    for dx, dy in zip(dx_values, dy_values):
                        neighbor = (x + dx, y + dy)
                        mask = np.all(marked_pixel == neighbor, axis=1)
                        if np.any(mask):
                            queue.append(neighbor)
                            marked_pixel = marked_pixel[~mask]
                            b = 1

            marked_object.append(queue)
            i += 1

        for obj in marked_object.copy():
            if len(obj) <= min_size:
                marked_object.remove(obj)

        self.best = 0
        if len(marked_object) == 1:
            for n in marked_object:
                for (i, j) in n:
                    for k in range(i - 1, i + 1):
                        for l in range(j - 1, j + 1):
                            self.test[k - self.coordinates[0] - 1 + 5, l - self.coordinates[2] - 1 + 5] = (256, 0, 0)
        elif len(marked_object) > 1:
            mx = max(len(x) for x in marked_object)
            for n in marked_object:
                if len(n) == mx:
                    self.best = n
                    for (i, j) in n:
                        for k in range(i - 1, i + 1):
                            for l in range(j - 1, j + 1):
                                self.test[k - self.coordinates[0] - 1 + 5, l - self.coordinates[2] - 1 + 5] = (
                                256, 0, 0)
        return marked_object

    def _measure(self, path, name, out1):
        '''Measure coordinates, size, hight of a object.'''
        self.centre = ((int(sum(x for (x, y) in self.marked_object2[self.best]) / len(self.marked_object2[self.best])),
                   int(sum(y for (x, y) in self.marked_object2[self.best]) / len(self.marked_object2[self.best]))))

        # mark shapes of image
        shape = Image.open(f'{path}/output/objects/{name}_object{self.id}.png')
        shape = gamma_correct(shape, 1.5)
        shape = change_contrast(shape, 100)
        shape.save(f'{path}/output/objects/{name}_object{self.id}_proc1.png')

        shape = cv2.imread(f'{path}/output/objects/{name}_object{self.id}_proc1.png')
        shape = cv2.cvtColor(shape, cv2.COLOR_BGR2RGB)
        shape = cv2.addWeighted(shape, 4, shape, 0, 0)
        shape = cv2.cvtColor(shape, cv2.COLOR_BGR2GRAY)
        shape = cv2.Canny(shape, 300, 100)
        cv2.imwrite(f'{path}/output/objects/{name}_object{self.id}_proc2.png', shape)

        prc = Image.open(f'{path}/output/objects/{name}_object{self.id}_proc2.png')  # open corrected original photo
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
        for i in range(self.output2.size[0] - 3):
            red = 0
            for j in range(self.output2.size[1] - 3):
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

        if out1 == 1:
            self.output2.save(
                f'{path}/output/objects/{name}_object{self.id}_proc0.png')  # store photo of area of detect object

        self.width = self.output.width
        self.hight = self.output.height
        return None

    @property
    def pos_x(self) -> float:
        return self.centre[0] * self.calib

    @property
    def pos_y(self) -> float:
        return self.centre[1] * self.calib

    @property
    def area(self) -> float:
        return self.full_size2 * self.calib ** 2

    @property
    def sizeX(self) -> float:
        return  self.width * self.calib

    @property
    def sizeY(self) -> float:
        return  self.hight * self.calib

    @property
    def transparency(self) -> float:
        return  1 - self.size2 / self.full_size2

    @property
    def bright(self) -> float:
        return self.bright2 / (3*self.size2)

    @property
    def height(self) -> float:
        return  20 * self.bright2 / self.size2 - 6940

    @property
    def ratio(self) -> float:
        return max(((-self.size2 - (self.size2 ** 2
                           - 16 * self.full_size2) ** 0.5) / 4) / (
                4 * self.full_size2 /
                (-self.size2 - (self.size2 ** 2 - 16 * self.full_size2) ** 0.5)),
        (4 * self.full_size2 / (-self.size2
                                  - (self.size2 ** 2 - 16 * self.full_size2) ** 0.5)) / (
                (-self.size2 - (self.size2 ** 2
                                  - 16 * self.full_size2) ** 0.5) / 4))

    @property
    def contourI(self) -> int:
        return self.size

    @property
    def contourII(self) -> int:
        return self.full_size

    @property
    def filter_contour(self) -> (str, float):
        if 3.5 < self.full_size / self.size < 5:
            return "OK",  abs(self.full_size / self.size - (3.5 + 5) / 2)
        else:
            return "NO", 0

    @property
    def filter_transparency(self) -> (str, float):
        if 0.08 < 1 - self.size2 / self.full_size2:
            return "OK", abs(1 - self.size2 / self.full_size2) - 0.08
        else:
            return "NO", 0


class ExcelOutput:
    """Generate Excel sheet with identified flakes and image information"""
    def __init__(self, image: ImageCrawler):
        self.workbook = Workbook()
        self.filename = f"{image.path}/output/Catalogue_{image.name}.xlsx"
        self._generate_metadata_header()

        self._generate_object_table(image)
        self._save_to_disk(self.filename)

    def _generate_metadata_header(self):
        """Insert general information (min_size, sensitivity, calibration)"""

        sheet = self.workbook.active
        sheet["A1"] = "id"
        sheet["B1"] = "x (um)"
        sheet["C1"] = "y (um)"
        sheet["D1"] = "size (um^2)"
        sheet["E1"] = "Size X (um)"
        sheet["F1"] = "Size Y (um)"
        sheet["G1"] = "transparency (%)"
        sheet["H1"] = "Bright (RGB)"
        sheet["I1"] = "Height (Å)"
        sheet["J1"] = "size ratio"
        sheet["K1"] = "photo"
        sheet["L1"] = "contourI"
        sheet["M1"] = "contourII"
        sheet["N1"] = "filter - contour"  # Does the object have a constant contour?  3,5 (3,7) - 5
        sheet["O1"] = "Value - bigger is better"
        sheet["P1"] = "filter - transparency"  # Is the object transparent?  >0,1 (0,08)
        sheet["Q1"] = "Value - bigger is better"

        return None

    def _generate_object_table(self, image):
        """Insert object table header and contenct"""
        # generate header ...
        # iterate over all flakes
        sheet = self.workbook.active
        max_width = 0
        for index, flake in enumerate(image):
            # fill Excel table
            sheet[f"A{index + 2}"] = index
            sheet[f"B{index + 2}"] = flake.pos_x
            sheet[f"C{index + 2}"] = flake.pos_y
            sheet[f"D{index + 2}"] = flake.area
            sheet[f"E{index + 2}"] = flake.sizeX
            sheet[f"F{index + 2}"] = flake.sizeY
            sheet[f"G{index + 2}"] = flake.transparency
            sheet[f"H{index + 2}"] = flake.bright
            sheet[f"I{index + 2}"] = flake.height
            sheet[f"J{index + 2}"] = flake.ratio
            # add image
            img = Xl(f"{image.path}/output/objects/{image.name}_object{index}.png")
            sheet.add_image(img, f'K{index + 1}')
            img2 = Image.open(f"{image.path}/output/objects/{image.name}_object{index}.png")
            sheet.row_dimensions[index + 1].height = img2.height * 0.8

            '''
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
            '''
            if max_width < img2.size[0]:
                max_width = img2.size[0]

        sheet.column_dimensions['K'].width = max_width * 0.15

        # and much more...

    def _save_to_disk(self, filename):
        """Store the excel sheet on the filesystem"""
        self.workbook.save(self.filename)  # save Excel table
