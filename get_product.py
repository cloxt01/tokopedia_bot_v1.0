import requests
import re
import json
import time
import sys
import os
from datetime import datetime, timezone, timedelta

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
def format_url(url):
    try:
        # Menggunakan re.search untuk menemukan pola yang cocok
        pattern = r'tokopedia\.com/([^/]+)/([^/?]+)'
        match = re.search(pattern, url)

        # Jika match ditemukan, ambil shop domain dan product key
        if match:
            shop_domain = match.group(1)
            product_key = match.group(2)
            return {"shop_domain" : shop_domain,"product_key": product_key}
        else:
            raise ValueError("URL tidak sesuai format yang diharapkan")
    except Exception as e:
        print(f'Terjadi kesalahan: {e}')

def times():
    utc_now = datetime.now(timezone.utc)

    # Menambahkan 7 jam untuk mendapatkan waktu GMT+7
    gmt_plus_7_time = utc_now + timedelta(hours=7)

    # Menampilkan waktu dalam format yang diinginkan
    return gmt_plus_7_time.strftime('%Y-%m-%d %H:%M:%S')

def main():
    user_data_dir = pilih_user_data_dir()
    with open(f'{user_data_dir}/AddressProfile.json', 'r') as file:
        address_data = file.read()
        address = json.loads(address_data)
    address_id = str(address['address_id'])
    district_id = address['district_id']
    city_id = str(address['city_id'])
    postal_code = str(address['postal_code'])
    latitude = str(address['latitude'])
    longitude = str(address['longitude'])
    geolocation = f"{latitude},{longitude}"
    destination = f"{district_id}|{postal_code}|{latitude},{longitude}"

    url = input("Masukan URL Produk: ")
    try:
        with open(f'{user_data_dir}/cookie.txt', 'r') as cookie:
            cookies = cookie.read()
        url_content = format_url(url)
        product_key = url_content['product_key']
        shop_domain = url_content['shop_domain']
        print(product_key, shop_domain)
    except Exception as e:
        print(f"Terjadi kesalahan saat memparsing url: {e}")
    
    try:
        url = [
            'https://gql.tokopedia.com/graphql/PDPGetLayoutQuery',
            'https://gql.tokopedia.com/graphql/PDPGetDataP2',
            'https://gql.tokopedia.com/graphql/AddToCartOCCMulti'
        ]
        xtkpdakamai = [
                'pdpGetLayout',
                'pdpGetData',
                'atcoccmulti'
        ]
        
        #DEKLARASI
        product_id = ''
        pdpSession = ''
        shop_id = ''
        warehouse_id = ''

        for i in range(len(url)):
            payload = [
            [{"operationName":"PDPGetLayoutQuery","variables":{"shopDomain":shop_domain,"productKey":product_key,"layoutID":"","apiVersion":1,"tokonow":{"shopID":"0","whID":"0","serviceType":"ooc"},"deviceID":"","userLocation":{"cityID":city_id,"addressID":address_id,"districtID":str(district_id),"postalCode":postal_code,"latlon":geolocation},"extParam":""},"query":"fragment ProductVariant on pdpDataProductVariant {\n  errorCode\n  parentID\n  defaultChild\n  sizeChart\n  totalStockFmt\n  variants {\n    productVariantID\n    variantID\n    name\n    identifier\n    option {\n      picture {\n        urlOriginal: url\n        urlThumbnail: url100\n        __typename\n      }\n      productVariantOptionID\n      variantUnitValueID\n      value\n      hex\n      stock\n      __typename\n    }\n    __typename\n  }\n  children {\n    productID\n    price\n    priceFmt\n    slashPriceFmt\n    discPercentage\n    optionID\n    optionName\n    productName\n    productURL\n    picture {\n      urlOriginal: url\n      urlThumbnail: url100\n      __typename\n    }\n    stock {\n      stock\n      isBuyable\n      stockWordingHTML\n      minimumOrder\n      maximumOrder\n      __typename\n    }\n    isCOD\n    isWishlist\n    campaignInfo {\n      campaignID\n      campaignType\n      campaignTypeName\n      campaignIdentifier\n      background\n      discountPercentage\n      originalPrice\n      discountPrice\n      stock\n      stockSoldPercentage\n      startDate\n      endDate\n      endDateUnix\n      appLinks\n      isAppsOnly\n      isActive\n      hideGimmick\n      isCheckImei\n      minOrder\n      __typename\n    }\n    thematicCampaign {\n      additionalInfo\n      background\n      campaignName\n      icon\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ProductMedia on pdpDataProductMedia {\n  media {\n    type\n    urlOriginal: URLOriginal\n    urlThumbnail: URLThumbnail\n    urlMaxRes: URLMaxRes\n    videoUrl: videoURLAndroid\n    prefix\n    suffix\n    description\n    variantOptionID\n    __typename\n  }\n  videos {\n    source\n    url\n    __typename\n  }\n  __typename\n}\n\nfragment ProductCategoryCarousel on pdpDataCategoryCarousel {\n  linkText\n  titleCarousel\n  applink\n  list {\n    categoryID\n    icon\n    title\n    isApplink\n    applink\n    __typename\n  }\n  __typename\n}\n\nfragment ProductHighlight on pdpDataProductContent {\n  name\n  price {\n    value\n    currency\n    priceFmt\n    slashPriceFmt\n    discPercentage\n    __typename\n  }\n  campaign {\n    campaignID\n    campaignType\n    campaignTypeName\n    campaignIdentifier\n    background\n    percentageAmount\n    originalPrice\n    discountedPrice\n    originalStock\n    stock\n    stockSoldPercentage\n    threshold\n    startDate\n    endDate\n    endDateUnix\n    appLinks\n    isAppsOnly\n    isActive\n    hideGimmick\n    __typename\n  }\n  thematicCampaign {\n    additionalInfo\n    background\n    campaignName\n    icon\n    __typename\n  }\n  stock {\n    useStock\n    value\n    stockWording\n    __typename\n  }\n  variant {\n    isVariant\n    parentID\n    __typename\n  }\n  wholesale {\n    minQty\n    price {\n      value\n      currency\n      __typename\n    }\n    __typename\n  }\n  isCashback {\n    percentage\n    __typename\n  }\n  isTradeIn\n  isOS\n  isPowerMerchant\n  isWishlist\n  isCOD\n  preorder {\n    duration\n    timeUnit\n    isActive\n    preorderInDays\n    __typename\n  }\n  __typename\n}\n\nfragment ProductCustomInfo on pdpDataCustomInfo {\n  icon\n  title\n  isApplink\n  applink\n  separator\n  description\n  __typename\n}\n\nfragment ProductInfo on pdpDataProductInfo {\n  row\n  content {\n    title\n    subtitle\n    applink\n    __typename\n  }\n  __typename\n}\n\nfragment ProductDetail on pdpDataProductDetail {\n  content {\n    title\n    subtitle\n    applink\n    showAtFront\n    isAnnotation\n    __typename\n  }\n  __typename\n}\n\nfragment ProductDataInfo on pdpDataInfo {\n  icon\n  title\n  isApplink\n  applink\n  content {\n    icon\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment ProductSocial on pdpDataSocialProof {\n  row\n  content {\n    icon\n    title\n    subtitle\n    applink\n    type\n    rating\n    __typename\n  }\n  __typename\n}\n\nfragment ProductDetailMediaComponent on pdpDataProductDetailMediaComponent {\n  title\n  description\n  contentMedia {\n    url\n    ratio\n    type\n    __typename\n  }\n  show\n  ctaText\n  __typename\n}\n\nquery PDPGetLayoutQuery($shopDomain: String, $productKey: String, $layoutID: String, $apiVersion: Float, $userLocation: pdpUserLocation, $extParam: String, $tokonow: pdpTokoNow, $deviceID: String) {\n  pdpGetLayout(shopDomain: $shopDomain, productKey: $productKey, layoutID: $layoutID, apiVersion: $apiVersion, userLocation: $userLocation, extParam: $extParam, tokonow: $tokonow, deviceID: $deviceID) {\n    requestID\n    name\n    pdpSession\n    basicInfo {\n      alias\n      createdAt\n      isQA\n      id: productID\n      shopID\n      shopName\n      minOrder\n      maxOrder\n      weight\n      weightUnit\n      condition\n      status\n      url\n      needPrescription\n      catalogID\n      isLeasing\n      isBlacklisted\n      isTokoNow\n      menu {\n        id\n        name\n        url\n        __typename\n      }\n      category {\n        id\n        name\n        title\n        breadcrumbURL\n        isAdult\n        isKyc\n        minAge\n        detail {\n          id\n          name\n          breadcrumbURL\n          isAdult\n          __typename\n        }\n        __typename\n      }\n      txStats {\n        transactionSuccess\n        transactionReject\n        countSold\n        paymentVerified\n        itemSoldFmt\n        __typename\n      }\n      stats {\n        countView\n        countReview\n        countTalk\n        rating\n        __typename\n      }\n      __typename\n    }\n    components {\n      name\n      type\n      position\n      data {\n        ...ProductMedia\n        ...ProductHighlight\n        ...ProductInfo\n        ...ProductDetail\n        ...ProductSocial\n        ...ProductDataInfo\n        ...ProductCustomInfo\n        ...ProductVariant\n        ...ProductCategoryCarousel\n        ...ProductDetailMediaComponent\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"}],
            [{"operationName":"PDPGetDataP2","variables":{"affiliate":None,"productID":product_id,"pdpSession":pdpSession,"deviceID":"","userLocation":{"cityID":city_id,"addressID":address_id,"districtID":str(district_id),"postalCode":postal_code,"latlon":geolocation},"tokonow":{"shopID":shop_id,"whID":"0","serviceType":"ooc"}},"query":"query PDPGetDataP2($productID: String!, $pdpSession: String!, $deviceID: String, $userLocation: pdpUserLocation, $affiliate: pdpAffiliate) {\n  pdpGetData(productID: $productID, pdpSession: $pdpSession, deviceID: $deviceID, userLocation: $userLocation, affiliate: $affiliate) {\n    error {\n      Code\n      Message\n      DevMessage\n      __typename\n    }\n    callsError {\n      shopInfo {\n        Code\n        Message\n        __typename\n      }\n      cartRedirection {\n        Code\n        Message\n        __typename\n      }\n      nearestWarehouse {\n        Code\n        Message\n        __typename\n      }\n      __typename\n    }\n    productView\n    wishlistCount\n    shopFinishRate {\n      finishRate\n      __typename\n    }\n    shopInfo {\n      shopTier\n      badgeURL\n      closedInfo {\n        closedNote\n        reason\n        detail {\n          openDate\n          __typename\n        }\n        __typename\n      }\n      isOpen\n      favoriteData {\n        totalFavorite\n        alreadyFavorited\n        __typename\n      }\n      activeProduct\n      createInfo {\n        epochShopCreated\n        __typename\n      }\n      shopAssets {\n        avatar\n        __typename\n      }\n      shopCore {\n        domain\n        shopID\n        name\n        shopScore\n        url\n        ownerID\n        __typename\n      }\n      shopLastActive\n      location\n      statusInfo {\n        statusMessage\n        shopStatus\n        isIdle\n        __typename\n      }\n      isAllowManage\n      isOwner\n      ownerInfo {\n        id\n        __typename\n      }\n      isCOD\n      shopType\n      tickerData {\n        title\n        message\n        color\n        link\n        action\n        actionLink\n        tickerType\n        actionBottomSheet {\n          title\n          message\n          reason\n          buttonText\n          buttonLink\n          __typename\n        }\n        __typename\n      }\n      shopCredibility {\n        showOnlineStatus\n        showFollowButton\n        stats {\n          icon\n          value\n          __typename\n        }\n        __typename\n      }\n      partnerLabel\n      __typename\n    }\n    merchantVoucher {\n      vouchers {\n        voucher_id\n        voucher_name\n        voucher_type {\n          voucher_type\n          identifier\n          __typename\n        }\n        voucher_code\n        amount {\n          amount\n          amount_type\n          amount_formatted\n          __typename\n        }\n        minimum_spend\n        valid_thru\n        tnc\n        banner {\n          desktop_url\n          mobile_url\n          __typename\n        }\n        status {\n          status\n          identifier\n          __typename\n        }\n        in_use_expiry\n        __typename\n      }\n      __typename\n    }\n    nearestWarehouse {\n      product_id\n      stock\n      stock_wording\n      price\n      warehouse_info {\n        warehouse_id\n        is_fulfillment\n        district_id\n        postal_code\n        geolocation\n        __typename\n      }\n      __typename\n    }\n    installmentRecommendation {\n      data {\n        term\n        mdr_value\n        mdr_type\n        interest_rate\n        minimum_amount\n        maximum_amount\n        monthly_price\n        os_monthly_price\n        partner_code\n        partner_name\n        partner_icon\n        subtitle\n        __typename\n      }\n      __typename\n    }\n    productWishlistQuery {\n      value\n      __typename\n    }\n    cartRedirection {\n      status\n      error_message\n      data {\n        product_id\n        config_name\n        hide_floating_button\n        available_buttons {\n          text\n          color\n          cart_type\n          onboarding_message\n          show_recommendation\n          __typename\n        }\n        unavailable_buttons\n        __typename\n      }\n      __typename\n    }\n    shopTopChatSpeed {\n      messageResponseTime\n      __typename\n    }\n    shopRatingsQuery {\n      ratingScore\n      __typename\n    }\n    shopPackSpeed {\n      speedFmt\n      hour\n      __typename\n    }\n    ratesEstimate {\n      warehouseID\n      products\n      data {\n        destination\n        title\n        subtitle\n        chipsLabel\n        courierLabel\n        eTAText\n        cheapestShippingPrice\n        fulfillmentData {\n          icon\n          prefix\n          description\n          __typename\n        }\n        errors {\n          code: Code\n          message: Message\n          devMessage: DevMessage\n          __typename\n        }\n        __typename\n      }\n      bottomsheet {\n        title\n        iconURL\n        subtitle\n        buttonCopy\n        __typename\n      }\n      __typename\n    }\n    restrictionInfo {\n      message\n      restrictionData {\n        productID\n        isEligible\n        action {\n          actionType\n          title\n          description\n          attributeName\n          badgeURL\n          buttonText\n          buttonLink\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    ticker {\n      tickerInfo {\n        productIDs\n        tickerData {\n          title\n          message\n          color\n          link\n          action\n          actionLink\n          tickerType\n          actionBottomSheet {\n            title\n            message\n            reason\n            buttonText\n            buttonLink\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    navBar {\n      name\n      items {\n        componentName\n        title\n        __typename\n      }\n      __typename\n    }\n    bebasOngkir {\n      products {\n        productID\n        boType\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"}],
            [{"operationName":"AddToCartOCCMulti","variables":{"param":{"carts":[{"product_id":product_id,"quantity":1,"notes":"","shop_id":shop_id,"warehouse_id":warehouse_id}],"source":"pdp","lang":"id","tracker_data":"","chosen_address":{"mode":1,"address_id":address_id,"district_id":district_id,"postal_code":postal_code,"geolocation":geolocation}}},"query":"mutation AddToCartOCCMulti($param: OneClickCheckoutMultiATCParam) {\n  add_to_cart_occ_multi(param: $param) {\n    error_message\n    status\n    data {\n      message\n      success\n      toaster_action {\n        text\n        show_cta\n        __typename\n      }\n      out_of_service {\n        id\n        code\n        image\n        title\n        description\n        buttons {\n          id\n          code\n          message\n          color\n          __typename\n        }\n        __typename\n      }\n      carts {\n        cart_id\n        notes\n        product_id\n        quantity\n        shop_id\n        warehouse_id\n        __typename\n      }\n      next_page\n      __typename\n    }\n    __typename\n  }\n}\n"}]
        ]
            headers = {
                    'Host': 'gql.tokopedia.com',
                    'Cookie': cookies,
                    'Content-Length': str(len(json.dumps(payload[i]))),
                    'X-Tkpd-Akamai': xtkpdakamai[i],
                    'Sec-Ch-Ua': '"Not;A=Brand";v="24", "Chromium";v="128"',
                    'X-Version': 'bd78eaf',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.120 Safari/537.36',
                    'Content-Type': 'application/json',
                    'Accept': '*/*',
                    'X-Source': 'tokopedia-lite',
                    'X-Device': 'default_v3',
                    'X-Tkpd-Lite-Service': 'zeus',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Origin': 'https://www.tokopedia.com',
                    'Sec-Fetch-Site': 'same-site',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Dest': 'empty',
                    'Referer': 'https://www.tokopedia.coml',
                    'Priority': 'u=1'
                    }
            try:
                response = requests.post(url=url[i],json=payload[i],headers = headers)
                response_json = response.json()
                processing_time = response.headers.get('Gql-Request-Processing-Time')
                print(f"[{times()}] {response.status_code} >> POST {url[i]} >> {processing_time}ms")
                if i == 0:
                    pdpSession = response_json[0]['data']['pdpGetLayout']['pdpSession']
                    product_id = response_json[0]['data']['pdpGetLayout']['basicInfo']['id']
                elif i == 1:
                    shop_id = response_json[0]['data']['pdpGetData']['shopInfo']['shopCore']['shopID']
                    warehouse_id = response_json[0]['data']['pdpGetData']['nearestWarehouse'][0]['warehouse_info']['warehouse_id']
                elif i == 2:
                    cart_details = {}
                    carts = response_json[0]['data']['add_to_cart_occ_multi']['data']['carts']
                    for cart in carts:
                        cart_id = cart['cart_id']
                        notes = cart['notes']
                        product_id = cart['product_id']
                        quantity = cart['quantity']
                        shop_id = cart['shop_id']
                        warehouse_id = cart['warehouse_id']
                        typename = cart['__typename']
                        cart_details = {
                            "cart_id": cart_id,
                            "notes": notes,
                            "product_id": product_id,
                            "quantity": quantity,
                            "shop_id": shop_id,
                            "warehouse_id": warehouse_id,
                            "__typename": typename
                            }
                    with open(f'{user_data_dir}/cart_details.json', 'w') as cart:
                        json.dump(cart_details, cart, indent=2)
                    status = response_json[0]['data']['add_to_cart_occ_multi']['data']['message'][0]  # Menggunakan json.dump untuk menulis ke file
                    print(f"[{times()}] {status}")

            except Exception as e:
                print(f"Terjadi kesalahan di permintaan ke {i}: {e}")
    except Exception as e:
        print(f"Terjadi kesalahan : {e}")
if __name__ == "__main__":
    main()
