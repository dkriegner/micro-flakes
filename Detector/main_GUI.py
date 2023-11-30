from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QPlainTextEdit,
                             QFileDialog, QCheckBox, QSpinBox, QDoubleSpinBox, QHBoxLayout)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QTextCursor
import sys
import os
from .find_objects import ImageCrawler
from .functions import take_webcam_image
import logging as log

# set logging to terminal
log.getLogger().setLevel(log.INFO)
logger = log.getLogger(os.path.split(__file__)[-1])


class EmittingStream(QObject):
    """
    Stream to communicate between the threads
    """
    name = "GUIStream"
    text_written = pyqtSignal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass

class MyApp(QWidget):
    """Create a windows widget with user's input dialog."""

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        """The content of the window widget."""
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        self.label0 = QLabel('Welcome in software to automatic detect flakes in a microscope.')
        vbox.addWidget(self.label0)

        self.label1 = QLabel('Choose a input photo:')
        vbox.addWidget(self.label1)

        hbox = QHBoxLayout()  # Create a horizontal box layout for the buttons
        vbox.addLayout(hbox)

        self.button = QPushButton('Choose File')
        self.button.clicked.connect(self.open_file_dialog)
        self.button.setToolTip('Open existing photo with Flakes in a microscope in the black field mode')
        hbox.addWidget(self.button)

        self.saveButton = QPushButton('Take a photo')
        self.saveButton.clicked.connect(self.save_file_dialog)
        self.saveButton.setToolTip('Take a photo by a USB webcam with Flakes in a microscope in the black field mode')
        hbox.addWidget(self.saveButton)

        self.checkbox1 = QCheckBox('Do you want output images?')
        self.checkbox1.setChecked(False)  # Set the checkbox to be unchecked by default
        self.checkbox1.setToolTip("Image from the first iteration. It\'s usable to control process.")
        vbox.addWidget(self.checkbox1)

        hbox4 = QHBoxLayout()  # Create a horizontal box layout for the buttons
        vbox.addLayout(hbox4)

        self.label3 = QLabel('Minimal area of edge of object in um^2:')
        hbox4.addWidget(self.label3)

        self.spinbox = QDoubleSpinBox()
        self.spinbox.setValue(42.4)  # Set the default value
        self.spinbox.setRange(0, 500)
        # Set the width of the spinbox to 100 pixels
        self.spinbox.setFixedWidth(100)
        self.spinbox.setToolTip("Smaller flakes will be removed as noice.")
        hbox4.addWidget(self.spinbox)

        hbox3 = QHBoxLayout()  # Create a horizontal box layout for the buttons
        vbox.addLayout(hbox3)

        self.label4 = QLabel('Sensitivity of script on objects:')
        hbox3.addWidget(self.label4)

        self.spinbox2 = QSpinBox()
        self.spinbox2.setValue(40)  # Set the default value
        self.spinbox2.setRange(0, 255)
        self.spinbox2.setFixedWidth(100)

        self.spinbox2.setToolTip("Ever pixel having RGB value bigger this value will be marked.")
        hbox3.addWidget(self.spinbox2)

        self.button2 = QPushButton('Start')
        self.button2.clicked.connect(self.on_click)
        self.button2.setToolTip("Find flakes.")
        vbox.addWidget(self.button2)

        self.logbox = QPlainTextEdit()
        self.logbox.setReadOnly(True)
        self.logbox.setMinimumSize(350, 150)
        # set outputStream as stdout (i.e. all output is written to status)
        self.output_stream = EmittingStream(text_written=self.output_written)
        sys.stdout = self.output_stream
        # add new handler to logger
        handler = log.StreamHandler(self.output_stream)
        handler.setLevel(log.DEBUG)
        formatter = log.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        vbox.addWidget(self.logbox)

        self.button3 = QPushButton('Open Catalogue in Excel')
        self.button3.clicked.connect(self.on_click2)
        vbox.addWidget(self.button3)

        hbox2 = QHBoxLayout()  # Create a horizontal box layout for the buttons
        vbox.addLayout(hbox2)

        self.weblink = QLabel('<a href="https://github.com/dkriegner/micro-flakes/tree/main/Detector">Project webpage</a>')
        self.weblink.setOpenExternalLinks(True)
        hbox2.addWidget(self.weblink)

        self.label5 = QLabel('Version 0.0.6')
        self.label5.setAlignment(Qt.AlignmentFlag.AlignRight)
        hbox2.addWidget(self.label5)

        self.setWindowTitle('Flakes detector')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'ICON.ico')))  # Set the window icon
        self.setGeometry(300, 300, 300, 200)
        self.show()
        print("test print3")
        logger.info("test log3")


    def output_written(self, text):
        """
        appends the most recent text to the end of the display and makes sure
        that the cursor remains at the end
        """
        if text.strip("\n") != "":
            self.logbox.appendPlainText(text.strip("\n"))
            self.logbox.repaint()
            try:
                self.logbox.moveCursor(QTextCursor.MoveOperation.End)
            except Exception:  # upon cleanup after exception this can fail
                pass

    def open_file_dialog(self):
        """Action of Choose File button."""
        self.fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "Images (*.png *.xpm *.jpg *.bmp *.gif);;All Files (*)")
        if self.fileName:
            self.logbox.appendPlainText(f'Selected input file: {self.fileName}')
        else:
            self.logbox.appendPlainText('No file selected.')

    def save_file_dialog(self):
        """Action of Take a photo button."""
        self.fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "", "All Files (*)")
        if self.fileName:
            self.logbox.appendPlainText("Opening a webcam.\nPress Esc to take a new photo.")
            self.logbox.repaint()
            path, name = os.path.split(self.fileName)
            take_webcam_image(path, name)
            self.fileName += ".jpg"
            self.logbox.appendPlainText(f'The photo is saved to: {self.fileName}')
        else:
            self.logbox.appendPlainText('No file saved.')

    def on_click(self):
        """Action of Start button."""
        # Fixed setting parameters
        calibration = 0.187  # calibration factor to get real size of sample (converting from px to um)
        print("test print2")
        logger.info("test log2")
        # Get user input from the  windows widget.
        try:
            str(self.fileName)
        except:
            self.logbox.appendPlainText('Nothing input is selected!')
            return None
        path, name = os.path.split(self.fileName)

        more_output = self.checkbox1.isChecked()

        min_size = float(self.spinbox.value())/1.6952

        sensitivity = int(self.spinbox2.value())

        self.logbox.appendPlainText(f'Finding flakes with user\'s parameters:\n'
                                    f'Path: {path}\nName: {name}\nMin. size: {min_size*1.6952}\nSensitivity: {sensitivity}')
        self.logbox.repaint()
        log.debug(f'User entered: {name}, {path}, {more_output}, {min_size*1.6952}, {sensitivity}')

        # Load an image, find all flakes and make a catalogue them.
        figure1 = ImageCrawler(path, name, more_output, min_size, sensitivity, calibration, 2)
        self.logbox.appendPlainText(f"The task has been finished. {len(figure1.marked_objects)} objects have been processed.\n"
                                    f"The catalogue is saved to: {path}/output/Catalogue_{name}.xlsx")
        self.output = f"{path}/output/Catalogue_{name}.xlsx"

    def on_click2(self):
        """Action of Open catalogue in Excel button."""
        try:
            os.system(self.output)
        except:
            self.logbox.appendPlainText("There is no output. Click to start!")


def main():
    if os.name == 'nt':
        try:
            from ctypes import windll  # Only exists on Windows.

            myappid = f'python.micro-flakes.gui.version'
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except ImportError:
            pass



    # Create window widget
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec())


#main()  # For debuging in a code editor. Remove before install.
