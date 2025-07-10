from flask import Flask

app = Flask(__name__)


def get_hello_world():
    return "Hello World"


@app.route("/", methods=["GET"])
def hello_world():
    return get_hello_world()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
