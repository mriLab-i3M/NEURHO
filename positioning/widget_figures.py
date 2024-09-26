"""
@author:    José Miguel Algarín
@email:     josalggui@i3m.upv.es
@affiliation:MRILab, i3M, CSIC, Valencia, Spain
"""
from pyqtgraph import LayoutWidget


class FiguresLayoutWidget(LayoutWidget):
    def __init__(self, main=None):
        super().__init__()

        self.main = main

    def clear_figures_layout(self) -> None:
        """
        Clear the figures' layout.

        This method removes all widgets from the figures layout.

        Returns:
            None
        """
        for ii in range(self.layout.count()):
            item = self.layout.takeAt(0)
            item.widget().deleteLater()
