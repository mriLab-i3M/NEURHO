import paramiko  # Import the Paramiko library for SSH functionality.
import configs.hw_config as hw  # Import configuration settings for the connection.
import time


class Bora(paramiko.SSHClient):  # Inherit from paramiko.SSHClient.
    """
        A class to manage and control the Bora robotic system from Symétrie via SSH using the Paramiko library.

        This class inherits from `paramiko.SSHClient` and extends its functionality to handle
        Bora-specific commands, allowing initialization, configuration, and positional control.

        Attributes:
            stderr (file-like object): Standard error stream for the SSH session.
            stdout (file-like object): Standard output stream for the SSH session.
            stdin (file-like object): Standard input stream for the SSH session.
        """

    def __init__(self):
        """
        Initializes the Bora class and establishes an SSH connection to the Bora system.

        The connection uses credentials provided in the `config.hw_config` module.
        If the connection is successful, the Bora application is initialized.

        Raises:
            Exception: If the SSH connection fails or an error occurs during initialization.
        """
        super().__init__()  # Initialize the parent class (paramiko.SSHClient).

        # Set the policy to automatically add unknown host keys to the known hosts.
        self.stderr = None
        self.stdout = None
        self.stdin = None
        self.ssh_ready = False
        self.timeout = 0.5
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the remote server using credentials from the configuration module.
        print("Connecting to Bora by ssh...")
        n = 0
        while not self.ssh_ready:
            try:
                self.connect(
                    hostname=hw.bora_ip,  # The hostname or IP address of the server.
                    username=hw.bora_user,  # Username for authentication.
                    password=hw.bora_password,  # Password for authentication.
                    port=hw.bora_port,  # SSH connection port (default is 22).
                    timeout=5
                )
                print("Connected to Bora by ssh!")
                self.ssh_ready = True
            except:
                print("No connection...")
                n += 1
            if n == 1:
                break

        if self.ssh_ready:
            self.initialize_bora()
        else:
            print("Connection failed.")

    def initialize_bora(self):
        """
        Initializes the Bora application on the server.

        This method starts the Bora application by executing the `gpascii -2` command
        on the server and then calls `configure_bora` to finalize the configuration.

        Raises:
            Exception: If there is an error during initialization.
        """
        try:
            print("Initializing Bora application...")
            self.stdin, self.stdout, self.stderr = self.exec_command('gpascii -2')
            time.sleep(self.timeout)
            self.clean_outputs()

            self.wait_to_hardware()

            self.configure_bora()

            #self.move_absolute((0, 0, 0, 0, 0, 0, 0))
        except Exception as e:
            print(f"Failed to initialize Bora application: {e}")

    def configure_bora(self):
        """
        Configures the Bora application for use.

        This method sends a series of commands to clear errors, enable control, and
        set up the Bora system for operation.

        Raises:
            Exception: If there is an error during configuration.
        """
        try:
            print("Configuring Bora...")
            self.send_command('c_cmd=C_CLEARERROR')
            self.send_command('c_cmd=C_CONTROLON')
            self.clean_outputs()
            print("READY: Bora application is ready.")
        except Exception as e:
            print(f"Configuration error: {e}")

    def send_command(self, command):
        """
        Sends a single command to the Bora application.

        Parameters:
            command (str): The command string to send.

        Raises:
            Exception: If an error occurs while writing the command.
        """
        if self.ssh_ready:
            self.stdin.write(command + '\n')
            time.sleep(self.timeout)
            self.stdin.flush()

    def wait_to_hardware(self):
        """
        Waits for the hardware to initialize by continuously sending commands
        and checking for a specific status response.

        The function first checks if the SSH connection is ready. If so, it
        enters a loop where it sends the 's_hexa' command to the hardware,
        waits for the response, and checks if the status has been updated to '1',
        indicating that the hardware is ready. The loop continues until the
        status is '1', at which point the hardware is considered initialized.

        During the process, the function also sends the 'echo7' command and
        handles any exceptions that might occur when processing the status.

        This function uses the `timeout` attribute to control the delay between
        successive attempts to check the hardware status.

        Prints:
            "Waiting to hardware initialization..." when the process begins.
            "Hardware initialized!" once the hardware is successfully initialized.

        Raises:
            None: The function assumes that the status will eventually become '1'.
                  Any exceptions encountered while processing the status are caught
                  and ignored.
        """
        if self.ssh_ready:
            print("Waiting to hardware initialization...")
            status = '0'
            while status != '1':
                self.send_command('s_hexa')
                time.sleep(self.timeout)
                while not self.stdout.channel.recv_ready():
                    time.sleep(self.timeout)
                status = self.stdout.channel.recv(1024).decode('utf-8')
                self.send_command('echo7')
                try:
                    status = bin(int(status.split('\n')[1]))[3]
                except:
                    pass
            print("Hardware initialized!")

    def wait_to_finish(self):
        """
        Sends the 's_action' command to the remote system and waits for a response from stdout.

        The method repeatedly sends the 's_action' command until the response starts with '0',
        indicating a successful action or completion. It checks the stdout of the remote system
        for the response.

        Returns:
            None: This method does not return a value.
        """
        if self.ssh_ready:
            action = '\x06'
            while action[0] != "0":
                self.send_command('s_action')
                time.sleep(self.timeout)
                action = self.stdout.channel.recv(1024).decode('utf-8')

    def clean_outputs(self):
        """
        Clears any available data from the stdout buffer.

        This method checks if there is any data ready to be read from the stdout channel.
        If data is available, it reads and discards up to 1024 bytes to clear the buffer
        without processing the content. This is useful for removing any stale or leftover data
        that may have accumulated in the output stream.

        Returns:
            None
        """
        if self.ssh_ready:
            if self.stdout.channel.recv_ready():
                self.stdout.channel.recv(1024)

    def move_absolute(self, position):
        """
        Move the Bora hexapod to the specified absolute position.

        Parameters:
        position (tuple): A 7-element tuple representing the mode and target positions.

        Raises:
        ValueError: If the position is not a tuple with seven elements.
        """
        if self.ssh_ready:
            if not isinstance(position, (tuple, list)) or len(position) != 7:
                raise ValueError("Position must be a tuple or list with seven elements.")

            command = " ".join([f"c_par({i})={pos}" for i, pos in enumerate(position)])
            self.send_command(command)
            time.sleep(self.timeout)
            print("Moving Bora hexapod...")
            self.send_command("c_cmd=C_MOVE_PTP")
            time.sleep(self.timeout)
            self.wait_to_finish()
            print("READY: Movement ready!")
            return True
        else:
            return False

if __name__ == "__main__":
    from positioning.smc_jxc91 import smc
    # Example usage of the Bora class
    hexapod = Bora()
    hexapod.move_absolute((0, 0, 0, 0, 1, 1, 1))  # Move to the specified position
    hexapod.move_absolute((0, 0, 0, 0, 0, 0, 0))
