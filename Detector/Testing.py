import os
import sys
import logging

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPlainTextEdit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(os.path.split(__file__)[-1])


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


class MyMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.create_GUI_status()
        self.show()

    def create_GUI_status(self):
        self.status = QPlainTextEdit(self)
        self.status.setReadOnly(True)

        # set outputStream as stdout (i.e. all output is written to status)
        self.output_stream = EmittingStream(text_written=self.output_written)
        sys.stdout = self.output_stream
        # add new handler to logger
        handler = logging.StreamHandler(self.output_stream)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.status)
        self.widget = QWidget()
        self.widget.setLayout(self.layout)

        self.setCentralWidget(self.widget)

        print("test print")
        logger.info("test log")

    def output_written(self, text):
        """
        appends the most recent text to the end of the display and makes sure
        that the cursor remains at the end
        """
        if text.strip("\n") != "":
            self.status.appendPlainText(text.strip("\n"))
            try:
                self.status.moveCursor(QTextCursor.MoveOperation.End)
            except Exception:  # upon cleanup after exception this can fail
                pass


if __name__ == "__main__":

    if os.name == 'nt':
        try:
            from ctypes import windll  # Only exists on Windows.

            myappid = f'python.micro-flakes.gui.version'
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except ImportError:
            pass

    app = QApplication(sys.argv)
    app.setDesktopFileName(
        f"python.micro-flakes.gui")

    print("test to terminal")
    logger.info("test log before main window")
    mainwin = MyMainWindow()
    ret = app.exec()

    sys.stdout = sys.__stdout__  # reset stdout
    sys.exit(ret)