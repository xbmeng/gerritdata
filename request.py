import time

import requests

from Logger import Logger


def request_data(url):
    Logger.logi("request:\t" + url)
    s = requests.session()
    s.keep_alive = False
    try:
        req = requests.get(url, timeout=5)
        if req.status_code is not requests.codes.ok:
            print(req.status_code)
    except Exception as e:
        print("\n发送Request发生异常")
        print("url:" + url)
        Logger.loge(str(e))
        Logger.loge("发送Request发生异常:\t" + url)
        # print(req.status_code)
        time.sleep(5)
        req = request_data(url)
    return req
