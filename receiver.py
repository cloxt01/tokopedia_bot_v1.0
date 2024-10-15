import socket
import json
from datetime import datetime, timezone, timedelta

get_occ_multi = None 
one_click_checkout = None

def times():
    utc_now = datetime.now(timezone.utc)
    gmt_plus_7_time = utc_now + timedelta(hours=7)
    formatted_time = gmt_plus_7_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-2]
    return formatted_time

def receive_data():
    
    global get_occ_multi
    global one_click_checkout
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("localhost", 65432))
        server_socket.listen()

        print("Server berjalan di localhost:65432")
        conn, addr = server_socket.accept()
        print(f"Koneksi diterima dari {addr}")

        data_buffer = b""
        while True:
            data = conn.recv(4096)
            if not data:
                break
            data_buffer += data

        try:
            json_data = json.loads(data_buffer.decode('utf-8'))
            if "get_occ_multi" in json_data:
                get_occ_multi = json_data
            elif "one_click_checkout" in json_data:
                one_click_checkout = json_data
            else:
                print("Sinyal tidak valid:", json_data)

        except json.JSONDecodeError:
            print("Error decoding JSON data")

        conn.close()
        print("Koneksi ditutup.")
        server_socket.close()
        print("Server socket ditutup.")
    except KeyboardInterrupt:
        print("Program dihentikan oleh pengguna.")

if __name__ == "__main__":
    receive_data()
