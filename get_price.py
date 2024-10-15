import asyncio
import aiohttp
import aiofiles
import json
import random
import keyboard
import time
import traceback
import sys
import socket
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


async def send_data(writer, data):
    # Mengonversi data ke format JSON dan mengirimnya
    json_data = json.dumps(data).encode('utf-8')
    writer.write(json_data)
    await writer.drain()

async def times():
    utc_now = datetime.now(timezone.utc)

    # Menambahkan 7 jam untuk mendapatkan waktu GMT+7
    gmt_plus_7_time = utc_now + timedelta(hours=7)

    # Menampilkan waktu dalam format yang diinginkan
    formatted_time = gmt_plus_7_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-2]
    return formatted_time

async def wait_for_signal(stop_time_str, target_time_str, lock):
    jakarta_tz = ZoneInfo("Asia/Jakarta")
    start_time = datetime.now(jakarta_tz)
    stop_time = datetime.strptime(stop_time_str, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=jakarta_tz)
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=jakarta_tz)

    # Perf_counter_ns for precise timing in nanoseconds
    start_perf_ns = time.perf_counter_ns()

    while True:
        # Calculate elapsed time in nanoseconds
        elapsed_time_ns = time.perf_counter_ns() - start_perf_ns
        elapsed_time_td = timedelta(microseconds=elapsed_time_ns / 1000)  # Convert to timedelta

        # Calculate the current time using start_time + elapsed nanoseconds
        now_time = start_time + elapsed_time_td

        # Display elapsed time in seconds for easier reading
        elapsed_time_s = elapsed_time_ns / 1_000_000_000

        # Output for monitoring the progress
        async with lock:
            print(f"\rStart: {start_time.strftime('%H:%M:%S.%f')[:-3]} | Now: {now_time.strftime('%H:%M:%S.%f')[:-3]} | Stop: {stop_time.strftime('%H:%M:%S.%f')[:-3]} | Elapsed: {elapsed_time_s:.3f}s | Target: {target_time.strftime('%H:%M:%S.%f')[:-3]}", end='')

        # Compare nanosecond-precision now_time with stop_time
        if now_time >= stop_time:
            async with lock:
                print()  # Move to new line
                print("MULAI!")
            break

        await asyncio.sleep(0.01)

        
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
async def request_price(session, writer, start_price, url, payload, headers, stop_event,stop_signal,stop,target,lock):
    try:
        send_time = await times()
        async with session.post(url, json=payload, headers=headers) as response:
            recv_time = await times()
            #response.raise_for_status()
            response_json = await response.json()

            

            # Ambil harga saat ini
            processing_time = response.headers.get('Gql-Request-Processing-Time', 'N/A')
            price_now = response_json[0]['data']['get_occ_multi']['data']['total_product_price']
            sprice_now = random.randint(10000,100000)
            
            payment_fee_detail = (
                response_json[0]
                .get('data', {})
                .get('get_occ_multi', {})
                .get('data', {})
                .get('profile', {})
                .get('payment', {})
                .get('payment_fee_detail', [])
            )
            
            # Ambil spids
            id = random.randint(1000,9999)
            spids = fspids(response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['shop_shipments'])
            weight = response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['product_weight'] / 1000
            quantity = fquantity(1, response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['product_min_order'])
            ut = response_json[0]['data']['get_occ_multi']['data']['kero_unix_time']

            fee_app = payment_fee_detail[0].get('fee', 0) if len(payment_fee_detail) > 0 else 0
            fee_service = payment_fee_detail[1].get('fee', 0) if len(payment_fee_detail) > 1 else 0
            ut_raw = datetime.fromtimestamp(ut)

            ut_time = ut_raw.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            data_price = {
                "operation": "get_occ_multi",
                "id":id,
                "price_now": price_now,
                "metadata": response_json[0]['data']['get_occ_multi']['data']['profile']['payment'].get('metadata'),
                "gateway_code": response_json[0]['data']['get_occ_multi']['data']['profile']['payment'].get('gateway_code'),
                "is_free_shipping": response_json[0]['data']['get_occ_multi']['data']['profile']['shipment'].get('is_free_shipping_selected', False),
                "warehouse_id": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['warehouse']['warehouse_id'],
                "is_fulfillment": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['warehouse'].get('is_fulfillment', False),
                "product_info": {
                    "cat_id": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['category_id'],
                    "product_min_order": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['product_min_order'],
                    "product_weight": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['product_weight'],
                    "product_insurance": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['cart_details'][0]['products'][0]['product_finsurance'],
                    "product_price": price_now
                },
                "shop_info": {
                    "shop_tier": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['shop_type_info']['shop_tier'],
                    "store_postal_code": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['postal_code'],
                    "store_district_id": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['district_id'],
                    "store_latitude": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['latitude'],
                    "store_longitude": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['longitude']
                },
                "origin": f"{response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['district_id']}|{response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['postal_code']}|{response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['latitude']},{response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shop']['longitude']}",
                "group_metadata": response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['group_metadata'],
                "is_preorder": int(response_json[0]['data']['get_occ_multi']['data']['group_shop_occ'][0]['shipment_information']['preorder']['is_preorder']),
                "fee": {
                    "fee_app": fee_app,
                    "fee_service": fee_service
                },
                "token": response_json[0]['data']['get_occ_multi']['data']['kero_token'],
                "ut": response_json[0]['data']['get_occ_multi']['data']['kero_unix_time'],
                "spids": spids,
                "weight": weight,
                "quantity": quantity
            }

            
            respon = {
                "url": url,
                "id":id,
                "request_time": f"{send_time}",
                "response_time":f"{recv_time}", 
                "server":{
                    "ut_time": ut_time,
                    "ut": ut,
                    "price": price_now,
                    "processing_time": f"{processing_time}ms"
                    }
                }
            #print(json.dumps(respon,indent=2))\
            # and ut_time == target
            if (sprice_now != start_price) and not stop_event.is_set():
                stop_event.set()
                await send_data(writer,data_price)
                print(f" TRUE  > {id} > {send_time} > {ut_time} == {target} > {price_now}",end='')
                
                
            elif (price_now == start_price and ut_time != target) and not stop_event.is_set():
                print(f" FALSE > {id} > {send_time} > {ut_time} != {target} > {price_now}",end='')
            print()
            return respon
            
            
            
    except Exception as e:
        print(f"[{await times()}] Terjadi kesalahan saat membaca info keranjang")
        print(f"[{await times()}] Details :{e}")
        traceback.print_exc()

