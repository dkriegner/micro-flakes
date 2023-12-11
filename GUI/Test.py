from PyQt6.QtWidgets import QApplication, QWidget, QPushButton
import sys

class MainWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.button = QPushButton('Open New Widget', self)
        self.button.clicked.connect(self.openNewWidget)
        self.button.resize(150, 30)
        self.button.move(50, 50)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Main Widget')
        self.show()

    def openNewWidget(self):
        # Create a new widget instance
        self.new_widget = NewWidget()
        # Show the new widget
        self.new_widget.show()

class NewWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(600, 300, 200, 100)
        self.setWindowTitle('New Widget')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_widget = MainWidget()
    sys.exit(app.exec())
