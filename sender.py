import socket

def main():
    # Membuat socket klien
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("localhost", 6789))  # Menghubungkan ke server

    # Mengirim sinyal dengan pemisah newline
    client_socket.sendall(b"Found\n")  # Mengirim sinyal "Found"
    client_socket.sendall(b"Another Message\n")  # Mengirim sinyal pesan lain
    client_socket.sendall(b"STOP\n")   # Mengirim sinyal "STOP"

    client_socket.close()  # Menutup koneksi

if __name__ == "__main__":
    main()
