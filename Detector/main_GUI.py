from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QComboBox, QLabel, QPlainTextEdit,
                             QFileDialog, QStackedWidget)
import sys
import os
from find_objects import ImageCrawler
from functions import take_webcam_image
import logging as log


class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        self.stackedWidget = QStackedWidget()
        vbox.addWidget(self.stackedWidget)

        self.welcome = Welcome(self.stackedWidget)
        self.option1 = Option1()
        self.option2 = Option2()

        self.stackedWidget.addWidget(self.welcome)
        self.stackedWidget.addWidget(self.option1)
        self.stackedWidget.addWidget(self.option2)

        self.setWindowTitle('Flakes detector')
        self.setGeometry(300, 300, 300, 200)
        self.show()

class Welcome(QWidget):
    def __init__(self, stackedWidget):
        super().__init__()

        self.stackedWidget = stackedWidget
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
        self.stackedWidget.setCurrentIndex(1)

    def open_option2(self):
        self.stackedWidget.setCurrentIndex(2)


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

        self.dirButton = QPushButton('Choose Directory')
        self.dirButton.clicked.connect(self.open_directory_dialog)
        vbox.addWidget(self.dirButton)

        self.label2 = QLabel('Do you want output images?')
        vbox.addWidget(self.label2)

        self.combobox = QComboBox()
        self.combobox.addItems(["No", "Yes"])
        vbox.addWidget(self.combobox)

        self.label3 = QLabel('Minimal area of edge of object in um^2 [42.4]:')
        vbox.addWidget(self.label3)

        self.textbox2 = QTextEdit()
        vbox.addWidget(self.textbox2)

        self.label4 = QLabel('Sensitivity of script on objects in dark field [40]:')
        vbox.addWidget(self.label4)

        self.textbox3 = QTextEdit()
        vbox.addWidget(self.textbox3)

        self.button = QPushButton('Start')
        self.button.clicked.connect(self.on_click)
        vbox.addWidget(self.button)

        self.logbox = QPlainTextEdit()
        self.logbox.setReadOnly(True)
        vbox.addWidget(self.logbox)

        self.button3 = QPushButton('Open Catalogue in Excel')
        self.button3.clicked.connect(self.on_click2)
        vbox.addWidget(self.button3)

        self.setGeometry(300, 300, 300, 200)
        self.show()

    def open_directory_dialog(self):
        self.directory = QFileDialog.getExistingDirectory(self, "QFileDialog.getExistingDirectory()", "")
        if not self.directory == "":
            self.logbox.appendPlainText(f'User selected directory: {self.directory}')
        else:
            self.logbox.appendPlainText('No directory selected.')

    def on_click(self):
        # Fixed setting parameters
        calibration = 0.187  # calibration factor to get real size of sample (converting from px to um)

        # User input
        path = str(self.directory)
        name = self.textbox.toPlainText()
        more_output = True if self.combobox.currentText() == "Yes" else False

        if self.textbox2.toPlainText():
            min_size = float(self.textbox2.toPlainText()) / 1.6952
        else:
            min_size = 42.4 / 1.6952

        if self.textbox3.toPlainText():
            sensitivity = int(self.textbox3.toPlainText())
        else:
            sensitivity = 40

        self.logbox.appendPlainText(f'Finding flakes with user\'s parameters:\n'
                                    f'Path: {path}\nName: {name}\nMin. size: {min_size*1.6952}\nSensitivity: {sensitivity}')
        log.debug(f'User entered: {name}, {path}, {more_output}, {min_size*1.6952}, {sensitivity}')

        self.logbox.appendPlainText("Taking a new photo.")
        take_webcam_image(path, name)
        name += ".jpg"

        # Load an image, find all flakes and make a catalogue them.
        figure1 = ImageCrawler(path, name, more_output, min_size, sensitivity, calibration, 2)
        self.logbox.appendPlainText(f"The task has been finished. {len(figure1.marked_objects)} objects have been processed.\n"
                                    f"The catalogue is saved to: {path}/output/Catalogue_{name}.xlsx")
        self.output = f"{path}/output/Catalogue_{name}.xlsx"

    def on_click2(self):
        try:
            os.system(self.output)
        except:
            self.logbox.appendPlainText("There is no output. Click to start!")


class Option2(QWidget):
    # Load an existed image
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

        self.label2 = QLabel('Do you want output images?')
        vbox.addWidget(self.label2)

        self.combobox = QComboBox()
        self.combobox.addItems(["No", "Yes"])
        vbox.addWidget(self.combobox)

        self.label3 = QLabel('Minimal area of edge of object in um^2 [42.4]:')
        vbox.addWidget(self.label3)

        self.textbox2 = QTextEdit()
        vbox.addWidget(self.textbox2)

        self.label4 = QLabel('Sensitivity of script on objects in dark field [40]:')
        vbox.addWidget(self.label4)

        self.textbox3 = QTextEdit()
        vbox.addWidget(self.textbox3)

        self.button2 = QPushButton('Start')
        self.button2.clicked.connect(self.on_click)
        vbox.addWidget(self.button2)

        self.logbox = QPlainTextEdit()
        self.logbox.setReadOnly(True)
        vbox.addWidget(self.logbox)

        self.button3 = QPushButton('Open Catalogue in Excel')
        self.button3.clicked.connect(self.on_click2)
        vbox.addWidget(self.button3)

        self.setGeometry(300, 300, 300, 200)
        self.show()

    def open_file_dialog(self):
        self.fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Python Files (*.py)")
        if self.fileName:
            self.logbox.appendPlainText(f'Selected input file: {self.fileName}')
        else:
            self.logbox.appendPlainText('No file selected.')

    def on_click(self):
        # Fixed setting parameters
        calibration = 0.187  # calibration factor to get real size of sample (converting from px to um)

        # User input
        try:
            path_name = str(self.fileName)
        except:
            self.logbox.appendPlainText('Nothing input is selected!')
            return None

        index = path_name.rfind("/")
        name = path_name[index+1:]
        path = path_name[:index]
        more_output = True if self.combobox.currentText() == "Yes" else False

        if self.textbox2.toPlainText():
            min_size = float(self.textbox2.toPlainText())/1.6952
        else:
            min_size = 42.4/1.6952
            
        if self.textbox3.toPlainText():
            sensitivity = int(self.textbox3.toPlainText())
        else:
            sensitivity = 40

        self.logbox.appendPlainText(f'Finding flakes wit user\'s parameters:\n'
                                    f'Path: {path}\nName: {name}\nMin. size: {min_size*1.6952}\nSensitivity: {sensitivity}')
        log.debug(f'User entered: {name}, {path}, {more_output}, {min_size*1.6952}, {sensitivity}')

        # Load an image, find all flakes and make a catalogue them.
        figure1 = ImageCrawler(path, name, more_output, min_size, sensitivity, calibration, 2)
        self.logbox.appendPlainText(f"The task has been finished. {len(figure1.marked_objects)} objects have been processed.\n"
                                    f"The catalogue is saved to: {path}/output/Catalogue_{name}.xlsx")
        self.output = f"{path}/output/Catalogue_{name}.xlsx"

    def on_click2(self):
        try:
            os.system(self.output)
        except:
            self.logbox.appendPlainText("There is no output. Click to start!")


def main():
    # Fixed setting parameters
    log.getLogger().setLevel(log.INFO)
    log.basicConfig(format='%(message)s')
    calibration = 0.187  # calibration factor to get real size of sample (converting from px to um)

    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec())


main()  # For debuging in a code editor. Remove before install.
