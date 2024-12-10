"""
Original file: ps5000aSigGen.py
Original Source: https://github.com/picotech/picosdk-python-wrappers/blob/master/ps5000aExamples/ps5000aSigGen.py
Original Repository: https://github.com/picotech/picosdk-python-wrappers.git

ps5000aSigGen.py has been modified to include a Graphical Interface to change the parameters of the function generator built-in PicoScope 5000 Series.
This GUI has been tested in a PicoScope 5444D MSO.

-------------------------------------------------------------------------------------------------------------------------------------------------------
Header from the original file:

#
# Copyright (C) 2018-2024 Pico Technology Ltd. See LICENSE file for terms.
#
# PicoScope 5000 (A API) Signal Generator Example
# This example demonstrates how to use the PicoScope 5000 Series (ps5000a) driver API functions to set up the signal generator to do the following:
# 
# 1. Output a sine wave 
# 2. Output a square wave 
# 3. Output a sweep of a square wave signal

End of header from the original file
-------------------------------------------------------------------------------------------------------------------------------------------------------
Terms from the original file:

Copyright © 2019 Pico Technology Ltd.

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted,
provided that the above copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. 
IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, 
WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
-------------------------------------------------------------------------------------------------------------------------------------------------------

Datasheet parameters:
- Voltage range: +/- 2 V
- Votlage step: 0.25 mV
- Frequency range: From 0.025 Hz to 20 MHz
- Frequency step: 0.025 Hz
"""

# UI DEBUG: App Debugging. Connection to PicoScope avoided when UI_DEBUG = True
UI_DEBUG = True

# DATASHEET CONSTANTS
VPEAKMAX = 2.0
VOLTAGESTEP = 0.00025
FREQMAX = 20000000
FREQMIN = 0.025
FREQSTEP = 0.025

# Wave types
WAVE_TYPES = ['Sine','Square','Triangle','Rising Sawtooth','Falling Sawtooth','Sinc','Gaussian','Half sine','DC Voltage']

# Imports. Get picosdk from: https://www.picotech.com/downloads
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox, QDoubleSpinBox, QLabel, QMessageBox
import qdarkstyle
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from scipy import signal, special
import ctypes
import time
if (not UI_DEBUG):
    from picosdk import ps5000a as ps
    from picosdk import assert_pico_ok

