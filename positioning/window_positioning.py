"""
@author:    José Miguel Algarín
@email:     josalggui@i3m.upv.es
@affiliation:MRILab, i3M, CSIC, Valencia, Spain
"""
import copy
import os
import sys

import numpy as np
import scipy as sp
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QApplication, QGridLayout
import qdarkstyle
from positioning.widget_manual_control import WidgetManualControl
from positioning.widget_plot3d import Plot3DWidget
from positioning.widget_figures import FiguresLayoutWidget


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
        self.layout_left = QVBoxLayout()
        self.layout_widgets.addLayout(self.layout_left, 0, 0)
        layout_main.addLayout(layout_toolbars)
        layout_main.addLayout(self.layout_widgets)

        ############## toolbars ###################

        # TODO: Include toolbars

        ################# layout_qwidget #####################

        # Add manual control widget
        manual_control_widget = WidgetManualControl(main=self)
        self.layout_left.addWidget(manual_control_widget)

        # Add figure display area
        self.figures_layout = FiguresLayoutWidget(main=self)
        self.layout_widgets.addWidget(self.figures_layout, 0, 1)

        # Define console
        try:
            self.console = self.main.MaRGE.console
        except:
            pass

        # Load a plot imaging from RAREprotocols_T1_SAG_Right.2023.10.24.19.28.37.989.mat
        self.rawDataLoading()

    def fix_console(self):
        self.layout_left.addWidget(self.console)

    def rawDataLoading(self, file_path="../", file_name="RAREprotocols_T1_SAG_Right.2023.10.24.19.28.37.989.mat"):
        """
        Load raw data from a .mat file and update the image view widget.
        """
        # Prompt the user to select a .mat file
        if not file_path:
            file_path = self.loadmatFile()
            file_name = os.path.basename(file_path)
        else:
            file_path = file_path+file_name

        # Load the .mat file and get the image and axes
        self.mat_data = sp.io.loadmat(file_path)
        image = np.abs(self.mat_data['image3D'])
        axes = self.mat_data['axesOrientation'][0]

        # Fix image orientation
        image, x_label, y_label, title = self.fixImage(image, axes)

        # Create the plot widget and add it to the figures_layout
        image_widget = Plot3DWidget(main=self, data=image, title=title, x_label=x_label, y_label=y_label)
        self.figures_layout.clear_figures_layout()
        self.figures_layout.addWidget(image_widget)

    def fixImage(self, matrix3d, axes=None):
        matrix = copy.copy(matrix3d)
        if axes is None:  # No orientation for h5 test
            title = "No orientation"
            matrix = matrix
            x_label = "X"
            y_label = "Y"
        elif axes[2] == 2:  # Sagittal
            title = "Sagittal"
            if axes[0] == 0 and axes[1] == 1:  # OK
                matrix = np.flip(matrix, axis=2)
                matrix = np.flip(matrix, axis=1)
                x_label = "(-Y) A | PHASE | P (+Y)"
                y_label = "(-X) I | READOUT | S (+X)"
            else:
                matrix = np.transpose(matrix, (0, 2, 1))
                matrix = np.flip(matrix, axis=2)
                matrix = np.flip(matrix, axis=1)
                x_label = "(-Y) A | READOUT | P (+Y)"
                y_label = "(-X) I | PHASE | S (+X)"
        elif axes[2] == 1:  # Coronal
            title = "Coronal"
            if axes[0] == 0 and axes[1] == 2:  # OK
                matrix = np.flip(matrix, axis=2)
                matrix = np.flip(matrix, axis=1)
                matrix = np.flip(matrix, axis=0)
                x_label = "(+Z) R | PHASE | L (-Z)"
                y_label = "(-X) I | READOUT | S (+X)"
            else:
                matrix = np.transpose(matrix, (0, 2, 1))
                matrix = np.flip(matrix, axis=2)
                matrix = np.flip(matrix, axis=1)
                matrix = np.flip(matrix, axis=0)
                x_label = "(+Z) R | READOUT | L (-Z)"
                y_label = "(-X) I | PHASE | S (+X)"
        elif axes[2] == 0:  # Transversal
            title = "Transversal"
            if axes[0] == 1 and axes[1] == 2:
                matrix = np.flip(matrix, axis=2)
                matrix = np.flip(matrix, axis=1)
                x_label = "(+Z) R | PHASE | L (-Z)"
                y_label = "(+Y) P | READOUT | A (-Y)"
            else:  # OK
                matrix = np.transpose(matrix, (0, 2, 1))
                matrix = np.flip(matrix, axis=2)
                matrix = np.flip(matrix, axis=1)
                x_label = "(+Z) R | READOUT | L (-Z)"
                y_label = "(+Y) P | PHASE | A (-Y)"

        return matrix, x_label, y_label, title


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PositioningWindow(session={'directory': 'experiments'})
    window.show()
    sys.exit(app.exec_())
