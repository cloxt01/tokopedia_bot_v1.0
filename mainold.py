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
        print(f"[{times()}] INFO    > {response.status_code} >> POST {url} >> {response_time}ms")
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
async def setup(page):
    try:
        # Mengambil cookie dari domain Tokopedia
        cookies = await page.context.cookies(["https://www.tokopedia.com"])  # Pastikan URL lengkap
        tokopedia_cookies = [cookie for cookie in cookies if 'tokopedia.com' in cookie['domain']]
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in tokopedia_cookies])

        # Menyimpan cookie ke file
        async with aiofiles.open('cookie/cookie.txt', 'w') as cookie_file:
            await cookie_file.write(cookie_string)

        # Membaca data address dari file
        async with aiofiles.open('address/AddressProfile.json', 'r') as file:
            address_data = await file.read()
            address = json.loads(address_data)  # Memastikan data diubah menjadi dict

        # Membaca data cart dari file
        async with aiofiles.open('cart/cart_details.json', 'r') as file:
            cart_data = await file.read()
            cart = json.loads(cart_data)  # Memastikan data diubah menjadi dict

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
        
        # Instal sshpass
        install_command = ["sudo", "apt", "install", "-y", "sshpass"]
        install_process = subprocess.Popen(install_command)
        install_process.wait()  # Tunggu hingga instalasi selesai
        
        # Jalankan perintah SSH
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
    global j, k, get_occ_multi
    try:
        send_time = await times()
        async with session.post(url, json=payload, headers=headers) as response:
            recv_time = await times()
            response_json = await response.json()

            processing_time = response.headers.get('Gql-Request-Processing-Time', 'N/A')
            price_now = response_json[0]['data']['get_occ_multi']['data']['total_product_price']
            sprice_now = random.randint(10000,100000)
            ut = response_json[0]['data']['get_occ_multi']['data']['kero_unix_time']
            ut_raw = datetime.fromtimestamp(ut)
            ut_time = ut_raw.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            #if (sprice_now != start_price) and not stop_event.is_set():
            if j == 12 and k == 0:
                get_occ_multi = response_json
                print(f"{j:03} > TRUE  > {id} > {send_time} > {ut_time} == {target} > {price_now}",end='\n')
                raise asyncio.CancelledError
            elif (price_now == start_price) and not stop_event.is_set():
                print(f"{j:03} > FALSE > {id} > {send_time} > {ut_time} != {target} > {price_now}",end='\n')
            j+=1
    except (IndexError, KeyError):
        print(f"{j:03} > NONE > {id} > {send_time}",end='\n')
        j+=1
        return  
    except Exception as e:
        print(f"[{await times()}] Terjadi kesalahan saat membaca info keranjang")
        print(f"[{await times()}] Details :{e}")
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
            task = asyncio.create_task(request_price(session, writer, start_price, url, payload, headers, stop_event, stop_signal, stop, target, lock, tasks))
            tasks.append(task)or _ in range(tasks_len) 
        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=6)
        except asyncio.CancelledError as e:
            print(f"\n[{await times()}] Tugas dihentikan.")
            break
        except asyncio.TimeoutError as e:
            print(f"\n[{await times()}] Waktu habis")
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            break
        k += 1


