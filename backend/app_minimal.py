from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return "Minimal Flask App - Working!", 200

@app.route('/api/test')
def test():
    return jsonify({'status': 'success', 'message': 'API is working'}), 200

if __name__ == '__main__':
    app.run()
