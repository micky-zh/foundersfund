from __future__ import division

import datetime
import os
import re
import time

import requests
from bs4 import BeautifulSoup

from es.base import gen_data

_headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
}


def craw_tt_jj(url, encoding="utf-8", headers=_headers):
    """
    下载网页,指定字符集
    """
    r = requests.get(url, headers)
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


# 从网页抓取数据
def get_fund_data(code, per=10, sdate='', edate='', proxies=None, pos=None):
    url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx'
    params = {'type': 'lsjz', 'code': code, 'page': 1, 'per': per, 'sdate': sdate, 'edate': edate}
    html = get_url(url, params, proxies)
    soup = BeautifulSoup(html, 'html.parser')

    # 获取总页数
    pattern = re.compile(r'pages:(.*),')
    result = re.search(pattern, html).group(1)
    pages = int(result)

    # 获取表头
    heads = []
    for head in soup.findAll("th"):
        heads.append(head.contents[0])

    # 数据存取列表
    records = []

    # 如果文件里面已经有了历史的记录,获取到文件记录的日期就可以了,不用在深度查询了.
    is_break = False

    # 从第1页开始抓取所有页面数据
    page = 1
    while page <= pages:
        params = {'type': 'lsjz', 'code': code, 'page': page, 'per': per, 'sdate': sdate, 'edate': edate}
        html = get_url(url, params, proxies)
        soup = BeautifulSoup(html, 'html.parser')

        # 获取数据
        for row in soup.findAll("tbody")[0].findAll("tr"):

            row_records = []
            counter = 0
            for record in row.findAll('td'):
                val = record.contents

                counter += 1
                # 如果是第一行
                if 1 == counter and pos and val[0] == pos:
                    is_break = True
                    print("基金代码: %s,基金净值已经更新到指定日期 %s" % (code, pos))
                    break

                # 处理空值
                if not val:
                    row_records.append("")
                else:
                    row_records.append(val[0])

            # 找到上次更新的位置 & 直接标记结束: 退出第一层大循环
            if is_break:
                page = pages + 1
                break

            # 记录数据
            records.append(row_records)

        # 下一页
        page = page + 1

    return records


def get_last_line(f_name):
    with open(f_name) as f:
        for line in f:
            pass
        last_line = line
        return last_line


def max_draw_down(code):
    """
    获取所有净值: 如果本地文件存在则跳过
    计算最大回撤
    """

    if not os.path.exists("../data/jingzhi"):
        os.makedirs("../data/jingzhi")

    f = "../data/jingzhi/%s.csv" % code

    # 如果存在就从上一次的地方更新
    pos = None
    if os.path.exists(f):
        last_line = get_last_line(f)
        pos = last_line.split(",")[0]
        print("基金代码: %s,上次净值更新日期: %s" % (code, pos))

    records = get_fund_data(code, pos=pos)
    records.reverse()

    if pos:
        with open(f, "a") as file:
            for item in records:
                file.write("%s,%s,%s,%s,%s,%s\n" % (item[0], item[1], item[2], item[3], item[4], item[5]))
                print("%s,%s,%s,%s,%s,%s\n" % (item[0], item[1], item[2], item[3], item[4], item[5]))
    else:
        with open(f, "w") as file:
            file.write("净值日期,单位净值,累计净值,日增长率,申购状态,赎回状态\n")
            for item in records:
                file.write("%s,%s,%s,%s,%s,%s\n" % (item[0], item[1], item[2], item[3], item[4], item[5]))
                # print("%s,%s,%s,%s,%s,%s\n" % (item[0], item[1], item[2], item[3], item[4], item[5]))

    result = []
    _counter = 0
    with open(f, 'r') as f:
        for line in f:
            _counter += 1
            if 1 == _counter:
                continue

            value_arr = line.strip('\n').split(',')

            # 数据为空的情况
            if not value_arr[1]:
                continue

            _dict = dict()
            _dict['date'] = value_arr[0]
            _dict['value'] = float(value_arr[1])

            result.append(_dict)

    # _90 = find_recent_1_year(result, 90)
    # _180 = find_recent_1_year(result, 180)
    _365 = find_recent_1_year(result, 365)

    return withdrawal(_365)


def find_recent_1_year(arr, _days):
    res = []

    today = datetime.datetime.now()
    date_point = today - datetime.timedelta(days=_days)
    print("%s 天起始时间" % _days, date_point.strftime("%Y-%m-%d"))

    for item in arr:
        if not item['date']:
            continue

        _date = datetime.datetime.strptime(item['date'], '%Y-%m-%d')
        if _date > date_point:
            res.append(item['value'])

    return res


def withdrawal(value_arr):
    rate = 0
    for idx, val in enumerate(value_arr):
        # print(idx, val)

        tmp = 0
        for i in range(idx + 1, len(value_arr)):

            if float(val) <= float(value_arr[i]):
                break

            _tmp = round((val - value_arr[i]) / val, 5)

            if _tmp > tmp:
                tmp = _tmp

        if tmp > rate:
            rate = tmp

    return rate


