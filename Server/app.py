from flask import Flask, request, jsonify
from huffman import decompress

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No se ha proporcionado un archivo"}), 400
    
    file = request.files['file']
    compressed_data = file.read()
    
    # Aquí necesitas cargar el reverse_mapping de alguna manera
    reverse_mapping = {}  # Por ejemplo, podrías enviarlo junto con los datos comprimidos
    
    decompressed_text = decompress(compressed_data, reverse_mapping)

    # Calcular los tamaños
    compressed_size = len(compressed_data)
    original_size = len(decompressed_text.encode('utf-8'))
    compression_ratio = compressed_size / original_size

    return jsonify({
        "original_size": original_size,
        "compressed_size": compressed_size,
        "compression_ratio": compression_ratio,
        "decompressed_text": decompressed_text
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
