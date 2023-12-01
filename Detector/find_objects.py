"""This file contains definitions of objects."""
from PIL import Image, ImageDraw
import numpy as np
from openpyxl import Workbook
from openpyxl.drawing.image import Image as pyxl_Image
import cv2
import shutil
import os
import logging as log
from threading import Thread
from functions import manage_subfolders, gamma_correct, change_contrast
# set logging to terminal
log.getLogger().setLevel(log.INFO)
logger = log.getLogger(os.path.split(__file__)[-1])


class ImageCrawler(list):
    """
    It loads the image from the disk into a PIL Image object (self.orig_photo) and creates a new photo of the detected object
    with centres and area of detected edges in low resolution (self.output). It identifies objects on an artificially
    lower-resolution image and stores them as a list of detected flakes (self.marked_objects). Every flake is a list of coordinates [x, y] of
    squares 7×7 pixels. Every square contains the same pixel. It is a method how to decrease resolution. Too small
    objects are removed (objects which contain less squares than self.min_size).
    Then, it creates a new object for each flake (Flake object). It repeats the same algorithm for finding flakes
    from the 1st iteration in high resolution.
    """
    def __init__(self, path: str, name: str, more_output: bool, min_size: float, sensitivity: int, calibration: float,
                 input_app=0):
        self.name = name  # The name of an image to load
        self.path = path  # The path of an image to load
        self.out1 = more_output  # Look at main.py (more_output)
        self.min_size = min_size  # Look at main.py
        self.sensitivity = sensitivity  # Look at main.py
        self.calibration = calibration  # Look at main.py
        self.detected_object = [] # List of detected flakes. Every flake is a list of coordinates [x, y]
        self.workbook = 0  # Excel table for a new catalogue
        self.max_width = 0  # Parameter to set a width of an image column in Excel table.
        self.input_app = input_app

        logger.info("The first iteration:")
        manage_subfolders(path)
        # Load an image
        self.orig_photo, self.output = self._load_image()
        self.orig_photo_copy = self.orig_photo.copy()
        self.pro = self.orig_photo_copy.load()
        self.new = self.output.load()
        # Find objects in the photo in low resolution
        self.marked_objects = self._find_objects_low_resolution()
        # create output photo of detected object with centres and area of detected edges in low resolution
        if self.out1 == 1:
            self._output_marked_objects()

        logger.info("The second iteration:")
        # Now, find objects from the first iteration in the same area in high resolution
        # Set area for finding object in high resolution
        logger.info(f"processing of {len(self.marked_objects)} objects:")

        for index, q in enumerate(self.marked_objects):
            # identify corners of objects
            x_min, x_max, y_min, y_max = (int(min(x for (x, y) in q)), int(max(x for (x, y) in q)),
                                          int(min(y for (x, y) in q)), int(max(y for (x, y) in q)))
            #if (x_max - x_min) * (y_max - y_min) < 50000:  # work around a bug where too big objects are linked together
            # Create a new object for each flake. Flake() repeat the same algorithm for finding flakes from the 1st iteraction in high resolution.
            self.append(Flake(self, index, (x_min, x_max, y_min, y_max))) # One parallel process (old)

        # Create an empty list of processes
        processes = []
        for index, flake in enumerate(self):
            p = Thread(target=flake.start, args=())
            # Add the process to the list
            processes.append(p)
            # Start the process
            p.start()

        # Wait for all the processes to finish
        for p in processes:
            p.join()

        # Wait for all the processes to finish
        for p in processes:
            p.join()

        ExcelOutput(self)  # Create a catalogue from the list of flakes in an Excel table.

        if not self.out1 == 1:
            self._clean()  # Clean images of flakes in output folder.


    def _load_image(self) -> (Image.Image, Image.Image):
        """Loads the image from the disk into a PIL Image object. """
        '''It finds and marks all object in the photo.'''
        if self.input_app == 0:
            orig_photo = Image.open(f"{self.path}/input/{self.name}")  # open the original photo
            logger.info("The photo has been opened.")
            #logger.info("changing gamma and contrast of the original photo")
        elif self.input_app == 2:
            orig_photo = Image.open(f"{self.path}/{self.name}")  # open the original photo
            #starter.logbox.appendPlainText("The photo has been opened.") # it doesn't work
            logger.info("The photo has been opened.")
            #logger.info("changing gamma and contrast of the original photo") # deactivated
        # orig_photo = gamma_correct(orig_photo, 1.5)
        # orig_photo = change_contrast(orig_photo, 100)

        # create new images for processing (object area in low resolution)
        output = Image.new('RGB', (orig_photo.size[0], orig_photo.size[1]), color='white')
        return orig_photo, output

    def _find_objects_low_resolution(self) -> list:
        """
        It marks pixels having R, G, B bigger than the sensitivity value. It splits the image into a matrix which contains
        groups of 7×7 pixels (squares). If a square contains more than 60 % marked pixels, it is marked as marked_pixel.
        It is a list of (x, y) coordinates of centres of squares. Then, neighbour squares are connected to objects.
        Objects are stored in marked_objects. It is a list of detected objects which are represented by a list of (x, y)
        coordinates of centres of squares. Too small objects are removed from marked_objects. The list (marked_objects)
        is the output of this function.
        """

        marked_pixel = []  # A list of (x, y) coordinates of marked squares of 7 by 7 pixels.
        marked_objects = []  # A list of detected object which is represented by a list of (x, y) coordinates

        logger.info("marking non-black area")
        for i in range(self.orig_photo.size[0] - 1):
            for j in range(self.orig_photo.size[1] - 1):
                R, G, B = self.pro[i, j]
                if R > self.sensitivity or G > self.sensitivity or B > self.sensitivity:
                    self.pro[i, j] = (255, 0, 0)

        logger.info("finding object area")
        for i in range(3, self.orig_photo.size[0] - 4, 6):
            for j in range(3, self.orig_photo.size[1] - 4, 6):
                red = 0  # number of red pixels
                px = 0  # number of all pixels
                for k in range(i - 3, i + 3):
                    for l in range(j - 3, j + 3):
                        if self.pro[k, l] == (255, 0, 0):
                            red += 1
                        px += 1
                if px != 0:
                    if red / float(px) > 0.6:
                        for k in range(i - 3, i + 3):
                            for l in range(j - 3, j + 3):
                                self.new[k, l] = (255, 0, 0)
                        marked_pixel.append((i, j))

        logger.info("finding whole objects")

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

        logger.info("deleting too small object")
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

        # Marked light pixel in original picture
        self.orig_photo.save(f'{self.path}/output/{self.name}_first_step2.png')
        # Marked squares with 7 by 7 (potential object area in low resolution)
        self.output.save(f'{self.path}/output/{self.name}_first_step1.png')
        # stored objects with a centre and an area of edge
        ts.save(f'{self.path}/output/{self.name}_first_step3.png')
        ts.close()  # close the 3rd image

        return None

    def _clean(self):
        """Clean output images from the 2nd interaction in ../output/objects."""
        shutil.rmtree(os.path.join(self.path, "output\\objects"))
        return None

