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


def read_file_to_dict(f_name):
    bull_dict = {}
    if os.path.isfile(f_name):
        with open(f_name) as f:
            for line in f:
                funder = line.split("\t")
                bull_dict[funder[0]] = funder[1]
    return bull_dict


def write_dict_to_file(f_name, bull_dict):
    with open(f_name) as file:
        for k, v in bull_dict.items():
            file.write("%s\t%s\n" % (k, v))


def crawl_max_draw_down(code):
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


def max_draw_down_count(code):
    result = []
    _counter = 0
    f = "../data/jingzhi/%s.csv" % code
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


def rate_of_return(fund_id):
    html = craw_tt_jj(
        "http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jdzf&code=%s" % fund_id)
    # print(html)
    self_dict = {}
    same_dict = {}
    soup = BeautifulSoup(html, 'html.parser')
    counter = 0
    for item in soup.find_all("ul"):
        # print(item)
        _arr = item.find_all("li")
        print(_arr[0].get_text(), _arr[1].get_text(), _arr[2].get_text())

        counter += 1

        if 1 == counter:
            continue
        if 2 == counter:
            self_dict.setdefault("this_year", _arr[1].get_text())
            same_dict.setdefault("this_year", _arr[2].get_text())
        if 3 == counter:
            self_dict.setdefault("week", _arr[1].get_text())
            same_dict.setdefault("week", _arr[2].get_text())
        if 4 == counter:
            self_dict.setdefault("1_month", _arr[1].get_text())
            same_dict.setdefault("1_month", _arr[2].get_text())
        if 5 == counter:
            self_dict.setdefault("3_month", _arr[1].get_text())
            same_dict.setdefault("3_month", _arr[2].get_text())
        if 6 == counter:
            self_dict.setdefault("6_month", _arr[1].get_text())
            same_dict.setdefault("6_month", _arr[2].get_text())
        if 7 == counter:
            self_dict.setdefault("1_year", _arr[1].get_text())
            same_dict.setdefault("1_year", _arr[2].get_text())
        if 8 == counter:
            self_dict.setdefault("2_year", _arr[1].get_text())
            same_dict.setdefault("2_year", _arr[2].get_text())
        if 9 == counter:
            self_dict.setdefault("3_year", _arr[1].get_text())
            same_dict.setdefault("3_year", _arr[2].get_text())
        if 10 == counter:
            self_dict.setdefault("5_year", _arr[1].get_text())
            same_dict.setdefault("5_year", _arr[2].get_text())

    return self_dict, same_dict


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

    items = soup.select("div.bs_gl label")[1]
    print("基金经理", items.contents[1].text if len(items.contents) >= 2 else "--")
    info_dict["fund_charge"] = items.contents[1].text if len(items.contents) >= 2 else "--"

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


def check_charge_is_bull(code):
    url = "https://j5.fund.eastmoney.com/sc/tfs/qt/v2.0.1/%s.json?deviceid=1234567.py.service&version=6.5.5&appVersion=6.5.5&product=EFund&plat=web&curTime=1709185730881" % code
    html = craw_tt_jj(url)
    dict_obj = json.loads(html)
    # print(dict_obj)
    if "JJJLNEW" in dict_obj:
        arr = dict_obj["JJJLNEW"]["Datas"][0]["MANGER"]
        for item in arr:
            if item["HJ_JN"] == 3:
                return True
    else:
        arr = dict_obj["JJJL"]["Expansion"]
        for item in arr:
            if item["HJ_JN"] == 3:
                return True

    return False