def parse_fund(html):
    """
    根据返回的内容获取到 基金的代号 以及 基金的名称
    """
    match_obj = re.match(r'.*datas:(.*),count', html, re.M | re.I)
    fund_dict = {}
    if not match_obj:
        print("No match!!")

    else:
        str_arr = match_obj.group(1)
        list_arr = eval(str_arr)
        for item_arr in list_arr:
            # print(item_arr[0], item_arr[1])
            fund_dict.setdefault("" + item_arr[0], item_arr[1])

    return fund_dict


def parse_fund_info(html):
    """
    解析html中的 信息、夏普比率、标准差
    """
    info_dict = {}
    soup = BeautifulSoup(html, 'html.parser')

    items = soup.select("table.fxtb tr")[1]
    print(items.contents[0].text, items.contents[1].text, items.contents[2].text, items.contents[3].text)
    info_dict["volatility"] = [items.contents[1].text, items.contents[2].text, items.contents[3].text]

    items = items.next_sibling
    print(items.contents[0].text, items.contents[1].text, items.contents[2].text, items.contents[3].text)
    info_dict["sharp"] = [items.contents[1].text, items.contents[2].text, items.contents[3].text]

    items = soup.select("div.bs_gl label")[0].contents[1]
    print("成立日期", items.text)
    info_dict["fund_create_date"] = items.text

    items = soup.select("div.bs_gl label")[1].contents[1]
    print("基金经理", items.text)
    info_dict["fund_charge"] = items.text

    items = soup.select("div.bs_gl label")[2].contents[1]
    print("类型", items.text)
    info_dict["fund_type"] = items.text

    items = soup.select("div.bs_gl label")[3].contents[1]
    print("基金公司", items.text)
    info_dict["fund_company"] = items.text

    # items = soup.select("span.chooseLow")
    # print("在所有基金中的风险等级", items[0].text)
    # print("在同类基金中的风险等级", items[1].text)
    # info_dict["fund_all_level"] = items[0].text
    # info_dict["fund_same_level"] = items[1].text

    items = soup.select("div.col-right label")
    print("日期", items[1].contents[1].text.strip())
    info_dict["date"] = items[1].contents[1].text.strip()
    return info_dict


def start():
    fund_dict = {}
    # 获取所有的基金代号，名称
    for i in range(1, 54):
        print("获取基金列表,当前第%s页" % i)
        list_url = "http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx?t=1&lx=1&letter=&gsid=&text=&sort=zdf,desc&page=%s,200&dt=1615542928187&atfc=&onlySale=0"
        html = craw_tt_jj(list_url % i)

        curr_dict = parse_fund(html)
        fund_dict.update(curr_dict)

    if not os.path.exists("../data"):
        os.makedirs("../data")

    _time = time.strftime("%Y-%m-%d", time.localtime())
    f = "../data/%s.csv" % _time
    with open(f, "w") as file:

        file.write("基金代号,基金名称,类型,公司,成立日期,基金经理,近1年夏普比率,近2年夏普比率,近3年夏普比率,近1年标准差,近2年标准差,近3年标准差,近1年最大回撤\n")

        # 解析所有代号的 夏普比率、标准差(波动率)
        info_url = "http://fundf10.eastmoney.com/tsdata_%s.html"
        for k, v in fund_dict.items():
            print(info_url % k)
            print("基金名称", v)
            print("基金代号", k)

            max_draw = round(max_draw_down(k) * 100, 2)
            print("最大回撤", max_draw)

            # 夏普比率,标准差
            html = craw_tt_jj(info_url % k)

            _dict = parse_fund_info(html)

            _volatility1 = _dict['volatility'][0]
            if "%" in _dict['volatility'][0]:
                _volatility1 = float(_dict['volatility'][0].replace("%", ""))

            _volatility2 = _dict['volatility'][1]
            if "%" in _dict['volatility'][1]:
                _volatility2 = float(_dict['volatility'][1].replace("%", ""))

            _volatility3 = _dict['volatility'][2]
            if "%" in _dict['volatility'][2]:
                _volatility3 = float(_dict['volatility'][2].replace("%", ""))

            # 计算最大回撤一年内
            file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
                k, v, _dict['fund_type'], _dict['fund_company'], _dict['fund_create_date'], _dict['fund_charge'],
                _dict['sharp'][0], _dict['sharp'][1], _dict['sharp'][2], _volatility1,
                _volatility2, _volatility3, max_draw))

            print()
            # break

    gen_data(f)


if __name__ == "__main__":
    start()
    # a = max_draw_down("001106")
    # print(a)

    # r = withdrawal([1, 0.9, 2, 1, 3, 1])
    # print(r)
