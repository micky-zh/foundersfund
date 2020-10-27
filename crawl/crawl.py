import requests;

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
    'Host': 'danjuanapp.com'
}


def crawl():
    r = requests.get('https://danjuanapp.com/djmodule/value-center?channel=1300100141', headers=headers)
    print(r.status_code)
    print(r.text)


crawl()
