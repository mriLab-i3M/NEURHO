"""
@author:    José Miguel Algarín
@email:     josalggui@i3m.upv.es
@affiliation:MRILab, i3M, CSIC, Valencia, Spain
"""
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QSizePolicy
from PyQt5.QtCore import QSize, QThreadPool
import qdarkstyle

from controller.controller_console import ConsoleController
from controller.controller_figures import FiguresLayoutController
from controller.controller_history_list import HistoryListController
from controller.controller_menu import MenuController
from controller.controller_protocol_inputs import ProtocolInputsController
from controller.controller_protocol_list import ProtocolListController
from controller.controller_toolbar_figures import FiguresController
from controller.controller_toolbar_marcos import MarcosController
from controller.controller_toolbar_protocols import ProtocolsController
from controller.controller_toolbar_sequences import SequenceController
from controller.controller_sequence_list import SequenceListController
from controller.controller_sequence_inputs import SequenceInputsController
from widgets.widget_custom_and_protocol import CustomAndProtocolWidget
from ui.window_postprocessing import MainWindow as PostWindow


class MainWindow(QWidget):
    def __init__(self, session, demo=False, parent=None):
        super(MainWindow, self).__init__(parent)
        self.app_open = True
        self.toolbar_sequences = None
        self.toolbar_marcos = None
        self.session = session
        self.demo = demo
        self.setWindowTitle(session['directory'])
        self.setGeometry(20, 40, 1680, 720)

        # Threadpool for parallel running
        self.threadpool = QThreadPool()

        # Set stylesheet
        self.styleSheet = qdarkstyle.load_stylesheet_pyqt5()
        self.setStyleSheet(self.styleSheet)

        # Create console
        self.console = ConsoleController()
        self.console.setup_console()
        self.console.setup_console()

        # Layouts
        layout_main = QVBoxLayout()
        layout_toolbars = QHBoxLayout()
        layout_widgets = QHBoxLayout()
        self.layout_inputs = QVBoxLayout()
        layout_outputs = QVBoxLayout()
        layout_outputs_h = QHBoxLayout()
        self.setLayout(layout_main)
        layout_main.addLayout(layout_toolbars)
        layout_main.addLayout(layout_widgets)
        layout_widgets.addLayout(self.layout_inputs)
        layout_widgets.addLayout(layout_outputs)

        ############## toolbars ###################

        # Add marcos toolbar
        self.toolbar_marcos = MarcosController(self, "MaRCoS toolbar")
        layout_toolbars.addWidget(self.toolbar_marcos)

        # Add sequence toolbar
        self.toolbar_sequences = SequenceController(self, "Sequence toolbar")
        layout_toolbars.addWidget(self.toolbar_sequences)

        # Add image toolbar
        self.toolbar_figures = FiguresController(self, "Figures toolbar")
        layout_toolbars.addWidget(self.toolbar_figures)

        # Add protocol toolbar
        self.toolbar_protocols = ProtocolsController(self, "Protocols toolbar")
        layout_toolbars.addWidget(self.toolbar_protocols)

        # # Status bar
        # self.setStatusBar(QStatusBar(self))

        ################# layout_qwidget #####################

        # Add custom_and_protocol widget
        self.custom_and_protocol = CustomAndProtocolWidget()
        self.layout_inputs.addWidget(self.custom_and_protocol)

        # Add sequence list to custom tab
        self.sequence_list = SequenceListController(parent=self)
        self.custom_and_protocol.custom_layout.addWidget(self.sequence_list)

        # Add sequence inputs to custom tab
        self.sequence_inputs = SequenceInputsController(parent=self)
        self.custom_and_protocol.custom_layout.addWidget(self.sequence_inputs)

        # Add protocols list to protocol tab
        self.protocol_list = ProtocolListController(main=self)
        self.custom_and_protocol.protocol_layout.addWidget(self.protocol_list)

        # Add protocol sequences to protocol tab
        self.protocol_inputs = ProtocolInputsController(main=self)
        self.custom_and_protocol.protocol_layout.addWidget(self.protocol_inputs)

        # Add layout to show the figures
        self.figures_layout = FiguresLayoutController(self)
        self.figures_layout.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout_outputs.addWidget(self.figures_layout)

        # Add console
        self.layout_inputs.addWidget(self.console)

        # Add list to show the history
        layout_outputs.addLayout(layout_outputs_h)
        self.history_list = HistoryListController(parent=self)
        layout_outputs_h.addWidget(self.history_list)
        self.history_list.setMaximumHeight(200)
        self.history_list.setMinimumHeight(200)

        # Table with input parameters from historic images
        self.input_table = QTableWidget()
        self.input_table.setMaximumHeight(200)
        self.input_table.setMinimumHeight(200)
        layout_outputs_h.addWidget(self.input_table)
