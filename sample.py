import asyncio
from datetime import datetime, timedelta
import pytz
import time

async def wait_until_target_time(target_hour, target_minute, target_second, target_ms):
    # Zona waktu Jakarta
    jakarta_tz = pytz.timezone("Asia/Jakarta")

    # Mendapatkan waktu sekarang di zona waktu Jakarta
    start_task = datetime.now(jakarta_tz)

    # Membuat waktu target dengan menambahkan milidetik secara eksplisit
    target_time = jakarta_tz.localize(datetime.now().replace(
        hour=target_hour,
        minute=target_minute,
        second=target_second,
        microsecond=0  # Set microsecond ke 0 dulu
    )) + timedelta(milliseconds=target_ms)

    # Konversi waktu target ke timestamp
    target_timestamp = target_time.timestamp()
    print("+---------------+--------------+--------------+--------------+")
    print("|     START     |     NOW      |    TARGET    |     TOTAL    |")
    print("+---------------+--------------+--------------+--------------+")

    # Menggunakan perf_counter untuk pengukuran waktu yang lebih presisi
    start_time = time.perf_counter()

    while True:
        # Mendapatkan waktu saat ini di zona waktu Jakarta
        now = datetime.now(jakarta_tz)
        now_timestamp = now.timestamp()

        # Memperbarui tampilan waktu saat ini
        elapsed_time = time.perf_counter() - start_time
        print(f"\r|  {start_task.strftime('%H:%M:%S.%f')[:-3]} | {now.strftime('%H:%M:%S.%f')[:-3]} |  {target_hour}:{target_minute}:{target_second}.{target_ms}  |      {elapsed_time:.2f}    |", end='')

        # Memeriksa apakah waktu saat ini sudah mencapai atau melewati waktu target dengan toleransi 1ms
        if now_timestamp >= target_timestamp - 0.001:  # Mengurangi toleransi 1ms
            print()  # Pindah ke baris baru untuk output berikutnya
            print("+---------------+--------------+--------------+--------------+")
            print("|                            MULAI                           |")
            print("+---------------+--------------+--------------+--------------+")  # Panggil tugas yang dijadwalkan
            break
        


# Fungsi utama
async def main():
    # Menentukan waktu target (jam, menit, detik, milidetik)
    target_hour = 13  # Ganti dengan jam target
    target_minute = 35   # Ganti dengan menit target
    target_second = 59  # Ganti dengan detik target
    target_ms = 0  # Ganti dengan milidetik target

    await wait_until_target_time(target_hour, target_minute, target_second, target_ms)

# Menjalankan fungsi main
if __name__ == "__main__":
    asyncio.run(main())
