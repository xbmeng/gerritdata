import json

from tqdm import tqdm

import database
from request import request_data

BASE_URL = "https://codereview.qt-project.org"


def get_account_info():
    url = BASE_URL + "/accounts/?o=DETAILS&q=is:active"
    r = request_data(url)
    content = r.text[5:]
    json_object = json.loads(content)
    accounts = []
    for obj in json_object:
        if "name" in obj.keys():
            if "username" in obj.keys():
                if "email" in obj.keys():
                    accounts += [(obj["_account_id"], obj["name"], obj["username"], obj["email"])]
                else:
                    accounts += [(obj["_account_id"], obj["name"], obj["username"], None)]
            else:
                accounts += [(obj["_account_id"], obj["name"], None, None)]
        else:
            accounts += [(obj["_account_id"], None, None, None)]
    while "_more_accounts" in json_object[-1].keys() and json_object[-1]["_more_accounts"] == True:
        url = BASE_URL + "/accounts/?o=DETAILS&q=is:active" + "&S=" + str(len(accounts))
        r = request_data(url)
        content = r.text[5:]
        if content == "[]":
            break
        json_object = json.loads(content)
        for obj in json_object:
            if "name" in obj.keys():
                if "username" in obj.keys():
                    if "email" in obj.keys():
                        accounts += [(obj["_account_id"], obj["name"], obj["username"], obj["email"])]
                    else:
                        accounts += [(obj["_account_id"], obj["name"], obj["username"], None)]
                else:
                    accounts += [(obj["_account_id"], obj["name"], None, None)]
            else:
                accounts += [(obj["_account_id"], None, None, None)]
        # print(len(accounts))
    return accounts


if __name__ == '__main__':
    accounts = get_account_info()
    print(type(accounts))
    print(accounts[:10])
    t = tqdm(range(len(accounts)), ncols=80)
    cot = 0
    for i in t:
        if i > 0 and i % 100 == 0:
            database.insert_many("account_info", accounts[cot:i])
            cot += 100
    database.insert_many("account_info", accounts[cot:])
