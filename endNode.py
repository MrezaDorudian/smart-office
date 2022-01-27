import os
import time
from paho.mqtt import client as mqtt_client
import asyncio

from aiocoap import *


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
        self.coap_uri = 'coap://localhost:5555/info'

    def print_menu(self):
        print('Welcome to the Smart Office System!')
        print('1. Enter the room')
        print('2. Exit')
        command = input()
        if command == '1':
            self.current_command = 'run'
        elif command == '2':
            self.current_command = 'exit'

    @staticmethod
    def decode_mqtt_data(client, userdata, message):
        msg = message.payload.decode("utf-8")
        print()

        if msg == 'False':
            print('wrong username or password')
            client.disconnect()
        else:
            print('Welcome to the Smart Office System!')
            print('You are now in the room')
            print('current light is: ' + msg)
            input('type "exit" to close the program\n')

    def mqtt_protocol(self, info):
        client = mqtt_client.Client()
        client.connect(self.mqtt_broker)
        client.loop_start()
        try:
            client.publish('info', f"{info['identifier']}:{info['password']}:{info['room_id']}")
        except KeyError:
            client.publish('info', 'exit')
        client.loop_stop()
        print('published to the broker')
        client.loop_start()
        client.subscribe('authentication')
        client.on_message = Device.decode_mqtt_data
        time.sleep(5)
        client.loop_stop()

    async def decode_coap_data(self, response):
        response = response.decode('utf-8')
        if response == 'False':
            print('wrong username or password')
            time.sleep(5)
            os.system('cls' if os.name == 'nt' else 'clear')
        else:
            print('Welcome to the Smart Office System!')
            print('You are now in the room')
            print('current light is: ' + response)
            input('type "exit" to close the program\n')
            proto = await Context.create_client_context()
            info = self.user.get_info()
            payload = f"{info['identifier']}:{info['password']}:{info['room_id']}:exit"
            request = Message(code=Code.POST, uri=self.coap_uri, payload=payload.encode('utf-8'))
            response = await proto.request(request).response

    async def coap_protocol(self, info):
        proto = await Context.create_client_context()
        try:
            payload = f"{info['identifier']}:{info['password']}:{info['room_id']}"
        except KeyError:
            payload = 'exit'
        request = Message(code=Code.POST, uri=self.coap_uri, payload=payload.encode('utf-8'))
        try:
            response = await proto.request(request).response
            await self.decode_coap_data(response.payload)
        except Exception as e:
            print(e)

    def send_to_server(self):
        info = self.user.get_info()

        if info['protocol'] == 'MQTT':
            self.mqtt_protocol(info)

        elif info['protocol'] == 'COAP':
            asyncio.get_event_loop().run_until_complete(self.coap_protocol(info))

    def run(self):
        while True:
            self.print_menu()
            if self.current_command == 'run':
                self.user.set_info()
                self.send_to_server()
            else:
                break


if __name__ == '__main__':
    device = Device()
    device.run()
