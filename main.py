import requests
import json
import cProfile
import pstats
import time
import pytz
import os
import sys
import traceback
import random
import brotli
import subprocess
import socket
import webbrowser
import asyncio,aiohttp,aiofiles, httpx

from urllib.parse import unquote
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright
from playwright._impl._errors import TargetClosedError, Error as PlaywrightError
from zoneinfo import ZoneInfo


get_occ_multi = None
one_click_checkout = None
headers_occ = None
global_writer = None

def fquantity(quantity,min):
    if min != quantity:
        return min
    else:
        return quantity 
def fspids(shop_shipments):
    ship_ids = []
    for shipment in shop_shipments:
        for product in shipment['ship_prods']:
            ship_ids.append(product['ship_prod_id'])
    spids = ','.join(map(str, ship_ids))
    return spids
def times():
    utc_now = datetime.now(timezone.utc)
    gmt_plus_7_time = utc_now + timedelta(hours=7)
    return gmt_plus_7_time.strftime('%Y-%m-%d %H:%M:%S') + f".{gmt_plus_7_time.microsecond // 1000:03d}"
async def write_query(data_occ, payload):
    async with aiofiles.open('query/OCCQuery.json', 'w') as json_file:
        await json_file.write(json.dumps(data_occ, indent=1))
    async with aiofiles.open('query/UpdateCartQuery.json', 'w') as json_file:
        await json_file.write(json.dumps(payload, indent=1))
async def load_cookies_occ(file):
    try:
        async with aiofiles.open(file, 'r') as f:
            cookies = await f.read()
            return cookies.strip()
    except Exception as e:
        print(f"Error membaca file '{file}': {e}")
        return None
async def wait_for_signal(f):
    while True:
        if os.path.exists(f):
            if os.path.getsize(f) > 0:
                print(f"\r[{times()}] INFO    > Signal ditemukan '{f}'",end='\n')
                break
            print(f"\r[{times()}] INFO    > Menunggu signal dari '{f}' ",end='')
async def signal_reset():
    async with aiofiles.open('signal.txt', 'w') as signal_file:
        await signal_file.write('')
async def price_reset():
    async with aiofiles.open('occ/total_product_price.txt', 'w') as f:
        await f.write('')
async def handle_client(reader, writer):
    global global_writer
    global get_occ_multi, one_click_checkout
    global_writer = writer
    
    while True:
        data = await reader.read(800)
        if not data:
            break
        
        try:
            # Dekompresi data yang diterima
            decompressed_data = brotli.decompress(data)
            # Mengonversi data yang didekompresi menjadi string
            message = decompressed_data.decode('utf-8')
            
            # Mengonversi string JSON menjadi objek Python
            json_message = json.loads(message)
            
            if "id" in json_message:
                get_occ_multi = json_message
                print(f"[{times()}] INFO    > {get_occ_multi}")
                print(f"[{times()}] INFO    > Data 'get_occ_multi' ditemukan")
                break
            elif "one_click_checkout" in json_message:
                one_click_checkout = json_message
                print(f"[{times()}] INFO    > Data 'one_click_checkout' ditemukan")
        
        except brotli.error as e:
            print(f"Error saat mendekompresi data: {e}")
            traceback.print_exc()

        except json.JSONDecodeError as e:
            print(f"Error saat mengonversi data ke JSON: {e}")
async def pilih_user_data_dir(base_dir="/home/ferdi_cloxt00/Profiles"):
    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
    if not folders:
        print("Tidak ada folder yang ditemukan di direktori.")
        return None
    print("Profiles List :")
    for idx, folder in enumerate(folders):
        print(f"{idx + 1}. {folder}")
    while True:
        try:
            choice = int(await asyncio.to_thread(input, f"Pilih profile : ")) - 1
            if 0 <= choice < len(folders):
                selected_folder = folders[choice]
                break
            else:
                print("[{times()}] ERROR > Nomor yang dipilih tidak valid. Silakan pilih lagi.")
        except ValueError:
            print(f"[{times()}] ERROR > Input harus berupa angka. Silakan coba lagi.")
    user_data_dir = os.path.join(base_dir, selected_folder)
    print(f"[{times()}] INFO    > {user_data_dir}")
    return user_data_dir

async def run_server():
    host = 'localhost'
    port = 8811
    server = await asyncio.start_server(handle_client, host, port)
    print(f"[{times()}] INFO    > Server berjalan di {host}:{port}")
    return server
async def request_occ(client,url, payload, headers):
    try:
        async with aiofiles.open('log/log.txt', 'a') as f:
            await f.write(f"POST {url} HTTP/2\n")
            for key, value in headers.items():
                await f.write(f"{key}: {value}\n")
            await f.write("\n")
            await f.write(json.dumps(payload, indent=2))
            await f.write("\n")
        timeout = httpx.Timeout(1, read=1)
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        try:
            response_json = response.json()
        except ValueError:
            response_json = {"error": "Response is not JSON"}
        response_time = response.headers.get('Gql-Request-Processing-Time', 'N/A')
        print(f"[{times()}] INFO    > {url} >> {response_time}ms")
        return response_json
    except httpx.HTTPStatusError as e:
        print(f"Request error: {str(e)}")
    except asyncio.TimeoutError:
        print(f"Request timed out: {timeout}")
    except Exception as e:
        if isinstance(e, httpx.ReadTimeout):
            pass
async def post_request(session, url, payload, cookie):
    try:
        headers = {
            'Host': 'gql.tokopedia.com',
            'Cookie': cookie,
            'X-Version': 'bd78eaf',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip',
            'X-Source': 'tokopedia-lite',
            'X-Device': 'default_v3',
            'X-Tkpd-Lite-Service': 'atreus',
            'Origin': 'https://www.tokopedia.com',
            'Referer': 'https://www.tokopedia.com',
            'Priority': 'u=1'
        }
        async with session.post(url, json=payload, headers=headers) as response:
            response.raise_for_status()
            response_json = await response.json()
        return response
    except aiohttp.ClientError as e:
        print(f"Request error: {str(e)}")
    except asyncio.TimeoutError:
        print("Request timed out")
    except Exception as e:
        print(f"Unhandled exception: {str(e)}")
async def handle_response(response):
    if "update_cart_occ_multi" in response.url:
        if response is None:
            print(f"[{times()}] ERROR > Terjadi kesalahan, jalankan 'get_product.py' dan coba lagi yaa")
            raise SystemExit()
        try:
            response_json = await response.json()
            if (not response_json or 
                'data' not in response_json[0] or 
                'update_cart_occ_multi' not in response_json[0]['data']):
                print(f"[{times()}] ERROR > Terjadi kesalahan, jalankan 'get_product.py' dan coba lagi yaa")
                raise SystemExit()
            status = response_json[0]['data']['update_cart_occ_multi']['status']
            if status != "OK":
                print(f"[{times()}] ERROR > Terjadi kesalahan, jalankan 'get_product.py' dan coba lagi yaa")
                raise SystemExit()
        except Exception as e:
            print(f"[{times()}] ERROR > Terjadi kesalahan, coba beberapa saat lagi yaa")
            print(f"[{times()}] ERROR > Details: {e}")
            raise SystemExit()
