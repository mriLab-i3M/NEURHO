import sys

import qdarkstyle
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel

from controller.controller_main import MainController
from controller.controller_positioning import PositioningController


class WorkflowWindow(QMainWindow):
    def __init__(self, session=None, demo=True):
        super().__init__()

        self.session = session
        self.demo = demo

        self.setWindowTitle("NEURHO GUI")
        self.setGeometry(100, 100, 600, 400)

        # Create a QTabWidget
        self.tabs = QTabWidget()

        # Set stylesheet
        self.styleSheet = qdarkstyle.load_stylesheet_pyqt5()
        self.setStyleSheet(self.styleSheet)

        # Create the individual tabs
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()

        # Add the tabs to the QTabWidget
        self.tabs.addTab(self.tab1, "MRI Scan")
        self.tabs.addTab(self.tab2, "Co-register")
        self.tabs.addTab(self.tab3, "Positioning")
        self.tabs.addTab(self.tab4, "Treatment")

        # Set up the layout for each tab
        self.setupTab1()
        self.setupTab2()
        self.setupTab3()
        self.setupTab4()

        # Set the central widget of the main window to be the tabs
        self.setCentralWidget(self.tabs)

        # Connect the signal for when the tab changes
        self.tabs.currentChanged.connect(self.onTabChange)

    def onTabChange(self, index):
        """Handle what happens when a tab is clicked."""
        if index == 0:
            self.MaRGE.fix_console()
            print("MRI Scan tab")
            # Add logic specific to MRI Scan tab here
        elif index == 1:
            print("Co-register tab clicked")
            # Add logic specific to Co-register tab here
        elif index == 2:
            self.PositioningController.fix_console()
            print("Positioning tab")
            # Add logic specific to Positioning tab here
        elif index == 3:
            print("Treatment tab clicked")
            # Add logic specific to Treatment tab here

    def setupTab1(self):
        self.MaRGE = MainController(self.session, demo=True)

        # Create a layout for the tab and add the existing GUI's central widget to it
        layout = QVBoxLayout()
        layout.addWidget(self.MaRGE)  # Add your existing GUI's central widget to the tab

        # Set the layout to the tab
        self.tab1.setLayout(layout)

    def setupTab2(self):
        layout = QVBoxLayout()
        label = QLabel("This is Tab 2")
        layout.addWidget(label)
        self.tab2.setLayout(layout)

    def setupTab3(self):
        self.PositioningController = PositioningController(session=self.session, main=self)

        # Create a layout for the tab and add the Positioning GUI
        layout_positioning = QVBoxLayout()
        layout_positioning.addWidget(self.PositioningController)

        # Set the layout to the tab
        self.tab3.setLayout(layout_positioning)

    def setupTab4(self):
        layout = QVBoxLayout()
        label = QLabel("This is Tab 4")
        layout.addWidget(label)
        self.tab4.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorkflowWindow(session={'directory': 'experiments'}, demo=True)
    window.show()
    sys.exit(app.exec_())
