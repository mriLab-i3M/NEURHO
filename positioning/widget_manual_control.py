import sys

import numpy as np
from scipy.spatial.transform import Rotation

import configs.hw_config as hw

from PyQt5.QtWidgets import QGroupBox, QSizePolicy, QLabel, QLineEdit, QPushButton, QGridLayout, QApplication, \
    QHBoxLayout

from positioning.robot import Robot

def get_center(points):
    """Computes the centroid of three 3D points."""
    if len(points) != 3:
        raise ValueError("Exactly three points are required")
    p_prov = (np.array(points[0]) + np.array(points[1])) / 2.0
    r_center = (p_prov * 70 + np.array(points[2]) * 60.62) / 130.62

    return r_center[0], r_center[1], r_center[2]

def get_distances(points):
    """Computes the distances between three 3D points."""
    if len(points) != 3:
        raise ValueError("Exactly three points are required")

    # points
    pa = np.array(points[0])
    pb = np.array(points[1])
    pc = np.array(points[2])

    # Distance between a and b
    pba = pb - pa
    dba = np.sqrt(pba[0] ** 2 + pba[1] ** 2 + pba[2] ** 2)
    print(f"AB = {round(dba, 1)} mm")

    # Distance between a and c
    pca = pc - pa
    dca = np.sqrt(pca[0] ** 2 + pca[1] ** 2 + pca[2] ** 2)
    print(f"AC = {round(dca, 1)} mm")

    # Distance between b and c
    pcb = pc - pb
    dcb = np.sqrt(pcb[0] ** 2 + pcb[1] ** 2 + pcb[2] ** 2)
    print(f"BC = {round(dcb, 1)} mm")

def compute_euler_angles(a, b, c):
    """Computes the Euler angles from three 3D points."""
    # Step 1: Compute vectors defining the plane
    ab = b - a
    ca = a - c

    # Step 2: Compute the new x' axis (normal to the plane)
    x_new = np.cross(ab, ca)
    x_new = x_new / np.linalg.norm(x_new)  # Normalize

    # Step 3: Define new z' axis (aligned with v1)
    z_new = ab / np.linalg.norm(ab)

    # Step 4: Compute new y' axis (perpendicular to x' and z')
    y_new = np.cross(z_new, x_new)
    y_new = y_new / np.linalg.norm(y_new)  # Normalize

    # Step 5: Construct the rotation matrix
    R_matrix = np.column_stack((x_new, y_new, z_new))

    # Step 6: Convert rotation matrix to Euler angles (ZYX convention)
    euler_angles = Rotation.from_matrix(R_matrix).as_euler('xyz', degrees=True)
    euler_angles = [-angle for angle in euler_angles]

    return euler_angles


