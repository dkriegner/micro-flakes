from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QPlainTextEdit,
                             QFileDialog, QCheckBox, QSpinBox, QDoubleSpinBox, QHBoxLayout)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QTextCursor
import sys
import os
import logging as log

from find_objects import ImageCrawler
from functions import take_webcam_image, read_cache


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

    def __init__(self, log_stream):
        self.output = None
        self.fileName = None
        self.log_stream = log_stream
        super().__init__()
        try:
            # default directory for explorer dialogs
            self.default_dir = read_cache()[0]
            # calibration factor to get real size of sample (converting from px to um)
            self.calibration = float(read_cache()[1])
        except:
            self.default_dir = None
            self.calibration = 0.187

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

        hbox5 = QHBoxLayout()  # Create a horizontal box layout for the buttons
        vbox.addLayout(hbox5)

        self.save = QPushButton('Start')
        self.save.clicked.connect(self.on_click)
        self.save.setToolTip("Find flakes.")
        hbox5.addWidget(self.save)

        self.config = QPushButton('Configurations')
        self.config.clicked.connect(self.on_click3)
        self.config.setToolTip("Calibrations")
        hbox5.addWidget(self.config)

        self.logbox = QPlainTextEdit()
        self.logbox.setReadOnly(True)
        self.logbox.setMinimumSize(350, 150)
        self.log_stream.text_written.connect(self.output_written)
        vbox.addWidget(self.logbox)

        self.button3 = QPushButton('Open Catalogue in Excel')
        self.button3.clicked.connect(self.on_click2)
        vbox.addWidget(self.button3)

        hbox2 = QHBoxLayout()  # Create a horizontal box layout for the buttons
        vbox.addLayout(hbox2)

        self.weblink = QLabel(
            '<a href="https://github.com/dkriegner/micro-flakes/tree/main/Detector">Project webpage</a>')
        self.weblink.setOpenExternalLinks(True)
        hbox2.addWidget(self.weblink)

        self.label5 = QLabel('Version 0.1.1')
        self.label5.setAlignment(Qt.AlignmentFlag.AlignRight)
        hbox2.addWidget(self.label5)

        self.setWindowTitle('Flakes detector')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'ICON.ico')))  # Set the window icon
        self.setGeometry(300, 300, 300, 200)
        self.show()

    @pyqtSlot(str)
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
        # Load last working directory
        if os.path.exists(self.default_dir):
            self.fileName, _ = QFileDialog.getOpenFileName(self, "Open an input File", self.default_dir,
                                                           "Images (*.png *.xpm *.jpg *.bmp *.gif);;All Files (*)")
        else:
            log.warning("The default path does not exist!")
            self.fileName, _ = QFileDialog.getOpenFileName(self, "Open an input File", "",
                                                           "Images (*.png *.xpm *.jpg *.bmp *.gif);;All Files (*)")
        if self.fileName:
            self.logbox.appendPlainText(f'Selected input file: {self.fileName}')
        else:
            self.logbox.appendPlainText('No file selected.')

    def save_file_dialog(self):
        """Action of Take a photo button."""
        if os.path.exists(self.default_dir):
            self.fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", self.default_dir,
                                                           "*.jpg;;*.png;;*.bmp;;*.gif")
        else:
            self.fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                           "*.jpg;;*.png;;*.bmp;;*.gif")
        if self.fileName:
            self.logbox.appendPlainText("Opening a webcam.\nPress Enter to take a new photo.")
            self.logbox.repaint()
            path, name = os.path.split(self.fileName)
            take_webcam_image(path, name)
            self.logbox.appendPlainText(f'The photo is saved to: {self.fileName}')
        else:
            self.logbox.appendPlainText('No file saved.')

    def on_click(self):
        """Action of Start button."""
        # Get user input from the widget.
        try:
            str(self.fileName)
        except:
            self.logbox.appendPlainText('Nothing input is selected!')
            return None
        path, name = os.path.split(self.fileName)

        more_output = self.checkbox1.isChecked()

        min_size = float(self.spinbox.value()) / 1.6952

        sensitivity = int(self.spinbox2.value())

        self.logbox.appendPlainText(f'Finding flakes with user\'s parameters:\n'
                                    f'Path: {path}\nName: {name}\nMin. size: {min_size * 1.6952}\nSensitivity: {sensitivity}')
        self.logbox.repaint()
        log.debug(f'User entered: {name}, {path}, {more_output}, {min_size * 1.6952}, {sensitivity}')

        # Load an image, find all flakes and make a catalogue them.
        figure1 = ImageCrawler(path, name, more_output, min_size, sensitivity, self.calibration)
        self.logbox.appendPlainText(
            f"The task has been finished. {len(figure1.marked_objects)} objects have been processed.\n"
            f"The catalogue is saved to: {path}/output/Catalogue_{name}.xlsx")
        self.output = f"{path}/output/Catalogue_{name}.xlsx"

    def on_click2(self):
        """Action of Open catalogue in Excel button."""
        try:
            if sys.platform.startswith('win'):
                os.system(self.output)
            else:
                os.system(f"xdg-open {self.output}")
        except:
            self.logbox.appendPlainText("There is no output. Click to start!")

    def on_click3(self):
        # Create a new widget instance
        self.new_widget = Configurations(self)
        # Show the new widget
        self.new_widget.show()


