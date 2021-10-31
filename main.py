import json
from tqdm import tqdm
import requests
import database

BASE_URL = "https://codereview.qt-project.org"


def request_data(url):
    # print("Now request:" + url)
    req = requests.get(url)
    return req


def get_commentinfo(project, changeID):
    project.replace("/", "%")
    url = BASE_URL + "/changes/qt%2Fqtlocation~dev~I39e9d9a97d65af7daf2dca30a00d563b2bf6aa80/comments"
    r = request_data(url)
    # project = "qt/2Fqtlocation"
    # changeid = "qt%2Fqtlocation~dev~I39e9d9a97d65af7daf2dca30a00d563b2bf6aa80"
    content = r.text[5:]
    json_str = json.loads(content)
    # print(type(json_str))
    # print(type(json_str["/COMMIT_MSG"]))
    for data in json_str["/COMMIT_MSG"]:
        id = data["id"]
        patch_set = data["patch_set"]
        update = data["updated"]
        message = data["message"]
        author_id = data["author"]["_account_id"]
        line = data["line"]
        # print(type(data["unresolved"]))
        unresolved = 1 if data["unresolved"] == True else 0


def get_changeinfo(changeId):

    url = BASE_URL + "/changes/" + changeId + "?o=DETAILED_LABELS&o=ALL_REVISIONS&o=ALL_COMMITS&o=ALL_FILES&o=DETAILED_ACCOUNTS&o=REVIEWER_UPDATES&o=MESSAGES&o=CURRENT_ACTIONS&o=CHANGE_ACTIONS&o=REVIEWED&o=COMMIT_FOOTERS"
    # changeID = "qt%2Fqtdeclarative~dev~I155826a52090c5b13d14be6330813dc5a27f28e5"
    r = request_data(url)
    # print(r.text)
    str = r.text[5:]
    # print(str)
    json_object = json.loads(str)
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
    return data


if __name__ == '__main__':
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
    data = []
    t = tqdm(range(len(changeids[:10])), ncols=80)
    for i in t:
        tqdm.write("Collecting:" + changeids[i], end="")
        data += get_changeinfo(changeids[i])
        if i % 1000 == 0:
            database.insert_many("change_id", data)
            data.clear()
    t.close()
    database.insert_many("change_id", data)


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
