import json
from tqdm import tqdm
import requests
import database

BASE_URL = "https://codereview.qt-project.org"


def request_data(url):
    # print("Now request:" + url)
    s = requests.session()
    s.keep_alive = False
    req = requests.get(url)
    return req


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


def get_commentinfo(project, changeID):
    url = BASE_URL + "/changes/" + changeID + "?o=DETAILED_LABELS&o=ALL_REVISIONS&o=ALL_COMMITS&o=ALL_FILES&o=DETAILED_ACCOUNTS&o=REVIEWER_UPDATES&o=MESSAGES&o=CURRENT_ACTIONS&o=CHANGE_ACTIONS&o=REVIEWED&o=COMMIT_FOOTERS"
    r = request_data(url)
    content = r.text[5:]
    json_object = json.loads(content)
    current_revision = json_object["current_revision"]
    url = BASE_URL + "/changes/" + changeID + "/revisions/" + current_revision + "/commit"
    r = request_data(url)
    content = r.text[5:]
    json_object = json.loads(content)
    commit = json_object["commit"]
    parent = json_object["parents"]["commit"]
    url = BASE_URL + "/changes/" + changeID + "/comments"
    r = request_data(url)
    content = r.text[5:]
    json_object = json.loads(content)
    # print(type(json_object))
    comment_info = []
    for file in json_object.keys():
        for data in json_object[file]:
            patch_set = data["patch_set"]
            id = data["id"]
            path = file
            side = data["side"]
            line = data["line"]
            if "range" in json_object.keys():
                range_str = "range:" + data["range"]
            else:
                range_str = None
            if "in_reply_to" in json_object.keys():
                in_reply_to = data["in_reply_to"]
            else:
                in_reply_to = None
            message = data["message"]
            updated = data["updated"]
            author_id = data["author"]["_account_id"]
            unresolved = 1 if data["unresolved"] == True else 0
            comment_info += [(project, changeID, patch_set, id, path, side, parent, line, range_str, in_reply_to,
                              message, updated, author_id, unresolved, commit)]
    return comment_info
    # print(type(json_str["/COMMIT_MSG"]))
    # for data in json_object:
    # id = data["id"]
    # patch_set = data["patch_set"]
    # update = data["updated"]
    # message = data["message"]
    # author_id = data["author"]["_account_id"]
    # line = data["line"]
    # # print(type(data["unresolved"]))
    # unresolved = 1 if data["unresolved"] == True else 0


def get_changeinfo(changeId):
    url = BASE_URL + "/changes/" + changeId + "?o=DETAILED_LABELS&o=ALL_REVISIONS&o=ALL_COMMITS&o=ALL_FILES&o=DETAILED_ACCOUNTS&o=REVIEWER_UPDATES&o=MESSAGES&o=CURRENT_ACTIONS&o=CHANGE_ACTIONS&o=REVIEWED&o=COMMIT_FOOTERS"
    # changeID = "qt%2Fqtdeclarative~dev~I155826a52090c5b13d14be6330813dc5a27f28e5"
    r = request_data(url)
    # print(r.text)
    contnet = r.text[5:]
    # print(str)
    json_object = json.loads(contnet)
    id = json_object["id"]
    project = json_object["project"]
    branch = json_object["branch"]
    changeid = json_object["change_id"]
    subject = json_object["subject"]
    status = json_object["status"]
    created = json_object["created"]
    updated = json_object["updated"]
    if "submitted" in json_object.keys():
        submitted = json_object["submitted"]
        submitter_id = json_object["submitter"]["_account_id"]
    else:
        submitted = None
        submitter_id = None
    owner_id = json_object["owner"]["_account_id"]
    insertions = json_object["insertions"]
    deletions = json_object["deletions"]
    total_comment_count = json_object["total_comment_count"]
    unresolved_comment_count = json_object["unresolved_comment_count"]
    number = json_object["_number"]
    data = [(id, project, branch, changeid, subject, status, created, updated, submitted, submitter_id, owner_id,
             insertions, deletions, total_comment_count, unresolved_comment_count, number)]
    # print(type(data[0]))
    message = get_change_message(changeid, json_object["messages"], project)
    revisions, commit_relation = get_revisions_info(changeid, json_object["revisions"], project)

    return data, revisions, commit_relation, message


