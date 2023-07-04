"""
session_controller.py
@author:    José Miguel Algarín
@email:     josalggui@i3m.upv.es
@affiliation:MRILab, i3M, CSIC, Valencia, Spain
"""
from ui.window_session import SessionWindow
from controller.controller_main import MainController
import os
import sys
import configs.hw_config as hw


class SessionController(SessionWindow):
    def __init__(self, demo):
        super(SessionController, self).__init__()
        self.main_gui = None
        self.demo = demo

        # Set slots for toolbar actions
        self.launch_gui_action.triggered.connect(self.runMainGui)
        self.close_action.triggered.connect(self.close)

    def runMainGui(self):
        self.updateSessionDict()

        # Create folder
        self.session['directory'] = 'experiments/acquisitions/%s/%s/%s/%s' % (
            self.session['project'], self.session['subject_id'], self.session['study'], self.session['side'])
        if not os.path.exists(self.session['directory']):
            os.makedirs(self.session['directory'])

        # Open the main gui
        self.main_gui = MainController(self.session, self.demo)
        self.hide()
        self.main_gui.show()

    def closeEvent(self, event):
        print('GUI closed successfully!')
        super().closeEvent(event)

    def close(self):
        print('GUI closed successfully!')
        sys.exit()

    def updateSessionDict(self):
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
