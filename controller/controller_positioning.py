import copy

from ui.window_positioning import PositioningWindow
from controller.controller_plot3d import Plot3DController as Spectrum3DPlot
import os
import scipy as sp
import numpy as np

class PositioningController(PositioningWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = self.main.MaRGE.console

        # Load a plot imaging from RAREprotocols_T1_SAG_Right.2023.10.24.19.28.37.989.mat
        self.rawDataLoading()

    def fix_console(self):
        self.layout_left.addWidget(self.console)

    def rawDataLoading(self, file_path="../", file_name="RAREprotocols_T1_SAG_Right.2023.10.24.19.28.37.989.mat"):
        """
        Load raw data from a .mat file and update the image view widget.
        """
        # self.clearCurrentImage()
        # Prompt the user to select a .mat file
        if not file_path:
            file_path = self.loadmatFile()
            file_name = os.path.basename(file_path)
        else:
            file_path = file_path+file_name
        self.main.file_name = file_name
        self.mat_data = sp.io.loadmat(file_path)
        image = np.abs(self.mat_data['image3D'])
        axes = self.mat_data['axesOrientation'][0]
        image, x_label, y_label, title = self.fixImage(image, axes)

        image_widget = Spectrum3DPlot(main=self, data=image, title=title, x_label=x_label, y_label=y_label)
        image_widget.hideAxis('bottom')
        image_widget.hideAxis('left')
        image_widget.showHistogram(False)
        self.figures_layout.clearFiguresLayout()
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