import paho.mqtt.client as mqtt_client
from utils import authenticate
import utils

jwt_secret_key = 'super-secret'


class MQTTClient:
    broker_address = 'broker.emqx.io'

    def __init__(self):
        self.client = mqtt_client.Client()
        self.client.connect(MQTTClient.broker_address)

    @staticmethod
    def handle_info(client, _userdata, message):
        print(message)
        message = (message.payload.decode("utf-8"))
        user_id, password, room_id = message.split(':')
        auth = authenticate(user_id, password)
        client.loop_start()
        if auth:
            return_value = str(utils.send_get_request_to_central_server(user_id, '4679', jwt_secret_key, '1'))
        else:
            return_value = f'{auth}'
        print(return_value)
        client.publish('authentication', f'{return_value}'.encode('utf-8'))

    def subscribe(self):
        self.client.subscribe('info')
        self.client.on_message = self.handle_info
        self.client.loop_forever()


def setup_mqtt_client():
    server = MQTTClient()
    server.subscribe()


if __name__ == '__main__':
    setup_mqtt_client()
