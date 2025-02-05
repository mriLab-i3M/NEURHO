from pycomm3 import CIPDriver, Services, INT
import time
import configs.hw_config as hw


class actuador_smc():

    def __init__(self, axis='x'):
        self.config = {}

        # Configure SMC
        self.configure_smc()

        print("Starting pycomm3 CIPDriver demo application...")
        print("Listing device identity...")
        response = CIPDriver.list_identity(self.config['SMC_DRIVER_IP'])
        print("IP Address: {}".format(response['ip_address']))
        print("Vendor: {}".format(response['vendor']))
        print("Product Type: {}".format(response['product_type']))
        print("Product Code: {}".format(response['product_code']))
        print("Revision: {}.{}".format(response['revision']['major'], response['revision']['minor']))
        print("Serial: {}".format(response['serial']))
        print("Product Name: {}".format(response['product_name']))

        self.driver = CIPDriver(self.config['SMC_DRIVER_IP'])
        print("Opening connection to {}...".format(self.config['SMC_DRIVER_IP']))
        self.driver.open()
        if self.driver.connected:
            print("Connection sucessfull!")
        else:
            print("ERROR: Cannot connect to device!")

    def configure_smc(self, axis='x'):
        if axis == 'x':
            self.config['SMC_DRIVER_IP'] = hw.smc_ip_x
            self.config['zero'] = hw.smc_zero_x
        elif axis == 'y':
            self.config['SMC_DRIVER_IP'] = hw.smc_ip_y
            self.config['zero'] = hw.smc_zero_y
        elif axis == 'z':
            self.config['SMC_DRIVER_IP'] = hw.smc_ip_z
            self.config['zero'] = hw.smc_zero_z

    def powerOn(self):
        print("Sending PowerOn command...")
        data_str = "000200000000000000000000000000000000000000000000000000000000000000000000"
        self.driver.generic_message(
            service=Services.set_attribute_single,
            class_code=b'\x04',
            instance=b'\x96',
            attribute=b'\x03',
            request_data=bytes.fromhex(data_str),
            connected=True,
            unconnected_send=False,
            route_path=True
        )
        time.sleep(1.5)  # 1 #Tiene que estar si o si

    def home(self):
        print("Sending StartHoming command...")
        data_str = "001200000000000000000000000000000000000000000000000000000000000000000000"
        self.driver.generic_message(
            service=Services.set_attribute_single,
            class_code=b'\x04',
            instance=b'\x96',
            attribute=b'\x03',
            request_data=bytes.fromhex(data_str),
            connected=True,
            unconnected_send=False,
            route_path=True
        )
        '''resp=self.escuchar()
        print(resp)
        word0=resp[:4]
        while word0[3]!='e':
            resp=self.escuchar()
            word0=resp[:4]'''
        # time.sleep(1.5)#1.5

    def conversor_pos(self, pos_mm):
        new_pos = float(pos_mm) * 100
        pos_hex = hex(int(new_pos))
        aux = str(pos_hex).split('0x')
        ceros = ''
        for i in range(8 - len(aux[1])):
            ceros = ceros + '0'
        pos = ceros + str(aux[1])
        l = len(pos)
        pos_h = pos[:l // 2]
        pos_l = pos[l // 2:]
        pos_h = pos_h[l // 4:] + pos_h[:l // 4]
        pos_l = pos_l[l // 4:] + pos_l[:l // 4]
        return pos_h, pos_l

    def move(self, data_str, data_start):
        print("Sending Move command...")

        '''self.driver.generic_message(
                service=Services.set_attribute_single,
                class_code=b'\x04',
                instance=b'\x96',
                attribute=b'\x03',
                request_data=bytes.fromhex(data_str),
                connected=True,
                unconnected_send=False,
                route_path=True
            )
        time.sleep(1)#1   #Si bajas de 1 va mal porque se salta la posición anterior'''
        print('Moviendo')
        self.driver.generic_message(
            service=Services.set_attribute_single,
            class_code=b'\x04',
            instance=b'\x96',
            attribute=b'\x03',
            request_data=bytes.fromhex(data_start),
            connected=True,
            unconnected_send=False,
            route_path=True
        )
        # 10
        # time.sleep(1)#1
        resp = self.escuchar()
        print(resp)
        word0 = resp[:4]
        if int(word0[2]) >= 8:  # Indica alarma activada
            print('WARNING: Alarm.')
            self.reset_alarm()
        while word0[3] != 'e':
            resp = self.escuchar()
            word0 = resp[:4]

    def powerOff(self):
        print("Sending PowerOff command...")
        data_str = "000000000000000000000000000000000000000000000000000000000000000000000000"
        self.driver.generic_message(
            service=Services.set_attribute_single,
            class_code=b'\x04',
            instance=b'\x96',
            attribute=b'\x03',
            request_data=bytes.fromhex(data_str),
            connected=True,
            unconnected_send=False,
            route_path=True
        )
        print("Closing connection...")
        self.driver.close()

    def reset_alarm(self):
        print("Sending Reset command...")
        data_reset = '000af0ff000100000000000000000000000000000a006400000000000000000032000000'
        # data_str = "000000000000000000000000000000000000000000000000000000000000000000000000"
        self.driver.generic_message(
            service=Services.set_attribute_single,
            class_code=b'\x04',
            instance=b'\x96',
            attribute=b'\x03',
            request_data=bytes.fromhex(data_reset),
            connected=True,
            unconnected_send=False,
            route_path=True
        )
        time.sleep(1)  # 1
        self.powerOn()
        self.home_mm()

    def escuchar(self):
        print('Escuchando')
        data_recv = self.driver.generic_message(
            service=Services.get_attribute_single,
            class_code=b'\x04',
            instance=b'\x64',
            attribute=b'\x03',
            # request_data=bytes.fromhex(data_str),
            connected=True,
            unconnected_send=False,
            route_path=True
        )
        respuesta = data_recv[1].hex()
        return respuesta

    def move_mm(self, position):
        position = str(position - self.config['zero'])

        # Power on the actuator
        self.powerOn()
        time.sleep(1)

        # Miscellaneous
        w01 = '0002f0ff'
        w2 = '0001'
        w2_start = '0101'
        speed = '9600'
        pos_h, pos_l = self.conversor_pos(position)
        aceleracion = 'e803'
        deceleracion = aceleracion
        w8_17 = '000000000a006400000000000000000032000000'
        data_str_start = w01 + w2_start + speed + pos_l + pos_h + aceleracion + deceleracion + w8_17
        data_str = w01 + w2 + speed + pos_l + pos_h + aceleracion + deceleracion + w8_17

        # Move actuator to desired position
        self.move(data_str, data_str_start)

        # Power off the actuator
        self.powerOff()

    def home_mm(self):
        print("Sending Home command...")
        self.move_mm(position=0)


if __name__ == '__main__':
    smc_x = actuador_smc(axis='x')
    smc_x.move_mm(position=10)
