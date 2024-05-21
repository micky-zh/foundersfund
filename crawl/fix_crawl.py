from __future__ import division

import datetime
import json
import os
import random
import re
import time

import requests
from bs4 import BeautifulSoup

_headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
}


def craw_tt_jj(url, encoding="utf-8"):
    """
    下载网页,指定字符集
    """
    r = requests.get(url, headers=_headers, timeout=5)
    r.encoding = encoding

    # print(r.encoding)
    # print(r.status_code)
    # print(r.text)
    return r.text


# 抓取网页
def get_url(url, params=None, proxies=None):
    rsp = requests.get(url, params=params, proxies=proxies)
    rsp.raise_for_status()
    return rsp.text


def check_charge_is_bull(code):
    url = "https://j5.fund.eastmoney.com/sc/tfs/qt/v2.0.1/%s.json?deviceid=1234567.py.service&version=6.5.5&appVersion=6.5.5&product=EFund&plat=web&curTime=1709185730881" % code
    html = craw_tt_jj(url)
    dict_obj = json.loads(html)
    # print(dict_obj)

    risk_type = 0
    if "JJXQ" in dict_obj:
        risk_type = dict_obj["JJXQ"]["Datas"]["RISKLEVEL"]
    risk = risk_type
    if int(risk_type) == 1:
        risk = "低风险"
    if int(risk_type) == 2:
        risk = "中低风险"
    if int(risk_type) == 3:
        risk = "中风险"
    if int(risk_type) == 4:
        risk = "中高风险"

    if "JJJLNEW" in dict_obj:
        arr = dict_obj["JJJLNEW"]["Datas"][0]["MANGER"]
        for item in arr:
            return item["HJ_JN"], risk
    if "JJJL" in dict_obj:
        arr = dict_obj["JJJL"]["Expansion"]
        for item in arr:
            return item["HJ_JN"], risk

    return 0, risk


def start():
    lines = []
    _time = time.strftime("%Y-%m-%d", time.localtime())
    bull_f = "../data/2024-03-01.csv"
    lines_set = set()
    if os.path.exists(bull_f):
        with open(bull_f, 'r') as file:
            for line in file:
                print(line.strip())
                lines.append(line.replace("\n", ""))

    local_cache_file = "../data/2024-03-01_new.cache"
    if os.path.exists(local_cache_file):
        with open(local_cache_file) as tmp_file:
            for line in tmp_file:
                lines_set.add(line.replace("\n", ""))

    csv_f = "../data/2024-03-01_new.csv"
    if not os.path.exists(csv_f):
        with open(csv_f, "w") as file:
            file.write(
                "基金代号,基金名称,类型,公司,成立日期,基金经理,近1年夏普比率,近2年夏普比率,近3年夏普比率,近1年标准差,近2年标准差,近3年标准差,近1年最大回撤,近1周,近1月,近3月,近6月,今年以来,近1年,近两年,近三年,换手率,评级,金牛经理,风险\n")

    # os.remove(csv_f)
    counter = 0
    head = True
    for item in lines:
        if head:
            head = False
            continue

        counter += 1
        print(counter, len(lines))
        arr = str(item).split(",")
        if arr[0] in lines_set:
            continue

        # if counter % 3 == 0:
        #     time.sleep(1)
        print(arr[0], arr[1])
        res, risk = check_charge_is_bull(arr[0])
        arr[-1] = str(res)
        arr.append(str(risk))

        joined_string = ','.join(arr)

        with open(csv_f, "a") as file:
            file.write(joined_string + "\n")

        lines_set.add(arr[0])
        with open(local_cache_file, "a") as tmp_file:
            tmp_file.write(arr[0] + "\n")


if __name__ == "__main__":
    start()

    # res = check_charge_is_bull("000254")
    # print(res)

    # html = craw_tt_jj("http://fundf10.eastmoney.com/tsdata_014758.html")

    # _dict = parse_fund_info(html)

    # parse_income("011113")
    # a = max_draw_down("001106")
    # print(a)

    # r = withdrawal([1, 0.9, 2, 1, 3, 1])
    # print(r)

    # rate_of_return("011473")