class WidgetManualControl(QGroupBox):
    def __init__(self, main):
        super().__init__("Manual Control")
        self.main = main
        self.mode = "Absolute"  # "Absolute" or "Relative"

        # Connect to fus robot
        self.fus_robot = Robot()

        # Set size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMaximumWidth(400)

        # Initialized parameters
        self.o_ima_edits = []
        self.o_hex_labels = []
        self.t_ima_edits = []
        self.t_hex_labels = []

        # Labels for coordinates
        labels_text = ["X0 (mm)", "Y0 (mm)", "Z0 (mm)", "Rx (deg)", "Ry (deg)", "Rz (deg)"]

        # Layout for the widget
        layout = QGridLayout()

        # Add header labels for "Origin" and "Target"
        layout.addWidget(QLabel("O_ima"), 0, 1)
        layout.addWidget(QLabel("O_hex"), 0, 2)
        layout.addWidget(QLabel("T_ima"), 0, 3)
        layout.addWidget(QLabel("T_hex"), 0, 4)

        # Loop to create labels, origin values, and input fields
        for i, label in enumerate(labels_text):
            layout.addWidget(QLabel(label), i + 1, 0)

            # Origin in image QLineEdit (with placeholder text as 0)
            o_ima_edit = QLineEdit()
            o_ima_edit.setPlaceholderText("0")
            self.o_ima_edits.append(o_ima_edit)
            layout.addWidget(o_ima_edit, i + 1, 1)

            # Origin in hexapod QLabel (defaulted to 0)
            o_hex_label = QLabel("0")
            self.o_hex_labels.append(o_hex_label)
            layout.addWidget(o_hex_label, i + 1, 2)

            # Target in image QLineEdit (with placeholder text as 0)
            t_ima_edit = QLineEdit()
            t_ima_edit.setPlaceholderText("0")
            self.t_ima_edits.append(t_ima_edit)
            layout.addWidget(t_ima_edit, i + 1, 3)

            # Target in hexapod QLabel (defaulted to 0)
            t_hex_label = QLabel("0")
            self.t_hex_labels.append(t_hex_label)
            layout.addWidget(t_hex_label, i + 1, 4)

        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout, len(labels_text) + 1, 0, 1, 5)

        # Create and add the "Go" button
        self.button_go = QPushButton("Go")
        buttons_layout.addWidget(self.button_go)

        # Create and add the "Home" button
        self.button_home = QPushButton("Home")
        buttons_layout.addWidget(self.button_home)

        # Create and add the "Go Back" button
        self.button_go_back = QPushButton("Go back")
        buttons_layout.addWidget(self.button_go_back)

        self.button_position = QPushButton("Get position")
        buttons_layout.addWidget(self.button_position)

        self.button_target = QPushButton("Get target position")
        buttons_layout.addWidget(self.button_target)

        # Set the layout
        self.setLayout(layout)

        # Connect the buttons to their handlers
        self.button_go.clicked.connect(self.go_clicked)
        self.button_home.clicked.connect(self.home_clicked)
        self.button_go_back.clicked.connect(self.go_back_clicked)
        self.button_position.clicked.connect(self.get_position_clicked)
        self.button_target.clicked.connect(self.get_target_clicked)

        # Connect the QLineEdit to their handlers
        for line_edit in self.o_ima_edits:
            line_edit.textChanged.connect(self.o_ima_edits_changed)

        for line_edit in self.t_ima_edits:
            line_edit.textChanged.connect(self.t_ima_edits_changed)

        # Set origin position to hw defined home position
        self.set_position(point="origin", coordinates=hw.fus_home)

        # Set initial values
        self.o_ima_edits_changed()
        self.t_ima_edits_changed()

        # Append initial position
        pos_ima, pos_hex = self.get_hex_position(point='origin')
        self.positions_ima = [pos_ima]  # Store positions in image
        self.positions_hex = [pos_hex]  # Store positions of hexapod

    def get_target_clicked(self):
        """
        Computes the centroid and Euler angles based on three selected MRI points and updates the UI.

        This function retrieves three 3D points selected in the MRI image, calculates their centroid,
        determines the Euler angles representing the orientation of the plane they define, and updates
        the corresponding UI text fields.

        Raises:
        - ValueError: If the number of selected points is not exactly three.

        Updates:
        - QTextEdit fields in `self.o_ima_edits` with the computed centroid coordinates (in mm) and Euler angles.
        """
        # Retrieve selected points from the MRI interface
        try:
            points_mri = self.main.image_widget.puntos_real
        except AttributeError:
            print("ERROR: no link to image_widget.")
            return

        if len(points_mri) != 3:
            print("You need 3 points to get the coordinates")
        else:
            centroid = get_center(points_mri)
            euler_angles = compute_euler_angles(np.array(points_mri[0]),
                                                np.array(points_mri[1]),
                                                np.array(points_mri[2]))

            # Update the QTextEdits with centroid (converted to mm) and Euler angles
            coord = [centroid[0], centroid[1], centroid[2],
                     euler_angles[0], euler_angles[1], euler_angles[2]]

            for n, edit in enumerate(self.t_ima_edits):
                edit.setText("%0.1f" % coord[n])

    def get_position_clicked(self):
        """
        Computes the centroid and Euler angles based on three selected MRI points and updates the UI.

        This function retrieves three 3D points selected in the MRI image, calculates their centroid,
        determines the Euler angles representing the orientation of the plane they define, and updates
        the corresponding UI text fields.

        Raises:
        - ValueError: If the number of selected points is not exactly three.

        Updates:
        - QTextEdit fields in `self.o_ima_edits` with the computed centroid coordinates (in mm) and Euler angles.
        """

        # Retrieve selected points from the MRI interface
        try:
            points_mri = self.main.image_widget.puntos_real
        except AttributeError:
            print("ERROR: no link to image_widget.")
            return

        if len(points_mri) != 3:
            print("You need 3 points to get the coordinates")
        else:
            centroid = get_center(points_mri)
            euler_angles = compute_euler_angles(np.array(points_mri[0]),
                                                np.array(points_mri[1]),
                                                np.array(points_mri[2]))
            get_distances(points_mri)

            # Update the QTextEdits with centroid (converted to mm) and Euler angles
            coord = [centroid[0], centroid[1], centroid[2],
                     euler_angles[0], euler_angles[1], euler_angles[2]]

            for n, edit in enumerate(self.o_ima_edits):
                edit.setText("%0.1f" % coord[n])

    def get_hex_position(self, point=None):
        """
        Computes the position of the hexapod base given the selected point type and its corresponding coordinates.

        This function retrieves the coordinates and Euler angles from the user interface, computes the base position
        of the hexapod using the given pole length, and returns both the image coordinates and the computed hexapod coordinates.

        Methods:
        - get_z_axis_from_euler(euler_angles, convention, degrees): Computes the new z-axis after applying the given Euler angles.
        - compute_hexapod_position(P_top, euler_angles, L, convention, degrees): Computes the hexapod base position.

        Parameters:
        - point (str, optional): Determines which coordinates to extract.
          Accepts 'origin' (extracts from `self.o_ima_edits`) or 'target' (extracts from `self.t_ima_edits`).

        Returns:
        - tuple: (r_ima, r_hex), where:
            - r_ima (list): The extracted coordinates and Euler angles from the UI.
            - r_hex (list): The computed hexapod base coordinates and angles.

        Raises:
        - ValueError: If an invalid `point` argument is given.
        - TypeError: If coordinate extraction from the UI fails.

        """

        def compute_hexapod_position(P_top, euler_angles, convention='xyz', degrees=True):
            # Compute rotation matrix from Euler angles
            rotation = Rotation.from_euler(convention, euler_angles, degrees=degrees)
            R_matrix = rotation.as_matrix()

            # Extract the new z-axis direction (third column of R)
            x_new = R_matrix[0, :]

            # Compute the hexapod base position
            P_hexapod = P_top - hw.pole_length * x_new

            return P_hexapod

        # Extract coordinates from UI based on the selected point type
        r_ima = []
        if point == 'origin':
            source_edits = self.o_ima_edits
        elif point == 'target':
            source_edits = self.t_ima_edits
        else:
            print("point parameter not found")
            return False

        # Attempt to extract numerical values from the text fields
        try:
            for edit in source_edits:
                r_ima.append(float(edit.text() if edit.text() else float(edit.placeholderText())))
        except ValueError:
            return False

        # Compute hexapod base coordinates
        r_hex = list(compute_hexapod_position(np.array(r_ima[:3]), r_ima[3:]))
        r_hex.extend(r_ima[3:])  # Append Euler angles to the result

        return r_ima, r_hex

    def set_position(self, point=None, coordinates=None):
        if point == 'origin':
            for i, value in enumerate(coordinates):
                self.o_ima_edits[i].setText(str(value))
        elif point == 'target':
            for i, value in enumerate(coordinates):
                self.t_ima_edits[i].setText(str(value))
        else:
            print("point parameter not found")
            return 0

    def o_ima_edits_changed(self):
        try:
            # Get hexapod coordinates
            _, r_hex = self.get_hex_position('origin')

            # Set values to the hexapod coordiante labels
            for ii in range(len(self.o_hex_labels)):
                self.o_hex_labels[ii].setText("%.1f" % r_hex[ii])
        except:
            pass

    def t_ima_edits_changed(self):
        # Get hexapod coordinates
        result = self.get_hex_position('target')
        if result is not False:
            # Set values to the hexapod coordiante labels
            _, r_hex = result
            for ii in range(len(self.t_hex_labels)):
                self.t_hex_labels[ii].setText("%.1f" % r_hex[ii])

    def go_clicked(self):
        # thread = threading.Thread(target=self.go_to, args=())
        # thread.start()
        self.go_to()

        r_ima_target, _ = self.get_hex_position('target')
        self.set_position(point='origin', coordinates=r_ima_target)

    def go_to(self):
        def go_to_absolute():
            # Get hexapod target coordinates
            r_ima_target, r_hex_target = self.get_hex_position('target')

            # Fix coordinate system to smc and hexapod
            position = [r_hex_target[0] + hw.pole_length - hw.fus_home[0],
                        r_hex_target[1] - hw.fus_home[1],
                        r_hex_target[2] - hw.fus_home[2],
                        + r_hex_target[4],
                        + r_hex_target[5],
                        - r_hex_target[3]]
            print("Position in smc coordinates:")
            print(position)

            # Move the robot
            if self.fus_robot.move(position=position):
                # Store the positions
                self.positions_ima.append(r_ima_target)
                self.positions_hex.append(r_hex_target)

        def go_to_relative():
            pass

        print("Moving FUS...")
        if self.mode == "Absolute":
            go_to_absolute()
        elif self.mode == "Relative":
            go_to_relative()
        print("READY: Movement completed.\n")

    def home_clicked(self):
        def go_home():
            # Set target to Zero
            self.set_position(point="target", coordinates=hw.fus_home)
            self.go_to()

        go_home()

    def go_back_clicked(self):
        def go_back():
            if len(self.positions_ima) <= 1:
                print("WARNING: No movements to revert.\n")
                return

            # Set target to last position
            self.set_position(point='target', coordinates=self.positions_ima[-2])
            self.go_to()
        go_back()
        self.positions_ima.pop()
        self.positions_hex.pop()

    def check_collision(self):
        # TODO: method to check for collisions between the pole and the shielding
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WidgetManualControl(None)
    window.show()
    sys.exit(app.exec_())
