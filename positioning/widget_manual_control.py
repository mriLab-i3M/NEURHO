import threading

import numpy as np

import positioning.hw_positioning as hwp

from PyQt5.QtWidgets import QGroupBox, QSizePolicy, QLabel, QLineEdit, QPushButton, QGridLayout, QApplication, \
    QHBoxLayout


class WidgetManualControl(QGroupBox):
    def __init__(self, main):
        super().__init__("Manual Control")
        self.main = main

        # Set size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMaximumWidth(400)

        # Initialized parameters
        self.o_ima_edits = []
        self.o_hex_labels = []
        self.t_ima_edits = []
        self.t_hex_labels = []
        self.movements = []  # Class parameter to store movements

        # Labels for coordinates
        labels_text = ["X0 (mm)", "Y0 (mm)", "Z0 (mm)", "Phi (deg)", "Theta (deg)"]

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

        # Set the layout
        self.setLayout(layout)

        # Connect the buttons to their handlers
        self.button_go.clicked.connect(self.go_clicked)
        self.button_home.clicked.connect(self.home_clicked)
        self.button_go_back.clicked.connect(self.go_back_clicked)

        # Connect the QLineEdit to their handlers
        for line_edit in self.o_ima_edits:
            line_edit.textChanged.connect(self.o_ima_edits_changed)

        for line_edit in self.t_ima_edits:
            line_edit.textChanged.connect(self.t_ima_edits_changed)

        # Set initial values
        self.o_ima_edits[-1].setPlaceholderText("90")
        self.t_ima_edits[-1].setPlaceholderText("90")
        self.o_ima_edits_changed()
        self.t_ima_edits_changed()

    def o_ima_edits_changed(self):
        # Get image coordinates
        r_ima = []
        for edit in self.o_ima_edits:
            r_ima.append(float(edit.text() if edit.text() else float(edit.placeholderText())))

        # Calculate hexapod coordinates
        x_hex = r_ima[0] - hwp.length * np.cos(r_ima[3] * np.pi/180) * np.sin(r_ima[4] * np.pi/180)
        y_hex = r_ima[1] - hwp.length * np.sin(r_ima[3] * np.pi/180) * np.sin(r_ima[4] * np.pi/180)
        z_hex = r_ima[2] - hwp.length * np.cos(r_ima[4] * np.pi/180)
        phi_hex = r_ima[3]
        theta_hex = r_ima[4]

        # Set values to the hexapod coordiante labels
        self.o_hex_labels[0].setText("%.1f" % x_hex)
        self.o_hex_labels[1].setText("%.1f" % y_hex)
        self.o_hex_labels[2].setText("%.1f" % z_hex)
        self.o_hex_labels[3].setText("%.1f" % phi_hex)
        self.o_hex_labels[4].setText("%.1f" % theta_hex)

    def t_ima_edits_changed(self):
        # Get image coordinates
        r_ima = []
        for edit in self.t_ima_edits:
            r_ima.append(float(edit.text() if edit.text() else float(edit.placeholderText())))

        # Calculate hexapod coordinates
        x_hex = r_ima[0] - hwp.length * np.cos(r_ima[3] * np.pi / 180) * np.sin(r_ima[4] * np.pi / 180)
        y_hex = r_ima[1] - hwp.length * np.sin(r_ima[3] * np.pi / 180) * np.sin(r_ima[4] * np.pi / 180)
        z_hex = r_ima[2] - hwp.length * np.cos(r_ima[4] * np.pi / 180)
        phi_hex = r_ima[3]
        theta_hex = r_ima[4]

        # Set values to the hexapod coordiante labels
        self.t_hex_labels[0].setText("%.1f" % x_hex)
        self.t_hex_labels[1].setText("%.1f" % y_hex)
        self.t_hex_labels[2].setText("%.1f" % z_hex)
        self.t_hex_labels[3].setText("%.1f" % phi_hex)
        self.t_hex_labels[4].setText("%.1f" % theta_hex)

    def set_target(self, target_values):
        if len(target_values) != 3:
            print("ERROR: Expected a list of 3 elements.")
            return

        for i, value in enumerate(target_values):
            self.t_ima_edits[i].setText(str(value))

    def set_origin(self, origin_values):
        if len(origin_values) != 3:
            print("ERROR: Expected a list of 3 elements.")

        # Set values for origin image coordinates
        for i, value in enumerate(origin_values):
            self.o_ima_edits[i].setText(str(value))

    def go_clicked(self):
        thread = threading.Thread(target=self.go_to)
        thread.start()

    def go_to(self):
        # Initialize lists to store the calculated deltas
        deltas = []

        # Loop through the target edits and origin labels to calculate movements
        for i in range(len(self.target_edits)):
            # Retrieve the origin value from QLabel
            origin_value = float(self.origin_labels[i].text())

            # Retrieve the target value from QLineEdit
            target_value = float(self.target_edits[i].text()) if self.target_edits[i].text() else 0.0

            # Calculate the movement (delta)
            delta = target_value - origin_value
            deltas.append(delta)

            # Update the origin label with the target value
            self.origin_labels[i].setText(str(target_value))

            # Print the movement for debugging purposes
            label_text = ["X0", "Y0", "Z0", "Rx", "Ry", "Rz"]
            print(f"Movement in {label_text[i]}: {delta} {'mm' if i < 3 else 'deg'}")

        # Store the deltas in the movements parameter
        self.movements.append(deltas)

        print("READY: Movement completed.\n")

    def home_clicked(self):
        thread = threading.Thread(target=self.go_home)
        thread.start()

    def go_home(self):
        # Revert all movements to their initial state (e.g., 0)
        for i, label in enumerate(self.origin_labels):
            current_value = float(label.text())
            displacement = -current_value  # Moving back to home (0)

            # Update the origin label to 0
            label.setText("0")

            # Print the displacement for debugging purposes
            label_text = ["X0", "Y0", "Z0", "Rx", "Ry", "Rz"]
            print(f"Movement in {label_text[i]}: {displacement} {'mm' if i < 3 else 'deg'}")

        # Clear the target edits
        for edit in self.target_edits:
            edit.clear()

        # Clear the movements list
        self.movements.clear()
        print("READY: All movements reverted to home position.\n")

    def go_back_clicked(self):
        thread = threading.Thread(target=self.go_back)
        thread.start()

    def go_back(self):
        if not self.movements:
            print("WARNING: No movements to revert.\n")
            return

        # Get the last movement
        last_movement = self.movements.pop()  # Retrieve and remove the last movement

        # Loop through the origin labels to apply the reverse movement
        for i, label in enumerate(self.origin_labels):
            current_value = float(label.text())  # Get the current value

            # Calculate the new position by reversing the last movement
            new_value = current_value - last_movement[i]

            # Update the origin label with the new value
            label.setText(str(new_value))

            # Print the reverse displacement for debugging purposes
            label_text = ["X0", "Y0", "Z0", "Rx", "Ry", "Rz"]
            print(f"Reverted movement in {label_text[i]}: {-last_movement[i]} {'mm' if i < 3 else 'deg'}")

        # Clear the target edits
        for edit in self.target_edits:
            edit.clear()

        print("READY: Last movement reverted.\n")

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = WidgetManualControl(None)
    window.show()
    sys.exit(app.exec_())

