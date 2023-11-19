import logging as log
import cv2
import os
import shutil


def take_webcam_image(path: str, filename: str):
    '''This function takes a photo by a USB webcam. The first parameter is the path of a new photo.
    The second parameter is the name of a new photo.'''
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
        raise log.error("Cannot open webcam")
    while True:
        ret, frame = cap.read()
        # cv2.normalize(frame, frame, 100, 255, cv2.NORM_MINMAX)
        # frame = cv2.resize(frame, None, fx=1, fy=1, interpolation=cv2.INTER_AREA)
        cv2.imshow('Input', frame)
        cv2.imwrite(filename=f'{path}/{filename}.jpg', img=frame)
        c = cv2.waitKey(1)
        if c == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    return None

def float_question(question: str, default: float | None = None) -> float:
    """Get a float answer for a question."""
    choices = f' [{default}]: ' if default else ':'
    reply = str(input(question + choices)).lower().strip() or default
    try:
        return float(reply)
    except (ValueError, TypeError):
        log.warning("invalid input! try again")  # optional print message
        return float_question(question, default)

def RGB_question(question: int, default: int | None = None) -> int:
    """Get an integer answer between 0 and 255 for a question."""
    choices = f' [{default}]: ' if default else ':'
    reply = str(input(question + choices)).lower().strip() or default
    try:
        test = int(reply)
        if 0 <= test <= 255:
            return int(reply)
        else:
            log.warning("invalid input! write integer between 0 and 255")  # optional print message
            return float_question(question, default)
    except (ValueError, TypeError):
        log.warning("invalid input! try again")  # optional print message
        return float_question(question, default)

def yes_no_question(question: str, default: bool = True) -> bool:
    """Get boolean answer for a question."""
    choices = ' [Y/n]: ' if default else ' [y/N]:'
    default_answer = 'y' if default else 'n'
    reply = str(input(question + choices)).lower().strip() or default_answer
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        log.warning("invalid input! try again")  # optional print message
        return yes_no_question(question, default)

def manage_subfolders(path: str):
    '''Create the output and input subfolder or clean the output subfolder'''
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

