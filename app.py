from flask import Flask, request, jsonify, render_template
from interpreter import interpret_cscript

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code', '')
    inputs = data.get('inputs', '')
    output = interpret_cscript(code, inputs)
    return jsonify({"output": output})

if __name__ == '__main__':
    app.run(debug=True)
