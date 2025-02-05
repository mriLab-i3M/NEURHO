import threading
import sys

import numpy as np
from scipy.spatial.transform import Rotation

import positioning.hw_positioning as hwp
import configs.hw_config as hw

from PyQt5.QtWidgets import QGroupBox, QSizePolicy, QLabel, QLineEdit, QPushButton, QGridLayout, QApplication, \
    QHBoxLayout

from positioning.bora import Bora


class WidgetManualControl(QGroupBox):
    def __init__(self, main):
        super().__init__("Manual Control")
        self.main = main

        # Connect to Bora
        self.bora = Bora()

        # Connect to SMC
        # TODO: Connect to SMC

        # Set size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMaximumWidth(400)

        # Initialized parameters
        self.o_ima_edits = []
        self.o_hex_labels = []
        self.t_ima_edits = []
        self.t_hex_labels = []
        self.movements = []  # Store movements
        self.positions_ima = []  # Store positions in image
        self.positions_hex = []  # Store positions of hexapod

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
        self.button_go_back = QPushButton("Go Back")
        buttons_layout.addWidget(self.button_go_back)

        self.button_position = QPushButton("Get Position")
        buttons_layout.addWidget(self.button_position)

        # Set the layout
        self.setLayout(layout)

        # Connect the buttons to their handlers
        self.button_go.clicked.connect(self.go_clicked)
        self.button_home.clicked.connect(self.home_clicked)
        self.button_go_back.clicked.connect(self.go_back_clicked)
        self.button_position.clicked.connect(self.get_position_clicked)

        # Connect the QLineEdit to their handlers
        for line_edit in self.o_ima_edits:
            line_edit.textChanged.connect(self.o_ima_edits_changed)

        for line_edit in self.t_ima_edits:
            line_edit.textChanged.connect(self.t_ima_edits_changed)

        # Set initial values
        self.o_ima_edits_changed()
        self.t_ima_edits_changed()

    def get_position_clicked(self):
        """
        Computes the centroid and Euler angles based on three selected MRI points and updates the UI.

        This function retrieves three 3D points selected in the MRI image, calculates their centroid,
        determines the Euler angles representing the orientation of the plane they define, and updates
        the corresponding UI text fields.

        Methods:
        - get_center(points): Computes the centroid of three 3D points.
        - compute_euler_angles(A, B, C): Computes the Euler angles from three 3D points.

        Raises:
        - ValueError: If the number of selected points is not exactly three.

        Updates:
        - QTextEdit fields in `self.o_ima_edits` with the computed centroid coordinates (in mm) and Euler angles.
        """

        def get_center(points):
            if len(points) != 3:
                raise ValueError("Exactly three points are required")

            x_center = sum(p[0] for p in points) / 3
            y_center = sum(p[1] for p in points) / 3
            z_center = sum(p[2] for p in points) / 3

            return (x_center, y_center, z_center)

        def compute_euler_angles(A, B, C):
            # Step 1: Compute vectors defining the plane
            v1 = B - A
            v2 = C - A

            # Step 2: Compute the new z' axis (normal to the plane)
            z_new = np.cross(v1, v2)
            z_new = z_new / np.linalg.norm(z_new)  # Normalize

            # Step 3: Define new x' axis (aligned with v1)
            x_new = v1 / np.linalg.norm(v1)

            # Step 4: Compute new y' axis (perpendicular to x' and z')
            y_new = np.cross(z_new, x_new)
            y_new = y_new / np.linalg.norm(y_new)  # Normalize

            # Step 5: Construct the rotation matrix
            R_matrix = np.column_stack((x_new, y_new, z_new))

            # Step 6: Convert rotation matrix to Euler angles (ZYX convention)
            euler_angles = Rotation.from_matrix(R_matrix).as_euler('zyx', degrees=True)

            return euler_angles

        # Retrieve selected points from the MRI interface
        points_mri = self.main.image_widget.puntos_real

        if len(points_mri) != 3:
            print("You need 3 points to get the coordinates")
        else:
            # Reformat points from scanner to bora coordinates for further processing
            points_bora = [[p[1], p[2], p[0]] for p in points_mri]

            # Compute centroid and Euler angles
            centroid = get_center(points_bora)
            euler_angles = compute_euler_angles(np.array(points_bora[0]),
                                                np.array(points_bora[1]),
                                                np.array(points_bora[2]))

            # Update the QTextEdits with centroid (converted to mm) and Euler angles
            coord = [centroid[0] * 1e3, centroid[1] * 1e3, centroid[2] * 1e3,
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

        def compute_hexapod_position(P_top, euler_angles, convention='zyx', degrees=True):
            # Compute rotation matrix from Euler angles
            rotation = Rotation.from_euler(convention, euler_angles, degrees=degrees)
            R_matrix = rotation.as_matrix()

            # Extract the new z-axis direction (third column of R)
            z_new = R_matrix[:, 2]

            # Compute the hexapod base position
            P_hexapod = P_top - hw.pole_length * z_new

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

    def get_fus_position(self, r_hex):
        """
        Computes the position of a point given the hexapod base position, its Euler angles, and the pole length.

        This function reverses the computation from `get_position`, finding the top point position
        from the hexapod base.

        Parameters:
        - r_hex (list or np.array): The position and orientation of the hexapod in the form:
            [x_hex, y_hex, z_hex, alpha, beta, gamma]

        Returns:
        - np.array: The computed position of the point in global coordinates [x, y, z, alpha, beta, gamma].
        """

        def compute_point_position(P_hexapod, euler_angles, convention='zyx', degrees=True):
            """
            Computes the position of the top point given the hexapod base position, its Euler angles, and the pole length.

            Parameters:
            - P_hexapod (np.array): Position of the hexapod base in global coordinates [x, y, z].
            - euler_angles (list or np.array): Euler angles [alpha, beta, gamma] in degrees or radians.
            - L (float): Length of the pole.
            - convention (str, optional): Rotation convention (default is 'zyx').
            - degrees (bool, optional): True if angles are in degrees.

            Returns:
            - np.array: The computed position of the top point in global coordinates [x, y, z].
            """
            # Compute rotation matrix from Euler angles
            rotation = Rotation.from_euler(convention, euler_angles, degrees=degrees)
            R_matrix = rotation.as_matrix()

            # Extract the new z-axis direction (third column of R)
            z_new = R_matrix[:, 2]

            # Compute the top point position
            P_top = P_hexapod + hw.pole_length * z_new

            return P_top

        # Extract hexapod position and Euler angles
        P_hexapod = np.array(r_hex[:3])
        euler_angles = np.array(r_hex[3:])

        # Compute the top point position
        P_top = compute_point_position(P_hexapod, euler_angles)

        # Return the full coordinate set (position + orientation)
        return list(P_top) + list(euler_angles)

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
        # Get hexapod coordinates
        _, r_hex = self.get_hex_position('origin')

        # Set values to the hexapod coordiante labels
        for ii in range(len(self.o_hex_labels)):
            self.o_hex_labels[ii].setText("%.1f" % r_hex[ii])

    def t_ima_edits_changed(self):
        # Get hexapod coordinates
        result = self.get_hex_position('target')
        if result is not False:
            # Set values to the hexapod coordiante labels
            _, r_hex = result
            for ii in range(len(self.t_hex_labels)):
                self.t_hex_labels[ii].setText("%.1f" % r_hex[ii])

    def go_clicked(self):
        thread = threading.Thread(target=self.go_to)
        thread.start()

    def move_fus(self, target=None, origin=None):
        # Delta angle for hexapod coordinates:
        d_angle = list(np.array(target[3:]) - np.array(origin[3:]))
        # Move bora hexapod
        if self.move_bora(d_angle=d_angle):
            fus_pos = self.get_fus_position(r_hex=[origin[0], origin[1], origin[2], target[3], target[4], target[5]])
            self.set_position(point='origin', coordinates=fus_pos)
        else:
            print("ERROR: Hexapod displacement failed.")
            return False

        # Move smc actuators
        if self.move_smc(list(np.array(target[:3]) - np.array(fus_pos[:3]))):
            self.set_position(point='origin', coordinates=target)
        else:
            print("ERROR: SMC displacement failed")
            return False

        return True

    def move_bora(self, d_angle=None):
        if d_angle is None:
            d_angle = [0.0, 0.0, 0.0]

        return self.bora.move_absolute((0, 0, 0, 0, d_angle[0], d_angle[1], d_angle[2]))

    def move_smc(self, d_position=None):
        if d_position is None:
            d_position = [0.0, 0.0, 0.0]

        return False

    def go_to(self):
        # Get hexapod coordinates and displacement
        _, r_hex_origin = self.get_hex_position('origin')
        r_ima_target, r_hex_target = self.get_hex_position('target')
        deltas = list(np.array(r_hex_target) - np.array(r_hex_origin))

        # Move the robot according to the deltas
        if self.move_fus(target=r_hex_target, origin=r_hex_origin):

            # Print the movement for debugging purposes
            label_text = ["X0", "Y0", "Z0", "Rx", "Ry", "Rz"]
            for ii, label in enumerate(label_text):
                print("Movement in %s: %.1f %s" % (label, deltas[ii], 'mm' if ii < 3 else 'deg'))

            # Store the deltas in the movements parameter
            self.movements.append(deltas)
            self.positions_ima.append(r_ima_target)
            self.positions_hex.append(r_hex_target)

            print("READY: Movement completed.\n")

    def home_clicked(self):
        thread = threading.Thread(target=self.go_home)
        thread.start()

    def go_home(self):
        # Set target to Zero
        self.set_position(point="target", coordinates=[0, 0, 0, 0, 90])
        self.go_to()

    def go_back_clicked(self):
        thread = threading.Thread(target=self.go_back)
        thread.start()

    def go_back(self):
        if len(self.movements) <= 1:
            print("WARNING: No movements to revert.\n")
            return

        # Get the last movement
        last_position_ima = self.positions_ima[-2]

        # Set target to last position
        self.set_position(point='target', coordinates=last_position_ima)
        self.go_to()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WidgetManualControl(None)
    window.show()
    sys.exit(app.exec_())
