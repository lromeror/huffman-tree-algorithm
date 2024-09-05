from flask import Flask, request, jsonify, send_file
import os
import json
import sys
import matplotlib.pyplot as plt
import uuid  # Para generar nombres únicos de archivo

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from huffman import decompress, draw_huffman_tree, calculate_frequency, build_heap, merge_nodes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATIC_FOLDER'] = 'static'

global_decompressed_text = ""

# Crear el directorio de subida si no existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def home():
    return "Servidor de Huffman funcionando. Para subir archivos comprimidos, use la ruta /upload con una solicitud POST."

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
        # Generar un nombre único para el archivo utilizando UUID
        unique_filename = str(uuid.uuid4()) + "_" + file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Guardar el archivo en la carpeta de uploads
        with open(file_path, 'wb') as f:
            f.write(compressed_data)

        # Descomprimir el texto utilizando Huffman
        decompressed_text = decompress(compressed_data, reverse_mapping)
        global_decompressed_text = decompressed_text

        # Calcular los tamaños
        compressed_size = len(compressed_data)
        original_size = len(decompressed_text.encode('utf-8'))
        compression_ratio = compressed_size / original_size if original_size != 0 else 0

        return jsonify({
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio
        })

    except Exception as e:
        print(f"Error al descomprimir los datos: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/draw_tree', methods=['GET'])
def draw_tree():
    global global_decompressed_text
    try:
        if not global_decompressed_text:
            return jsonify({"error": "No hay texto descomprimido para dibujar el árbol."}), 400

        # Generar y guardar el árbol de Huffman
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
        print(f"Error al generar el árbol de Huffman: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # Ruta completa al archivo dentro de la carpeta de uploads
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Verifica si el archivo existe antes de enviarlo
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"error": "El archivo no existe en el servidor."}), 404
    except Exception as e:
        print(f"Error al descargar el archivo {filename}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/list_files', methods=['GET'])
def list_files():
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        return jsonify(files)
    except Exception as e:
        print(f"Error al listar archivos: {e}")
        return jsonify([])

@app.route('/download_tree', methods=['GET'])
def download_tree():
    try:
        tree_image_path = os.path.join(app.config['STATIC_FOLDER'], 'huffman_tree.png')
        if os.path.exists(tree_image_path):
            return send_file(tree_image_path, as_attachment=True)
        else:
            return jsonify({"error": "El archivo no existe en el servidor."}), 404
    except Exception as e:
        print(f"Error al descargar el árbol de Huffman: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
