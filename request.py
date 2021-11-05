import requests


def request_data(url):
    # print("Now request:" + url)
    s = requests.session()
    s.keep_alive = False
    try:
        req = requests.get(url)
    except Exception:
        print("发送Request发生异常")
        print("url" + url)
    return req

