import os

def pilih_user_data_dir(base_dir="/home/ferdi_cloxt00/Profiles"):
    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
    if not folders:
        print("Tidak ada folder yang ditemukan di direktori.")
        return None
    print("Profiles List :")
    for idx, folder in enumerate(folders):
        print(f"{idx + 1}. {folder}")
    while True:
        try:
            choice = int(input("\nPilih nomor folder yang akan digunakan (masukkan nomor): ")) - 1
            if 0 <= choice < len(folders):
                selected_folder = folders[choice]
                break
            else:
                print("Nomor yang dipilih tidak valid. Silakan pilih lagi.")
        except ValueError:
            print("Input harus berupa angka. Silakan coba lagi.")
    user_data_dir = os.path.join(base_dir, selected_folder)
    print(f"\nFolder yang dipilih: {selected_folder}")
    print(f"Path untuk user_data_dir: {user_data_dir}")
    return user_data_dir

user_data_dir = pilih_user_data_dir()
os.makedirs(user_data_dir, exist_ok=True)  # Membuat folder jika belum ada

# File tempat menyimpan cookie
cookie_file = os.path.join(user_data_dir, "cookies_occ.txt")

def save_cookies(cookies):
    """Simpan cookies ke file teks"""
    with open(cookie_file, "w") as file:
        file.write(cookies)
    print(f"Cookies berhasil disimpan di {cookie_file}")

def main():
    # Meminta input cookie dari pengguna
    cookie_input = input("Masukkan cookie: ")

    # Menyimpan cookies ke file
    save_cookies(cookie_input)

if __name__ == "__main__":
    main()