async def handle_request(route, request):
    global headers_occ
    if "one_click_checkout" in request.url and "POST" in request.method:
        headers_occ = request.headers
        if headers_occ:
            print(f"[{times()}] INFO    > Sample 'one_click_checkout' disimpan")
        await route.abort()
    else:
        await route.continue_()
async def setup(page,user_data_dir):
    try:
        cookies = await page.context.cookies(["https://www.tokopedia.com"])  # Pastikan URL lengkap
        tokopedia_cookies = [cookie for cookie in cookies if 'tokopedia.com' in cookie['domain']]
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in tokopedia_cookies])
        async with aiofiles.open(f'{user_data_dir}/cookie.txt', 'w') as cookie_file:
            await cookie_file.write(cookie_string)
        async with aiofiles.open(f'{user_data_dir}/AddressProfile.json', 'r') as file:
            address_data = await file.read()
            address = json.loads(address_data)
        async with aiofiles.open(f'{user_data_dir}/cart_details.json', 'r') as file:
            cart_data = await file.read()
            cart = json.loads(cart_data)

        # Reset sinyal
        await signal_reset()

        # Mengembalikan hasil dalam dictionary
        return {"cookies": cookie_string, "address": address, "cart": cart}
    
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
async def button_validation(ua):
    if "Android" in ua:
        # Jika User-Agent mengandung 'Android', cek tombol btn_pay
        button = 'button[data-testid="btn_pay"]'
    elif "Windows" in ua:
        # Jika User-Agent mengandung 'Windows', cek tombol occBtnPayment
        button = 'button[data-testid="occBtnPayment"]'
    else:
        print(f"User-Agent tidak dikenali: {ua}")
        button = None
    return button
async def selector_validation(ua):
    if 'Windows' in ua:
        element = '//html/body/div[1]/div/div[2]/div/div/div[2]/p/p'
    elif 'Android' in ua:
        element = '//html/body/div[1]/div/div/div/div[2]/div[1]/div/p/p'
    else:
        print(f"Elemen tidak ditemukan")
    return element
async def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0
async def check_ssh_continuous(port, delay=1):
    while True:
        if await is_port_in_use(port):
            print(f"\r[{times()}] INFO    > SSH siap di port {port}")
            return True
        else:
            print(f"\r[{times()}] INFO    > Menunggu SSH di port {port}...")
            await asyncio.sleep(delay)
async def ssh_setup(user, port, password="12345"):
    if not await is_port_in_use(port):
        print(f"[{times()}] WARNING > SSH tidak terdeteksi, menginstal sshpass...")
        install_command = ["sudo", "apt", "install", "-y", "sshpass"]
        with open(os.devnull, 'w') as devnull:
            install_process = subprocess.Popen(install_command, stdout=devnull, stderr=devnull)
            install_process.wait()
        print(f"[{times()}] INFO    > Menjalankan perintah SSH...")
        ssh_command = [
            "sshpass", "-p", password,
            "ssh", "-D", f"{port}", "-f", "-C", "-q", 
            user, "-p", "22", "-N"
        ]
        subprocess.Popen(ssh_command)
        ssh_ready = await check_ssh_continuous(port)
        if ssh_ready:
            print(f"[{times()}] INFO    > Koneksi SSH sudah siap!")
        else:
            print(f"[{times()}] ERROR > Koneksi SSH gagal disiapkan.")
    else:
        print(f"[{times()}] INFO    > SSH sudah terdeteksi di port {port}")
async def close_connection():
    global global_writer
    if global_writer:
        global_writer.close()
        await global_writer.wait_closed()
        print(f"[{times()}] INFO    > Koneksi ditutup.")
async def wait_for_signal(stop_time_str, target_time_str, lock):
    jakarta_tz = ZoneInfo("Asia/Jakarta")
    start_time = datetime.now(jakarta_tz)
    stop_time = datetime.strptime(stop_time_str, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=jakarta_tz)
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=jakarta_tz)

    start_perf_ns = time.perf_counter_ns()
    input("Enter untuk Mulai")

    while True:
        # Calculate elapsed time in nanoseconds
        elapsed_time_ns = time.perf_counter_ns() - start_perf_ns
        elapsed_time_td = timedelta(microseconds=elapsed_time_ns / 1000)
        now_time = start_time + elapsed_time_td
        elapsed_time_s = elapsed_time_ns / 1_000_000_000
        async with lock:
            print(f"\rStart: {start_time.strftime('%H:%M:%S.%f')[:-3]} | Now: {now_time.strftime('%H:%M:%S.%f')[:-3]} | Stop: {stop_time.strftime('%H:%M:%S.%f')[:-3]} | Elapsed: {elapsed_time_s:.3f}s | Target: {target_time.strftime('%H:%M:%S.%f')[:-3]}", end='')
        if now_time >= stop_time:
            async with lock:
                print()  # Move to new line
            break

        await asyncio.sleep(0.01)   
async def request_price(session, start_price, url, payload, headers, stop_event,stop_signal,stop,target,lock,tasks):
    global j, k, get_occ_multi, get_occ_multi_event
    try:
        send_time = times()
        async with session.post(url, json=payload, headers=headers) as response:
            recv_time = times()
            response_json = await response.json()
            sprice_now = random.randint(10000,100000)
            price_now = response_json[0]['data']['get_occ_multi']['data']['total_product_price']
            ut = response_json[0]['data']['get_occ_multi']['data']['kero_unix_time']
            ut_raw = datetime.fromtimestamp(ut)

            ut_time = ut_raw.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            #if (price_now != start_price) and not stop_event.is_set():
            if j == 12 and k == 0 and not stop_event.is_set() and not get_occ_multi_event.is_set():
                get_occ_multi = response_json
                get_occ_multi_event.set()
                stop_event.set()
                print(f"{j:03} > TRUE  > {send_time} > {ut_time} == {target} > {price_now}",end='\n')
                raise asyncio.CancelledError
            elif price_now == start_price and not stop_event.is_set():
                print(f"{j:03} > FALSE > {send_time} > {ut_time} != {target} > {price_now}",end='\n')
            j+=1
    except (IndexError, KeyError):
        print(f"{j:03} > NONE > {id} > {send_time}",end='\n')
        j+=1
        return  
    except Exception as e:
        print(f"[{times()}] Terjadi kesalahan saat membaca info keranjang")
        print(f"[{times()}] Details :{e}")
        detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
        if detail == 'y' or detail == 'Y':
            traceback.print_exc()
        return
