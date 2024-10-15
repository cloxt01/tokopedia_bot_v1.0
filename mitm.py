import json
import httpx
import asyncio
import time
import aiofiles
from mitmproxy import http
from datetime import datetime, timezone, timedelta

async def save_headers_to_file(headers_dict: dict, file_path: str):
    # Simpan header dalam format JSON ke file
    async with aiofiles.open(file_path, mode='w') as file:
        json_formatted = json.dumps(headers_dict, indent=4)
        await file.write(json_formatted)
def times():
    utc_now = datetime.now(timezone.utc)
    gmt_plus_7_time = utc_now + timedelta(hours=7)
    return gmt_plus_7_time.strftime('%Y-%m-%d %H:%M:%S')

async def load_data(file):
    async with aiofiles.open(file, 'r') as f:
        data = await f.read()
        return json.loads(data)

async def log_raw(flow):
    raw_filename = "log/log.txt"
    
    # Ambil informasi request
    request_line = f"\n{flow.request.method} {flow.request.path} {flow.request.http_version}\n"
    host = f"Host: {flow.request.host}\n"
    headers = ''.join([f"{k}: {v.replace(',', ';')}\n" if k.lower() == "cookie" else f"{k}: {v}\n"
    for k, v in flow.request.headers.items()])
    body = flow.request.text if flow.request.text else 'No Body'
    
    async with aiofiles.open(raw_filename, 'a') as raw_log_file:
        # Tulis request line (e.g., POST /graphql/one_click_checkout HTTP/2)
        await raw_log_file.write(request_line)
        await raw_log_file.write(host)
        await raw_log_file.write(headers)
        
        if body and body != 'No Body':
            await raw_log_file.write("\n")
            try:
                # Load body as JSON and then pretty print with indentation
                parsed_body = json.loads(body)
                pretty_body = json.dumps(parsed_body, indent=2)
                await raw_log_file.write(pretty_body)
            except json.JSONDecodeError:
                # If it's not valid JSON, write the body as is
                await raw_log_file.write(body)
        else:
            await raw_log_file.write("No Body\n")
        
        await raw_log_file.write("\n")

async def log_response(filename, flow):
    try:
        response_json = json.loads(flow.response.text)
        async with aiofiles.open(filename, 'a') as log_file:
            await log_file.write(json.dumps(response_json, indent=1))
            await log_file.write("\n")
        return True  # Kembali True jika berhasil menyimpan
    except Exception as e:
        print(f"Error saat menyimpan respons: {e}")  # Menampilkan pesan kesalahan
        return False  # Kembali False jika gagal

async def load_cookies_from_file(file):
    try:
        async with aiofiles.open(file, 'r') as f:
            cookies = await f.read()  # Pastikan menggunakan await untuk f.read()
            return cookies.strip()  # Panggil strip() setelah await selesai
    except Exception as e:
        print(f"Error membaca file cookie: {e}")
        return None

time_now = times()
request_counter = 0
cookie_occ = 'cookie/cookie_occ.txt'
file_OCCQuery = 'query/OCCQuery.json'
file_UpdateCartQuery = 'query/UpdateCartQuery.json'
ucom = "https://gql.tokopedia.com/graphql/update_cart_occ_multi"
occ = "https://gql.tokopedia.com/graphql/one_click_checkout"


# Fungsi request handler
async def request(flow: http.HTTPFlow):
    global request_counter
    global cookie_occ
    global file_OCCQuery
    global file_UpdateCartQuery
    global time_now
    global occ,ucom
    try:
        url = flow.request.url
        method = flow.request.method
        
        
        #if (occ in url) and method == "POST":
        #    print(f"[{time_now}] > REQUEST > {method} > {url}")
        

        if flow.request.url == occ and flow.request.method == "POST":
            try:
                time_now = time.strftime("%Y-%m-%d %H:%M:%S")
                headers = flow.request.headers
                formatted_headers = {key: value for key, value in headers.items()}
                file_path = "occ/headers_occ.json"
                await save_headers_to_file(formatted_headers, file_path)
                with open('signal.txt', 'w') as signal_file:
                    signal_file.write('done')
                flow.kill()
            except json.JSONDecodeError:
                print("Error: Tidak dapat mengdecode payload JSON.")
            except Exception as e:
                print(f"Error saat menyimpan headers: {e}")
            await log_raw(flow)
        else:
            flow.resume()
    except KeyboardInterrupt:
        print("Menghentikan...")
# Fungsi response handler
async def response(flow: http.HTTPFlow):
    global request_counter
    global time_now
    global occ,ucom
    try:
        if flow.request.url == ucom and flow.request.method == "POST":
            try:
                filename = f"log/log.txt"
                response_json = json.loads(flow.response.text)
                if request_counter == 2:
                    print(f"RESPONSE > {flow.request.method} > {flow.request.url} > {flow.response.status_code}")
                    print(f"TEXT     > {flow.response.text}")
                    update_cart_data = response_json[0]["data"].get("update_cart_occ_multi", {})
                    status = update_cart_data.get("status", "Unknown Status")
                    
            except json.JSONDecodeError:
                print("Error: Tidak dapat mengdecode respons JSON.")
    except KeyboardInterrupt:
        print("Menghentikan...")