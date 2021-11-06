import json
from tqdm import tqdm
import database
from request import request_data

BASE_URL = "https://codereview.qt-project.org"


def get_commentinfo(changeID):
    url = BASE_URL + "/changes/" + changeID + "?o=DETAILED_LABELS&o=ALL_REVISIONS&o=ALL_COMMITS&o=ALL_FILES&o=DETAILED_ACCOUNTS&o=REVIEWER_UPDATES&o=MESSAGES&o=CURRENT_ACTIONS&o=CHANGE_ACTIONS&o=REVIEWED&o=COMMIT_FOOTERS"
    r = request_data(url)
    content = r.text[5:]
    json_object = json.loads(content)
    project = json_object["project"]
    current_revision = json_object["current_revision"]
    url = BASE_URL + "/changes/" + changeID + "/revisions/" + current_revision + "/commit"
    r = request_data(url)
    content = r.text[5:]
    json_object = json.loads(content)
    commit = json_object["commit"]
    parent = json_object["parents"][0]["commit"]
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
            side = "REVISION" if "side" not in data.keys() else data["side"]
            line = None if "line" not in data.keys() else data["line"]
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
            change_message_id = None
            comment_info += [(project, changeID, patch_set, id, path, side, parent, line, range_str, in_reply_to,
                              message, updated, author_id, unresolved, commit, change_message_id)]
    return comment_info


def get_changeinfo(changeId):
    url = BASE_URL + "/changes/" + changeId + "?o=DETAILED_LABELS&o=ALL_REVISIONS&o=ALL_COMMITS&o=ALL_FILES&o=DETAILED_ACCOUNTS&o=REVIEWER_UPDATES&o=MESSAGES&o=CURRENT_ACTIONS&o=CHANGE_ACTIONS&o=REVIEWED&o=COMMIT_FOOTERS"
    r = request_data(url)
    contnet = r.text[5:]
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
    message = get_change_message(id, json_object["messages"], project)
    # message = []
    revisions, commit_relation, commit_info, file_info = get_revisions_info(id, json_object["revisions"], project)

    return data, revisions, commit_relation, commit_info, message, file_info


def get_change_message(changeid, messages, project):
    ret = []
    for index in range(len(messages)):
        id = messages[index]["id"]
        author_id = messages[index]["author"]["_account_id"]
        real_author_id = messages[index]["real_author"]["_account_id"]
        date = messages[index]["date"]
        message = messages[index]["message"]
        revision_number = messages[index]["_revision_number"]
        position = index
        ret += [(changeid, id, author_id, real_author_id, date, message, revision_number, position, project)]
    return ret


def get_revisions_info(changeid, revisions, project):
    # print(type(reversions))
    ret = []
    commit_relation = []
    commit_infos = []
    file_infos = []
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

        commit, parents, author_name, author_email, committer_name, committer_email, subject, message = get_commit(
            changeid, revision_id)
        file_infos = get_file(changeid,revision_id)
        ret += [
            (None, project, changeid, kind, number, created, uploader_id, ref, commit_with_footers, commit)]  # 自增主码
        for parent in parents:
            commit_relation += [(commit, parent)]
            # print(commit, "-" , parent)
        commit_infos += [(commit, author_name, author_email, committer_name, committer_email, subject, message)]
        for i in range(len(file_infos)):
            file_infos[i] = ((project, commit) + file_infos[i])
        # [(project, commit, filename, status, binary, old_path, lines_inserted, lines_deleted, size_delta, size)]
    return ret, commit_relation, commit_infos, file_infos


def get_commit(changeid, revision_id):
    commit_url = BASE_URL + "/changes/" + changeid + "/revisions/" + revision_id + "/commit"
    r = request_data(commit_url)
    commit_contnet = r.text[5:]
    # print("content:" + contnet)
    try:
        json_commit = json.loads(commit_contnet)
    except Exception:
        print("\ncontent:" + commit_contnet)
        return None
    commit = json_commit["commit"]
    # parent = json_commit["parents"][0]["commit"]
    parents = []
    for i in range(len(json_commit["parents"])):
        parents += [(json_commit["parents"][i]["commit"])]
    author_name = json_commit["author"]["name"]
    author_email = json_commit["author"]["email"]
    committer_name = json_commit["author"]["name"]
    committer_email = json_commit["author"]["email"]
    subject = json_commit["subject"]
    message = json_commit["message"]
    return commit, parents, author_name, author_email, committer_name, committer_email, subject, message


