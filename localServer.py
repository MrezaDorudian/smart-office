import json
import time
from datetime import timedelta

import paho.mqtt.client as mqtt_client
import threading
import flask
import jwt
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity, JWTManager, create_access_token
from flask_caching import Cache
import mysql.connector as mysql
import multiprocessing


class MQTTClient:
    broker_address = 'broker.emqx.io'

    def __init__(self):
        self.client = mqtt_client.Client()
        self.client.connect(MQTTClient.broker_address)

    @staticmethod
    def handle_info(client, userdata, message):
        message = (message.payload.decode("utf-8"))
        user_id, password, room_id = message.split(':')
        auth = MQTTClient.authenticate(user_id, password)
        print(user_id, password, room_id, auth)
        # client.connect(MQTTClient.broker_address)
        client.publish('auth', f'{auth}')

    @staticmethod
    def authenticate(user_id, password):
        with open('localServerDatabase.json', 'r') as f:
            database = json.load(f)
            for key, value in database['users'].items():
                if value['username'] == user_id:
                    if value['password'] == password:
                        return True
            return False

    def subscribe(self):
        self.client.subscribe('info')
        self.client.on_message = self.handle_info
        self.client.loop_forever()


def setup_mqtt_client():
    server = MQTTClient()
    server.subscribe()


