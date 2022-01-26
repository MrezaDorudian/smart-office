import flask


class HTTPServer:
    app = flask.Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "super-secret"

    @staticmethod
    @app.route("/api/office/register", methods=['PUT', 'POST'])
    def register():
        return "register"

    def run(self):
        self.app.run(port=8888, debug=True)


if __name__ == '__main__':
    server = HTTPServer()
    server.run()
