from flask import Flask, request, render_template, jsonify, send_file
import os
import requests
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from huffman import compress 

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

SERVER_IP = '192.168.1.174'  
SERVER_URL = f'http://{SERVER_IP}:5001/upload'
TREE_URL = f'http://{SERVER_IP}:5001/draw_tree'
DOWNLOAD_COMPRESSED_URL = f'http://{SERVER_IP}:5001/download/compressed'
DOWNLOAD_DECOMPRESSED_URL = f'http://{SERVER_IP}:5001/download/decompressed'
LIST_FILES_URL = f'http://{SERVER_IP}:5001/list_files'

def get_file_lists():
    """Función para obtener la lista de archivos comprimidos y descomprimidos."""
    try:
        response = requests.get(LIST_FILES_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@app.route('/')
def index():
    files_data = get_file_lists() 
    return render_template('index.html', 
                           compressed_files=files_data.get('compressed_files', []), 
                           decompressed_files=files_data.get('decompressed_files', []), 
                           DOWNLOAD_COMPRESSED_URL=DOWNLOAD_COMPRESSED_URL, 
                           DOWNLOAD_DECOMPRESSED_URL=DOWNLOAD_DECOMPRESSED_URL)

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
        response = requests.post(SERVER_URL, files={
            'file': ('compressed.bin', compressed_data),
            'reverse_mapping': ('reverse_mapping.json', reverse_mapping_json)
        })
        response.raise_for_status()

        if response.status_code == 200:
            compression_result = response.json()
            files_data = get_file_lists() 
            return render_template('index.html', 
                                   result=compression_result, 
                                   compressed_files=files_data.get('compressed_files', []), 
                                   decompressed_files=files_data.get('decompressed_files', []), 
                                   DOWNLOAD_COMPRESSED_URL=DOWNLOAD_COMPRESSED_URL, 
                                   DOWNLOAD_DECOMPRESSED_URL=DOWNLOAD_DECOMPRESSED_URL)
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
            with open('static/huffman_tree.png', 'wb') as f:
                f.write(response.content)  
            files_data = get_file_lists()  
            return render_template('index.html', 
                                   tree_generated=True, 
                                   compressed_files=files_data.get('compressed_files', []), 
                                   decompressed_files=files_data.get('decompressed_files', []), 
                                   DOWNLOAD_COMPRESSED_URL=DOWNLOAD_COMPRESSED_URL, 
                                   DOWNLOAD_DECOMPRESSED_URL=DOWNLOAD_DECOMPRESSED_URL)
        else:
            return f"Error al generar el árbol de Huffman: {response.status_code} {response.text}", 500
    except requests.exceptions.RequestException as e:
        return f"Error al generar el árbol de Huffman: {e}", 500

@app.route('/show_tree', methods=['GET'])
def show_tree():
    try:
        return send_file('static/huffman_tree.png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
