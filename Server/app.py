from flask import Flask, request, jsonify, send_file
import sys
import os
import json
import matplotlib.pyplot as plt
import networkx as nx

# Agrega el directorio raíz del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa el módulo huffman después de ajustar sys.path
from huffman import decompress, draw_huffman_tree, calculate_frequency, build_heap, merge_nodes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Variable global para almacenar el texto descomprimido
global_decompressed_text = ""

# Ruta de inicio opcional
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

    # Leer el reverse_mapping desde el archivo JSON
    reverse_mapping_file = request.files['reverse_mapping']
    reverse_mapping = json.load(reverse_mapping_file)

    try:
        decompressed_text = decompress(compressed_data, reverse_mapping)
        global_decompressed_text = decompressed_text  # Guardar para dibujar el árbol más tarde
        
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
            plt.savefig('static/huffman_tree.png')
            plt.close()
            return jsonify({"message": "Árbol de Huffman generado correctamente.", "image_url": "/download_tree"})
        else:
            return jsonify({"error": "No se pudo generar el árbol de Huffman."}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download_tree', methods=['GET'])
def download_tree():
    try:
        return send_file('static/huffman_tree.png', as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Escuchar en todas las interfaces con host='0.0.0.0'
    app.run(host='0.0.0.0', port=5001, debug=True)  # Servidor escucha en el puerto 5001
