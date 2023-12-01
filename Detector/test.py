import os
import sys
import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPlainTextEdit, QPushButton


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


class test_class_for_logging:
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.log.info("other class initialized")

    def log_something(self, msg):
        self.log.info(msg)


class MyMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.create_GUI_status()
        a = test_class_for_logging()
        a.log_something("test from other class, __init__")
        self.show()

    def create_GUI_status(self):
        self.status = QPlainTextEdit(self)
        self.status.setReadOnly(True)
        self.button = QPushButton("test log")
        self.button.clicked.connect(self.say_hello)

        sys.stdout = log_stream
        log_stream.text_written.connect(self.output_written)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.status)

        self.layout.addWidget(self.button)

        self.widget = QWidget()
        self.widget.setLayout(self.layout)

        self.setCentralWidget(self.widget)

        print("test print")
        logger.info("test log")

    def say_hello(self):
        print("Button clicked, Hello!")
        a = test_class_for_logging()
        a.log_something("test from other class, button")

    @pyqtSlot(str)
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

    handlers = []
    log_stream = EmittingStream()
    handlers.append(logging.StreamHandler(stream=log_stream))
    logging.basicConfig(level=logging.INFO, handlers=handlers)
    logger = logging.getLogger(os.path.split(__file__)[-1])

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