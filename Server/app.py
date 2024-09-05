from flask import Flask, request, jsonify, send_file
import os
import json
import sys
import uuid
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from huffman import decompress, compress, draw_huffman_tree, calculate_frequency, build_heap, merge_nodes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['COMPRESSED_FOLDER'] = 'compressed'
app.config['DECOMPRESSED_FOLDER'] = 'decompressed'
app.config['STATIC_FOLDER'] = 'static'

for folder in [app.config['UPLOAD_FOLDER'], app.config['COMPRESSED_FOLDER'], app.config['DECOMPRESSED_FOLDER']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

global_decompressed_text = ""  

@app.route('/')
def home():
    return "Servidor de Huffman funcionando."

@app.route('/upload', methods=['POST'])
def upload_file():
    global global_decompressed_text
    if 'file' not in request.files or 'reverse_mapping' not in request.files:
        return jsonify({"error": "No se han proporcionado todos los archivos necesarios"}), 400

    file = request.files['file']
    compressed_data = file.read()

    reverse_mapping_file = request.files['reverse_mapping']
    reverse_mapping = json.load(reverse_mapping_file)

    try:
        unique_filename = str(uuid.uuid4()) + "_" + file.filename
        compressed_file_path = os.path.join(app.config['COMPRESSED_FOLDER'], unique_filename)

        with open(compressed_file_path, 'wb') as f:
            f.write(compressed_data)

        reverse_mapping_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename + '_mapping.json')
        with open(reverse_mapping_path, 'w') as f:
            json.dump(reverse_mapping, f)

        decompressed_text = decompress(compressed_data, reverse_mapping)

        if not decompressed_text:
            return jsonify({"error": "Error al descomprimir el archivo. El texto descomprimido está vacío."}), 400

        global_decompressed_text = decompressed_text

        decompressed_filename = unique_filename.replace('.bin', '.txt')
        decompressed_file_path = os.path.join(app.config['DECOMPRESSED_FOLDER'], decompressed_filename)

        with open(decompressed_file_path, 'w', encoding='utf-8') as f:
            f.write(decompressed_text)

        compressed_size = len(compressed_data)
        original_size = len(decompressed_text.encode('utf-8'))
        compression_ratio = compressed_size / original_size if original_size != 0 else 0

        return jsonify({
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "filename": unique_filename
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para listar archivos disponibles
@app.route('/list_files', methods=['GET'])
def list_files():
    try:
        compressed_files = os.listdir(app.config['COMPRESSED_FOLDER'])
        decompressed_files = os.listdir(app.config['DECOMPRESSED_FOLDER'])

        return jsonify({
            "compressed_files": compressed_files,
            "decompressed_files": decompressed_files
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<folder>/<filename>', methods=['GET'])
def download_file(folder, filename):
    try:
        if folder == "compressed":
            file_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
        elif folder == "decompressed":
            file_path = os.path.join(app.config['DECOMPRESSED_FOLDER'], filename)
        else:
            return jsonify({"error": "Carpeta no válida."}), 400

        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"error": "El archivo no existe en el servidor."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/draw_tree', methods=['GET'])
def draw_tree():
    global global_decompressed_text
    try:
        if not global_decompressed_text:
            return jsonify({"error": "No hay texto descomprimido para dibujar el árbol. Descomprime un archivo primero."}), 400

        frequency = calculate_frequency(global_decompressed_text)
        heap = build_heap(frequency)
        heap = merge_nodes(heap)
        root = heap[0] if heap else None

        if root:
            plt.figure(figsize=(12, 8))
            draw_huffman_tree(root)
            tree_image_path = os.path.join(app.config['STATIC_FOLDER'], 'huffman_tree.png')
            plt.savefig(tree_image_path)
            plt.close()
            return send_file(tree_image_path, mimetype='image/png')
        else:
            return jsonify({"error": "No se pudo generar el árbol de Huffman."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)