class Configurations(QWidget):
    """Create a windows widget with user's configurations."""

    def __init__(self, parent: MyApp):
        self.folder_name = None
        self.parent = parent
        try:
            # Set the default directory to the user's home directory
            self.default_dir = read_cache()[0]
        except:
            self.default_dir = None
        super().__init__()
        self.initUI()

    def initUI(self):
        """The content of the configuration widget."""
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        self.button = QPushButton('Choose default path')
        self.button.clicked.connect(self.chooseFolderDialog)
        self.button.setToolTip('Set existing directory')
        vbox.addWidget(self.button)

        hbox = QHBoxLayout()  # Create a horizontal box layout for the buttons
        vbox.addLayout(hbox)

        self.label3 = QLabel('Size scale in um/px')
        hbox.addWidget(self.label3)

        self.spinbox = QDoubleSpinBox()
        try:
            default_ratio = float(read_cache()[1])
            self.spinbox.setValue(default_ratio)  # Set the default value
        except:
            self.spinbox.setValue(0.187)  # Set the default value
        self.spinbox.setRange(0, 10)
        # Set the width of the spinbox to 100 pixels
        self.spinbox.setFixedWidth(100)
        self.spinbox.setDecimals(4)
        self.spinbox.setSingleStep(0.001)
        self.spinbox.setToolTip("Set scale to calculate of size and area of objects")
        hbox.addWidget(self.spinbox)

        hbox2 = QHBoxLayout()  # Create a horizontal box layout for the buttons
        vbox.addLayout(hbox2)

        self.save = QPushButton('Apply')
        self.save.clicked.connect(self.on_click)
        self.save.setToolTip("Save configurations to CACHE")
        hbox2.addWidget(self.save)

        self.discard = QPushButton('Cancel')
        self.discard.clicked.connect(self.on_click2)
        self.discard.setToolTip("Discard new configurations")
        hbox2.addWidget(self.discard)

        self.setWindowTitle('Configurations')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'ICON.ico')))  # Set the window icon
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def chooseFolderDialog(self):
        if not (self.default_dir is None):
            # Invoke the QFileDialog.getExistingDirectory function with the default directory
            self.folder_name = QFileDialog.getExistingDirectory(self, "Choose Folder", self.default_dir)
        else:
            # Invoke the QFileDialog.getExistingDirectory function with the default directory
            self.folder_name = QFileDialog.getExistingDirectory(self, "Choose Folder", "")

    def on_click(self):
        # Open the file in write mode, which will overwrite the existing content
        if self.folder_name is None and self.default_dir is None:
            toWrite = ["", str(self.spinbox.value())]
        elif self.folder_name is None and not (self.default_dir is None):
            toWrite = [self.default_dir, str(self.spinbox.value())]
        else:
            toWrite = [self.folder_name, str(self.spinbox.value())]

        with open("CACHE", 'w') as file:
            # Loop through each element in the list
            for element in toWrite:
                # Write the element to the file, followed by a newline character
                file.write(element + '\n')
        self.parent.logbox.appendPlainText(f"Default directory: {toWrite[0]}\nDefault scale: {toWrite[0]} um/px")
        self.close()

    def on_click2(self):
        self.parent.logbox.appendPlainText("The new configuration does not save.")
        self.close()


def main():
    handlers = []
    log_stream = EmittingStream()
    sys.stdout = log_stream
    handlers.append(log.StreamHandler(stream=log_stream))
    log.basicConfig(level=log.INFO, handlers=handlers, format='%(message)s')
    logger = log.getLogger(os.path.split(__file__)[-1])

    if os.name == 'nt':
        try:
            from ctypes import windll  # Only exists on Windows.

            myappid = f'python.micro-flakes.gui.version'
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except ImportError:
            pass

    # Create window widget
    app = QApplication(sys.argv)
    ex = MyApp(log_stream)
    sys.exit(app.exec())


main()