async def run_tasks_with_timeout(session, start_price, url, payload, headers, stop_event, stop_signal, stop, target, lock):
    await wait_for_signal(stop, target, lock)
    global k
    k = 0
    while True:
        global j
        j = 0
        tasks = []
        tasks_len = 100
        for _ in range(tasks_len):
            task = asyncio.create_task(request_price(session, start_price, url, payload, headers, stop_event, stop_signal, stop, target, lock, tasks))
            tasks.append(task)or _ in range(tasks_len) 
        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=6)
        except asyncio.CancelledError as e:
            print(f"\n[{times()}] Tugas dihentikan.")
            for task in tasks:
                task.cancel()
            break
        except asyncio.TimeoutError as e:
            print(f"\n[{times()}] Waktu habis")
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            break
        k += 1
def important_note():
    # Menambahkan catatan penting dengan warna dan format bold
    print(f"PENTING !!!")
    print(f"1. Pastikan koneksi internet stabil")
    print(f"2. Pertama, ambil cookie dengan memasukan perintah 'python get_cookie.py'")
    print(f"3. Setelah itu, ambil product dengan memasukan perintah 'python get_product.py'")
    print(f"4. Lalu, perbarui cookie 'one_click_checkout' dengan memasukan perintah 'python get_cookies_occ.py'")
    print(f"5. Terakhir, jalankan 'python main.py' untuk memulai")
    print()
