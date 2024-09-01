from flask import Flask, request, render_template, jsonify
import os
import requests
import socket
import sys
import json

# Agrega el directorio raíz del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from huffman import compress  # Importa desde el directorio raíz

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Obtener la IP local de la máquina de forma automática
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
SERVER_URL = f'http://{local_ip}:5001/upload'  # Ruta para cargar y comprimir datos
TREE_URL = f'http://{local_ip}:5001/draw_tree'  # Ruta para dibujar el árbol de Huffman

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

    # Convertir reverse_mapping a una cadena JSON para enviar al servidor
    reverse_mapping_json = json.dumps(reverse_mapping)

    # Enviar el archivo comprimido y el reverse_mapping al servidor
    try:
        response = requests.post(SERVER_URL, files={
            'file': ('compressed.bin', compressed_data),
            'reverse_mapping': ('reverse_mapping.json', reverse_mapping_json)
        })
        response.raise_for_status()  # Lanza una excepción para códigos de error HTTP

        if response.status_code == 200:
            return render_template('index.html', result=response.json())
        else:
            return f"Error al enviar datos al servidor: {response.status_code} {response.text}", 500
    except requests.exceptions.RequestException as e:
        return f"Error al enviar datos al servidor: {e}", 500

@app.route('/request_tree', methods=['POST'])
def request_tree():
    try:
        response = requests.get(TREE_URL)
        response.raise_for_status()

        if response.status_code == 200:
            return render_template('index.html', tree_generated=True)
        else:
            return f"Error al generar el árbol de Huffman: {response.status_code} {response.text}", 500
    except requests.exceptions.RequestException as e:
        return f"Error al generar el árbol de Huffman: {e}", 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)  # Cliente escucha en el puerto 5000