def get_change_message(changeid, messages, project):
    """
        没找到position在哪
    """
    # print(messages)
    json_mess = json.loads(messages)
    # changeId = changeid
    id = json_mess["id"]
    author_id = json_mess["author"]["_account_id"]
    real_author_id = json_mess["real_author"]["_account_id"]
    date = json_mess["date"]
    message = json_mess["message"]
    revision_number = json_mess["_revision_number"]
    return [(changeid, id, author_id, real_author_id, date, message, revision_number, project)]


def get_revisions_info(changeid, revisions, project):
    # print(type(reversions))
    ret = []
    commit_relation = []
    for revision_id in revisions.keys():
        kind = revisions[revision_id]["kind"]
        number = revisions[revision_id]["_number"]
        created = revisions[revision_id]["created"]
        uploader_id = revisions[revision_id]["uploader"]["_account_id"]
        ref = revisions[revision_id]["ref"]
        if "commit_with_footers" in revisions[revision_id].keys():
            commit_with_footers = revisions[revision_id]["commit_with_footers"]
        else:
            commit_with_footers = None

        url = BASE_URL + "/changes/" + changeid + "/revisions/" + revision_id + "/commit"
        r = request_data(url)
        contnet = r.text[5:]
        json_object = json.loads(contnet)
        commit = json_object["commit"]
        parent = json_object["parents"][0]["commit"]
        ret += [(project, changeid, kind, number, created, uploader_id, ref, commit_with_footers, commit)]
        commit_relation += [(commit, parent)]
    return ret, commit_relation


if __name__ == '__main__':
    # data, revisions, commit_relations = get_changeinfo(
    #     "qt%2Fqtdeclarative~dev~I155826a52090c5b13d14be6330813dc5a27f28e5")
    # print(commit_relations)
    # print(revisions)
    # get_commentinfo("666", "qt%2Fqtdeclarative~dev~I155826a52090c5b13d14be6330813dc5a27f28e5")
    # accounts = get_account_info()
    # print(type(accounts))
    # print(accounts[:10])
    # t = tqdm(range(len(accounts)), ncols=80)
    # cot = 0
    # for i in t:
    #     if i > 0 and i % 100 == 0:
    #         database.insert_many("account_info", accounts[cot:i])
    #         cot += 100
    # database.insert_many("account_info", accounts[cot:])

    url = BASE_URL + "/changes/"
    r = request_data(url)
    content = r.text[5:]
    json_object = json.loads(content)
    changeids = []
    for obj in json_object:
        changeids.append(obj["id"])
    while "_more_changes" in json_object[-1].keys() and json_object[-1]["_more_changes"] == True:
        url = BASE_URL + "/changes/" + "?S=" + str(len(changeids))
        r = request_data(url)
        content = r.text[5:]
        json_object = json.loads(content)
        for obj in json_object:
            changeids.append(obj["id"])
    print(len(changeids))
    change_datas = []
    revision_infos = []
    commit_relations = []
    change_messages = []
    t = tqdm(range(len(changeids[:10])), ncols=80)
    for i in t:
        tqdm.write("Collecting:" + changeids[i], end="")
        change_data, revision_info, commit_relation, change_message = get_revisions_info(changeids[i])
        change_datas += change_data
        revision_infos += revision_info
        commit_relations += commit_relation
        change_messages += change_message
        if i > 0 and i % 1000 == 0:
            database.insert_many("change_id", change_data)
            change_data.clear()
        if i > 0 and i % 100 == 0:
            database.insert_many("revision_info", revision_infos)

    t.close()
    database.insert_many("change_id", change_data)

    # for change in changeids:
    #     data += get_changeinfo(change)
    # print(data)
    # data = get_changeinfo("qt%2Fqtdeclarative~dev~I155826a52090c5b13d14be6330813dc5a27f28e5")
    # print(data)
    # database.insert_many("change_id", data)
    # data += get_changeinfo("qt%2Fqtbase~dev~I7a091fc967bd6b9d18ac2de39db16e3b4b9a76ea")
    # print(data)
    # with database.UsingMysql(log_time=True) as um:
    #     database.insert_many("change_id", data)
