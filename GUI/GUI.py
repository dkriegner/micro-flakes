from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QComboBox, QLabel, QPlainTextEdit, QFileDialog
import sys
from openpyxl import Workbook
import cv2
import os
import shutil
from find_objects import ImageCrawler
from functions import take_webcam_image, float_question, RGB_question, manage_subfolders, read_cache, yes_no_question
import argparse
import logging as log

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        self.label1 = QLabel('Welcome in software to automatic detect flakes in a microscope.')
        vbox.addWidget(self.label1)

        self.label2 = QLabel('Please select a source of input data:')
        vbox.addWidget(self.label2)

        self.button1 = QPushButton('Take a new photo of samples')
        self.button1.clicked.connect(self.open_option1)
        vbox.addWidget(self.button1)

        self.button2 = QPushButton('Load a photo of samples')
        self.button2.clicked.connect(self.open_option2)
        vbox.addWidget(self.button2)

        self.setWindowTitle('Flakes detector')
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def open_option1(self):
        self.option1 = Option1()

    def open_option2(self):
        self.option2 = Option2()

class Option1(QWidget):
    def __init__(self):
        super().__init__()
        self.directory = ""
        self.initUI()

    def initUI(self):
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        self.label = QLabel('Name of a new image:')
        vbox.addWidget(self.label)

        self.textbox = QTextEdit()
        vbox.addWidget(self.textbox)

        self.combobox = QComboBox()
        self.combobox.addItems(["Yes", "No"])
        vbox.addWidget(self.combobox)

        self.dirButton = QPushButton('Choose Directory')
        self.dirButton.clicked.connect(self.open_directory_dialog)
        vbox.addWidget(self.dirButton)

        self.button = QPushButton('Press Me')
        self.button.clicked.connect(self.on_click)
        vbox.addWidget(self.button)

        self.logbox = QPlainTextEdit()
        self.logbox.setReadOnly(True)
        vbox.addWidget(self.logbox)

        self.setWindowTitle('Option 1')
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def open_directory_dialog(self):
        self.directory = QFileDialog.getExistingDirectory(self, "QFileDialog.getExistingDirectory()", "")
        if not self.directory == "":
            self.logbox.appendPlainText(f'User selected directory: {self.directory}')
        else:
            self.logbox.appendPlainText('No directory selected.')

    def on_click(self):
        text = self.textbox.toPlainText()
        option = True if self.combobox.currentText() == "Yes" else False
        self.logbox.appendPlainText(f'User entered: {text}')
        self.logbox.appendPlainText(f'User selected: {option}')
        # Load an image, find all flakes and make a catalogue them.
        figure1 = ImageCrawler(self.directory, option, more_output, min_size, sensitivity, calibration)


class Option2(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        self.label = QLabel('Choose a File:')
        vbox.addWidget(self.label)

        self.button = QPushButton('Choose File')
        self.button.clicked.connect(self.open_file_dialog)
        vbox.addWidget(self.button)

        self.logbox = QPlainTextEdit()
        self.logbox.setReadOnly(True)
        vbox.addWidget(self.logbox)

        self.setWindowTitle('Option 2')
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def open_file_dialog(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Python Files (*.py)")
        if fileName:
            self.logbox.appendPlainText(f'User selected file: {fileName}')
        else:
            self.logbox.appendPlainText('No file selected.')


def main():
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

