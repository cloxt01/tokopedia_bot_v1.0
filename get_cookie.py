from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime, timezone, timedelta

def times():
    utc_now = datetime.now(timezone.utc)
    gmt_plus_7_time = utc_now + timedelta(hours=7)
    return gmt_plus_7_time.strftime('%Y-%m-%d %H:%M:%S')
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
def save_cookies(file, cookies):
    tokopedia_cookies = [cookie for cookie in cookies if 'tokopedia.com' in cookie['domain']]
    cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in tokopedia_cookies])
    
    with open(file, 'w') as cookie:
        cookie.write(cookie_string)
    print(f"[{times()}] Saved to {file}")
def main():
    user_data_dir = pilih_user_data_dir()

    with sync_playwright() as p:
        browser = p.firefox.launch_persistent_context(
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            user_data_dir=user_data_dir,
            headless=True,
            proxy={"server": "socks5://127.0.0.1:1080"},
            args = ["--disable-http3"]
        )

        page = browser.pages[0]
        url = "https://www.tokopedia.com"
        print(f"[{times()}] {url}")
        
        # Tunggu halaman sepenuhnya dimuat
        try:
            page.goto(url, wait_until='networkidle', timeout=60000)  # Set timeout ke 60 detik
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return

        print(f"[{times()}] Mengambil cookie..")
        cookies = page.context.cookies()

        # Filter cookies sesuai dengan domain
        filtered_cookies = [
            cookie for cookie in cookies 
            if cookie['domain'].endswith('.tokopedia.com')
        ]

        # Pastikan direktori untuk menyimpan file ada
        os.makedirs('cookie', exist_ok=True)

        # Simpan cookie yang telah difilter ke dalam file
        file_cookies = f'{user_data_dir}/cookie.txt'
        with open('cookie/tokopedia.txt', 'w') as f:
            json.dump(filtered_cookies, f, indent=2)
        save_cookies(file_cookies, filtered_cookies)  # Pastikan yang disimpan adalah filtered_cookies

if __name__ == "__main__":
    main()
