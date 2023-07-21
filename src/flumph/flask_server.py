from flask import Flask, request, jsonify

app = Flask(__name__)
app.debug = False


@app.route('/', methods=['POST'])
def receive_text():
    t = request.get_data(as_text=True)
    print(f'from http: {t}')
    return jsonify(success=True)


def start_flask():
    print("Starting Flask server...")
    app.run(port=1414)