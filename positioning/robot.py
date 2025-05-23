import copy

from positioning.smc_jxc91 import actuator_smc
from positioning.bora import Bora
import threading
import numpy as np


class Robot:
    """
    A class representing a robot system with three SMC actuators and a Bora hexapod.
    The actuators and the hexapod are initialized in parallel using threads.
    """

    def __init__(self):
        """
        Initializes the robot by creating and initializing three SMC actuators
        (for x, y, and z axes) and a Bora hexapod in parallel using threads.
        """
        # Create a list to hold the threads
        threads = []
        self.smc_devices = [None] * 3  # Initialize a list to store SMC actuators
        self.bora = None  # Initialize to store the Bora hexapod
        try:
            self.position = np.array(np.load('position.npy'))
        except:
            self.position = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        print("Initial position:")
        print(self.position)

        # Create and start a thread for each SMC initialization
        for ii, axis in enumerate(['x', 'y', 'z']):
            thread = threading.Thread(target=self._init_smc, args=(ii, axis))
            threads.append(thread)
            thread.start()

        # Create and start a thread for Bora hexapod initialization
        thread = threading.Thread(target=self._init_bora, args=())
        threads.append(thread)
        thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    def _init_smc(self, index, axis):
        """
        Initializes an SMC actuator for a given axis and stores it in the smc_devices list.

        Args:
            index (int): The index in the smc_devices list.
            axis (str): The axis associated with the actuator ('x', 'y', or 'z').
        """
        self.smc_devices[index] = actuator_smc(axis=axis)

    def _init_bora(self):
        """
        Initializes the Bora hexapod and stores it in the bora attribute.
        """
        self.bora = Bora()

    def get_info(self, position=None, mode='relative'):
        if mode == 'absolute':
            # Get position
            if position is None:
                position = np.array([0, 0, 0, 0, 0, 0])
            position_0 = copy.deepcopy(self.position)
            position = position
            smc_position_0 = position_0[:3]
            smc_position = position[:3]
            bora_position_0 = np.array([0, 0, 0, 0, position_0[3], position_0[4], position_0[5]])
            bora_position = np.array([0, 0, 0, 0, position[3], position[4], position[5]])
            dr = (smc_position - smc_position_0) / 4
            smc_positions = []
            bora_positions = []
            smc_positions.append(smc_position_0 + dr)
            smc_positions.append(smc_position_0 + 2 * dr)
            smc_positions.append(smc_position_0 + 3 * dr)
            smc_positions.append(smc_position)
            dphi = (bora_position - bora_position_0) / 4
            bora_positions.append(bora_position_0 + dphi)
            bora_positions.append(bora_position_0 + 2 * dphi)
            bora_positions.append(bora_position_0 + 3 * dphi)
            bora_positions.append(bora_position)
        elif mode == 'relative':
            if position is None:
                position = np.array([0, 0, 0, 0, 0, 0])
            position_0 = copy.deepcopy(self.position)
            position = self.position + position
            smc_position_0 = position_0[:3]
            smc_position = position[:3]
            bora_position_0 = np.array([0, 0, 0, 0, position_0[3], position_0[4], position_0[5]])
            bora_position = np.array([0, 0, 0, 0, position[3], position[4], position[5]])
            dr = (smc_position - smc_position_0) / 4
            smc_positions = []
            bora_positions = []
            smc_positions.append(smc_position_0 + dr)
            smc_positions.append(smc_position_0 + 2 * dr)
            smc_positions.append(smc_position_0 + 3 * dr)
            smc_positions.append(smc_position)
            dphi = (bora_position - bora_position_0) / 4
            bora_positions.append(bora_position_0 + dphi)
            bora_positions.append(bora_position_0 + 2 * dphi)
            bora_positions.append(bora_position_0 + 3 * dphi)
            bora_positions.append(bora_position)


        for ii in range(4):
            smc_position_a = smc_positions[ii]
            bora_position_a = tuple(bora_positions[ii].tolist())
            position_1 = [smc_position_a[0], smc_position_a[1], smc_position_a[2], bora_position_a[4], bora_position_a[5], bora_position_a[6]]
            print("Next position:")
            print(position_1)

        return True


    def move(self, position=None, mode='relative'):
        """
        Moves the robot to the specified position by controlling the SMC actuators
        and the Bora hexapod in parallel using threads.

        Args:
            position (list, optional): A list of six values representing the target positions.
                                      The first three values correspond to the SMC actuators (x, y, z),
                                      and the last three values correspond to the Bora hexapod rotations.
                                      Note that the coordinate system of the SMC actuators
                                      may differ from that of the Bora hexapod.
                                      Defaults to [0, 0, 0, 0, 0, 0].

        Returns:
            bool: True when movement is completed.
        """
        if mode == 'absolute':
            # Get position
            if position is None:
                position = np.array([0, 0, 0, 0, 0, 0])
            position_0 = copy.deepcopy(self.position)
            self.position = position
            smc_position_0 = position_0[:3]
            smc_position = position[:3]
            bora_position_0 = np.array([0, 0, 0, 0, position_0[3], position_0[4], position_0[5]])
            bora_position = np.array([0, 0, 0, 0, position[3], position[4], position[5]])
            dr = (smc_position - smc_position_0) / 4
            smc_positions = []
            bora_positions = []
            smc_positions.append(smc_position_0 + dr)
            smc_positions.append(smc_position_0 + 2 * dr)
            smc_positions.append(smc_position_0 + 3 * dr)
            smc_positions.append(smc_position)
            dphi = (bora_position - bora_position_0) / 4
            bora_positions.append(bora_position_0 + dphi)
            bora_positions.append(bora_position_0 + 2 * dphi)
            bora_positions.append(bora_position_0 + 3 * dphi)
            bora_positions.append(bora_position)
        elif mode == 'relative':
            if position is None:
                position = np.array([0, 0, 0, 0, 0, 0])
            position_0 = copy.deepcopy(self.position)
            self.position = self.position + position
            smc_position_0 = position_0[:3]
            smc_position = self.position[:3]
            bora_position_0 = np.array([0, 0, 0, 0, position_0[3], position_0[4], position_0[5]])
            bora_position = np.array([0, 0, 0, 0, self.position[3], self.position[4], self.position[5]])
            dr = (smc_position - smc_position_0) / 4
            smc_positions = []
            bora_positions = []
            smc_positions.append(smc_position_0 + dr)
            smc_positions.append(smc_position_0 + 2 * dr)
            smc_positions.append(smc_position_0 + 3 * dr)
            smc_positions.append(smc_position)
            dphi = (bora_position - bora_position_0) / 4
            bora_positions.append(bora_position_0 + dphi)
            bora_positions.append(bora_position_0 + 2 * dphi)
            bora_positions.append(bora_position_0 + 3 * dphi)
            bora_positions.append(bora_position)


        for ii in range(4):
            smc_position_a = smc_positions[ii]
            bora_position_a = tuple(bora_positions[ii].tolist())
            position_1 = [smc_position_a[0], smc_position_a[1], smc_position_a[2], bora_position_a[4], bora_position_a[5], bora_position_a[6]]
            print("Next position:")
            print(position_1)

            # Create a list of threads
            threads = []

            # Create and start a thread for each SMC actuator movement
            for ii in range(len(self.smc_devices)):
                thread = threading.Thread(target=self.smc_devices[ii].move_mm, args=(smc_position_a[ii],))
                threads.append(thread)
                thread.start()

            # Create and start a thread for the Bora hexapod movement
            thread = threading.Thread(target=self.bora.move_absolute, args=(bora_position_a,))
            threads.append(thread)
            thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            print("Partial movement ready")

        print("READY!")
        np.save('position.npy', self.position)
        print("Final position:")
        print(self.position)

        return True


if __name__ == '__main__':
    device = Robot()
    # device.move(position=np.array([-10, -10, 10, 3, 3, 3]), mode='relative')
    device.move(position=np.array([0, 0, 0, 0, 0, 0]), mode='absolute')
