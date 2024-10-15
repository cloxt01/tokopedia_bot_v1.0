from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime, timezone, timedelta

def times():
    utc_now = datetime.now(timezone.utc)
    gmt_plus_7_time = utc_now + timedelta(hours=7)
    return gmt_plus_7_time.strftime('%Y-%m-%d %H:%M:%S')

def save_cookies(file, cookies):
    tokopedia_cookies = [cookie for cookie in cookies if 'tokopedia.com' in cookie['domain']]
    cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in tokopedia_cookies])
    
    with open(file, 'w') as cookie:
        cookie.write(cookie_string)
    print(f"[{times()}] Saved to {file}")

def main():
    user_data_dir = r"/home/ferdi_cloxt00/wwd3mtg7.Greatness"

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
        file_cookies = 'cookie/cookie.txt'
        with open('cookie/tokopedia.txt', 'w') as f:
            json.dump(filtered_cookies, f, indent=2)
        save_cookies(file_cookies, filtered_cookies)  # Pastikan yang disimpan adalah filtered_cookies

if __name__ == "__main__":
    main()