class HTTPServer:
    app = flask.Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "super-secret"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=45)
    jwt = JWTManager(app)

    @staticmethod
    def check_user_in_database(username, database):
        with open('localServerDatabase.json', 'r') as file:
            data = json.load(file)[database]
            print(data)
            for key, value in data.items():
                if value['username'] == username:
                    return True
            return False

    @staticmethod
    def check_user_pass_in_database(username, password, database):
        with open('localServerDatabase.json', 'r') as file:
            data = json.load(file)[database]
            for key, value in data.items():
                if value['username'] == username and value['password'] == password:
                    return True
            return False

    # ================================== admin endpoints ==================================
    @staticmethod
    @app.route('/api/admin/register', methods=['PUT', 'POST'])
    @jwt_required()
    def admin_register():
        request_body = flask.request.get_json()
        try:
            username = request_body['username']
            password = request_body['password']
        except KeyError:
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'Missing username or password'}), 400
            )
        if HTTPServer.check_user_in_database(username, 'admins'):
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'Admin already exists'}), 400
            )

        with open('localServerDatabase.json', 'r+') as file:
            data = json.load(file)
            data['admins'][f'Admin {len(data["admins"]) + 1}'] = {'username': username, 'password': password}
            with open('localServerDatabase.json', 'w') as output_file:
                json.dump(data, output_file, indent=4)
                return flask.make_response(
                    flask.jsonify({'status': 'success', 'message': 'admin created'}), 200
                )

    @staticmethod
    @app.route('/api/admin/login', methods=['PUT', 'POST'])
    def admin_login():
        request_body = flask.request.get_json()
        try:
            username = request_body['username']
            password = request_body['password']
        except KeyError:
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'Missing username or password'}), 400
            )
        if HTTPServer.check_user_pass_in_database(username, password, 'admins'):
            access_token = create_access_token(identity=username)
            return flask.make_response(
                flask.jsonify({'status': 'success', 'message': 'admin logged in', 'access_token': access_token}), 200
            )
        return flask.make_response(
            flask.jsonify({'status': 'error', 'message': 'Wrong username or password'}), 400
        )

    @staticmethod
    @app.route('/api/admin/user/register', methods=['PUT', 'POST'])
    @jwt_required()
    def user_register():
        request_body = flask.request.get_json()
        try:
            username = request_body['username']
            password = request_body['password']
            room = request_body['room']
        except KeyError:
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'Missing information'}), 400
            )
        if HTTPServer.check_user_in_database(username, 'users'):
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'User already exists'}), 400
            )
        with open('localServerDatabase.json', 'r+') as file:
            data = json.load(file)
            data['users'][f'User {len(data["users"]) + 1}'] = {'username': username, 'password': password, 'room': room}
            with open('localServerDatabase.json', 'w') as output_file:
                json.dump(data, output_file, indent=4)
                return flask.make_response(
                    flask.jsonify({'status': 'success', 'message': 'user created'}), 200
                )

    @staticmethod
    @app.route('/api/admin/activities', methods=['GET'])
    @jwt_required()
    def user_activities():
        return 'activities viewed'

    @staticmethod
    @app.route('/api/admin/changepass', methods=['PUT', 'POST'])
    @jwt_required()
    def admin_change_pass():
        request_body = flask.request.get_json()
        try:
            username = request_body['username']
            password = request_body['password']
            new_password = request_body['new_password']
        except KeyError:
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'Missing information'}), 400
            )
        if HTTPServer.check_user_pass_in_database(username, password, 'admins'):
            with open('localServerDatabase.json', 'r+') as file:
                data = json.load(file)
                data['admins'][f'Admin {len(data["admins"])}'] = {'username': username, 'password': new_password}
                with open('localServerDatabase.json', 'w') as output_file:
                    json.dump(data, output_file, indent=4)
                    return flask.make_response(
                        flask.jsonify({'status': 'success', 'message': 'admin password changed'}), 200
                    )
        return flask.make_response(
            flask.jsonify({'status': 'error', 'message': 'Wrong username or password'}), 400
        )

    @staticmethod
    @app.route('/api/admin/delete', methods=['Delete'])
    @jwt_required()
    def admin_delete():
        current_admin = get_jwt_identity()
        request_body = flask.request.get_json()
        try:
            username = request_body['username']
            password = request_body['password']
        except KeyError:
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'Missing information'}), 400
            )
        if username == current_admin:
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'Cannot delete yourself'}), 400
            )
        if HTTPServer.check_user_pass_in_database(username, password, 'admins'):
            with open('localServerDatabase.json', 'r+') as file:
                data = json.load(file)
                print(data['admins'])
                for key, value in data['admins'].items():
                    if value['username'] == username:
                        del data['admins'][key]
                        break
                with open('localServerDatabase.json', 'w') as output_file:
                    json.dump(data, output_file, indent=4)
                    return flask.make_response(
                        flask.jsonify({'status': 'success', 'message': 'admin deleted'}), 200
                    )
        return flask.make_response(
            flask.jsonify({'status': 'error', 'message': 'Wrong username or password'}), 400
        )

    @staticmethod
    @app.route('/api/admin/user/delete', methods=['DELETE'])
    @jwt_required()
    def user_delete():
        request_body = flask.request.get_json()
        try:
            username = request_body['username']
            password = request_body['password']
        except KeyError:
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'Missing information'}), 400
            )
        if HTTPServer.check_user_pass_in_database(username, password, 'users'):
            with open('localServerDatabase.json', 'r+') as file:
                data = json.load(file)
                for key, value in data['users'].items():
                    if value['username'] == username:
                        del data['users'][key]
                        break
                with open('localServerDatabase.json', 'w') as output_file:
                    json.dump(data, output_file, indent=4)
                    return flask.make_response(
                        flask.jsonify({'status': 'success', 'message': 'user deleted'}), 200
                    )
        return flask.make_response(
            flask.jsonify({'status': 'error', 'message': 'Wrong username or password'}), 400
        )

    # ================================== user  endpoints ==================================

    @staticmethod
    @app.route('/api/user/login', methods=['PUT', 'POST'])
    def user_login():
        request_body = flask.request.get_json()
        try:
            username = request_body['username']
            password = request_body['password']
        except KeyError:
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'Missing username or password'}), 400
            )
        if HTTPServer.check_user_pass_in_database(username, password, 'users'):
            access_token = create_access_token(identity=username)
            return flask.make_response(
                flask.jsonify({'status': 'success', 'message': 'user logged in', 'access_token': access_token}), 200
            )
        return flask.make_response(
            flask.jsonify({'status': 'error', 'message': 'Wrong username or password'}), 400
        )
        pass

    @staticmethod
    @app.route(f'/api/user/:<userid>', methods=['PUT', 'POST'])
    @jwt_required()
    def user_update(userid):
        light_value = flask.request.args.get('lights')
        print(userid, light_value)
        return 'user updated'

    @staticmethod
    @app.route('/api/user/changepass', methods=['PUT', 'POST'])
    @jwt_required()
    def user_change_pass():
        request_body = flask.request.get_json()
        try:
            username = request_body['username']
            password = request_body['password']
            new_password = request_body['new_password']
        except KeyError:
            return flask.make_response(
                flask.jsonify({'status': 'error', 'message': 'Missing username or password'}), 400
            )
        if HTTPServer.check_user_pass_in_database(username, password, 'users'):
            with open('localServerDatabase.json', 'r+') as file:
                data = json.load(file)
                for key, value in data['users'].items():
                    if value['username'] == username:
                        data['users'][key]['password'] = new_password
                        break
                with open('localServerDatabase.json', 'w') as output_file:
                    json.dump(data, output_file, indent=4)
                    return flask.make_response(
                        flask.jsonify({'status': 'success', 'message': 'password changed'}), 200
                    )
        return flask.make_response(
            flask.jsonify({'status': 'error', 'message': 'Wrong username or password'}), 400
        )

    def run(self):
        self.app.run(port=8080, debug=True)


def setup_http_server():
    server = HTTPServer()
    server.run()


if __name__ == '__main__':
    setup_mqtt_client()
    # jobs = []
    # p1 = multiprocessing.Process(target=setup_http_server)
    # jobs.append(p1)
    # p2 = multiprocessing.Process(target=setup_mqtt_client)
    # jobs.append(p2)
    # p1.start()
    # p2.start()