class MyApp(QWidget):
    def __init__(self, main=None):
        super().__init__()
        self.main=main

        # Hardware parameters
        self.status = {}
        self.chandle = ctypes.c_int16()

        # Connect pico
        self.picoHWinit()
        
        # Signal parameters
        self.wave_type = 0          # Number of wavetype
        self.V_pk = 1.0             # Peak voltage in V
        self.frequency = 1000000    # Signal frequency
        self.V_offset = 0           # Offset voltage in V
        self.N_cycles = 20          # Number of cycles
        self.PRP_time = 0.005       # PRP time in seconds. Inverse of pulse-repetition frequency (PRF). PRP = 1/PRF
        self.N_bursts = 100         # Number of singal bursts

        # Set the window title and size
        self.setWindowTitle('Signal generator UI')
        self.setGeometry(300, 300, 1400, 600) # 300, 300, 500, 500

        # WAVE TYPE
        # Create a label to display wave types
        self.select_wave_label = QLabel('Select the wave type:', self)
        # Create a Dropdown menu
        self.select_wave_combo_box = QComboBox(self)
        self.select_wave_combo_box.addItem('0: Sine')  # Add options to the combo box
        self.select_wave_combo_box.addItem('1: Square')
        self.select_wave_combo_box.addItem('2: Triangle')
        self.select_wave_combo_box.addItem('3: Rising sawtooth')
        self.select_wave_combo_box.addItem('4: Falling sawtooth')
        self.select_wave_combo_box.addItem('5: Sinc')
        self.select_wave_combo_box.addItem('6: Gaussian')
        self.select_wave_combo_box.addItem('7: Half sine')
        self.select_wave_combo_box.addItem('8: DC Voltage')
        # Connect the selection change event to a method
        self.select_wave_combo_box.currentIndexChanged.connect(self.wavetype_changed)
        # Wave Type Layout
        selectwave_layout = QHBoxLayout()
        selectwave_layout.addWidget(self.select_wave_label)
        selectwave_layout.addWidget(self.select_wave_combo_box)

        # PEAK VOLTAGE
        self.vpeak_label = QLabel('Set peak voltage in V:', self)
        self.vpeak_box = QDoubleSpinBox(self)
        self.vpeak_box.setRange(0.0, VPEAKMAX)      # Set range of values
        self.vpeak_box.setValue(self.V_pk)          # Set the default value
        self.vpeak_box.setSingleStep(VOLTAGESTEP)   # Set step between values
        self.vpeak_box.setDecimals(5)               # Number of decimal places
        # Event
        self.vpeak_box.valueChanged.connect(self.vpeak_changed)
        # Layout
        vpeak_layout = QHBoxLayout()
        vpeak_layout.addWidget(self.vpeak_label)
        vpeak_layout.addWidget(self.vpeak_box)

        # FREQUENCY
        self.freq_label = QLabel('Set frequency in Hz:', self)
        self.freq_box = QDoubleSpinBox(self)
        self.freq_box.setRange(FREQMIN, FREQMAX)
        self.freq_box.setValue(self.frequency)
        self.freq_box.setSingleStep(FREQSTEP)
        self.freq_box.setDecimals(3)
        # Event
        self.freq_box.valueChanged.connect(self.freq_changed)
        # Layout
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(self.freq_label)
        freq_layout.addWidget(self.freq_box)

        # V_OFFSET
        self.voff_label = QLabel('Set offset voltage in V:', self)
        self.voff_box = QDoubleSpinBox(self)
        self.voff_box.setRange(-VPEAKMAX, VPEAKMAX)
        self.voff_box.setValue(self.V_offset)
        self.voff_box.setSingleStep(VOLTAGESTEP)
        self.voff_box.setDecimals(5)
        # Event
        self.voff_box.valueChanged.connect(self.voff_changed)
        # Layout
        voff_layout = QHBoxLayout()
        voff_layout.addWidget(self.voff_label)
        voff_layout.addWidget(self.voff_box)

        # NUMBER OF CYCLES
        self.ncycles_label = QLabel('Number of cycles (Use 0 to generate a continuous wave):', self)
        self.ncycles_box = QSpinBox(self)
        self.ncycles_box.setRange(0, 2147483647)              # Max value in data type uint32_t: 4294967295. Max int value: 2147483647
        self.ncycles_box.setValue(self.N_cycles)
        self.ncycles_box.setSingleStep(1)
        # Event
        self.ncycles_box.valueChanged.connect(self.ncycles_changed)
        # Layout
        ncycles_layout = QHBoxLayout()
        ncycles_layout.addWidget(self.ncycles_label)
        ncycles_layout.addWidget(self.ncycles_box)

        # PRP Time
        self.prptime_label = QLabel('PRP Time in seconds:', self)
        self.prptime_box = QDoubleSpinBox(self)
        self.prptime_box.setRange(0.0, 2147483647)               # Max int value: 2147483647
        self.prptime_box.setValue(self.PRP_time)
        self.prptime_box.setSingleStep(0.00001)
        self.prptime_box.setDecimals(5)
        # Event
        self.prptime_box.valueChanged.connect(self.prptime_changed)
        # Layout
        prptime_layout = QHBoxLayout()
        prptime_layout.addWidget(self.prptime_label)
        prptime_layout.addWidget(self.prptime_box)

        # NUMBER OF BURSTS
        self.nbursts_label = QLabel('Number of bursts:', self)
        self.nbursts_box = QSpinBox(self)
        self.nbursts_box.setRange(0, 2147483647)     # Max int value: 2147483647
        self.nbursts_box.setValue(self.N_bursts)        
        self.nbursts_box.setSingleStep(1)
        # Event
        self.nbursts_box.valueChanged.connect(self.nbursts_changed)
        # Layout
        nbursts_layout = QHBoxLayout()
        nbursts_layout.addWidget(self.nbursts_label)
        nbursts_layout.addWidget(self.nbursts_box)

        # Create buttons. Add buttons to the layout
        self.preview_button = QPushButton('Preview signal', self)
        self.preview_button.clicked.connect(self.preview_button_click)
        self.signal_generate_button = QPushButton('Generate signal', self)
        self.signal_generate_button.clicked.connect(self.signal_generate_button_click)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.preview_button)
        buttons_layout.addWidget(self.signal_generate_button)

        # Define console
        try:
            self.console = self.main.MaRGE.console
        except AttributeError as e:
            print(f"Error accessing MaRGE console: {e}")
            self.console = None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.console = None

        # Create a vertical layout
        self.param_layout = QVBoxLayout()
        self.param_layout.addLayout(selectwave_layout)
        self.param_layout.addLayout(vpeak_layout)
        self.param_layout.addLayout(freq_layout)
        self.param_layout.addLayout(voff_layout)
        self.param_layout.addLayout(ncycles_layout)
        self.param_layout.addLayout(prptime_layout)
        self.param_layout.addLayout(nbursts_layout)
        self.param_layout.addLayout(buttons_layout)


         # Create Matplotlib Figure and Canvas
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.canvas)

        # Create main layout
        layout = QHBoxLayout()
        layout.addLayout(self.param_layout)
        layout.addLayout(plot_layout)

        # Set the layout for the window
        self.setLayout(layout)

        # Create a subplot once for the whole application
        self.axs = self.fig.add_subplot(111)

        # Create the confirmation message box with multiline text
        self.confirm_msg = QMessageBox(self)
        self.confirm_msg.setIcon(QMessageBox.Warning)
        self.confirm_msg.setWindowTitle('Configuration')
        self.confirm_msg.setText('Do you want to proceed with the following configuration?')  # Main message
        self.confirm_msg.setInformativeText(
            f"Wave type: {self.wave_type} : {WAVE_TYPES[self.wave_type]}\n"
            +"Peak voltage: {:.5f} V \n".format(self.V_pk)
            +"Frequency: {:.3f} Hz \n".format(self.frequency)
            +"Offset voltage: {:.5f} V \n".format(self.V_offset)
            +f"Cycles: {self.N_cycles} \n"
            +"PRP time: {:.5f} s  \n".format(self.PRP_time)
            +f"Bursts: {self.N_bursts} \n"
        )
        self.confirm_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.confirm_msg.setDefaultButton(QMessageBox.No)

        # Confirmation box for continuous wave
        self.cont_wave_msg = QMessageBox(self)
        self.cont_wave_msg.setIcon(QMessageBox.Information)
        self.cont_wave_msg.setText("Press Stop to stop signal generation")
        self.cont_wave_msg.setWindowTitle("Continuous wave mode")
        cont_wave_button = self.cont_wave_msg.addButton(QMessageBox.Ok)
        cont_wave_button.setText("Stop")

    def fix_console(self):
        self.param_layout.addWidget(self.console)

    # GUI functions
    def wavetype_changed(self):
        # Get the selected text from the combo box
        selected_option = self.select_wave_combo_box.currentText()
        # Save self.wave_type into variable
        self.wave_type = int(selected_option.split(':')[0])

        print(f"Selected option: {selected_option}. self.wave_type value: {self.wave_type}")

    def vpeak_changed(self, value):
        if abs(self.V_offset)+value > VPEAKMAX:
            self.vpeak_box.setValue(self.V_pk)
        else:
            self.V_pk = value
            print("Peak voltage set to: {:.5f} V".format(self.V_pk))
        
    def freq_changed(self, value):
        if (self.N_cycles/value) > self.PRP_time:
            self.freq_box.setValue(self.frequency)
        else:
            self.frequency = value
            print("Frequency set to: {:.3f} Hz".format(self.frequency))

    def voff_changed(self, value):
        if self.V_pk + abs(value) > VPEAKMAX:
            self.voff_box.setValue(self.V_offset)
        else:
            self.V_offset = value
            print("Offset voltage set to: {:.5f} V".format(self.V_offset))

    def ncycles_changed(self, value):
        if (value/self.frequency) > self.PRP_time:
            self.ncycles_box.setValue(self.N_cycles)
        else:
            self.N_cycles = value
            print("Number of cycles changed to: ", self.N_cycles)

    def prptime_changed(self, value):
        if (self.N_cycles/self.frequency) > value:
            self.prptime_box.setValue(self.PRP_time)
        else:
            self.PRP_time = value
            print("PRP time changed to: {:.5f} s".format(self.PRP_time))

    def nbursts_changed(self, value):
        self.N_bursts = value
        print("Number of bursts changed to: ", self.N_bursts)

    def signal_generate_button_click(self):
        # Update the plot before generating the signal
        self.update_plot()
        # Ask the user for confirmation
        if self.confirmation_dialog():
            print("Configuration confirmed")
            if (not UI_DEBUG):
                # Show status
                offset_V = int(self.V_offset * 1000000)         # Offset Voltage in uV
                V_pkpk = int(self.V_pk * 1000000 * 2)           # peak to peak Voltage in uV
                wavetype = ctypes.c_int32(int(self.wave_type))  # waveType = ctypes.c_int16(0) = PS5000A_SINE
                startFreq = int(self.frequency)                 # Start frequency
                endFreq = int(self.frequency)                   # End frequency. It is the same frequency as the start frequency in this case
                increment = 0
                dwelltime = 1
                sweepType = ctypes.c_int32(0)                   # sweepType = ctypes.c_int16(1) = PS5000A_UP
                operation = 0
                shots = self.N_cycles                           # Number of cycles. If shots are equal to 0, the generated signal will be continuous
                sweeps = 0
                triggertype = ctypes.c_int32(0)                 # triggerType = ctypes.c_int16(0) = PS5000a_SIGGEN_RISING
                triggerSource = ctypes.c_int32(4)               # triggerSource = ctypes.c_int16(0) = P5000a_SIGGEN_NONE.
                extInThreshold = 1
                self.status["SetSigGenBuiltInV2"] = ps.ps5000aSetSigGenBuiltInV2(self.chandle, offset_V, V_pkpk, wavetype, startFreq, endFreq, increment, dwelltime, sweepType, operation, shots, sweeps, triggertype, triggerSource, extInThreshold)
                
                # Burst mode. DC Voltage does not work in burst mode.
                if (self.N_cycles != 0 and self.wave_type != 8):
                    print("Burst mode")
                    for n in range(0,self.N_bursts):
                        start_time = time.time()
                        self.status["SigGenSoftwareControl"] = ps.ps5000aSigGenSoftwareControl(self.chandle, 0)
                        while (time.time()-start_time) < self.PRP_time:
                            pass
                    print("End")
                # Continuous mode
                else:
                    print('Continuous mode')
                    self.cont_wave_msg.exec_()
                    self.status["SetSigGenBuiltInV2"] = ps.ps5000aSetSigGenBuiltInV2(self.chandle, 0, 0, ctypes.c_int32(8), startFreq, endFreq, increment, dwelltime, sweepType, operation, 0, sweeps, triggertype, triggerSource, extInThreshold)
                    print("End")

            else:
                print("Signal generation HW DEBUG MODE")
        else:
            print("Signal not generated")


    def update_plot(self):
        num_of_cycles = self.N_cycles
        # If continuous wave mode, the number of cycles will be 0. An arbitrary value has been set to show the signal
        if num_of_cycles == 0:
            num_of_cycles = 5
        # Signal parameters
        f = self.frequency          # Signal frequency (Hz)
        t_max = num_of_cycles / f   # Time span for N cycles
        sampling_rate = f * 500     # Sampling rate (samples per second)
        t = np.linspace(0, t_max, int(t_max * sampling_rate), endpoint=False)  # Time array
        plot_signal = []
        plot_title = ''
        # Sine wave
        if self.wave_type == 0:
            plot_signal = np.sin(2 * np.pi * f * t)
            plot_title = 'Sine Wave'
        # Square wave
        elif self.wave_type == 1:
            plot_signal = signal.square(2 * np.pi * f * t)
            plot_title = 'Square Wave'
        # Triangular wave
        elif self.wave_type == 2:
            plot_signal = signal.sawtooth(2 * np.pi * f * t + np.pi/2, 0.5)  # 0.5 for a symmetric triangle
            plot_title = 'Triangle Wave'
        # Rising Sawtooth
        elif self.wave_type == 3:
            plot_signal = signal.sawtooth(2 * np.pi * f * t, 1)
            plot_title = 'Rising Sawtooth'
        # Falling Sawtooth
        elif self.wave_type == 4:
            plot_signal = signal.sawtooth(2 * np.pi * f * t, 0)
            plot_title = 'Falling Sawtooth'
        # Periodic Sinc
        elif self.wave_type == 5:
            plot_signal = special.diric(2 * np.pi * f * t + np.pi, 23)
            plot_title = 'Sinc'
        # Periodic Gaussian
        elif self.wave_type == 6:
            plot_signal = np.zeros_like(t)
            period = 1/f
            std = period/10
            for i in range(0, num_of_cycles):
                plot_signal += np.exp(-0.5 * ((t - i * period - period/2) / std) ** 2)
            plot_signal = 2*plot_signal-1
            plot_title = 'Gaussian'
        # Half sine
        elif self.wave_type == 7:
            plot_signal = np.abs(np.sin(2 * np.pi * f * t / 2))
            plot_title = 'Half sine'
        # DC Voltage
        elif self.wave_type == 8:
            plot_signal = np.sin(2 * np.pi * f * t) * 0.0
            plot_title = 'DC Voltage'
        else:
            plot_signal = np.sin(2 * np.pi * f * t)
            plot_title = 'Sine Wave'

        # Signal denormalization
        plot_signal = plot_signal*self.V_pk + self.V_offset

        # Plot waveform
        self.axs.clear()
        self.axs.plot(t, plot_signal)
        self.axs.set_title(plot_title)
        self.axs.set_ylabel('Voltage (V)')
        self.axs.set_xlabel('Time (s)')
        self.axs.grid(True)
        self.canvas.draw()

    def preview_button_click(self):
        # It updates the plot when the user requests a preview
        self.update_plot()

    def picoHWinit(self):
        if (not UI_DEBUG):
            # Open the device
            self.status["openUnit"] = ps.ps5000aOpenUnit(ctypes.byref(self.chandle), None, 1)
            try:
                assert_pico_ok(self.status["openUnit"])
            except: # PicoNotOkError:
                powerStatus = self.status["openUnit"]
                if powerStatus == 286:
                    self.status["changePowerSource"] = ps.ps5000aChangePowerSource(self.chandle, powerStatus)
                elif powerStatus == 282:
                    self.status["changePowerSource"] = ps.ps5000aChangePowerSource(self.chandle, powerStatus)
                else:
                    raise
                assert_pico_ok(self.status["changePowerSource"])
        else:
            print("Starting app: UI DEBUG")
        
    def closeEvent(self, event):
        # When app is closed
        print("Closing app")
        if (not UI_DEBUG):
            self.status["close"] = ps.ps5000aCloseUnit(self.chandle)
        print("App closed")

    def confirmation_dialog(self):
        # The confirmation dialog shows the signal parameters before proceeding to signal generation
        number_of_cycles = self.N_cycles
        if number_of_cycles == 0:
            number_of_cycles = '0 (continuous wave)'
        self.confirm_msg.setInformativeText(
            f"Wave type: {self.wave_type} : {WAVE_TYPES[self.wave_type]}\n"
            +"Peak voltage: {:.5f} V \n".format(self.V_pk)
            +"Frequency: {:.3f} Hz \n".format(self.frequency)
            +"Offset voltage: {:.5f} V \n".format(self.V_offset)
            +f"Cycles: {number_of_cycles} \n"
            +"PRP time: {:.5f} s  \n".format(self.PRP_time)
            +f"Bursts: {self.N_bursts} \n"
        )
        reply = self.confirm_msg.exec_()
        if reply == QMessageBox.Yes:
            return True
        else:
            return False
        

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Apply qdarkstyle
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    # Create and show the main window
    window = MyApp()
    window.show()

    # Run the application's event loop
    sys.exit(app.exec_())
