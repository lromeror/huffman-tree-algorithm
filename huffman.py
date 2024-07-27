import tkinter as tk
from tkinter import filedialog, messagebox
import heapq
import networkx as nx
import matplotlib.pyplot as plt
import os

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def calculate_frequency(text):
    frequency = {}
    for char in text:
        if not char in frequency:
            frequency[char] = 0
        frequency[char] += 1
    return frequency

def build_heap(frequency):
    heap = []
    for key in frequency:
        node = Node(key, frequency[key])
        heapq.heappush(heap, node)
    return heap

def merge_nodes(heap):
    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)
        merged = Node(None, node1.freq + node2.freq)
        merged.left = node1
        merged.right = node2
        heapq.heappush(heap, merged)
    return heap

def make_codes_helper(node, current_code, codes, reverse_mapping):
    if node is None:
        return
    if node.char is not None:
        codes[node.char] = current_code
        reverse_mapping[current_code] = node.char
        return
    make_codes_helper(node.left, current_code + "0", codes, reverse_mapping)
    make_codes_helper(node.right, current_code + "1", codes, reverse_mapping)

def make_codes(heap):
    root = heap[0]
    current_code = ""
    codes = {}
    reverse_mapping = {}
    make_codes_helper(root, current_code, codes, reverse_mapping)
    return codes, reverse_mapping

def get_encoded_text(text, codes):
    encoded_text = ""
    for char in text:
        encoded_text += codes[char]
    return encoded_text

def pad_encoded_text(encoded_text):
    extra_padding = 8 - len(encoded_text) % 8
    for i in range(extra_padding):
        encoded_text += "0"
    padded_info = "{0:08b}".format(extra_padding)
    encoded_text = padded_info + encoded_text
    return encoded_text

def get_byte_array(padded_encoded_text):
    b = bytearray()
    for i in range(0, len(padded_encoded_text), 8):
        byte = padded_encoded_text[i:i+8]
        b.append(int(byte, 2))
    return b

def compress(text):
    frequency = calculate_frequency(text)
    heap = build_heap(frequency)
    heap = merge_nodes(heap)
    codes, reverse_mapping = make_codes(heap)
    encoded_text = get_encoded_text(text, codes)
    padded_encoded_text = pad_encoded_text(encoded_text)
    return get_byte_array(padded_encoded_text), codes, reverse_mapping

def remove_padding(padded_encoded_text):
    padded_info = padded_encoded_text[:8]
    extra_padding = int(padded_info, 2)
    padded_encoded_text = padded_encoded_text[8:]
    encoded_text = padded_encoded_text[:-1 * extra_padding]
    return encoded_text

def decode_text(encoded_text, reverse_mapping):
    current_code = ""
    decoded_text = ""
    for bit in encoded_text:
        current_code += bit
        if current_code in reverse_mapping:
            character = reverse_mapping[current_code]
            decoded_text += character
            current_code = ""
    return decoded_text

def decompress(input_bytes, reverse_mapping):
    bit_string = ""
    for byte in input_bytes:
        bit_string += f"{byte:08b}"
    encoded_text = remove_padding(bit_string)
    return decode_text(encoded_text, reverse_mapping)

# Función para crear el gráfico del árbol
def create_huffman_tree_graph(node, graph, pos=None, x=0, y=0, layer=1, parent=None):
    if pos is None:
        pos = {}
    pos[node] = (x, y)
    if parent:
        graph.add_edge(parent, node)
    if node.left:
        l = x - 1 / layer
        create_huffman_tree_graph(node.left, graph, pos=pos, x=l, y=y-1, layer=layer+1, parent=node)
    if node.right:
        r = x + 1 / layer
        create_huffman_tree_graph(node.right, graph, pos=pos, x=r, y=y-1, layer=layer+1, parent=node)
    return graph, pos

def draw_huffman_tree(root):
    graph = nx.DiGraph()
    graph, pos = create_huffman_tree_graph(root, graph)
    labels = {node: f'{node.char}\nFreq: {node.freq}' if node.char else f'Freq: {node.freq}' for node in graph.nodes()}
    plt.figure(figsize=(12, 8))
    nx.draw(graph, pos, labels=labels, with_labels=True, node_size=3000, node_color='lightblue', font_size=10, font_color='black', font_weight='bold', arrows=False)
    plt.show()

def compress_file(input_file, output_file):
    with open(input_file, 'r') as file:
        text = file.read()
    compressed_data, codes, reverse_mapping = compress(text)
    with open(output_file, 'wb') as file:
        file.write(bytes(compressed_data))
    return codes, reverse_mapping

def decompress_file(input_file, output_file, reverse_mapping):
    with open(input_file, 'rb') as file:
        input_bytes = file.read()
    decompressed_data = decompress(input_bytes, reverse_mapping)
    with open(output_file, 'w') as file:
        file.write(decompressed_data)

# Interfaz gráfica
class HuffmanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Compresión y Descompresión con Huffman")
        self.file_path = None
        self.codes = None
        self.reverse_mapping = None

        self.label = tk.Label(root, text="Seleccione un archivo para comprimir y descomprimir:")
        self.label.pack(pady=10)

        self.upload_button = tk.Button(root, text="Cargar Archivo", command=self.upload_file)
        self.upload_button.pack(pady=5)

        self.compress_button = tk.Button(root, text="Comprimir Archivo", command=self.compress_file)
        self.compress_button.pack(pady=5)

        self.decompress_button = tk.Button(root, text="Descomprimir Archivo", command=self.decompress_file)
        self.decompress_button.pack(pady=5)

    def upload_file(self):
        self.file_path = filedialog.askopenfilename()
        if self.file_path:
            messagebox.showinfo("Archivo Cargado", f"Archivo cargado: {self.file_path}")
        else:
            messagebox.showwarning("Advertencia", "No se seleccionó ningún archivo")

    def compress_file(self):
        if not self.file_path:
            messagebox.showwarning("Advertencia", "Primero debe cargar un archivo")
            return

        compressed_file = 'compressed.bin'
        self.codes, self.reverse_mapping = compress_file(self.file_path, compressed_file)
        original_size = os.path.getsize(self.file_path)
        compressed_size = os.path.getsize(compressed_file)
        messagebox.showinfo("Compresión Completa", f"Archivo comprimido guardado como {compressed_file}\n"
                                                   f"Tamaño original: {original_size} bytes\n"
                                                   f"Tamaño comprimido: {compressed_size} bytes")
        self.draw_huffman_tree()

    def decompress_file(self):
        if not self.codes or not self.reverse_mapping:
            messagebox.showwarning("Advertencia", "Primero debe comprimir un archivo")
            return

        compressed_file = 'compressed.bin'
        decompressed_file = 'decompressed.txt'
        decompress_file(compressed_file, decompressed_file, self.reverse_mapping)
        messagebox.showinfo("Descompresión Completa", f"Archivo descomprimido guardado como {decompressed_file}")

    def draw_huffman_tree(self):
        frequency = calculate_frequency(open(self.file_path, 'r').read())
        heap = build_heap(frequency)
        heap = merge_nodes(heap)
        root = heap[0]
        draw_huffman_tree(root)

if __name__ == "__main__":
    root = tk.Tk()
    app = HuffmanApp(root)
    root.mainloop()
