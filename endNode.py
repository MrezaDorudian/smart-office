import time
from paho.mqtt import client as mqtt_client


class User:
    def __init__(self):
        self.protocol = None
        self.room_id = None
        self.password = None
        self.identifier = None

    def set_info(self):
        self.identifier = input('Enter your ID: ')
        self.password = input('Enter your password: ')
        self.room_id = input('Enter your room ID: ')
        self.protocol = input('Enter The protocol you want to use (1. MQTT   2. COAP): ')
        if self.protocol == '1':
            self.protocol = 'MQTT'
        elif self.protocol == '2':
            self.protocol = 'COAP'

    def get_info(self):
        return {
            'identifier': self.identifier,
            'password': self.password,
            'room_id': self.room_id,
            'protocol': self.protocol
        }


class Device:
    def __init__(self):
        self.user = User()
        self.current_command = None
        self.mqtt_broker = 'broker.emqx.io'

    def print_menu(self):
        print('\n ----------------------- Main Menu ----------------------- \n')
        print(' Welcome to the Smart Office System!                     ')
        print(' 1. Enter the room                                       ')
        print(' 2. Exit                                                 ')
        command = input()
        if command == '1':
            self.current_command = 'run'
        elif command == '2':
            self.current_command = 'exit'

    @staticmethod
    def decode_data(client, userdata, message):
        message = (message.payload.decode("utf-8"))
        print()
        if message == 'False':
            print('wrong username or password')
            client.disconnect()
        else:
            print('Welcome to the Smart Office System!')
            print('You are now in the room')

    def send_to_server(self):
        info = self.user.get_info()

        if info['protocol'] == 'MQTT':
            client = mqtt_client.Client()
            client.connect(self.mqtt_broker)
            client.loop_start()
            client.publish('info', f"{info['identifier']}:{info['password']}:{info['room_id']}")
            client.loop_stop()
            print('published to the broker')
            client.loop_start()
            client.subscribe('auth')
            client.on_message = Device.decode_data
            time.sleep(5)
            client.loop_stop()
        elif info['protocol'] == 'COAP':
            pass

    def run(self):
        while True:
            self.print_menu()
            if self.current_command == 'run':
                self.user.set_info()
                self.send_to_server()
            else:
                break


Device().run()
