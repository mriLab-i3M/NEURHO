"""
@author:    José Miguel Algarín
@email:     josalggui@i3m.upv.es
@affiliation:MRILab, i3M, CSIC, Valencia, Spain
"""
import sys
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QSizePolicy, \
    QApplication, QGridLayout
from PyQt5.QtCore import QSize, QThreadPool
import qdarkstyle
from controller.controller_figures import PositioningFiguresLayoutController



class PositioningWindow(QWidget):
    def __init__(self, session=None, main=None):
        super(PositioningWindow, self).__init__()

        # Define parameters
        self.main = main
        self.session = session
        self.setWindowTitle("Positioning Window")
        self.setGeometry(300, 300, 500, 500)
        self.styleSheet = qdarkstyle.load_stylesheet_pyqt5()
        self.setStyleSheet(self.styleSheet)

        # Layouts
        layout_main = QVBoxLayout()
        layout_toolbars = QHBoxLayout()
        self.layout_widgets = QGridLayout()
        self.setLayout(layout_main)
        layout_main.addLayout(layout_toolbars)
        layout_main.addLayout(self.layout_widgets)

        ############## toolbars ###################

        # TODO: Include toolbars

        ################# layout_qwidget #####################

        self.figures_layout = PositioningFiguresLayoutController(main=self)
        self.layout_widgets.addWidget(self.figures_layout, 0, 1)





if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PositioningWindow(session={'directory': 'experiments'})
    window.show()
    sys.exit(app.exec_())