class Flake:
    """
    Represents and processes an identified object on an image. At first, self._load_image2 load the original image
    to self.edit_orig_photo and crops to self.output and self.output2. The 2nd and 3rd image contains only one object.
    The next function (self._find_objects_high_resolution) makes the same procedure as self._find_objects_low_resolution
    in ImageCrawler in high resolution. Now the function operates with squares 3×3 pixels. The output of this function
    is self.marked_object2. It has the same structure as self.marked_object in ImageCrawler. The 3rd function
    (self._measure) measures many parameters of objects which is stored in self.marked_object2.
    """
    def __init__(self, parent: ImageCrawler, identifier: int, coordinates: (int, int, int, int)):
        """Process flake in high resolution."""
        # calibration for converting to the real size
        self.calib = parent.calibration
        # define all needed properties of a flake
        self.id = identifier  # identification number
        self.coordinates = coordinates  # maximal and minimal value of coordinates (x_min, x_max, y_min, y_max)
        self.width = 0  # width of an object in pixels
        self.height = 0  # height of an object in pixels
        self.bright2 = 0  # The sum of RGB values of all pixels of an object
        self.centre = (0, 0)  # (x, y) coordinates of centre of an object
        self.size = 0  # The area of edges of an object in a contour mode
        self.full_size = 0  # The area of the whole object in a contour mode
        self.size2 = 0  # The area of edges of an object in a mode of marked pixel in the original image
        self.full_size2 = 0  # The area of the whole object in a mode of marked pixel in the original image
        self.object_filename = f'{parent.path}/output/objects/{parent.name}_object{self.id}.png'
        self.parent = parent

    def start(self):
        logger.info(f"{round(100*(self.id + 1)/len(self.parent.marked_objects), 1)} %")
        self.output, self.output2 = self._load_image2()
        self.org = self.parent.orig_photo.load()
        self.new = self.output.load()
        self.test = self.output2.load()
        self.marked_object2 = self._find_objects_high_resolution()
        self._measure()
        return None

    def _load_image2(self) -> (Image.Image, Image.Image):
        """Crop original image and make output images"""

        output = Image.new('RGB', (self.coordinates[1] - self.coordinates[0] + 8,
                               self.coordinates[3] - self.coordinates[2] + 8), color='white')  # create a new image
        output2 = output.copy()
        return output, output2

    def _find_objects_high_resolution(self) -> list:
        """Crop original image a detect object in height resolution and delete too small objects."""
        marked_pixel = []

        # Crop original photo
        for i in range(self.coordinates[0] - 4, self.coordinates[1] + 4):
            for j in range(self.coordinates[2] - 4, self.coordinates[3] + 4):
                R, G, B = self.org[i, j]
                self.new[i - self.coordinates[0] - 1 + 5, j - self.coordinates[2] - 1 + 5] = self.org[i, j]
                self.bright2 += R + G + B
                if R > self.parent.sensitivity or G > self.parent.sensitivity or B > self.parent.sensitivity:
                    self.org[i, j] = (256, 0, 0)
        self.output.save(self.object_filename)  # storage image n-th objects

        # Mark light pixels
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

        # Connect neighbouring pixel to object
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

        # remove too small object
        for obj in marked_object.copy():
            if len(obj) <= self.parent.min_size:
                marked_object.remove(obj)

        # Choose the bigger object and store to output image (red and white)
        self.best = 0  # index of biggest object
        if len(marked_object) == 1:  # if only one object was detected
            for n in marked_object:
                for (i, j) in n:
                    for k in range(i - 1, i + 1):
                        for l in range(j - 1, j + 1):
                            self.test[k - self.coordinates[0] - 1 + 5, l - self.coordinates[2] - 1 + 5] = (256, 0, 0)
        elif len(marked_object) > 1:  # if more object were detected
            mx = max(len(x) for x in marked_object)
            for n in marked_object:
                if len(n) == mx:
                    self.best = n
                    for (i, j) in n:
                        for k in range(i - 1, i + 1):
                            for l in range(j - 1, j + 1):
                                self.test[k - self.coordinates[0] - 1 + 5, l - self.coordinates[2] - 1 + 5] = (256, 0, 0)
        return marked_object

    def _measure(self):
        """Measure coordinates of centre of gravity, size, height of an object."""
        # measure centre
        self.centre = ((int(sum(x for (x, y) in self.marked_object2[self.best]) / len(self.marked_object2[self.best])),
                   int(sum(y for (x, y) in self.marked_object2[self.best]) / len(self.marked_object2[self.best]))))

        # mark shapes of image
        shape = self.output.copy()
        shape = gamma_correct(shape, 1.5)
        shape = change_contrast(shape, 100)

        shape = np.array(shape)
        shape = cv2.cvtColor(shape, cv2.COLOR_BGR2RGB)
        shape = cv2.addWeighted(shape, 4, shape, 0, 0)
        shape = cv2.cvtColor(shape, cv2.COLOR_BGR2GRAY)
        shape = cv2.Canny(shape, 300, 100)
        cv2.imwrite(self.object_filename[:-4] + "_contures.png", shape)
        shape = cv2.cvtColor(shape, cv2.COLOR_BGR2RGB)
        shape = Image.fromarray(shape)

        pc = shape.load()

        # calculate area of the object from the contour output image
        x_min = x_max = 0
        for i in range(shape.size[0]):
            white = 0
            for j in range(shape.size[1]):
                R = pc[i, j][0]
                if R == 255 and white == 0:
                    white = 1
                    self.size += 1
                    x_min = j
                elif R == 255 and white == 1:
                    self.size += 1
                    x_max = j
            self.full_size += (x_max - x_min)
            x_min = x_max = 0

        # calculate area of the object from the red and white output image
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

        if self.parent.out1 == 1:
            self.output2.save(self.object_filename[:-4] + "_marked.png")  # store photo of area of detect object

        # get size of the image
        self.width, self.height = self.output.size
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
        return  self.height * self.calib

    @property
    def transparency(self) -> float:
        return  1 - self.size2 / self.full_size2

    @property
    def bright(self) -> float:
        return self.bright2 / (3*self.size2)

    @property
    def object_height(self) -> float:
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
    """
    Generate Excel sheet with identified flakes. The table contains a ID, images of objects and their all measures parameters.
    """
    def __init__(self, image: ImageCrawler):
        self.workbook = Workbook()  # Create a new table
        self.image = image
        self.filename = f"{image.path}/output/Catalogue_{image.name}.xlsx" # Set the name of the table
        self.image_name = f"{image.path}/output/objects/{image.name}_object" # The beginnig of names of images adding to the table
        # Create a header of the table with congiguration of measuring and explanatory notes
        self._generate_metadata_header()
        # Add all stored flakes in self.detected_object in ImageCrawler
        self._generate_object_table()
        # Save the table
        self._save_to_disk()

    def _generate_metadata_header(self):
        """Insert general information (min_size, sensitivity, calibration)"""

        sheet = self.workbook.active
        sheet["A1"] = f"The catalogue of Flakes in {self.image.name}"
        sheet["A2"] = "calibration"
        sheet["B2"] = self.image.calibration
        sheet["C2"] = "um/px"
        sheet["A3"] = "min_size"
        sheet["B3"] = self.image.min_size*1.6952
        sheet["C3"] = "um^3"
        sheet["A4"] = "sensitivity"
        sheet["B4"] = self.image.sensitivity
        sheet["C4"] = "RGB value"

        sheet["A6"] = "id"
        sheet["B6"] = "x (um)"
        sheet["C6"] = "y (um)"
        sheet["D6"] = "size (um^2)"
        sheet["E6"] = "Size X (um)"
        sheet["F6"] = "Size Y (um)"
        sheet["G6"] = "transparency (%)"
        sheet["H6"] = "Bright (RGB)"
        sheet["I6"] = "Height (Å)"
        sheet["J6"] = "size ratio"
        sheet["K6"] = "photo"
        sheet["L6"] = "contourI"
        sheet["M6"] = "contourII"
        sheet["N6"] = "filter - contour"  # Does the object have a constant contour?  3,5 (3,7) - 5
        sheet["O6"] = "Value - bigger is better"
        sheet["P6"] = "filter - transparency"  # Is the object transparent?  >0,1 (0,08)
        sheet["Q6"] = "Value - bigger is better"

        return None

    def _generate_object_table(self):
        """Insert object table header and contenct"""
        # generate header ...
        # iterate over all flakes
        sheet = self.workbook.active
        max_width = 0
        for index, flake in enumerate(self.image):
            # fill Excel table
            sheet[f"A{index + 7}"] = index
            sheet[f"B{index + 7}"] = flake.pos_x
            sheet[f"C{index + 7}"] = flake.pos_y
            sheet[f"D{index + 7}"] = flake.area
            sheet[f"E{index + 7}"] = flake.sizeX
            sheet[f"F{index + 7}"] = flake.sizeY
            sheet[f"G{index + 7}"] = flake.transparency
            sheet[f"H{index + 7}"] = flake.bright
            sheet[f"I{index + 7}"] = flake.object_height
            sheet[f"J{index + 7}"] = flake.ratio
            # add image
            img = pyxl_Image(self.image_name + f"{index}.png")
            sheet.add_image(img, f'K{index + 7}')

            # set the height of the (index+7)-th row because of the image
            sheet.row_dimensions[index + 7].height = flake.height * 0.8

            sheet[f"L{index + 7}"] = flake.contourI
            sheet[f"M{index + 7}"] = flake.contourII
            sheet[f"N{index + 7}"] = flake.filter_contour[0]
            sheet[f"O{index + 7}"] = flake.filter_contour[1]
            sheet[f"P{index + 7}"] = flake.filter_transparency[0]
            sheet[f"Q{index + 7}"] = flake.filter_transparency[1]

            if max_width < flake.width:
                max_width = flake.width

        # set the width of the K-th column because of the image
        sheet.column_dimensions['K'].width = max_width * 0.15

        return None

    def _save_to_disk(self):
        """Store the excel sheet on the filesystem"""
        self.workbook.save(self.filename)  # save Excel table

        return None
