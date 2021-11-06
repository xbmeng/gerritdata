import requests

from Logger import Logger


def request_data(url):
    Logger.logi("request:\t" + url)
    s = requests.session()
    s.keep_alive = False
    try:
        req = requests.get(url)
    except Exception:
        print("发送Request发生异常")
        print("url" + url)
    return req
