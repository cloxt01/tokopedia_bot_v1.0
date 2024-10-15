import httpx
import webbrowser

# URL pengalihan dengan parameter di URL
url = ("https://pay.tokopedia.com/v2/payment/redirect"
       "?device=default_v3"
       "&merchant_code=tokopedia"
       "&signature=01fe73681625da24e768b70a68a1661769a1eef7"
       "&transaction_id=2835151322"
       "&back_url=https://www.tokopedia.com/beli-langsung")

# Headers untuk permintaan POST
headers = {
    "Host": "pay.tokopedia.com",
    "Cookie": "_UUID_NONLOGIN_=5f344c9651893962c93fff2aaf792157; _UUID_NONLOGIN_.sig=KxgttjqAgwvj6B6NqkRvOxH_3io; FPF=1; DID=137aae36aaed9dc4ba3aca85e496fcf68dac7c33b0b0810e2150b12bff1623456b7368b43591025c1ae49135a568b969; _tt_enable_cookie=1; _ttp=ObHpgABukox8ddXZ07-DVAOJ4bL; dt_intl=JT_4Ikjx9zZXzdgfOlsBTYwhJ1OjedFeo_1BxCy1FxN9d-; _dc_gtm_UA-9801603-1=1; _gat_UA-9801603-1=1; webauthn-session=ef7e9e19-978a-47d1-b6a3-dd6f6c2c06a9; _CASE_=7a23604865233b23303534393835373832232d23624865233b3035302d23654865233b303432312d236d547165233b23333133352c30312c31385530373b31323b33312a31363b3131232d236d6075233b232c372f323231383437232d236d636d233b2353746c6069214c7469606c6065214764736568606f72786069232d236d6e6f66233b233031372f323837333336232d2371426e233b233533323930232d23724865233b30303432313436322d237255787164233b236e6e62232d23764865233b312d23766972233b235a5c232d2376697272233b235a5c237c; _UUID_CAS_=64104b17-5c28-4666-8c1a-aaa65d8a30b9; home_libra_parameters=%7B%22experiment%22%3A%22home_revamp_3_type%22%2C%22variant%22%3A%22variant1%22%7D; _fbp=fb.1.1728464605899.884240096; _gcl_au=1.1.1457391822.1728380122; bm_mi=EF105E226680AD2B0F4C84419E156494~YAAQv7jbF9c6KHSSAQAAWwIndRka8aK7pzTwmOfmAKpn/748iVMfXfBW6kPwghyPvP8CeRRp3axtjAR6mfyrkV7HfGWo8W2jqmwBVEQambdAaRi2tBCBE/a0dr4D1lMotYUQ84TxSmAg+YY4K7qBRkG4vIZmnLHHWL2x7UqncBRwNz4sGQWthH9qw1PJspRGl1BZJHWPSju0v3jjsjlaQgzb/yULMvPfZe6BMWxAXudY4Jw6zWNBwFeCPBIb2Mx7x7Wwh7O8AAwdnyhZhIXtrTfW1Qb7e5+RvDtNM0cHindILxxEmH+JXv8H0FzBAjPEcE0LIVg0yIY+n9Ci124=~1; ak_bmsc=3098D52ACA462A62901A76F78BE873B0~000000000000000000000000000000~YAAQzDLVjK0m7HWSAQAA8HjMdhm8zokYaZZkvrzp8fv61Iii2QTKwlX/n/FTy3GfVPXR10HGnGq/zz2Mb4HxTI6xv+jdoEGsonuLGETRfeEP99mho8Ratep8ilvsEc+0JncbGvNSGJKfo8o2jXYCUrDw71uUCAHsApmN4MjVMqRHZLpRmwJJQkQPfqNAvYgyZ1egL1OQc9Zo0X5hd47ufaxmrTw/ZgTtRXvQL9ZCZ0ZiS6Sr6Z09lMhJxSXtMiDwnvGwtxYWBdb/uQ4wNBLYrWxfJRPGPAGodIdnOfHQXZpYFLnxCQJusbYXWgljwgh/DHb3WLJbz9/HzZR+UATlvlI1CmrgEv7hUqf12iqqfEBoZPtwDzn5I/xYfKmnSjh3subWUr1tv4W3qw63aFbHOj8cGT4uWBWGOLwN4EP4BNgyjkkDmnnzYPeXCkFI9Sru9Ld8vqMT3U8OOvoZF2yjMRWoC1xdhcc=; AMP_TOKEN=%24NOT_FOUND; ect=4g; bm_sz=03C3EF0CA5EAB98CF923922976806C62~YAAQ5TLVjCqzi3KSAQAAgyENdxmeICopYTou4jm2qL+Q3pkwyknOIskRgJpRYkwjH4sGzK+OFIXArCzuM6BKX7zmv9195LRKxzuArtZg/dJXY+EUg4HY2HwHSVDQdMvEESszBhV3V8Q+oclGUsQqFY3wj+MX0lemgoE29+oOurb0K5Y9ZlIB97zlCKzuhMDvEzHm2KmxdjsPxsin/haokIoiV7vXzGzAzJVtxzFrbMziUonN65qAunF5a3I2KGpkEJK1dt+T4GkjpVahWkkha/mdu32OrftRN70/U+URIbFUjynh9aM6Gwv3zvX2XncKzfN18x7gURoPPR5G09F/qFfHkIw9jgBuhRDxAYdM1F8VglYCvGW5J/f3wUlJPhZYM7EOhbej6E4MFAWIlkfu4VkUWwR35ysKlKneWuJfvY6wXYppeEHeyVYIkSi+MjUdHRvf6CNpBju8ylaZPasw9nXxkirqctB/B1Zv3JZjmtofxPwL9GzPSbVnDb5ja9DlHX7Cj9uObS1GrvxPFpOknfbk/cHq/xeLFhz9/DUXQLhI1P13~3618885~4599877; gec_id=415427009443806912; uidh=+sj3q4AH/sTHgLwJlceeatoI4gig717LASMGs2Crdow=; uide=tA/yWfkb2Q7KcxTrFHM0PZWH+x3/khyPCqptWx6/qX1rb0Ir; DID_JS=MTM3YWFlMzZhYWVkOWRjNGJhM2FjYTg1ZTQ5NmZjZjY4ZGFjN2MzM2IwYjA4MTBlMjE1MGIxMmJmZjE2MjM0NTZiNzM2OGI0MzU5MTAyNWMxYWU0OTEzNWE1NjhiOTY547DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=; l=1; aus=1; _SID_Tokopedia_=_VNIMWDdZOUP2n9kH8GNJ48T7BNILQHvJsqOIwz5nvqWqLhUNbbnZve7FCnn27FYMUNidzB5Qj3oLrW-Mu4cGuax1MM_qP9VhccwOC8skTpCIri9t_I4y2T_i2cGCSRC; tuid=96724138; _gat_gtag_UA_9801603_6=1; _dc_gtm_UA-126956641-6=1; ISID=%7B%22www.tokopedia.com%22%3A%22d3d3LnRva29wZWRpYS5jb20%3D.862b5faa7def741e7b2029b479ce7d1c.1728380122369.1728380122369.1728574204464.193%22%7D; _dc_gtm_UA-9801603-6=1; _abck=5A7ED7AFA9809803C01600DA324ABD68~-1~YAAQ5TLVjMi0i3KSAQAAWE4Ndwy2EsNGG8U+p3nvKdFmdxGhZv19x3BFmmAdikt1ZSu+lIqB8VmdUg9Hur6zQ8YC+21WXYdvasQHBjH+wxTnTJTfp19P6Rfluxlk0FrYGC+mkrkr9E0JTZH19eFJq4MLZCisNad4yVqo5Ok6KZrXcNj1s2upr9xcECaJxodWYokswMyXtoCI020Rdes7Z8fodJ33j/DaeEx3hzUp/dKbc9h0svLeBKis9qMFXckuQRvrka5u7hDw59RtjpTuzGejv+popAaWhu4CuExESbgbw5Q2WbHTG4dMzfmk5A7GmQ/2EYNpd8g4LtpF7Dv3fvmvj4MjJUtsOXi1ciyXPjn7OYK8wICssbmqdXjGVwA5MXbhPQlzO/Q/1G13qyd9iq6Ipr/COniB2POuvGf3AEQRmH9xOK2dOyYPxUiuOAi53XGuxvSqn5Pjd2FTO+7CuMNfLi+LlSVkfhOvOUYqiMmYqh7ff7yjMhGSQa88ZzXNSnJAkeLYcWkunatqQUbQ3YkS1UsRafOJK1p3unvaQzTcRGLaJgaxAVHdqTEevzFaA7L2olxmPgGUhqZ5miBeX9hkFdLmiv/8nJuIv+YduzmFlD6qKbyou3OBXSkGUl+Pwoj5DUypwS1mQGBcnWCfo1/5h+a3pzrtlxpRNDiuTVH+X3nwb0qjBi9Vd5a8nzhP9jxlhLAzyeFWZHjBH/z3kPRH3gZUSSjxbVDCrMAxjMl//n7QqldVhY6xY6Svfh19M6/UE/FbDfph2ry38xbJKdV9bv0xaMY=~-1~||0||~-1; _ga=GA1.2.362168989.1728380123; _gid=GA1.2.455195242.1728380123; _gat_UA-9801603-6=1; _ga_70947XW48P=GS1.1.1728570933.1.1.1728574217.48.0.0",
    "Content-Length": "0",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/129.0.6668.71 Safari/537.36",
    "Referer": "https://www.tokopedia.com/beli-langsung",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
              "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}

# Lakukan POST request tanpa body
with httpx.Client() as client:
    response = client.post(url, headers=headers)

# Cetak URL pengalihan terakhir
print(f"Final URL setelah redirect: {response.url}")
redirect_url = response.headers.get("Location")

chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'

print(f"Payment URL : {redirect_url}")
webbrowser.get(chrome_path).open(redirect_url)

