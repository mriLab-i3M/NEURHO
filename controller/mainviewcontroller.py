"""
Main View Controller

@author:    Yolanda Vives

@status:    Sets up the main view, its views and controllers
@todo:

"""
from PyQt5.QtWidgets import QListWidgetItem,  QMessageBox,  QFileDialog
from PyQt5.QtCore import QFile, QTextStream,  pyqtSignal, pyqtSlot
from PyQt5.uic import loadUiType, loadUi
from PyQt5 import QtGui
from controller.acquisitioncontroller import AcquisitionController
from scipy.io import savemat, loadmat
import pyqtgraph.exporters
import os
import ast
from controller.sequencecontroller import SequenceList,  SequenceParameter
from controller.connectiondialog import ConnectionDialog
from plotview.sequenceViewer import SequenceViewer
from controller.outputparametercontroller import Output
from sequencemodes import defaultsequences
from manager.datamanager import DataManager
from datetime import date,  datetime 
from globalvars import StyleSheets as style

MainWindow_Form, MainWindow_Base = loadUiType('ui/mainview.ui')


class MainViewController(MainWindow_Form, MainWindow_Base):
    """
    MainViewController Class
    """
    onSequenceChanged = pyqtSignal(str)

    def __init__(self):
        super(MainViewController, self).__init__()
        self.ui = loadUi('ui/mainview.ui')
        self.setupUi(self)
        self.styleSheet = style.breezeLight
        self.setupStylesheet(self.styleSheet)

        # Initialisation of sequence list
        self.sequencelist = SequenceList(self)
        self.sequencelist.itemClicked.connect(self.sequenceChangedSlot)
        self.layout_operations.addWidget(self.sequencelist)

        # Initialisation of output section
        outputsection = Output(self)
        
        # Initialisation of acquisition controller
        acqCtrl = AcquisitionController(self, outputsection, self.sequencelist)
        
        # Toolbar Actions
        self.action_connect.triggered.connect(self.marcos_server)
        self.action_changeappearance.triggered.connect(self.changeAppearanceSlot)
        self.action_acquire.triggered.connect(acqCtrl.startAcquisition)
        self.action_loadparams.triggered.connect(self.load_parameters)
        self.action_saveparams.triggered.connect(self.save_parameters)
        self.action_close.triggered.connect(self.close)    
        self.action_savedata.triggered.connect(self.save_data)
        self.action_exportfigure.triggered.connect(self.export_figure)
        self.action_viewsequence.triggered.connect(self.represent_sequence)
        
    def marcos_server(self):
        self.con = ConnectionDialog(self)
        self.con.show()
    
    @pyqtSlot(bool)
    def changeAppearanceSlot(self) -> None:
        """
        Slot function to switch application appearance
        @return:
        """
        if self.styleSheet is style.breezeDark:
            self.setupStylesheet(style.breezeLight)
        else:
            self.setupStylesheet(style.breezeDark)
       
    def close(self):
        quit()    

    def setupStylesheet(self, style) -> None:
        """
        Setup application stylesheet
        @param style:   Stylesheet to be set
        @return:        None
        """
        self.styleSheet = style
        file = QFile(style)
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        self.setStyleSheet(stylesheet)  
        

        
    @pyqtSlot(QListWidgetItem)
    def sequenceChangedSlot(self, item: QListWidgetItem = None) -> None:
        """
        Operation changed slot function
        @param item:    Selected Operation Item
        @return:        None
        """
        self.sequence = item.text()
        self.onSequenceChanged.emit(self.sequence)
        self.action_acquire.setEnabled(True)
        self.clearPlotviewLayout()
    
    def clearPlotviewLayout(self) -> None:
        """
        Clear the plot layout
        @return:    None
        """
        for i in reversed(range(self.plotview_layout.count())):
            self.plotview_layout.itemAt(i).widget().setParent(None)
          
    
    def save_data(self):
        