async def post_all(page,client,session,server):
    try: 
        global occ
        global get_occ_multi, one_click_checkout, headers_occ

        query = await setup(page)
        address = query['address']
        cart =  query['cart']
        cookies =  query['cookies']

        print(f"[{times()}] INFO    > Menunggu sinyal dari 'get_price.py'")
        while get_occ_multi is None:
            await asyncio.sleep(0)
        
        get =get_occ_multi
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
        metadata = get['metadata']
        group_metadata = get['group_metadata']
        gateway_code = get['gateway_code']
        is_free_shipping = get['is_free_shipping']
        warehouse_id = get['warehouse_id']
        is_fulfillment = get['is_fulfillment']
        product_info = get['product_info']
        cat_id = product_info['cat_id']
        product_min_order = product_info['product_min_order']
        product_weight = product_info['product_weight']
        product_insurance = product_info['product_insurance']
        product_price = product_info['product_price']
        shop_info = get['shop_info']
        shop_tier = shop_info['shop_tier']
        store_postal_code = shop_info['store_postal_code']
        store_district_id = shop_info['store_district_id']
        store_latitude = shop_info['store_latitude']
        store_longitude = shop_info['store_longitude']

        fee_app = get['fee']['fee_app']
        fee_service = get['fee']['fee_service']

        origin = get['origin']
        group_metadata = get['group_metadata']
        is_preorder = get['is_preorder']
        token = get['token']
        ut = get['ut']
        spids = get['spids']
        weight = get['weight']
        quantity = get['quantity']

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
                'https://gql.tokopedia.com/graphql/RatesV3Query',
                'https://gql.tokopedia.com/graphql/getPaymentFee',
                'https://gql.tokopedia.com/graphql/update_cart_occ_multi'
                ]
        for i in range(len(urls)):
            payloads = [
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
            elif i == 1:
                slashed_fee = response_json[0]['data']['getPaymentFee']['data'][0]['slashed_fee']
                total_amount = (ship_insurance + product_price + ongkir + fee_service + fee_app) - slashed_fee
            elif i == 2:
                status = response_json[0]['data']['update_cart_occ_multi']['status']
                if status == "OK" and occ == True:
                    url_occ = 'https://gql.tokopedia.com/graphql/one_click_checkout'
                    file_cookies_occ = 'occ/cookies_occ.txt'
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
                            elif checkout and checkout[0]['data']['one_click_checkout']['data']['success'] != 1:
                                print(f"[{times()}] INFO    > Checkout {i}: {checkout}")
                            elif checkout and checkout[0]['data']['one_click_checkout']['data']['success'] == 1:
                                print(f"[{times()}] INFO    > Checkout {i} berhasil. Keluar dari program.")
                                
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

                                with httpx.Client() as client:
                                    response = client.post(url_redirect, headers=headers)
                                    redirect_url = response.headers.get("Location")

                                print(f"Redirect URL : {redirect_url}")
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
    global occ
    occ = True
    if occ is False:
        print(f"[{times()}] WARNING > occ > {occ}")
        next = input(f"[{times()}] WARNING > Lanjutkan ([y/n]) : ")
        if (next != 'Y' and next != 'y') and (next != 'N' and next != 'n'):
            print(f"[{times()}] ERROR > Input salah")
            raise asyncio.CancelledError
        elif next != 'y' and next != 'Y':
            raise asyncio.CancelledError
    ua_list = {
        "android": "Mozilla/5.0 (Linux; Android 10; M2006C3MG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36 ABB/3.4.5",
        "windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"
    }
    currentUA = 'android'
    ua = ua_list.get(currentUA)
    user_data_dir = r"/home/ferdi_cloxt00/wwd3mtg7.Greatness"
    user_ssh = "cloxt00@idx2vpn.jagoanssh.com"
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
            url = "https://www.tokopedia.com/beli-langsung"
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)
            print(f"[{times()}] INFO    > Meluncur ke halaman")
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
                    raise asyncio.CancelledError
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
                    print(f"[{times()}] ERROR > Tombol tidak aktif, tidak bisa diklik.")
                    raise asyncio.CancelledError
                async with aiohttp.ClientSession() as session:
                    async with httpx.AsyncClient() as client:
                        server = await run_server()
                        server_task = asyncio.create_task(server.serve_forever())

                        try:
                            result = await asyncio.gather(
                                post_all(page, client, session, server),
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
                            print(f"[{times()}] INFO     > Program selesai tanpa kesalahan.")
                        elif any(res is False for res in result):
                            print(f"[{times()}] WARNING  > Program selesai dengan kesalahan")
                        else:
                            print(f"[{times()}] ERROR    > Terjadi kesalahan pada sisi return requests")

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
            print(f"[{times()}] ERROR > Details : {e}")
            detail = input(f"[{times()}] ERROR > Tampilkan lebih detail (y/N) : ")
            if detail == 'y' or detail == 'Y':
                traceback.print_exc()
            raise ValueError
        finally:
            try:
                await close_connection()
                await browser.close()
            except TargetClosedError:
                print(f"Browser sudah ditutup sebelumnya, mengabaikan error ini.")
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