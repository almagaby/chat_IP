import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import os
import struct 

SERVER_HOST = '172.168.0.107'
SERVER_PORT = 9685

clients = []
usernames = {}
screenshot_count = 1

def broadcast(message, source_client=None):
    for client in clients:
        if client != source_client:
            try:
                client.send(message.encode())
            except:
                clients.remove(client)

def handle_client(client_socket, client_address):
    username = f"{client_address[0]} ({client_address[1]})"
    usernames[client_socket] = username
    welcome_message = f"Bienvenido {username} al chat."
    update_log(welcome_message)
    broadcast(welcome_message, client_socket)

    while True:
        try:
            message = client_socket.recv(1024)
            if not message:
                update_log(f"Cliente {client_address} desconectado.")
                clients.remove(client_socket)
                client_socket.close()
                break

            if message.decode(errors='ignore').startswith("SCREENSHOT"):
                save_screenshot(client_socket)
            else:
                try:
                    decoded_message = message.decode('utf-8')
                    update_log(f"Mensaje recibido de {username}: {decoded_message}")
                    broadcast(f"{username}: {decoded_message}", client_socket)
                except UnicodeDecodeError:
                    update_log(f"Error al decodificar mensaje de {username}")

        except Exception as e:
            update_log(f"Error al recibir mensajes de {client_address}: {str(e)}")
            clients.remove(client_socket)
            client_socket.close()
            break

def save_screenshot(client_socket):
    global screenshot_count
    try:
        length_bytes = client_socket.recv(8)
        if len(length_bytes) < 8:
            raise ValueError("No se recibió la longitud completa de la captura de pantalla.")
        
        length = struct.unpack('>Q', length_bytes)[0]
        screenshot_data = b""
        
        while len(screenshot_data) < length:
            packet = client_socket.recv(min(4096, length - len(screenshot_data)))
            if not packet:
                raise ConnectionError("Conexión perdida al recibir la captura de pantalla.")
            screenshot_data += packet

        if screenshot_data:
            root.withdraw()  # Ocultar la ventana principal temporalmente
            file_path = filedialog.askdirectory(title="Selecciona la carpeta para guardar la captura de pantalla")
            root.deiconify()  # Mostrar la ventana principal nuevamente
            if file_path:
                file_name = os.path.join(file_path, f"img{screenshot_count}.jpg")
                while os.path.exists(file_name):
                    overwrite = messagebox.askyesno("Sobrescribir archivo", f"El archivo {file_name} ya existe. ¿Deseas sobrescribirlo?")
                    if overwrite:
                        break
                    else:
                        screenshot_count += 1
                        file_name = os.path.join(file_path, f"img{screenshot_count}.jpg")

                with open(file_name, "wb") as f:
                    f.write(screenshot_data)
                update_log(f"Captura de pantalla guardada de {usernames[client_socket]} en {file_name}.")
                
                screenshot_count += 1
            else:
                update_log("No se seleccionó un directorio para guardar la captura de pantalla.")
        else:
            update_log("No se recibieron datos para la captura de pantalla.")

    except Exception as e:
        update_log(f"Error al recibir captura de pantalla: {str(e)}")

def accept_connections():
    while True:
        client_socket, client_address = server_socket.accept()
        update_log(f"Nueva conexión entrante de {client_address}")
        clients.append(client_socket)
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

def send_message(event=None):
    message = message_entry.get()
    if message:
        update_log(f"Servidor: {message}")
        broadcast(f"Servidor: {message}")
        message_entry.delete(0, tk.END)

def request_screenshot():
    ip_to_capture = ip_entry.get()
    for client in clients:
        client_address = client.getpeername()[0]
        if client_address == ip_to_capture:
            client.send("SCREENSHOT".encode())
            update_log(f"Solicitud de captura de pantalla enviada a {ip_to_capture}.")
            break
    else:
        update_log(f"No se encontró el cliente con la IP: {ip_to_capture}.")

def update_log(message):
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, message + '\n')
    log_text.config(state=tk.DISABLED)
    log_text.see(tk.END)
    
def on_closing():
    for client in clients:
        client.close()
    server_socket.close()
    root.destroy()

# Crear un socket TCP/IP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen()

# Crear ventana de la interfaz gráfica
root = tk.Tk()
root.title("Chat Servidor")

log_text = scrolledtext.ScrolledText(root, state=tk.DISABLED, width=50, height=20)
log_text.pack(padx=10, pady=10)

message_entry = tk.Entry(root, width=40)
message_entry.pack(padx=10, pady=(0, 10))
message_entry.bind("<Return>", send_message)

send_button = tk.Button(root, text="Enviar", command=send_message)
send_button.pack(pady=(0, 10))

# Entrada de IP para captura de pantalla
ip_entry = tk.Entry(root, width=30)
ip_entry.pack(padx=10, pady=(0, 10))

screenshot_button = tk.Button(root, text="Tomar captura de pantalla", command=request_screenshot)
screenshot_button.pack(pady=(0, 10))

root.protocol("WM_DELETE_WINDOW", on_closing)

accept_thread = threading.Thread(target=accept_connections)
accept_thread.start()

root.mainloop()
