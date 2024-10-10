"""
@author:    José Miguel Algarín
@email:     josalggui@i3m.upv.es
@affiliation:MRILab, i3M, CSIC, Valencia, Spain
"""
import numpy as np
import pyqtgraph as pg


class Plot3DWidget(pg.ImageView):
    def __init__(self, main, data=np.array([]), x_label='', y_label='', title=''):

        # Save inputs into the self
        self.main = main
        self.data = data
        self.x_label = x_label
        self.y_label = y_label
        self.title = title

        # Define the PlotItem to display the image
        self.plot_item = pg.PlotItem()

        # Execute the parent init
        super(Plot3DWidget, self).__init__(view=self.plot_item)

        # Set plot_item properties
        self.plot_item.setLabel(axis='left', text=y_label)
        self.plot_item.setLabel(axis='bottom', text=x_label)
        self.plot_item.setTitle(title=title)

        # Change button names
        self.ui.menuBtn.setText("Target")
        self.ui.roiBtn.setText("Origin")
        self.ui.menuBtn.setCheckable(True)
        self.ui.roiBtn.setCheckable(True)

        # Define origin marker
        self.marker_o = pg.ScatterPlotItem([0], [0], symbol='o', size=10, pen=pg.mkPen('r', width=2), brush='r')
        self.marker_o.setPos(0, 0)
        self.marker_o.hide()
        self.plot_item.addItem(self.marker_o)

        # Define target marker
        self.marker_t = pg.ScatterPlotItem([0], [0], symbol='o', size=10, pen=pg.mkPen('g', width=2), brush='g')
        self.marker_t.setPos(0, 0)
        self.marker_t.hide()
        self.plot_item.addItem(self.marker_t)

        # Add image
        self.setImage(self.data)

    def roiClicked(self):
        self.ui.menuBtn.setChecked(False)
        self.imageItem.mouseClickEvent = self.mouseClickEvent

    def menuClicked(self):
        self.ui.roiBtn.setChecked(False)
        self.imageItem.mouseClickEvent = self.mouseClickEvent

    def mouseClickEvent(self, event):
        """
        Handle mouse click events when ROI mode is active.

        Args:
            event: The mouse event object containing the click information.
        """
        # Get the position of the click in data coordinates
        pos = event.pos()
        x, y = int(pos[0]), int(pos[1])
        z = self.currentIndex

        # Ensure the coordinates are within bounds of the image data
        if 0 <= x < self.data.shape[1] and 0 <= y < self.data.shape[2]:
            if self.ui.roiBtn.isChecked():  # Origin
                # Mark the position on the plot
                self.markPosition(x, y, z, self.marker_o)
                self.main.manual_control_widget.set_position(point='origin', coordinates=[x, y, z])
                print(f"Origin coordinates: ({x}, {y}, {z})")
            elif self.ui.menuBtn.isChecked():  # Target
                # Mark the position on the plot
                self.markPosition(x, y, z, self.marker_t)
                self.main.manual_control_widget.set_position(point='target', coordinates=[x, y, z])
                print(f"Target coordinates: ({x}, {y}, {z})")

    def markPosition(self, x, y, z, marker):
        """
        Mark a position on the image where the user clicked.

        Args:
            x (int): The x-coordinate of the click.
            y (int): The y-coordinate of the click.
            z (int): The z-coordinate of the click.
            marker: marker from pyqtgraph
        """
        # Get the current slice index
        current_slice = self.currentIndex

        # Ensure we're adding the marker only to the 2D slice currently being displayed
        slice_data = self.data[current_slice]

        marker.setPos(x, y)
        marker.show()