def get_file(changeid, revision_id):
    file_url = BASE_URL + "/changes/" + changeid + "/revisions/" + revision_id + "/files"
    # print(file_url)
    r = request_data(file_url)
    file_contnet = r.text[5:]
    json_file = json.loads(file_contnet)
    ret = []
    list_file_values = [i for i in json_file.values()]
    list_file_keys = [i for i in json_file.keys()]
    status = "M" if "status" not in list_file_values[0].keys() else list_file_values[0]["status"]
    binary = False if "binary" not in list_file_values[0].keys() else list_file_values[0]["binary"]
    old_path = None if "old_path" not in list_file_values[0].keys() else list_file_values[0]["old_path"]
    for i in range(1, len(list_file_keys)):
        filename = list_file_keys[i]
        lines_inserted = 0 if "lines_inserted" not in list_file_values[i].keys() else list_file_values[i][
            "lines_inserted"]
        lines_deleted = 0 if "lines_deleted" not in list_file_values[i].keys() else list_file_values[i]["lines_deleted"]
        size_delta = list_file_values[i]["size_delta"]
        size = list_file_values[i]["size"]
        ret += [(filename, status, binary, old_path, lines_inserted, lines_deleted, size_delta, size)]
    return ret


if __name__ == '__main__':
    url = BASE_URL + "/changes/"
    r = request_data(url)
    content = r.text[5:]
    json_object = json.loads(content)
    changeids = []
    for obj in json_object:
        changeids.append(obj["id"])
    # while "_more_changes" in json_object[-1].keys() and json_object[-1]["_more_changes"] == True:
    #     url = BASE_URL + "/changes/" + "?S=" + str(len(changeids))
    #     r = request_data(url)
    #     content = r.text[5:]
    #     json_object = json.loads(content)
    #     for obj in json_object:
    #         changeids.append(obj["id"])
    print("Changes Sum : ", len(changeids))
    change_datas = []
    revision_infos = []
    commit_relations = []
    change_messages = []
    commit_infos = []
    file_infos = []
    comment_infos = []
    t = tqdm(range(len(changeids[:20])), ncols=80)
    for i in t:
        tqdm.write("Collecting:" + changeids[i], end="")
        change_data, revision_info, commit_relation, commit_info, change_message, file_info = get_changeinfo(
            changeids[i])
        comment_infos += get_commentinfo(changeids[i])

        change_datas += change_data
        revision_infos += revision_info
        commit_relations += commit_relation
        change_messages += change_message
        commit_infos += commit_info
        file_infos += file_info
        if i > 0 and i % 200 == 0:
            database.insert_many("change_info", change_datas)
            change_datas.clear()
        if i > 0 and i % 50 == 0:
            database.insert_many("revision_info", revision_infos)
            revision_infos.clear()
        if i > 0 and i % 10 == 0:
            database.insert_many("commit_relation", commit_relations)
            commit_relations.clear()
        if i > 0 and i % 150 == 0:
            database.insert_many("change_message_info", change_messages)
            change_messages.clear()
        if i > 0 and i % 5 == 0:
            database.insert_many("commit_info", commit_infos)
            commit_infos.clear()
        if i > 0 and i % 5 == 0:
            database.insert_many("file_info", file_infos)
            file_infos.clear()
        if i > 0 and i % 5 == 0:
            database.insert_many("comment_info", comment_infos)
            commit_infos.clear()
    database.insert_many("change_info", change_datas)
    database.insert_many("revision_info", revision_infos)
    database.insert_many("commit_relation", commit_relations)
    database.insert_many("change_message_info", change_messages)
    database.insert_many("commit_info", commit_infos)
    database.insert_many("file_info", file_infos)
    database.insert_many("comment_info", comment_infos)
    t.close()

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
