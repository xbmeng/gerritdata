import os
import time


class Logger:

    @staticmethod
    def logi(content):
        f = open(os.path.abspath(os.path.dirname(__file__)) + os.sep + "fetch.log", "a+", encoding='utf-8')
        # 写入文件
        f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) + "\tINFO\t" + content + "\n")

    @staticmethod
    def loge(content):
        f = open(os.path.abspath(os.path.dirname(__file__)) + os.sep + "fetch.log", "a+", encoding='utf-8')
        # 写入文件
        f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) + "\tERROR\t" + content + "\n")
