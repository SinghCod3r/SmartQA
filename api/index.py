from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
@app.route('/api')
@app.route('/api/')
def index():
    return jsonify({'status': 'success', 'message': 'Flask is working on Vercel!'}), 200

@app.route('/api/test')
def test():
    return jsonify({'test': 'passed'}), 200