def start():
    fund_dict = {}
    # fund_list = []
    # 获取所有的基金代号，名称
    for i in range(1, 101):
        print("获取基金列表,当前第%s页" % i)
        list_url = "http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx?t=1&lx=1&letter=&gsid=&text=&sort=zdf,desc&page=%s,200&dt=1615542928187&atfc=&onlySale=0"
        html = craw_tt_jj(list_url % i)

        curr_dict = parse_fund(html)
        fund_dict.update(curr_dict)
        # fund_list.extend(list(curr_dict.keys()))
        # break

    # fund_list.reverse()

    if not os.path.exists("../data"):
        os.makedirs("../data")

    _time = time.strftime("%Y-%m-%d", time.localtime())
    csv_f = "../data/%s.csv" % _time

    if not os.path.exists("../data/bull"):
        os.makedirs("../data/bull")

    bull_f = "../data/bull/buffalo"
    bull_dict = read_file_to_dict(bull_f)

    local_cache_file = "../data/%s.cache" % _time
    if not os.path.exists(local_cache_file):
        lines_set = set()
    else:
        with open(local_cache_file) as tmp_file:
            lines = tmp_file.readlines()
            lines_set = set(lines)
    # try:

    if not os.path.exists(csv_f):
        with open(csv_f, "w") as file:
            file.write(
                "基金代号,基金名称,类型,公司,成立日期,基金经理,近1年夏普比率,近2年夏普比率,近3年夏普比率,近1年标准差,近2年标准差,近3年标准差,近1年最大回撤,近1周,近1月,近3月,近6月,今年以来,近1年,近两年,近三年,换手率,评级,金牛经理\n")
            # 解析所有代号的 夏普比率、标准差(波动率)

    # 解析所有代号的 夏普比率、标准差(波动率)
    info_url = "http://fundf10.eastmoney.com/tsdata_%s.html"

    # for k in fund_list:
    for k, v in fund_dict.items():

        if k + "\n" in lines_set:
            print("hit cache! 基金名称: %s, 基金代号 : %s, url:%s" % (v, k, info_url % k))
            continue
        else:
            crawl_max_draw_down(k)

        random_number = random.randint(0, 2)
        # time.sleep(random_number)

        print("crawl 基金名称: %s, 基金代号 : %s, url:%s" % (v, k, info_url % k))
        # self_dict, same_dict = rate_of_return(k)

        # 年度收益
        inc_dict = parse_income(k)

        # 夏普比率,标准差
        html = craw_tt_jj(info_url % k)

        _dict = parse_fund_info(html)

        # 计算是否是金牛基金经理
        # charge = _dict['fund_charge']
        # if charge in bull_dict:
        #     _dict['fund_charge_bull'] = bull_dict[charge]
        # else:
        res_bull = "是" if check_charge_is_bull(k) else "否"
        _dict['fund_charge_bull'] = res_bull
        # bull_dict[charge] = res_bull

        _volatility1 = _dict['volatility'][0]
        if "%" in _dict['volatility'][0]:
            _volatility1 = float(_dict['volatility'][0].replace("%", ""))

        _volatility2 = _dict['volatility'][1]
        if "%" in _dict['volatility'][1]:
            _volatility2 = float(_dict['volatility'][1].replace("%", ""))

        _volatility3 = _dict['volatility'][2]
        if "%" in _dict['volatility'][2]:
            _volatility3 = float(_dict['volatility'][2].replace("%", ""))

        max_draw = round(max_draw_down_count(k) * 100, 2)
        print("最大回撤", max_draw)
        with open(csv_f, "a") as file:
            # 计算最大回撤一年内
            file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
                k, v, _dict['fund_type'], _dict['fund_company'], _dict['fund_create_date'], _dict['fund_charge'],
                _dict['sharp'][0], _dict['sharp'][1], _dict['sharp'][2], _volatility1,
                _volatility2, _volatility3, max_draw, inc_dict['week'], inc_dict["month"], inc_dict["3month"],
                inc_dict["6month"],
                inc_dict["year"], inc_dict["1year"], inc_dict["2year"], inc_dict["3year"], inc_dict["change"],
                inc_dict["rate"], _dict['fund_charge_bull']))

        if 10 > random.randint(1, 100):
            time.sleep(1)

        lines_set.add(k)
        with open(local_cache_file, "a") as tmp_file:
            tmp_file.write(k + "\n")

            # break

    # write_dict_to_file(bull_f, bull_dict)
    # except Exception as e:
    #     print()
    #     print("Oops!", e.__class__, e)
    #     print()
    #
    # with open(local_cache_file, "w") as tmp_file:
    #     for line in lines_set:
    #
    #         if line.strip():
    #             tmp_file.write(line+"\n")

    # gen_es_data(f)
    # gen_csv_data()


def parse_income(code):
    """
    解析html中的 最近收益
    """

    info_url = "http://fund.eastmoney.com/%s.html" % code
    html = craw_tt_jj(info_url)

    info_dict = {}
    soup = BeautifulSoup(html, 'html.parser')

    items = soup.select("#increaseAmount_stage tr div.Rdata")

    info_dict["week"] = items[0].text.replace("%", "")
    info_dict["month"] = items[1].text.strip().replace("%", "")
    info_dict["3month"] = items[2].text.strip().replace("%", "")
    info_dict["6month"] = items[3].text.strip().replace("%", "")
    info_dict["year"] = items[4].text.strip().replace("%", "")
    info_dict["1year"] = items[5].text.strip().replace("%", "")
    info_dict["2year"] = items[6].text.strip().replace("%", "")
    info_dict["3year"] = items[7].text.strip().replace("%", "")

    items2 = soup.select("div.poptableWrap.jjhsl td")
    if len(items2) == 1:
        info_dict["change"] = "暂无数据"
    else:
        info_dict["change"] = "%s %s %s %s %s %s %s %s" % (
            items2[0].text if len(items2) > 0 else "",
            items2[1].text if len(items2) > 1 else "",
            items2[2].text if len(items2) > 2 else "",
            items2[3].text if len(items2) > 3 else "",
            items2[4].text if len(items2) > 4 else "",
            items2[5].text if len(items2) > 5 else "",
            items2[6].text if len(items2) > 6 else "",
            items2[7].text if len(items2) > 7 else "")

    info_dict["change"] = info_dict["change"].strip()

    info_dict["rate"] = str(soup.select("div.infoOfFund div")[-1]["class"][0].replace("jjpj", ""))
    if not info_dict['rate']:
        info_dict['rate'] = "0"
    return info_dict


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
