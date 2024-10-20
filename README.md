# tokopedia_bot_v1.0

`tokopedia_bot_v1.0` adalah versi pertama dari bot Tokopedia yang dirancang untuk memudahkan pengguna dalam melakukan pembelian produk dan memantau status pesanan. Versi ini mencakup berbagai pembaruan dan perbaikan untuk meningkatkan kinerja serta stabilitas aplikasi.

## Fitur Utama

- **Pembelian Satu Klik**: Lakukan pembelian produk hanya dengan satu klik.
- **Pemantauan Status Pesanan**: Pantau status pesanan secara real-time.
- **Pembaruan Algoritma Penawaran**: Algoritma yang diperbarui untuk memberikan penawaran produk yang lebih akurat dan relevan.

## Instalasi

Untuk menginstal dan menjalankan `tokopedia_bot_v1.0`, ikuti langkah-langkah berikut:

1. Clone repo ini ke dalam komputer Anda:

    ```bash
    git clone https://github.com/cloxt01/tokopedia_bot_v1.0.git
    ```

2. Masuk ke direktori repo:

    ```bash
    cd tokopedia_bot_v1.0
    ```

3. Install dependencies menggunakan pip:

    ```bash
    pip install -r requirements.txt
    ```

4. Install paket lainnya dengan memasukan perintah:

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip
   ```

5. Install Browser Playwright:
   
  ```bash
  playwright install
  ```

6. Buat Virtual Environment (Recomended):

  ```bash
  python -m venv env
  ```
  
  ##### Linux/macOS:
  
  ```bash
  source env/bin/activate
  ```
  ##### Windows:
  
  ```bash
  env\Scripts\activate
  ```

## Konfigurasi File

`Profiles/(user_data_dir)/AddressProfile.json` adalah file untuk mengatur alamat pengguna yang sebelumnya sudah tersimpan di server.

`get_cookie.py` adalah skrip untuk mendapatkan cookie dari account yang akan digunakan.

`get_product.py` adalah skrip untuk memperbarui keranjang dari ***one_click_checkout***.

`get_cookies_occ.py` adalah untuk memperbarui cookie yang nantinya akan digunakan di permintaan checkout.

`main.py` adalah skrip utama yang digunakan untuk memulai program.

## Output
![Expected Results](https://drive.google.com/uc?export=view&id=1E8tTBcPxPaWs0FRbQMT66qjdFa414e-b)

## Lisensi

Aplikasi ini dilisensikan di bawah [MIT License](LICENSE).
