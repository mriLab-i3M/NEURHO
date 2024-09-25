import threading

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
        self.origin_labels = []
        self.target_edits = []
        self.movements = []  # Class parameter to store movements

        # Labels for coordinates
        labels_text = ["X0 (mm)", "Y0 (mm)", "Z0 (mm)", "Xe (mm)", "Ye (mm)", "Ze (mm)", "Rx (deg)", "Ry (deg)",
                       "Rz (deg)"]

        # Layout for the widget
        layout = QGridLayout()

        # Add header labels for "Origin" and "Target"
        layout.addWidget(QLabel("Origin"), 0, 1)
        layout.addWidget(QLabel("Target"), 0, 2)

        # Loop to create labels, origin values, and input fields
        for i, label in enumerate(labels_text):
            layout.addWidget(QLabel(label), i + 1, 0)

            # Origin QLabel (defaulted to 0)
            origin_label = QLabel("0")
            self.origin_labels.append(origin_label)
            layout.addWidget(origin_label, i + 1, 1)

            # Target QLineEdit (with placeholder text as 0)
            target_edit = QLineEdit()
            target_edit.setPlaceholderText("0")
            self.target_edits.append(target_edit)
            layout.addWidget(target_edit, i + 1, 2)

        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout, len(labels_text) + 1, 0, 1, 3)

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
            label_text = ["X0", "Y0", "Z0", "Xe", "Ye", "Ze", "Rx", "Ry", "Rz"]
            print(f"Movement in {label_text[i]}: {delta} {'mm' if i < 6 else 'deg'}")

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
            label_text = ["X0", "Y0", "Z0", "Xe", "Ye", "Ze", "Rx", "Ry", "Rz"]
            print(f"Movement in {label_text[i]}: {displacement} {'mm' if i < 6 else 'deg'}")

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
            label_text = ["X0", "Y0", "Z0", "Xe", "Ye", "Ze", "Rx", "Ry", "Rz"]
            print(f"Reverted movement in {label_text[i]}: {-last_movement[i]} {'mm' if i < 6 else 'deg'}")

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

