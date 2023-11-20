from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QComboBox, QLabel, QPlainTextEdit, QFileDialog
import sys
from openpyxl import Workbook
import cv2
import os
import shutil
from find_objects import ImageCrawler, MyApp
from functions import take_webcam_image, float_question, RGB_question, manage_subfolders, read_cache, yes_no_question
import argparse
import logging as log



def main():
    # Fixed setting parameters
    calibration = 0.187  # calibration factor to get real size of sample (converting from px to um)

    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec())


def work():
    # Show info messages
    log.getLogger().setLevel(log.INFO)

    # Fixed setting parameters
    calibration = 0.187  # calibration factor to get real size of sample (converting from px to um)

    # Print a welcome screen and ask user's inputs. This funftion can make a new image by a USB webcam.
    path, name, more_output, min_size, sensitivity = dialog()

    # Load an image, find all flakes and make a catalogue them.
    figure1 = ImageCrawler(path, name, more_output, min_size, sensitivity, calibration)

    input("\nThe task has been finished. Press some key for close a script.")

main()  # For debuging in a code editor. Remove before install.

