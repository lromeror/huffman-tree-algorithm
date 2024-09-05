from flask import Flask, request, render_template, jsonify, send_file
import os
import requests
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from huffman import compress 

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

SERVER_IP = '192.168.1.174'  # Cambia esto por la IP de tu servidor
SERVER_URL = f'http://{SERVER_IP}:5001/upload'
LIST_FILES_URL = f'http://{SERVER_IP}:5001/list_files'
TREE_URL = f'http://{SERVER_IP}:5001/draw_tree'

@app.route('/')
def index():
    # Solicita la lista de archivos disponibles del servidor
    try:
        response = requests.get(LIST_FILES_URL)
        response.raise_for_status()
        files = response.json()
    except requests.exceptions.RequestException as e:
        files = []
        print(f"Error al obtener la lista de archivos: {e}")
    
    return render_template('index.html', files=files)

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

    reverse_mapping_json = json.dumps(reverse_mapping)

    try:
        # Enviar datos comprimidos al servidor
        response = requests.post(SERVER_URL, files={
            'file': ('compressed.bin', compressed_data),
            'reverse_mapping': ('reverse_mapping.json', reverse_mapping_json)
        })
        response.raise_for_status()

        if response.status_code == 200:
            compression_result = response.json()

            # Obtener la lista de archivos del servidor después de la compresión
            try:
                list_response = requests.get(LIST_FILES_URL)
                list_response.raise_for_status()
                files = list_response.json()
            except requests.exceptions.RequestException as e:
                files = []
                print(f"Error al obtener la lista de archivos después de la compresión: {e}")

            return render_template('index.html', result=compression_result, files=files)
        else:
            return f"Error al enviar datos al servidor: {response.status_code} {response.text}", 500
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar datos al servidor: {e}")
        return f"Error al enviar datos al servidor: {e}", 500

@app.route('/request_tree', methods=['POST'])
def request_tree():
    try:
        response = requests.get(TREE_URL)
        response.raise_for_status()

        if response.status_code == 200:
            with open('static/huffman_tree.png', 'wb') as f:
                f.write(response.content)
            
            # Obtener la lista de archivos del servidor
            try:
                list_response = requests.get(LIST_FILES_URL)
                list_response.raise_for_status()
                files = list_response.json()
            except requests.exceptions.RequestException as e:
                files = []
                print(f"Error al obtener la lista de archivos después de la compresión: {e}")
                
            return render_template('index.html', tree_generated=True, files=files)
        else:
            return f"Error al generar el árbol de Huffman: {response.status_code} {response.text}", 500
    except requests.exceptions.RequestException as e:
        print(f"Error al generar el árbol de Huffman: {e}")
        return f"Error al generar el árbol de Huffman: {e}", 500

@app.route('/show_tree', methods=['GET'])
def show_tree():
    try:
        return send_file('static/huffman_tree.png')
    except Exception as e:
        print(f"Error al mostrar el árbol de Huffman: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