#        name = QtGui.QFileDialog.getSaveFileName(self, 'Save File', 'default.mat')
#        file = open(name[0],'w')
#        text = self.textEdit.toPlainText()
#        file.write(text)
#        file.close()
        
        dataobject: DataManager = DataManager(self.rxd, self.lo_freq, len(self.rxd))
        dict = vars(defaultsequences[self.sequence])
        dt = datetime.now()
        dt_string = dt.strftime("%d-%m-%Y_%H:%M")
        dt2 = date.today()
        dt2_string = dt2.strftime("%d-%m-%Y")
        dict["rawdata"] = self.rxd
        dict["fft"] = dataobject.f_fftData
        if not os.path.exists('experiments/acquisitions/%s' % (dt2_string)):
            os.makedirs('experiments/acquisitions/%s' % (dt2_string))
            
        if not os.path.exists('experiments/acquisitions/%s/%s' % (dt2_string, dt_string)):
            os.makedirs('experiments/acquisitions/%s/%s' % (dt2_string, dt_string)) 
            
        savemat("experiments/acquisitions/%s/%s/%s.mat" % (dt2_string, dt_string, self.sequence), dict)
        
        self.messages("Data saved")

    def export_figure(self):
        
        dt = datetime.now()
        dt_string = dt.strftime("%d-%m-%Y_%H:%M")
        dt2 = date.today()
        dt2_string = dt2.strftime("%d-%m-%Y")

        if not os.path.exists('experiments/acquisitions/%s' % (dt2_string)):
            os.makedirs('experiments/acquisitions/%s' % (dt2_string))    
        if not os.path.exists('experiments/acquisitions/%s/%s' % (dt2_string, dt_string)):
            os.makedirs('experiments/acquisitions/%s/%s' % (dt2_string, dt_string)) 
                    
        exporter1 = pyqtgraph.exporters.ImageExporter(self.f_plotview.scene())
        exporter1.export("experiments/acquisitions/%s/%s/Freq%s.png" % (dt2_string, dt_string, self.sequence))
        exporter2 = pyqtgraph.exporters.ImageExporter(self.t_plotview.scene())
        exporter2.export("experiments/acquisitions/%s/%s/Temp%s.png" % (dt2_string, dt_string, self.sequence))
        
        self.messages("Figures saved")

    def load_parameters(self):
    
        self.clearPlotviewLayout()
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Parameters File', "experiments/parameterisations/")
        
        if file_name:
            f = open(file_name,"r")
            contents=f.read()
            new_dict=ast. literal_eval(contents)
            f.close()

            #dict = loadmat(file_name)
#            dict = 
#            del dict['__globals__']
#            del dict['__version__']
#            del dict['__header__']      
#            del dict['plot_rx']
#            del dict['init_gpa']

#            setattr(defaultsequences[self.sequence], 'seq', dict['seq'])
     
            del new_dict['seq']
            for key in new_dict:
                SequenceParameter(key,[new_dict[key]] , self.sequence)
                setattr(defaultsequences[self.sequence], key, str([new_dict[key]])) 

            self.messages("Parameters of %s sequence loaded" %(self.sequence))


    def save_parameters(self):
        
        dt = datetime.now()
        dt_string = dt.strftime("%d-%m-%Y_%H:%M")
        dict = vars(defaultsequences[self.sequence]) 
    
        f = open("experiments/parameterisations/%s_params_%s.txt" % (self.sequence, dt_string),"w")
        f.write( str(dict) )
        f.close()
  
        #savemat("experiments/parameterisations/%s_params_%s.mat" % (self.sequence, dt_string), dict)
        self.messages("Parameters of %s sequence saved" %(self.sequence))
        
    def represent_sequence(self):
        self.seqViewer = SequenceViewer(self,  self.sequencelist).representSequence()
        self.seqViewer.show()
        
        
    def messages(self, text):
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(text)
        msg.exec();
