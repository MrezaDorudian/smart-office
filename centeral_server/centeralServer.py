import datetime
import json
import flask
import jwt


class HTTPServer:
    app = flask.Flask(__name__)
    jwt_secret_key = 'super-secret'

    @staticmethod
    @app.route("/", methods=["GET"])
    def index():
        token = flask.request.headers['Authorization'].split(' ')[1]
        payload = jwt.decode(token, HTTPServer.jwt_secret_key, algorithms=['HS256'])
        if payload['from'] == 'local_server':
            with open('centralServerDatabase.json', 'r') as f:
                data = json.load(f)
                for key, value in data['users'].items():
                    if value['id'] == payload['user_id']:
                        data['activity'][f'Activity {len(data["activity"]) + 1}'] = {
                            'username': payload['user_id'],
                            'office': payload['office_id'],
                            'datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'type': payload['type']
                        }
                        with open('centralServerDatabase.json', 'w') as output_file:
                            json.dump(data, output_file, indent=4)
                            return flask.make_response(flask.jsonify(value['light']), 200)
        else:
            return flask.make_response(flask.jsonify({'error': 'not authorized'}), 401)

    @staticmethod
    @app.route("/api/office/register", methods=['PUT', 'POST'])
    def register():
        request_body = flask.request.get_json()
        with open('centralServerDatabase.json', 'r') as f:
            data = json.load(f)
            data['office'][f'Office {len(data["office"]) + 1}'] = {'id': request_body['id'],
                                                                   'name': request_body['name']}
            with open('centralServerDatabase.json', 'w') as output_file:
                json.dump(data, output_file, indent=4)
                return flask.make_response(
                    flask.jsonify({'status': 'success', 'message': 'office created'}), 200
                )

    def run(self):
        self.app.run(port=8888, debug=True)


if __name__ == '__main__':
    server = HTTPServer()
    server.run()
