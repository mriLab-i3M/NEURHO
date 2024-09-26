"""
:author:    J.M. Algarín
:email:     josalggui@i3m.upv.es
:affiliation: MRILab, i3M, CSIC, Valencia, Spain

"""
from PyQt5.QtWidgets import QApplication

from ui.window_session import SessionWindow
from controller.controller_workflow import WorkflowController
import os
import sys
import configs.hw_config as hw

class SessionController(SessionWindow):
    """
    Controller class for managing the session.

    Inherits:
        SessionWindow: Base class for the session window.
    """
    def __init__(self):
        """
        Initializes the SessionController.
        """
        super(SessionController, self).__init__()
        self.main_gui = None

        # Set slots for toolbar actions
        self.launch_gui_action.triggered.connect(self.runMainGui)
        self.demo_gui_action.triggered.connect(self.runDemoGui)
        self.close_action.triggered.connect(self.close)

    def runMainGui(self):
        """
        Runs the main GUI and sets up the session.

        Creates a folder for the session and opens the main GUI.
        """
        self.updateSessionDict()

        # Create folder
        self.session['directory'] = 'experiments/acquisitions/%s/%s/%s/%s' % (
            self.session['project'], self.session['subject_id'], self.session['study'], self.session['side'])
        if not os.path.exists(self.session['directory']):
            os.makedirs(self.session['directory'])

        # Open the main gui
        self.main_gui = WorkflowController(session=self.session, demo=False)
        self.hide()
        self.main_gui.show()
        sys.exit(app.exec_())

    def runDemoGui(self):
        """
        Runs the main GUI in DEMO mode and sets up the session.

        Creates a folder for the session and opens the main GUI.
        """
        self.updateSessionDict()

        # Create folder
        self.session['directory'] = 'experiments/acquisitions/%s/%s/%s/%s' % (
            self.session['project'], self.session['subject_id'], self.session['study'], self.session['side'])
        if not os.path.exists(self.session['directory']):
            os.makedirs(self.session['directory'])

        # Open the main gui
        self.main_gui = WorkflowController(session=self.session, demo=True)
        self.hide()
        self.main_gui.show()

    def closeEvent(self, event):
        """
        Event handler for the session window close event.

        Args:
            event: The close event.
        """
        print('GUI closed successfully!')
        super().closeEvent(event)

    def close(self):
        """
        Closes the session and exits the program.
        """
        print('GUI closed successfully!')
        sys.exit()

    def updateSessionDict(self):
        """
        Updates the session dictionary with the current session information.
        """
        self.session = {
            'project': self.project_combo_box.currentText(),
            'study': self.study_combo_box.currentText(),
            'side': self.side_combo_box.currentText(),
            'orientation': self.orientation_combo_box.currentText(),
            'subject_id': self.id_line_edit.text(),
            'study_id': self.idS_line_edit.text(),
            'subject_name': self.name_line_edit.text(),
            'subject_surname': self.surname_line_edit.text(),
            'subject_birthday': self.birthday_line_edit.text(),
            'subject_weight': self.weight_line_edit.text(),
            'subject_height': self.height_line_edit.text(),
            'scanner': self.scanner_line_edit.text(),
            'rf_coil': self.rf_coil_combo_box.currentText(),
            'seriesNumber': 0,
        }
        hw.b1Efficiency = hw.antenna_dict[self.session['rf_coil']]

if __name__ == '__main__':
    # Only one QApplication for event loop
    app = QApplication(sys.argv)
    window = SessionController()
    window.show()
    sys.exit(app.exec_())