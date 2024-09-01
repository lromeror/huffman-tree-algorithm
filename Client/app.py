from flask import Flask, request, render_template, jsonify
import os
import requests
from huffman import compress

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
SERVER_URL = 'http://192.168.1.2:5001/upload'  # Reemplaza con la dirección IP del servidor

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compress_and_send', methods=['POST'])
def compress_and_send():
    text = ""
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        text = file.read().decode('utf-8')
    elif 'text' in request.form and request.form['text'].strip() != '':
        text = request.form['text']
    else:
        return "No se proporcionó ni archivo ni texto", 400

    compressed_data, codes, reverse_mapping = compress(text)
    
    if not compressed_data:
        return "No hay datos para comprimir", 400

    # Enviar el archivo comprimido al servidor
    response = requests.post(SERVER_URL, files={'file': ('compressed.bin', compressed_data)})

    if response.status_code == 200:
        return render_template('index.html', result=response.json())
    else:
        return "Error al enviar datos al servidor", 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
