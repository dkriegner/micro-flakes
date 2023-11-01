from PIL import Image, ImageDraw
import numpy as np


def find_objects(path, name, out1, min_size, sensitivity):
    pim = Image.open(f"{path}/input/{name}")  # open the original photo
    print("The photo has been opened.")

    print("changing gamma and contrast of the original photo")
    # pim = gamma_correct(pim, 1.5)
    # pim = change_contrast(pim, 100)
    pim.save(f"{path}/output/org_gc.png")  # save the original photo with gamma and contrast correction
    pro = pim.load()

    # create new images for processing (object area in low resolution)
    nw = Image.new('RGB', (pim.size[0], pim.size[1]), color='white')
    new = nw.load()

    detect = []  # coordinates of detected object area

    print("marking non-black area")
    for i in range(pim.size[0] - 1):
        for j in range(pim.size[1] - 1):
            R, G, B = pro[i, j]
            if R > sensitivity or G > sensitivity or B > sensitivity:
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
    for obj in anything.copy():
        if len(obj) <= min_size:
            anything.remove(obj)

    # create output photo of detected object with centres and area of detected edges
    if out1 == 1:

        ts = Image.new('RGB', (pim.size[0], pim.size[1]), color='white')
        test = ts.load()

        for n in anything:
            for (i, j) in n:
                for k in range(i - 3, i + 3):
                    for l in range(j - 3, j + 3):
                        test[k, l] = (256, 0, 0)

        centre = []
        for q in anything:
            centre.append((int(sum(x for (x, y) in q) / len(q)),
                           int(sum(y for (x, y) in q) / len(q))))

        p = 0
        for (i, j) in centre:
            ImageDraw.Draw(ts).text((i + 5, j + 5), str(len(anything[p])), (0, 0, 0))
            for k in range(i - 5, i + 5):
                for l in range(j - 5, j + 5):
                    test[k, l] = (0, 0, 0)
            p += 1

        name = "first_step"  # name output files of the first iteration
        ts.save(f'{path}/output/{name}_1.png')  # store detected objects with centre and size of edge
        pim.save(f'{path}/output/{name}_2.png')  # store marked object area
        nw.save(f'{path}/output/{name}_3.png')  # store object area in low resolution
        ts.close()

    pim.close()
    nw.close()

    return anything
