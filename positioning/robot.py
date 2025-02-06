from positioning.smc_jxc91 import actuator_smc
from positioning.bora import Bora
import threading


class robot():
    def __init__(self):
        # Create a list to hold the threads
        threads = []
        self.smc_devices = [None] * 3  # Initialize a list to store smc actuators
        self.bora = None  # Initialize to store the bora hexapod

        # Create and start a thread for each smc initialization
        for ii, axis in enumerate(['x', 'y', 'z']):
            thread = threading.Thread(target=self._init_smc, args=(ii, axis))
            threads.append(thread)
            thread.start()

        # Create and start a thread for bora hexapod
        thread = threading.Thread(target=self._init_bora, args=())
        threads.append(thread)
        thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

    def _init_smc(self, index, axis):
        # This method initializes each device and stores it in the self.devices list
        self.smc_devices[index] = actuator_smc(axis=axis)

    def _init_bora(self):
        self.bora = Bora()


    def move(self, position=None):
        # Get position
        if position is None:
            position = [0, 0, 0, 0, 0, 0]
        smc_position = position[:3]
        bora_position = (0, 0, 0, 0, position[3], position[4], position[5])

        # Create a list of threads
        threads = []

        # Create and start a thread for each device movement
        for ii in range(len(self.smc_devices)):
            thread = threading.Thread(target=self.smc_devices[ii].move_mm, args=(smc_position[ii],))
            threads.append(thread)
            thread.start()

        thread = threading.Thread(target=self.bora.move_absolute, args=(bora_position,))
        threads.append(thread)
        thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        print("READY!")

        return True

if __name__ == '__main__':
    device = robot()
    device.move(position=[50, -50, 50, 3, 3, 3])
    device.move(position=[0, 0, 0, 0, 0, 0])
