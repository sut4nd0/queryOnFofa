#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import re
import time
import base64
import warnings
import openpyxl
import requests
import urllib.parse
import urllib3
import argparse
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


urllib3.disable_warnings()
warnings.filterwarnings("ignore")
session = requests.Session()


private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAv0xjefuBTF6Ox940ZqLLUFFBDtTcB9dAfDjWgyZ2A55K+VdG
c1L5LqJWuyRkhYGFTlI4K5hRiExvjXuwIEed1norp5cKdeTLJwmvPyFgaEh7Ow19
Tu9sTR5hHxThjT8ieArB2kNAdp8Xoo7O8KihmBmtbJ1umRv2XxG+mm2ByPZFlTdW
RFU38oCPkGKlrl/RzOJKRYMv10s1MWBPY6oYkRiOX/EsAUVae6zKRqNR2Q4HzJV8
gOYMPvqkau8hwN8i6r0z0jkDGCRJSW9djWk3Byi3R2oSdZ0IoS+91MFtKvWYdnNH
2Ubhlnu1P+wbeuIFdp2u7ZQOtgPX0mtQ263e5QIDAQABAoIBAD67GwfeTMkxXNr3
5/EcQ1XEP3RQoxLDKHdT4CxDyYFoQCfB0e1xcRs0ywI1be1FyuQjHB5Xpazve8lG
nTwIoB68E2KyqhB9BY14pIosNMQduKNlygi/hKFJbAnYPBqocHIy/NzJHvOHOiXp
dL0AX3VUPkWW3rTAsar9U6aqcFvorMJQ2NPjijcXA0p1MlZAZKODO2wqidfQ487h
xy0ZkriYVi419j83a1cCK0QocXiUUeQM6zRNgQv7LCmrFo2X4JEzlujEveqvsDC4
MBRgkK2lNH+AFuRwOEr4PIlk9rrpHA4O1V13P3hJpH5gxs5oLLM1CWWG9YWLL44G
zD9Tm8ECgYEA8NStMXyAmHLYmd2h0u5jpNGbegf96z9s/RnCVbNHmIqh/pbXizcv
mMeLR7a0BLs9eiCpjNf9hob/JCJTms6SmqJ5NyRMJtZghF6YJuCSO1MTxkI/6RUw
mrygQTiF8RyVUlEoNJyhZCVWqCYjctAisEDaBRnUTpNn0mLvEXgf1pUCgYEAy1kE
d0YqGh/z4c/D09crQMrR/lvTOD+LRMf9lH+SkScT0GzdNIT5yuscRwKsnE6SpC5G
ySJFVhCnCBsQqq+ohsrXt8a99G7ePTMSAGK3QtC7QS3liDmvPBk6mJiLrKiRAZos
vgPg7nTP8VuF0ZIKzkdWbGoMyNxVFZXovQ8BYxECgYBvCR9xGX4Qy6KiDlV18wNu
ElYkxVqFBBE0AJRg/u+bnQ9jWhi2zxLa1eWZgtss80c876I8lbkGNWedOVZioatm
MFLC4bFalqyZWyO7iP7i60LKvfDJfkOSlDUu3OikahFOiqyG1VBz4+M4U500alIU
AVKD14zTTZMopQSkgUXsoQKBgHd8RgiD3Qde0SJVv97BZzP6OWw5rqI1jHMNBK72
SzwpdxYYcd6DaHfYsNP0+VIbRUVdv9A95/oLbOpxZNi2wNL7a8gb6tAvOT1Cvggl
+UM0fWNuQZpLMvGgbXLu59u7bQFBA5tfkhLr5qgOvFIJe3n8JwcrRXndJc26OXil
0Y3RAoGAJOqYN2CD4vOs6CHdnQvyn7ICc41ila/H49fjsiJ70RUD1aD8nYuosOnj
wbG6+eWekyLZ1RVEw3eRF+aMOEFNaK6xKjXGMhuWj3A9xVw9Fauv8a2KBU42Vmcd
t4HRyaBPCQQsIoErdChZj8g7DdxWheuiKoN4gbfK4W1APCcuhUA=
-----END RSA PRIVATE KEY-----"""

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://fofa.info/',
    'Origin': 'https://fofa.info',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.11'
}


def delete_proxy(p):
    session.get("http://127.0.0.1:5010/delete/?proxy={}".format(p))


def get_proxy():
    try:
        p = session.get("http://127.0.0.1:5010/get/").json().get("proxy")
        return p
    except Exception:
        return None


proxy = get_proxy()


def get_json_data(qu):
    global proxy
    if proxy:
        retry = 5
    else:
        retry = 0
    
    while True:
        try:
            response = session.get(url=qu, headers=headers, timeout=3, proxies={'http': f'http://{proxy}'}).json()
            if response['data']["distinct_ips"]:
                return response
        except Exception:
            retry -= 1
            if retry < 1:
                try:
                    response = session.get(url=qu, headers=headers, timeout=3).json()
                    if response['data']["distinct_ips"]:
                        return response
                except Exception:
                    retry = 5
            else:
                delete_proxy(proxy)
                while True:
                    proxy = get_proxy()
                    if proxy or retry < 1:
                        break
                    retry -= 1
                    time.sleep(2)


def rsa_sign(d):
    # 解析RSA私钥
    bin_private_key = RSA.import_key(private_key)
    # 计算SHA-256哈希值
    hash_obj = SHA256.new(d.encode())
    # 使用RSA私钥进行签名
    signature = pkcs1_15.new(bin_private_key).sign(hash_obj)
    # 将签名结果转换为Base64编码
    base64_signature = base64.b64encode(signature).decode()
    # 对Base64编码的签名结果进行URL编码
    url_encoded_signature = urllib.parse.quote(base64_signature, safe='')
    return url_encoded_signature


def query_on_fofa(cn, expr, o):
    fofa_url = 'https://api.fofa.info/v1/search/stats?qbase64='
    app_id = '9e9fb94330d97833acfbc041ee1a76793f1bc691'
    expr = f'body="{cn}" && {expr}'
    # 进行RSA签名
    qb = base64.b64encode(expr.encode()).decode()
    ts = int(time.time()) * 1000
    data = f'fullfalseqbase64{qb}ts{ts}'
    qb = urllib.parse.quote(qb, safe='')
    sign = rsa_sign(data)
    # 构造请求url
    query_url = f'{fofa_url}{qb}&full=false&fields=&ts={ts}&sign={sign}&app_id={app_id}'
    json_data = get_json_data(query_url)
    distinct_ips = json_data["data"]["distinct_ips"]

    if int(distinct_ips) > 15:
        # 获取首标题
        title = (json_data["data"]["ranks"]["title"][0]["name"]).strip()
        # 获取首标题数
        count = json_data["data"]["ranks"]["title"][0]["count"]
        print(f'[*]{cn}\n\t独立IP --->{distinct_ips}<---')
        print(f'\t首标题 --->{title}<---\n\t存在条数 --->{count}<---')
        # 结果写入result.xlsx
        wba = openpyxl.load_workbook(o)
        wsa = wba.active
        wsa.append([cn, distinct_ips, title, count])
        wba.save(o)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="根据文件内的公司名称在fofa上进行批量查询")
    parser.add_argument("-f", "--file", help="要处理的文件路径", required=True)
    parser.add_argument("-q", "--query", help='指定搜索表达式(需使用引号), 默认: body="公司名称" && country="CN" && (title="登录" || title="管理" || title="登陆" || title="后台" || title="平台" || title="系统")', default='country="CN" && (title="登录" || title="管理" || title="登陆" || title="后台" || title="平台" || title="系统")')
    output = time.strftime('%Y-%m-%d_%H%M%S', time.localtime())
    parser.add_argument("-o", "--output", help="指定输出文件名，默认为当前时间", default=output)

    args = parser.parse_args()
    args.output = args.output + '.xlsx'
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['公司名称', '独立IP数', '首标题', '首标题总数'])
    wb.save(args.output)

    with open(args.file, 'r', encoding='utf-8') as file:
        for line in file:
            cname = line.strip()
            if cname:
                try:
                    if '科技' in cname:
                        cname = cname[:re.search(r'科技', cname).end()]
                        if '(' in cname:
                            cname = cname.replace(re.search(r"\(.*?\)", cname).group(), '')
                        query_on_fofa(cname, args.query, args.output)
                    elif '技术' in cname:
                        cname = cname[:re.search(r'技术', cname).end()]
                        if '(' in cname:
                            cname = cname.replace(re.search(r"\(.*?\)", cname).group(), '')
                        query_on_fofa(cname, args.query, args.output)
                    elif '软件' in cname:
                        cname = cname[:re.search(r'软件', cname).end()]
                        if '(' in cname:
                            cname = cname.replace(re.search(r"\(.*?\)", cname).group(), '')
                        query_on_fofa(cname, args.query, args.output)
                    elif '股份' in cname:
                        cname = cname[:re.search(r'股份', cname).end()]
                        if '(' in cname:
                            cname = cname.replace(re.search(r"\(.*?\)", cname).group(), '')
                        query_on_fofa(cname, args.query, args.output)
                    elif '有限' in cname:
                        cname = cname[:re.search(r'有限', cname).end()-2]
                        if '(' in cname:
                            cname = cname.replace(re.search(r"\(.*?\)", cname).group(), '')
                        query_on_fofa(cname, args.query, args.output)
                    else:
                        if '(' in cname:
                            cname = cname.replace(re.search(r"\(.*?\)", cname).group(), '')
                        query_on_fofa(cname, args.query, args.output)
                except Exception as e1:
                    print(f'Main Error: {e1}')
