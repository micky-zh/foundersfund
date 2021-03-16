import json

import requests

_headers = {
    'Content-Type': 'application/json',
    'charset': 'UTF-8'
}


def delete_index():
    rsp = requests.delete("http://127.0.0.1:9200/fund_analysis")
    # rsp.raise_for_status()
    print(rsp.text)


def create_index():
    rsp = requests.put("http://127.0.0.1:9200/fund_analysis")
    rsp.raise_for_status()
    print(rsp.text)


def put_template():
    _str = open('../es/fund-template.json', 'r').read()
    rsp = requests.put("http://127.0.0.1:9200/_template/fund_template", data=_str, headers=_headers)
    rsp.raise_for_status()
    print(rsp.text)


def gen_csv_data(sharp_min=1, wave_min=0, wave_max=10, max_draw_down=10, top=20):
    rs = search(sharp_min, wave_min, wave_max, max_draw_down, top)
    _dict = json.loads(rs)

    f = "../data/result.csv"
    with open(f, "w") as file:
        file.write("基金代号,基金名称,类型,公司,成立日期,基金经理,近1年夏普比率,近2年夏普比率,近3年夏普比率,近1年标准差,近2年标准差,近3年标准差,近1年最大回撤\n")
        for big_item in _dict['aggregations']['kind']['buckets']:
            for item in big_item['top_sales_hits']['hits']['hits']:
                file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (item["_source"]['id'],
                                                                         item["_source"]['name'],
                                                                         item["_source"]['kind'],
                                                                         item["_source"]['company'],
                                                                         item["_source"]['created'],
                                                                         item["_source"]['manager'],
                                                                         item["_source"]['sharp1'],
                                                                         item["_source"]['sharp2'],
                                                                         item["_source"]['sharp3'],
                                                                         item["_source"]['wave1'],
                                                                         item["_source"]['wave2'],
                                                                         item["_source"]['wave3'],
                                                                         item["_source"].get('max_draw_down', 0)
                                                                         )
                           )


def search(sharp_min=1, wave_min=0, wave_max=10, max_draw_down=10, top=50):

    _str1 = '{"size":0,"query":{"bool":{"must":[{"range":{"created":{"lt":"2020-03-13"}}}' \
            ',{"range":{"sharp1":{"gt":%f}}},{"range":{"wave1":{"lte":%f,"gt":%f}}}' \
            ',{"range":{"max_draw_down":{"lte":%f,"gt":0}}}]}},' \
            '"aggs":{"kind":{"terms":{"field":"kind","size":100},"aggs":{"top_sales_hits":' \
            '{"top_hits":{"sort":[{"sharp1":{"order":"desc"}},{"wave1":{"order":"asc"}},' \
            '{"max_draw_down":{"order":"asc"}}],"size":%d}}}}}}' % (sharp_min, wave_max, wave_min, max_draw_down, top)

    rsp = requests.post("http://127.0.0.1:9200/fund_analysis/_search", data=_str1, headers=_headers)
    rsp.raise_for_status()
    print(rsp.text)
    return rsp.text


def bulk_insert(f_name):
    with open('data.json', 'w') as the_file:
        # the_file.write('Hello\n')

        with open(f_name) as file_in:
            counter = 0
            for line in file_in:
                counter += 1
                if counter == 1:
                    continue

                _arr = line.strip("\n").split(",")

                sharp1 = _arr[6] if "--" not in _arr[6] else 0
                sharp2 = _arr[7] if "--" not in _arr[7] else 0
                sharp3 = _arr[8] if "--" not in _arr[8] else 0

                wave1 = _arr[9] if "--" not in _arr[9] else 0
                wave2 = _arr[10] if "--" not in _arr[10] else 0
                wave3 = _arr[11] if "--" not in _arr[11] else 0

                max_draw_down = _arr[12] if "--" not in _arr[12] else 0

                _info = {"index": {"_index": "fund_analysis", "_id": _arr[0]}}
                _data = {"id": _arr[0], "name": _arr[1], "kind": _arr[2], "company": _arr[3], "created": _arr[4],
                         "manager": _arr[5], "sharp1": sharp1, "sharp2": sharp2,
                         "sharp3": sharp3, "wave1": wave1, "wave2": wave2, "wave3": wave3,
                         "max_draw_down": max_draw_down}

                # json.dump(_info, the_file)
                # json.dump(_data, the_file)

                the_file.write(json.dumps(_info) + "\n")
                the_file.write(json.dumps(_data, ensure_ascii=False) + "\n")

    _str = open('data.json', 'r').read()
    rsp = requests.post("http://127.0.0.1:9200/fund_analysis/_bulk", data=_str.encode("utf-8"), headers=_headers)
    rsp.raise_for_status()
    print(rsp.text)


def gen_es_data(f):
    put_template()
    delete_index()
    create_index()
    # bulk_insert("../data/2021-03-13.csv")
    bulk_insert(f)


if __name__ == "__main__":
    # gen_data()
    gen_csv_data(sharp_min=2, wave_min=5, wave_max=20, max_draw_down=10, top=50)