async def run_tasks_with_timeout(session,writer, start_price, url, payload, headers, stop_event,stop_signal,stop,target,lock):
    await wait_for_signal(stop, target, lock)
    tasks = [request_price(session,writer, start_price, url, payload, headers, stop_event,stop_signal,stop,target,lock) for _ in range(50)]  #
    try:
        results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=8)
        return results
    except asyncio.TimeoutError:
        print(f"\n[{await times()}] Tasks timed out!")
        return None
async def main():
    try:
        server_address = ('localhost', 8811)
        reader, writer = await asyncio.open_connection(*server_address)

        async with aiofiles.open('cookie/cookie.txt', 'r') as cookie_file:
            cookie = await cookie_file.read()
        async with aiofiles.open('address/AddressProfile.json', 'r') as file:
            address_data = await file.read()
            address = json.loads(address_data)
            address_id = address['address_id']
            district_id = address['district_id']
            city_id = address['city_id']
            postal_code = address['postal_code']
            latitude = address['latitude']
            longitude = address['longitude']
            latlon = f"{latitude},{longitude}"
            geolocation = f"{latitude},{longitude}"
            destination = f"{district_id}|{postal_code}|{latitude},{longitude}"

        url = 'https://gql.tokopedia.com/graphql/get_occ_multi'
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
        payload = [
            {"operationName":"get_occ_multi","variables":{"source":"pdp","chosen_address":{"mode":1,"address_id":str(address_id),"district_id":district_id,"postal_code":str(postal_code),"geolocation":str(geolocation)}},"query":"query get_occ_multi($source: String, $chosen_address: ChosenAddressParam) {\n  get_occ_multi(source: $source, chosen_address: $chosen_address) {\n    error_message\n    status\n    data {\n      errors\n      error_code\n      pop_up_message\n      max_char_note\n      kero_token\n      kero_unix_time\n      kero_discom_token\n      error_ticker\n      tickers {\n        id\n        message\n        page\n        title\n        __typename\n      }\n      messages {\n        ErrorFieldBetween\n        ErrorFieldMaxChar\n        ErrorFieldRequired\n        ErrorProductAvailableStock\n        ErrorProductAvailableStockDetail\n        ErrorProductMaxQuantity\n        ErrorProductMinQuantity\n        __typename\n      }\n      occ_main_onboarding {\n        force_show_coachmark\n        show_onboarding_ticker\n        coachmark_type\n        onboarding_ticker {\n          title\n          message\n          image\n          show_coachmark_link_text\n          coachmark_link_text\n          __typename\n        }\n        onboarding_coachmark {\n          skip_button_text\n          detail {\n            step\n            title\n            message\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      group_shop_occ {\n        group_metadata\n        errors\n        errors_unblocking\n        cart_string\n        is_disable_change_courier\n        auto_courier_selection\n        shipment_information {\n          shop_location\n          free_shipping {\n            eligible\n            badge_url\n            __typename\n          }\n          free_shipping_extra {\n            eligible\n            badge_url\n            __typename\n          }\n          preorder {\n            is_preorder\n            duration\n            __typename\n          }\n          __typename\n        }\n        courier_selection_error {\n          title\n          description\n          __typename\n        }\n        bo_metadata {\n          bo_type\n          bo_eligibilities {\n            key\n            value\n            __typename\n          }\n          additional_attributes {\n            key\n            value\n            __typename\n          }\n          __typename\n        }\n        shop {\n          shop_id\n          shop_name\n          shop_alert_message\n          shop_ticker\n          maximum_weight_wording\n          maximum_shipping_weight\n          is_gold\n          is_gold_badge\n          is_official\n          gold_merchant {\n            is_gold\n            is_gold_badge\n            gold_merchant_logo_url\n            __typename\n          }\n          official_store {\n            is_official\n            os_logo_url\n            __typename\n          }\n          shop_type_info {\n            shop_tier\n            shop_grade\n            badge\n            badge_svg\n            title\n            title_fmt\n            __typename\n          }\n          postal_code\n          latitude\n          longitude\n          district_id\n          shop_shipments {\n            ship_id\n            ship_name\n            ship_code\n            ship_logo\n            is_dropship_enabled\n            ship_prods {\n              ship_prod_id\n              ship_prod_name\n              ship_group_name\n              ship_group_id\n              minimum_weight\n              additional_fee\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        cart_details {\n          products {\n            cart_id\n            parent_id\n            product_id\n            product_name\n            product_price\n            product_url\n            category_id\n            category\n            errors\n            wholesale_price {\n              qty_min_fmt\n              qty_max_fmt\n              qty_min\n              qty_max\n              prd_prc\n              prd_prc_fmt\n              __typename\n            }\n            product_weight\n            product_weight_actual\n            product_weight_fmt\n            product_weight_unit_text\n            is_preorder\n            product_cashback\n            product_min_order\n            product_max_order\n            product_invenage_value\n            product_switch_invenage\n            product_image {\n              image_src_200_square\n              __typename\n            }\n            product_notes\n            product_quantity\n            campaign_id\n            product_original_price\n            product_price_original_fmt\n            initial_price\n            initial_price_fmt\n            slash_price_label\n            product_finsurance\n            warehouse_id\n            free_shipping {\n              eligible\n              __typename\n            }\n            free_shipping_extra {\n              eligible\n              __typename\n            }\n            product_preorder {\n              duration_day\n              __typename\n            }\n            product_tracker_data {\n              attribution\n              tracker_list_name\n              __typename\n            }\n            variant_description_detail {\n              variant_name\n              variant_description\n              __typename\n            }\n            product_warning_message\n            product_alert_message\n            product_information\n            purchase_protection_plan_data {\n              protection_available\n              protection_type_id\n              protection_price_per_product\n              protection_price\n              protection_title\n              protection_subtitle\n              protection_link_text\n              protection_link_url\n              protection_opt_in\n              protection_checkbox_disabled\n              tokopedia_protection_price\n              unit\n              protection_price_per_product_fmt\n              protection_price_fmt\n              source\n              protection_config\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        toko_cabang {\n          message\n          badge_url\n          __typename\n        }\n        warehouse {\n          warehouse_id\n          is_fulfillment\n          __typename\n        }\n        __typename\n      }\n      profile {\n        address {\n          address_id\n          receiver_name\n          address_name\n          address_street\n          district_id\n          district_name\n          city_id\n          city_name\n          province_id\n          province_name\n          phone\n          longitude\n          latitude\n          postal_code\n          state\n          state_detail\n          status\n          __typename\n        }\n        payment {\n          enable\n          active\n          gateway_code\n          gateway_name\n          image\n          description\n          minimum_amount\n          maximum_amount\n          wallet_amount\n          metadata\n          mdr\n          credit_card {\n            number_of_cards {\n              available\n              unavailable\n              total\n              __typename\n            }\n            available_terms {\n              term\n              mdr\n              mdr_subsidized\n              min_amount\n              is_selected\n              __typename\n            }\n            bank_code\n            card_type\n            is_expired\n            tnc_info\n            is_afpb\n            unix_timestamp\n            token_id\n            tenor_signature\n            __typename\n          }\n          error_message {\n            message\n            button {\n              text\n              link\n              __typename\n            }\n            __typename\n          }\n          occ_revamp_error_message {\n            message\n            button {\n              text\n              action\n              __typename\n            }\n            __typename\n          }\n          ticker_message\n          is_disable_pay_button\n          is_enable_next_button\n          is_ovo_only_campaign\n          ovo_additional_data {\n            ovo_activation {\n              is_required\n              button_title\n              error_message\n              error_ticker\n              __typename\n            }\n            ovo_top_up {\n              is_required\n              button_title\n              error_message\n              error_ticker\n              is_hide_digital\n              __typename\n            }\n            phone_number_registered {\n              is_required\n              button_title\n              error_message\n              error_ticker\n              __typename\n            }\n            __typename\n          }\n          bid\n          specific_gateway_campaign_only_type\n          wallet_additional_data {\n            wallet_type\n            enable_wallet_amount_validation\n            activation {\n              is_required\n              button_title\n              success_toaster\n              error_toaster\n              error_message\n              is_hide_digital\n              header_title\n              url_link\n              __typename\n            }\n            top_up {\n              is_required\n              button_title\n              success_toaster\n              error_toaster\n              error_message\n              is_hide_digital\n              header_title\n              url_link\n              __typename\n            }\n            phone_number_registered {\n              is_required\n              button_title\n              success_toaster\n              error_toaster\n              error_message\n              is_hide_digital\n              header_title\n              url_link\n              __typename\n            }\n            __typename\n          }\n          payment_fee_detail {\n            fee\n            show_slashed\n            show_tooltip\n            slashed_fee\n            title\n            tooltip_info\n            type\n            __typename\n          }\n          __typename\n        }\n        shipment {\n          service_id\n          service_duration\n          service_name\n          sp_id\n          recommendation_service_id\n          recommendation_sp_id\n          is_free_shipping_selected\n          __typename\n        }\n        __typename\n      }\n      promo {\n        last_apply {\n          code\n          data {\n            global_success\n            success\n            message {\n              state\n              color\n              text\n              __typename\n            }\n            codes\n            promo_code_id\n            title_description\n            discount_amount\n            cashback_wallet_amount\n            cashback_advocate_referral_amount\n            cashback_voucher_description\n            invoice_description\n            is_coupon\n            gateway_id\n            is_tokopedia_gerai\n            clashing_info_detail {\n              clash_message\n              clash_reason\n              is_clashed_promos\n              options {\n                voucher_orders {\n                  cart_id\n                  code\n                  shop_name\n                  potential_benefit\n                  promo_name\n                  unique_id\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            tokopoints_detail {\n              conversion_rate {\n                rate\n                points_coefficient\n                external_currency_coefficient\n                __typename\n              }\n              __typename\n            }\n            voucher_orders {\n              code\n              success\n              cart_id\n              unique_id\n              order_id\n              shop_id\n              is_po\n              duration\n              warehouse_id\n              address_id\n              type\n              cashback_wallet_amount\n              discount_amount\n              title_description\n              invoice_description\n              message {\n                state\n                color\n                text\n                __typename\n              }\n              benefit_details {\n                code\n                type\n                order_id\n                unique_id\n                discount_amount\n                discount_details {\n                  amount\n                  data_type\n                  __typename\n                }\n                cashback_amount\n                cashback_details {\n                  amount_idr\n                  amount_points\n                  benefit_type\n                  __typename\n                }\n                promo_type {\n                  is_exclusive_shipping\n                  is_bebas_ongkir\n                  __typename\n                }\n                benefit_product_details {\n                  product_id\n                  cashback_amount\n                  cashback_amount_idr\n                  discount_amount\n                  is_bebas_ongkir\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            benefit_summary_info {\n              final_benefit_text\n              final_benefit_amount\n              final_benefit_amount_str\n              summaries {\n                section_name\n                section_description\n                description\n                type\n                amount_str\n                amount\n                details {\n                  section_name\n                  description\n                  type\n                  amount_str\n                  amount\n                  points\n                  points_str\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            tracking_details {\n              product_id\n              promo_codes_tracking\n              promo_details_tracking\n              __typename\n            }\n            ticker_info {\n              unique_id\n              status_code\n              message\n              __typename\n            }\n            additional_info {\n              message_info {\n                message\n                detail\n                __typename\n              }\n              error_detail {\n                message\n                __typename\n              }\n              empty_cart_info {\n                image_url\n                message\n                detail\n                __typename\n              }\n              usage_summaries {\n                description\n                type\n                amount_str\n                amount\n                currency_details_str\n                __typename\n              }\n              sp_ids\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        error_default {\n          title\n          description\n          __typename\n        }\n        __typename\n      }\n      image_upload {\n        show_image_upload\n        text\n        left_icon_url\n        right_icon_url\n        checkout_id\n        front_end_validation\n        lite_url\n        __typename\n      }\n      customer_data {\n        id\n        name\n        email\n        msisdn\n        __typename\n      }\n      payment_additional_data {\n        merchant_code\n        profile_code\n        signature\n        change_cc_link\n        callback_url\n        __typename\n      }\n      prompt {\n        type\n        title\n        description\n        image_url\n        buttons {\n          text\n          link\n          action\n          color\n          __typename\n        }\n        __typename\n      }\n      total_product_price\n      placeholder_note\n      __typename\n    }\n    __typename\n  }\n}\n"}
            ]

        connector = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=connector) as session:
        
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                response_json = await response.json()
                start_price = response_json[0]['data']['get_occ_multi']['data']['total_product_price']
                print(f"Harga saat ini : {start_price}")
                if start_price == 0:
                    print(f"[{await times()}] Keranjang kosong nih, Tambahkan produk dulu ya")
                    return
            
                stop_event = asyncio.Event()
                stop_signal = asyncio.Event()
                lock = asyncio.Lock()

                now = datetime.now(timezone.utc)
                gmt_plus_7_time = now + timedelta(hours=7)
                date = gmt_plus_7_time.strftime('%Y-%m-%d')
                mnt = gmt_plus_7_time.minute
                hour = gmt_plus_7_time.hour
                target_mnt = mnt + 1
                if target_mnt == 60:
                    hour += 1
                    target_mnt = 0
                #target = f"{date} {hour:02}:{target_mnt:02}:00.000"
                #stop = f"{date} {hour:02}:{mnt:02}:56.230"
                target = "2024-10-15 17:00:00.000"
                stop   = "2024-10-15 16:59:56.000"
                
                await run_tasks_with_timeout(session,writer, start_price, url, payload, headers, stop_event,stop_signal,stop,target,lock)
    except OSError as e:
        print(f"[{await times()}] Jalankan 'main.py' terlebih dahulu yaa")
        print(f"[{await times()}] Details : {e}")
        return
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\nSelesai")

    