async def post_all(page,client,session,server,user_data_dir):
    try: 
        global occ
        global get_occ_multi, get_occ_multi_event, headers_occ

        query = await setup(page,user_data_dir)
        address = query['address']
        cart =  query['cart']
        cookies =  query['cookies']
        
        address_id = address['address_id']
        district_id = address['district_id']
        city_id = address['city_id']
        postal_code = address['postal_code']
        latitude = address['latitude']
        longitude = address['longitude']
        latlon = f"{latitude},{longitude}"
        geolocation = f"{latitude},{longitude}"
        destination = f"{district_id}|{postal_code}|{latitude},{longitude}"
        cart_id = cart['cart_id']
        notes = cart['notes']
        product_id = cart['product_id']
        quantity = cart['quantity']
        shop_id = cart['shop_id']
        warehouse_id = cart['warehouse_id']

        operation = 0
        product_price = 0
        metadata = 0
        gateway_code = 0
        is_free_shipping = 0
        warehouse_id = 0
        is_fulfillment = 0
        cat_id = 0
        product_min_order = 0
        product_weight = 0
        product_insurance = 0
        product_price = 0
        shop_tier = 0
        store_postal_code = 0
        store_district_id = 0
        store_latitude = 0
        store_longitude = 0
        origin = 0
        group_metadata = 0
        is_preorder = 0
        fee_app = 0
        fee_service = 0
        token = 0
        ut = 0
        spids = 0
        weight = 0
        quantity = 0
        
        service_id = 0
        service_name = 0
        rates_id = 0
        ship_id = 0
        ship_name= 0
        checksum = 0
        sp_id = 0
        ongkir = 0
        ship_insurance = 0
        paymentAmount = 0
        slashed_fee = 0
        total_amount = 0

        start_task = time.time()
        post_time = 0.0
        processing_time = 0.0
        urls = [
                'https://gql.tokopedia.com/graphql/get_occ_multi',
                'https://gql.tokopedia.com/graphql/RatesV3Query',
                'https://gql.tokopedia.com/graphql/getPaymentFee',
                'https://gql.tokopedia.com/graphql/update_cart_occ_multi'
                ]
        for i in range(len(urls)):
            payloads = [
                [{"operationName":"get_occ_multi","variables":{"source":"pdp","chosen_address":{"mode":1,"address_id":str(address_id),"district_id":district_id,"postal_code":str(postal_code),"geolocation":str(geolocation)}},"query":"query get_occ_multi($source: String, $chosen_address: ChosenAddressParam) {\n  get_occ_multi(source: $source, chosen_address: $chosen_address) {\n    error_message\n    status\n    data {\n      errors\n      error_code\n      pop_up_message\n      max_char_note\n      kero_token\n      kero_unix_time\n      kero_discom_token\n      error_ticker\n      tickers {\n        id\n        message\n        page\n        title\n        __typename\n      }\n      messages {\n        ErrorFieldBetween\n        ErrorFieldMaxChar\n        ErrorFieldRequired\n        ErrorProductAvailableStock\n        ErrorProductAvailableStockDetail\n        ErrorProductMaxQuantity\n        ErrorProductMinQuantity\n        __typename\n      }\n      occ_main_onboarding {\n        force_show_coachmark\n        show_onboarding_ticker\n        coachmark_type\n        onboarding_ticker {\n          title\n          message\n          image\n          show_coachmark_link_text\n          coachmark_link_text\n          __typename\n        }\n        onboarding_coachmark {\n          skip_button_text\n          detail {\n            step\n            title\n            message\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      group_shop_occ {\n        group_metadata\n        errors\n        errors_unblocking\n        cart_string\n        is_disable_change_courier\n        auto_courier_selection\n        shipment_information {\n          shop_location\n          free_shipping {\n            eligible\n            badge_url\n            __typename\n          }\n          free_shipping_extra {\n            eligible\n            badge_url\n            __typename\n          }\n          preorder {\n            is_preorder\n            duration\n            __typename\n          }\n          __typename\n        }\n        courier_selection_error {\n          title\n          description\n          __typename\n        }\n        bo_metadata {\n          bo_type\n          bo_eligibilities {\n            key\n            value\n            __typename\n          }\n          additional_attributes {\n            key\n            value\n            __typename\n          }\n          __typename\n        }\n        shop {\n          shop_id\n          shop_name\n          shop_alert_message\n          shop_ticker\n          maximum_weight_wording\n          maximum_shipping_weight\n          is_gold\n          is_gold_badge\n          is_official\n          gold_merchant {\n            is_gold\n            is_gold_badge\n            gold_merchant_logo_url\n            __typename\n          }\n          official_store {\n            is_official\n            os_logo_url\n            __typename\n          }\n          shop_type_info {\n            shop_tier\n            shop_grade\n            badge\n            badge_svg\n            title\n            title_fmt\n            __typename\n          }\n          postal_code\n          latitude\n          longitude\n          district_id\n          shop_shipments {\n            ship_id\n            ship_name\n            ship_code\n            ship_logo\n            is_dropship_enabled\n            ship_prods {\n              ship_prod_id\n              ship_prod_name\n              ship_group_name\n              ship_group_id\n              minimum_weight\n              additional_fee\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        cart_details {\n          products {\n            cart_id\n            parent_id\n            product_id\n            product_name\n            product_price\n            product_url\n            category_id\n            category\n            errors\n            wholesale_price {\n              qty_min_fmt\n              qty_max_fmt\n              qty_min\n              qty_max\n              prd_prc\n              prd_prc_fmt\n              __typename\n            }\n            product_weight\n            product_weight_actual\n            product_weight_fmt\n            product_weight_unit_text\n            is_preorder\n            product_cashback\n            product_min_order\n            product_max_order\n            product_invenage_value\n            product_switch_invenage\n            product_image {\n              image_src_200_square\n              __typename\n            }\n            product_notes\n            product_quantity\n            campaign_id\n            product_original_price\n            product_price_original_fmt\n            initial_price\n            initial_price_fmt\n            slash_price_label\n            product_finsurance\n            warehouse_id\n            free_shipping {\n              eligible\n              __typename\n            }\n            free_shipping_extra {\n              eligible\n              __typename\n            }\n            product_preorder {\n              duration_day\n              __typename\n            }\n            product_tracker_data {\n              attribution\n              tracker_list_name\n              __typename\n            }\n            variant_description_detail {\n              variant_name\n              variant_description\n              __typename\n            }\n            product_warning_message\n            product_alert_message\n            product_information\n            purchase_protection_plan_data {\n              protection_available\n              protection_type_id\n              protection_price_per_product\n              protection_price\n              protection_title\n              protection_subtitle\n              protection_link_text\n              protection_link_url\n              protection_opt_in\n              protection_checkbox_disabled\n              tokopedia_protection_price\n              unit\n              protection_price_per_product_fmt\n              protection_price_fmt\n              source\n              protection_config\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        toko_cabang {\n          message\n          badge_url\n          __typename\n        }\n        warehouse {\n          warehouse_id\n          is_fulfillment\n          __typename\n        }\n        __typename\n      }\n      profile {\n        address {\n          address_id\n          receiver_name\n          address_name\n          address_street\n          district_id\n          district_name\n          city_id\n          city_name\n          province_id\n          province_name\n          phone\n          longitude\n          latitude\n          postal_code\n          state\n          state_detail\n          status\n          __typename\n        }\n        payment {\n          enable\n          active\n          gateway_code\n          gateway_name\n          image\n          description\n          minimum_amount\n          maximum_amount\n          wallet_amount\n          metadata\n          mdr\n          credit_card {\n            number_of_cards {\n              available\n              unavailable\n              total\n              __typename\n            }\n            available_terms {\n              term\n              mdr\n              mdr_subsidized\n              min_amount\n              is_selected\n              __typename\n            }\n            bank_code\n            card_type\n            is_expired\n            tnc_info\n            is_afpb\n            unix_timestamp\n            token_id\n            tenor_signature\n            __typename\n          }\n          error_message {\n            message\n            button {\n              text\n              link\n              __typename\n            }\n            __typename\n          }\n          occ_revamp_error_message {\n            message\n            button {\n              text\n              action\n              __typename\n            }\n            __typename\n          }\n          ticker_message\n          is_disable_pay_button\n          is_enable_next_button\n          is_ovo_only_campaign\n          ovo_additional_data {\n            ovo_activation {\n              is_required\n              button_title\n              error_message\n              error_ticker\n              __typename\n            }\n            ovo_top_up {\n              is_required\n              button_title\n              error_message\n              error_ticker\n              is_hide_digital\n              __typename\n            }\n            phone_number_registered {\n              is_required\n              button_title\n              error_message\n              error_ticker\n              __typename\n            }\n            __typename\n          }\n          bid\n          specific_gateway_campaign_only_type\n          wallet_additional_data {\n            wallet_type\n            enable_wallet_amount_validation\n            activation {\n              is_required\n              button_title\n              success_toaster\n              error_toaster\n              error_message\n              is_hide_digital\n              header_title\n              url_link\n              __typename\n            }\n            top_up {\n              is_required\n              button_title\n              success_toaster\n              error_toaster\n              error_message\n              is_hide_digital\n              header_title\n              url_link\n              __typename\n            }\n            phone_number_registered {\n              is_required\n              button_title\n              success_toaster\n              error_toaster\n              error_message\n              is_hide_digital\n              header_title\n              url_link\n              __typename\n            }\n            __typename\n          }\n          payment_fee_detail {\n            fee\n            show_slashed\n            show_tooltip\n            slashed_fee\n            title\n            tooltip_info\n            type\n            __typename\n          }\n          __typename\n        }\n        shipment {\n          service_id\n          service_duration\n          service_name\n          sp_id\n          recommendation_service_id\n          recommendation_sp_id\n          is_free_shipping_selected\n          __typename\n        }\n        __typename\n      }\n      promo {\n        last_apply {\n          code\n          data {\n            global_success\n            success\n            message {\n              state\n              color\n              text\n              __typename\n            }\n            codes\n            promo_code_id\n            title_description\n            discount_amount\n            cashback_wallet_amount\n            cashback_advocate_referral_amount\n            cashback_voucher_description\n            invoice_description\n            is_coupon\n            gateway_id\n            is_tokopedia_gerai\n            clashing_info_detail {\n              clash_message\n              clash_reason\n              is_clashed_promos\n              options {\n                voucher_orders {\n                  cart_id\n                  code\n                  shop_name\n                  potential_benefit\n                  promo_name\n                  unique_id\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            tokopoints_detail {\n              conversion_rate {\n                rate\n                points_coefficient\n                external_currency_coefficient\n                __typename\n              }\n              __typename\n            }\n            voucher_orders {\n              code\n              success\n              cart_id\n              unique_id\n              order_id\n              shop_id\n              is_po\n              duration\n              warehouse_id\n              address_id\n              type\n              cashback_wallet_amount\n              discount_amount\n              title_description\n              invoice_description\n              message {\n                state\n                color\n                text\n                __typename\n              }\n              benefit_details {\n                code\n                type\n                order_id\n                unique_id\n                discount_amount\n                discount_details {\n                  amount\n                  data_type\n                  __typename\n                }\n                cashback_amount\n                cashback_details {\n                  amount_idr\n                  amount_points\n                  benefit_type\n                  __typename\n                }\n                promo_type {\n                  is_exclusive_shipping\n                  is_bebas_ongkir\n                  __typename\n                }\n                benefit_product_details {\n                  product_id\n                  cashback_amount\n                  cashback_amount_idr\n                  discount_amount\n                  is_bebas_ongkir\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            benefit_summary_info {\n              final_benefit_text\n              final_benefit_amount\n              final_benefit_amount_str\n              summaries {\n                section_name\n                section_description\n                description\n                type\n                amount_str\n                amount\n                details {\n                  section_name\n                  description\n                  type\n                  amount_str\n                  amount\n                  points\n                  points_str\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            tracking_details {\n              product_id\n              promo_codes_tracking\n              promo_details_tracking\n              __typename\n            }\n            ticker_info {\n              unique_id\n              status_code\n              message\n              __typename\n            }\n            additional_info {\n              message_info {\n                message\n                detail\n                __typename\n              }\n              error_detail {\n                message\n                __typename\n              }\n              empty_cart_info {\n                image_url\n                message\n                detail\n                __typename\n              }\n              usage_summaries {\n                description\n                type\n                amount_str\n                amount\n                currency_details_str\n                __typename\n              }\n              sp_ids\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        error_default {\n          title\n          description\n          __typename\n        }\n        __typename\n      }\n      image_upload {\n        show_image_upload\n        text\n        left_icon_url\n        right_icon_url\n        checkout_id\n        front_end_validation\n        lite_url\n        __typename\n      }\n      customer_data {\n        id\n        name\n        email\n        msisdn\n        __typename\n      }\n      payment_additional_data {\n        merchant_code\n        profile_code\n        signature\n        change_cc_link\n        callback_url\n        __typename\n      }\n      prompt {\n        type\n        title\n        description\n        image_url\n        buttons {\n          text\n          link\n          action\n          color\n          __typename\n        }\n        __typename\n      }\n      total_product_price\n      placeholder_note\n      __typename\n    }\n    __typename\n  }\n}\n"}],
                [{"operationName":"RatesV3Query","variables":{"input":{"address_id":f"{address_id}","cat_id":f"{cat_id}","destination":f"{destination}","from":"client","insurance":f"{product_insurance}","is_blackbox":0,"lang":"id","occ":"1","order_value":f"{product_price}","origin":f"{origin}","pdp":"0","preorder":is_preorder,"product_insurance":f"{product_insurance}","products":json.dumps([{"product_id": product_id, "is_free_shipping":is_free_shipping}]),"psl_code":"","shop_id":f"{shop_id}","spids":f"{spids}","token":f"{token}","type":"default_v3","user_history":-1,"ut":f"{ut}","vehicle_leasing":0,"weight":f"{weight}","actual_weight":f"{weight}","is_fulfillment":is_fulfillment,"po_time":0,"shop_tier":shop_tier,"warehouse_id":f"{warehouse_id}","group_metadata":group_metadata},"metadata":{}},"query":"query RatesV3Query($input: OngkirRatesV3Input!, $metadata: Metadata) {\n  ratesV3(input: $input, metadata: $metadata) {\n    ratesv3 {\n      id\n      rates_id\n      type\n      services {\n        service_name\n        service_id\n        service_order\n        status\n        range_price {\n          min_price\n          max_price\n          __typename\n        }\n        etd {\n          min_etd\n          max_etd\n          __typename\n        }\n        texts {\n          text_range_price\n          text_etd\n          text_notes\n          text_service_notes\n          text_price\n          text_service_desc\n          text_eta_summarize\n          text_service_ticker\n          error_code\n          __typename\n        }\n        products {\n          shipper_name\n          shipper_id\n          shipper_product_id\n          shipper_product_name\n          shipper_product_desc\n          shipper_weight\n          promo_code\n          is_show_map\n          status\n          recommend\n          checksum\n          ut\n          ui_rates_hidden\n          price {\n            price\n            formatted_price\n            __typename\n          }\n          eta {\n            text_eta\n            error_code\n            __typename\n          }\n          etd {\n            min_etd\n            max_etd\n            __typename\n          }\n          texts {\n            text_range_price\n            text_etd\n            text_notes\n            text_service_notes\n            text_price\n            text_service_desc\n            __typename\n          }\n          insurance {\n            insurance_price\n            insurance_type\n            insurance_type_info\n            insurance_used_type\n            insurance_used_info\n            insurance_used_default\n            insurance_actual_price\n            insurance_pay_type\n            __typename\n          }\n          error {\n            error_id\n            error_message\n            __typename\n          }\n          cod {\n            is_cod_available\n            cod_text\n            cod_price\n            formatted_price\n            __typename\n          }\n          features {\n            ontime_delivery_guarantee {\n              available\n              value\n              text_label\n              text_detail\n              icon_url\n              url_detail\n              __typename\n            }\n            dynamic_price {\n              text_label\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        error {\n          error_id\n          error_message\n          __typename\n        }\n        is_promo\n        cod {\n          is_cod\n          cod_text\n          __typename\n        }\n        order_priority {\n          is_now\n          price\n          formatted_price\n          inactive_message\n          available_label\n          static_messages {\n            duration_message\n            checkbox_message\n            warningbox_message\n            fee_message\n            pdp_message\n            __typename\n          }\n          __typename\n        }\n        features {\n          dynamic_price {\n            text_label\n            __typename\n          }\n          __typename\n        }\n        ui_rates_hidden\n        selected_shipper_product_id\n        __typename\n      }\n      recommendations {\n        service_name\n        shipping_id\n        shipping_product_id\n        price {\n          price\n          formatted_price\n          __typename\n        }\n        etd {\n          min_etd\n          max_etd\n          __typename\n        }\n        texts {\n          text_range_price\n          text_etd\n          text_notes\n          text_service_notes\n          text_price\n          text_service_desc\n          __typename\n        }\n        insurance {\n          insurance_price\n          insurance_type\n          insurance_type_info\n          insurance_used_type\n          insurance_used_info\n          insurance_used_default\n          insurance_actual_price\n          insurance_pay_type\n          __typename\n        }\n        error {\n          error_id\n          error_message\n          __typename\n        }\n        __typename\n      }\n      info {\n        cod_info {\n          failed_message\n          __typename\n        }\n        blackbox_info {\n          text_info\n          __typename\n        }\n        __typename\n      }\n      promo_stacking {\n        is_promo\n        promo_code\n        title\n        shipper_id\n        shipper_product_id\n        shipper_name\n        shipper_desc\n        promo_detail\n        benefit_desc\n        point_change\n        user_point\n        promo_tnc_html\n        shipper_disable_text\n        service_id\n        __typename\n      }\n      error {\n        error_id\n        error_message\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"}],
                [{"operationName":"getPaymentFee","variables":{"gatewayCode":gateway_code,"profileCode":"TKPD_DEFAULT","paymentAmount":paymentAmount},"query":"query getPaymentFee($profileCode: String!, $gatewayCode: String!, $paymentAmount: Float!) {\n  getPaymentFee(profileCode: $profileCode, gatewayCode: $gatewayCode, paymentAmount: $paymentAmount) {\n    success\n    errors {\n      code\n      message\n      __typename\n    }\n    data {\n      code\n      title\n      fee\n      tooltip_info\n      show_tooltip\n      show_slashed\n      slashed_fee\n      __typename\n    }\n    __typename\n  }\n}\n"}],            
                [{"operationName":"update_cart_occ_multi","variables":{"param":{"cart":[{"cart_id":cart_id,"quantity":quantity,"notes":notes,"product_id":product_id}],"profile":{"address_id":f"{address_id}","gateway_code":f"{gateway_code}","metadata":f"{metadata}","service_id":service_id,"shipping_id":ship_id,"sp_id":sp_id,"is_free_shipping_selected":is_free_shipping},"skip_shipping_validation":False,"source":"","chosen_address":{"mode":1,"address_id":f"{address_id}","district_id":district_id,"postal_code":f"{postal_code}","geolocation":f"{geolocation}"}}},"query":"mutation update_cart_occ_multi($param: OneClickCheckoutMultiUpdateCartParam) {\n  update_cart_occ_multi(param: $param) {\n    error_message\n    status\n    data {\n      messages\n      success\n      prompt {\n        type\n        title\n        description\n        image_url\n        buttons {\n          text\n          link\n          action\n          color\n          __typename\n        }\n        __typename\n      }\n      toaster_action {\n        text\n        show_cta\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"}]
                ]        
            start = time.time()
            response = await post_request(session,urls[i], payloads[i],cookies)
            elapsed = time.time() - start
            response_json = await response.json()
            response_time = response.headers.get('Gql-Request-Processing-Time', 'N/A')
            print(f"[{times()}] INFO    > {urls[i]} >> {response_time}ms")
            


            processing_time += float(response_time)
            post_time += elapsed
            if i == 0:
                print(f"GOM : {get_occ_multi}")
                product_name = response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['product_name']
                start_price = response_json[0]['data']['get_occ_multi']['data']['total_product_price']
                print(f"[{times()}] Product Name > {product_name}")
                print(f"[{times()}] Price        > {start_price}")
                if start_price == 0:
                    print(f"[{times()}] Keranjang kosong nih, Tambahkan produk dulu ya")
                    return False

                stop_event = asyncio.Event()
                get_occ_multi_event = asyncio.Event()
                stop_signal = asyncio.Event()
                lock = asyncio.Lock()

                headers_gom = {
                    'Host': 'gql.tokopedia.com',
                    'Cookie': cookies,
                    'X-Version': 'bd78eaf',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36',
                    'Content-Type': 'application/json',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip',
                    'X-Source': 'tokopedia-lite',
                    'X-Device': 'default_v3',
                    'X-Tkpd-Lite-Service': 'atreus',
                    'Origin': 'https://www.tokopedia.com',
                    'Referer': 'https://www.tokopedia.com',
                    'Priority': 'u=1'
                    }


                now = datetime.now(timezone.utc)
                gmt_plus_7_time = now + timedelta(hours=7)
                date = gmt_plus_7_time.strftime('%Y-%m-%d')
                mnt = gmt_plus_7_time.minute
                hour = gmt_plus_7_time.hour
                target_mnt = mnt + 1
                if target_mnt == 60:
                    hour += 1
                    target_mnt = 0
                
                DT = False
                print(f"[{times()}] WARNING > DynamicTime > {DT}")
                if DT is True:
                    target = f"{date} {hour:02}:{target_mnt:02}:00.000"
                    stop = f"{date} {hour:02}:{mnt:02}:55.000"
                    next = input(f"[{ times()}] WARNING > Lanjutkan ([y/n]) : ")
                    if next == 'Y' or next == 'y':
                        print(f"[{times()}] WARNING > Pastikan Waktunya sesuai yaa")
                    elif next != 'N' or next != 'n':
                        return
                    else:
                        print(f"[{times()}] ERROR > Input gak sesuai nih")
                else:
                    target = "2024-10-19 12:00:00.000"
                    stop   = "2024-10-19 11:59:55.000"
                print(f"[{times()}] INFO > TargetTime : {target}")
                print(f"[{times()}] INFO > StopTime   : {stop}")
                #await run_tasks_with_timeout(session, start_price, urls[i], payloads[i], headers_gom, stop_event,stop_signal,stop,target,lock)
                
                task = asyncio.create_task(run_tasks_with_timeout(session, start_price, urls[i], payloads[i], headers_gom, stop_event, stop_signal, stop, target, lock))
                print(f"[{times()}] Menunggu get_occ_multi...")
                await get_occ_multi_event.wait()
                end_wait_time = datetime.now()
                print(f"[{times()}] Event selesai, waktu: {end_wait_time.strftime('%H:%M:%S.%f')[:-3]}")

                #[2024-10-18 00:40:56.008] INFO    > https://gql.tokopedia.com/graphql/RatesV3Query >> 84.07ms

                payment_fee_detail = (
                    response_json[0]
                    .get('data', {})
                    .get('get_occ_multi', {})
                    .get('data', {})
                    .get('profile', {})
                    .get('payment', {})
                    .get('payment_fee_detail', [])
                    )
                product_price = get_occ_multi[0]['data']['get_occ_multi']['data']['total_product_price']
                metadata = get_occ_multi[0]['data']['get_occ_multi']['data']['profile']['payment'].get('metadata')
                gateway_code = get_occ_multi[0]['data']['get_occ_multi']['data']['profile']['payment'].get('gateway_code')
                is_free_shipping = get_occ_multi[0]['data']['get_occ_multi']['data']['profile']['shipment'].get('is_free_shipping_selected', False)
                warehouse_id = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['warehouse']['warehouse_id']
                is_fulfillment = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['warehouse'].get('is_fulfillment', False)
                cat_id = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['category_id']
                product_min_order = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['product_min_order']
                product_weight = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['product_weight']
                product_insurance = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['product_finsurance']
                shop_tier = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['shop_type_info']['shop_tier']
                store_postal_code = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['postal_code']
                store_district_id = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['district_id']
                store_latitude = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['latitude']
                store_longitude = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['longitude']
                origin = f"{store_district_id}|{store_postal_code}|{store_latitude},{store_longitude}"
                group_metadata = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['group_metadata']
                is_preorder = int(get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shipment_information']['preorder']['is_preorder'])
                fee_app = payment_fee_detail[0].get('fee', 0) if len(payment_fee_detail) > 0 else 0
                fee_service = payment_fee_detail[1].get('fee', 0) if len(payment_fee_detail) > 1 else 0
                token = get_occ_multi[0]['data']['get_occ_multi']['data']['kero_token']
                ut = get_occ_multi[0]['data']['get_occ_multi']['data']['kero_unix_time']
                spids = fspids(get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['shop_shipments'])
                weight = get_occ_multi[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['product_weight'] / 1000
                quantity = fquantity(1, product_min_order)


                
            elif i == 1:
                #print(json.dumps(response_json,indent=2))
                l = 0
                for services in response_json[0]['data']['ratesV3']['ratesv3']['services']:
                    if services['service_id'] == 1004:
                        break
                    l += 1
                service_id = response_json[0]['data']['ratesV3']['ratesv3']['services'][l]['service_id']
                service_name = response_json[0]['data']['ratesV3']['ratesv3']['services'][l]['service_name']
                rates_id = response_json[0]['data']['ratesV3']['ratesv3']['rates_id']
                ship_id = response_json[0]['data']['ratesV3']['ratesv3']['services'][l]['products'][0]['shipper_id']
                ship_name= response_json[0]['data']['ratesV3']['ratesv3']['services'][l]['products'][0]['shipper_name']
                checksum = response_json[0]['data']['ratesV3']['ratesv3']['services'][l]['products'][0]['checksum']
                sp_id = response_json[0]['data']['ratesV3']['ratesv3']['services'][l]['products'][0]['shipper_product_id']
                ongkir = response_json[0]['data']['ratesV3']['ratesv3']['services'][l]['products'][0]['price']['price']
                ship_insurance = response_json[0]['data']['ratesV3']['ratesv3']['services'][l]['products'][0]['insurance']['insurance_price']
                paymentAmount = product_price + ongkir + ship_insurance    
            elif i == 2:
                slashed_fee = response_json[0]['data']['getPaymentFee']['data'][0]['slashed_fee']
                total_amount = (ship_insurance + product_price + ongkir + fee_service + fee_app) - slashed_fee
            elif i == 3:
                status = response_json[0]['data']['update_cart_occ_multi']['status']
                if status == "OK" and occ == True:
                    url_occ = 'https://gql.tokopedia.com/graphql/one_click_checkout'
                    file_cookies_occ = f'{user_data_dir}/cookies_occ.txt'
                    cookies_occ =  await load_cookies_occ(file_cookies_occ)
                    payload_occ = [{"operationName":"one_click_checkout","variables":{"params":{"profile":{"profile_id":0},"carts":{"promos":[],"data":[{"address_id":address_id,"shop_products":[{"promos":[],"shop_id":shop_id,"product_data":[{"product_id":product_id,"product_quantity":quantity,"product_notes":"","is_ppp":False}],"warehouse_id":warehouse_id,"is_preorder":is_preorder,"finsurance":product_insurance,"shipping_info":{"shipping_id":ship_id,"sp_id":sp_id,"rates_id":rates_id,"ut":f"{ut}","checksum":checksum},"order_metadata":[]}]}],"mode":0,"feature_type":1}}},"query":"mutation one_click_checkout($params: oneClickCheckoutParams) {\n  one_click_checkout(params: $params) {\n    header {\n      process_time\n      reason\n      error_code\n      messages\n      __typename\n    }\n    data {\n      success\n      error {\n        code\n        image_url\n        message\n        __typename\n      }\n      payment_parameter {\n        callback_url\n        payload\n        redirect_param {\n          url\n          gateway\n          method\n          form\n          form_json\n          is_redirect\n          form_object {\n            product_list {\n              id\n              price\n              quantity\n              name\n              __typename\n            }\n            parameter {\n              merchant_code\n              profile_code\n              customer_id\n              customer_name\n              customer_email\n              customer_msisdn\n              transaction_id\n              transaction_date\n              gateway_code\n              pid\n              bid\n              nid\n              user_defined_value\n              amount\n              currency\n              language\n              signature\n              device_info {\n                device_name\n                device_version\n                __typename\n              }\n              payment_metadata\n              merchant_type\n              back_url\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      prompt {\n        type\n        title\n        description\n        image_url\n        buttons {\n          text\n          link\n          color\n          action\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    status\n    __typename\n  }\n}\n"}]
                    headers_occ['host'] = 'gql.tokopedia.com'
                    headers_occ['content-length'] = str(len(json.dumps(payload_occ)))
                    headers_occ['cookie'] = cookies_occ
                    async def checkout_request():
                        return await request_occ(client, url_occ, payload_occ, headers_occ)
                    success = False
                    while success is False:
                        tasks = [checkout_request() for _ in range(10)]
                        results = await asyncio.gather(*tasks)
                        for i, checkout in enumerate(results):
                            i += 1 
                            if checkout == None:
                                print(f"[{times()}] INFO    > Checkout {i}: N/A")
                            #elif checkout and checkout[0]['data']['one_click_checkout']['data']['success'] != 1:
                                #print(f"[{times()}] INFO    > Checkout {i}: {checkout}")
                            elif checkout and checkout[0]['data']['one_click_checkout']['data']['success'] == 1:
                                print(f"[{times()}] INFO    > Checkout {i} berhasil. Keluar dari program.")
                                print(f"[{times()}] INFO    > Checkout {i}: {checkout}")
                                
                                try:
                                    redirect_param = checkout[0]['data']['one_click_checkout']['data']['payment_parameter']['redirect_param']
                                    url = redirect_param['url']
                                    form = redirect_param['form']
                                except KeyError as e:
                                    print(f"Key Error : {e}")


                                url_raw = (f"{(url)}?{form}")
                                url_redirect = unquote(url_raw)
                                headers = {
                                    "Host": "pay.tokopedia.com",
                                    "Cookie": cookies,
                                    "Content-Length": "0",
                                    "Content-Type": "application/x-www-form-urlencoded",
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                                "(KHTML, like Gecko) Chrome/129.0.6668.71 Safari/537.36",
                                    "Referer": "https://www.tokopedia.com/beli-langsung",
                                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
                                            "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                                }

                                with httpx.Client(timeout=None) as client:
                                    response = client.post(url_redirect, headers=headers)
                                    
                                if response.status_code == 200 or response.status_code in [301, 302]:
                                    redirect_url = response.headers.get("Location")
                                    print(f"Redirect URL: {redirect_url}")
                                else:
                                    print(f"Error: Received status code {response.status_code}")
                                success = True
                                break
                elif status != "OK":
                    print(json.dumps(response_json))
                    print(f"[{times()}] ERROR > Ada yang salah nih, perbarui keranjang dan coba lagi yaa")
                    return False  
                
                elapsed_task = time.time() - start_task
                delay = float(post_time - (processing_time/1000))
                result = {
                    "gateway_code": gateway_code,
                    "total_amount": total_amount,
                    "price" : product_price,
                    "delay" : round(delay,2),
                    "server" : round(processing_time,2),
                    "response" : round(post_time,2),
                    "total": round(elapsed_task,2)
                }     
                server.close()
                await server.wait_closed()

                return True
 
    except Exception as e:
        print(f"[{times()}] ERROR > Ada yang salah nih, coba beberapa saat lagi yaa")
        print(f"[{times()}] ERROR > Details : {e}")
        detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
        if detail == 'y' or detail == 'Y':
            traceback.print_exc()
        return False  
async def main():
    important_note()
    global occ
    occ = True
    if occ is False:
        print(f"[{times()}] WARNING > occ > {occ}")
        next = input(f"[{times()}] WARNING > Lanjutkan ([y/n]) : ")
        if (next != 'Y' and next != 'y') and (next != 'N' and next != 'n'):
            print(f"[{times()}] ERROR > Input salah")
            raise KeyboardInterrupt
        elif next != 'y' and next != 'Y':
            raise asyncio.CancelledError

    ua_list = {
        "android": "Mozilla/5.0 (Linux; Android 10; M2006C3MG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36 ABB/3.4.5",
        "windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"
        }
    currentUA = 'android'
    ua = ua_list.get(currentUA)
    user_data_dir = await pilih_user_data_dir()
    user_ssh = "sshocean-cloxt11@id5.ssh0.net"
    port_ssh = 1080
    await ssh_setup(user_ssh,port_ssh)
    proxy = {"server":f"socks5://127.0.0.1:{str(port_ssh)}"}
    async with async_playwright() as p:
        browser = await p.firefox.launch_persistent_context(
            ignore_https_errors = True,
            user_agent = ua,
            user_data_dir = user_data_dir,
            headless = True,
            proxy = proxy
        )
        try:
            page = browser.pages[0]
            await page.route("**/*", handle_request)
            page.on("response", handle_response)
            print(f"[{times()}] INFO    > Meluncur ke halaman")
            url = "https://www.tokopedia.com/beli-langsung"
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)
            
            title = await page.title()
            if 'Login' in title:
                print(f"[{times()}] WARNING > Sesi berakhir nih, silahkan login lagi yaa")
                raise asyncio.CancelledError
            try:
                element_selector = await selector_validation(ua)
                await page.wait_for_selector(element_selector, timeout=3000)
                element = await page.locator(element_selector).text_content()
                if element:
                    print(f"[{times()}] WARNING > {element}")
                    raise KeyboardInterrupt
            except Exception:
                button = await button_validation(ua)
                await page.wait_for_selector(button, timeout=60000)

                print(f"[{times()}] INFO    > Tombol berhasil ditemukan")
                is_enabled = await page.evaluate(f"() => document.querySelector('{button}').disabled === false")

                if is_enabled:
                    try:
                        await page.click(button)
                        print(f"[{times()}] INFO    > Tombol berhasil diklik")

                        while headers_occ is None:
                            await asyncio.sleep(0)

                        print(f"[{times()}] INFO    > Sample 'one_click_checkout' disimpan")
                    except Exception as e:
                        print(f"[{times()}] ERROR > Coba cek tombolnya deh, kayaknya ada yang gak beres")
                        print(f"[{times()}] ERROR > Details : {e}")
                        detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
                        if detail == 'y' or detail == 'Y':
                            traceback.print_exc()
                        raise asyncio.CancelledError
                        return
                else:
                    print(f"[{times()}] ERROR > Ada yang salah nih, tidak bisa diklik.")
                    print(f"[{times()}] ERROR > Periksa koneksi internet atauperbarui keranjang dan coba lagi yaa")
                    
                    
                    raise asyncio.CancelledError
                async with aiohttp.ClientSession() as session:
                    async with httpx.AsyncClient() as client:
                        server = await run_server()
                        server_task = asyncio.create_task(server.serve_forever())

                        try:
                            result = await asyncio.gather(
                                post_all(page, client, session, server,user_data_dir),
                                return_exceptions=True
                            )
                        except Exception as e:
                            print(f"[{times()}] ERROR    > Terjadi kesalahan saat menjalankan task: {e}")
                        finally:
                            server_task.cancel()
                            try:
                                await server_task
                            except asyncio.CancelledError:
                                print(f"[{times()}] INFO    > Server task dibatalkan dengan sukses.")

                        if all(res is True for res in result):
                            print(f"[{times()}] INFO    > Program selesai tanpa kesalahan.")
                        elif any(res is False for res in result):
                            print(f"[{times()}] WARNING > Program selesai dengan kesalahan")
                        else:
                            print(f"[{times()}] ERROR   > Terjadi kesalahan pada sisi return requests")

        except FileNotFoundError:
            print(f"[{times()}] ERROR > Filenya gak keliatan nih, pastikan file sudah benar yaa ")
            print(f"[{times()}] ERROR > Details : {e}")
            detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
            if detail == 'y' or detail == 'Y':
                traceback.print_exc()
            raise KeyboardInterrupt
        except PlaywrightError as e:
            print(f"[{times()}] ERROR > Terjadi kesalahan di sisi playwright, coba beberapa saat lagi yaa")
            print(f"[{times()}] ERROR > Details : {e}")
            detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
            if detail == 'y' or detail == 'Y':
                traceback.print_exc()
            raise KeyboardInterrupt
        except asyncio.exceptions.InvalidStateError:
            print(f"[{times()}] ERROR > Terjadi kesalahan di sisi asyncio, coba beberapa saat lagi yaa")
            print(f"[{times()}] ERROR > Details : {e}")
            detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
            if detail == 'y' or detail == 'Y':
                traceback.print_exc()
            raise asyncio.CancelledError
        except Exception as e:
            print(f"[{times()}] ERROR > Ada yang salah nih, coba beberapa saat lagi yaa")
            #print(f"[{times()}] ERROR > Details : {e}")
            #detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
            #if detail == 'y' or detail == 'Y':
            #    traceback.print_exc()
            raise ValueError
        finally:
            try:
                await close_connection()
                await browser.close()
            except TargetClosedError:
                print(f"[{times()}] ERROR > Browser sudah ditutup sebelumnya, mengabaikan error ini.")
            except PlaywrightError as e:
                print(f"[{times()}] ERROR > Terjadi kesalahan saat menutup browser")
                print(f"[{times()}] ERROR > Details : {e}")
                detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
                if detail == 'y' or detail == 'Y':
                    traceback.print_exc()
                raise KeyboardInterrupt
if __name__ == "__main__":
    try:
        profiler = cProfile.Profile()
        profiler.enable()
        asyncio.run(main())
        print(f"[{times()}] Sukses")
        profiler.disable()
        with open('profiling_results.txt', 'w') as f:
            stats = pstats.Stats(profiler, stream=f)
            stats.strip_dirs()
            stats.sort_stats('cumulative')
            stats.print_stats('main.py')
    except asyncio.CancelledError as e:
        print(f"[{times()}] INFO    > Tugas dibatalkan.")
        print(f"[{times()}] ERROR > Details : {e}")
        detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
        if detail == 'y' or detail == 'Y':
            traceback.print_exc()
    except KeyboardInterrupt:
        print(f"[{times()}] INFO    > Program dihentikan")
    except ValueError as e:
        print(f"[{times()}] ERROR > Ada yang salah nih, coba beberapa saat lagi yaa")
        print(f"[{times()}] ERROR > Details : {e}")
        detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
        if detail == 'y' or detail == 'Y':
            traceback.print_exc()