import json
import os
from timeit import default_timer

import pymysql
import stringutils
from Logger import Logger

# host = "localhost"
# port = 3306
# db = "gerrit"
# user = "root"
# password = "123456"
from request import request_data

BASE_URL = "https://codereview.qt-project.org"
host = "cdb-er8xfzac.cd.tencentcdb.com"
port = 10174
db = "GERRIT"
user = "root"
password = "review123456"


def get_connection():
    conn = pymysql.connect(host=host, port=port, db=db, user=user, password=password)
    return conn


class UsingMysql(object):

    def __init__(self, commit=True, log_time=True, log_label='总用时'):
        """
        :param commit: 是否在最后提交事务(设置为False的时候方便单元测试)
        :param log_time:  是否打印程序运行总时间
        :param log_label:  自定义log的文字
        """
        self._log_time = log_time
        self._commit = commit
        self._log_label = log_label

    def __enter__(self):
        # 如果需要记录时间
        if self._log_time is True:
            self._start = default_timer()
        # 在进入的时候自动获取连接和cursor
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        conn.autocommit = False
        self._conn = conn
        self._cursor = cursor
        return self

    def __exit__(self, *exc_info):
        # 提交事务
        if self._commit:
            self._conn.commit()
        # 在退出的时候自动关闭连接和cursor
        self._cursor.close()
        self._conn.close()

        if self._log_time is True:
            diff = default_timer() - self._start
            print('-- %s: %.6f 秒' % (self._log_label, diff))

    @property
    def cursor(self):
        return self._cursor


# def check_it():
#     with UsingMysql(log_time=True) as um:
#         um.cursor.execute("select * from test")
#         data = um.cursor.fetchall()
#         print(type(data[0]))  # <class 'list'> <class 'dict'>
def create_table(cursor):
    '''
    新建表
    亲测branch 20不够长
    id100不够长
    '''
    sql = """
    CREATE TABLE if not exists `change_info`(
    `id` 	varchar(200) primary key not null,
    `project` 	varchar(50),
    `branch` 	varchar(50), 
    `change_id`	varchar(100),
    `subject`	blob,
    `status`	varchar(30),
    `created`	date,
    `updated`   date,
    `submitted`	date,
    `submitter_id`	varchar(30),
    `owner_id`  varchar(30),
    `insertions`	int,
    `deletions`	int,
    `total_comment_count`	int,
    `unresolved_comment_count`	int,
    `number`	int
    )ENGINE=InnoDB DEFAULT CHARSET=utf8;
    """
    cursor.execute(sql)
    sql = """
    CREATE TABLE if not exists `account_info`(
    `account_id` 	varchar(20) primary key not null,
    `name`			varchar(50),
    `username`		varchar(50),
    `email`			varchar(200)
    )ENGINE=InnoDB DEFAULT CHARSET=utf8;
    """
    cursor.execute(sql)
    sql = """
    CREATE TABLE if not exists `commit_relation`(
    `child`     varchar(50) not null,
    `parent`    varchar(50),
    PRIMARY KEY (`child`, `parent`)
    )ENGINE=InnoDB DEFAULT CHARSET=utf8;
    """
    cursor.execute(sql)
    sql = """
    CREATE TABLE if not exists `revision_info`(
    `id`    int primary key not null AUTO_INCREMENT,
    `project` 	varchar(50) ,
    `change_id`	varchar(200),
    `kind`		varchar(30),
    `number`	int,
    `created`   date,
    `uploader_id` varchar(20),
    `ref`       varchar(50),
    `commit_with_footers`   blob,
    `commit`    varchar(50)
    )ENGINE=InnoDB DEFAULT CHARSET=utf8;
    """
    cursor.execute(sql)
    sql = """
        CREATE TABLE if not exists `change_message_info`(
        `change_id`	varchar(200) not null,
        `id`		varchar(100),
        `author_id`	varchar(30),
        `real_author_id`	varchar(30),
        `date`   date,
        `message` blob,
        `revision_number`   int,
        `position`  int,
        `project`   varchar(50),
        PRIMARY KEY (`change_id`,`position`)
        )ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """
    cursor.execute(sql)
    sql = """
        CREATE TABLE if not exists `commit_info`(
        `commit`	varchar(100) primary key not null,
        `author_name`		varchar(50),
        `author_email`	varchar(200),
        `committer_name`	varchar(50),
        `committer_email`   varchar(200),
        `subject` blob,
        `message`   blob
        )ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """
    cursor.execute(sql)
    sql = """
        CREATE TABLE if not exists `file_info`(
        `project`	varchar(50),
        `commit`		varchar(100),
        `filename`	varchar(200),
        `status`	varchar(30),
        `binary`   tinyint(1),
        `old_path` varchar(200),
        `lines_inserted`    int,
        `lines_deleted`     int,
        `size_delta`        int,
        `size`              int,
        PRIMARY KEY (`commit`, `filename`)
        )ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """
    cursor.execute(sql)
    sql = """
        CREATE TABLE if not exists `comment_info`(
        `project`	varchar(50),
        `change_id`		varchar(200),
        `patch_set`	int,
        `id`	varchar(100) primary key not NULL,
        `path`   varchar(200),
        `side` varchar(50),
        `line`  int,
        `comment_range` blob,
        `in_reply_to`    varchar(100),
        `messaeg`     blob,
        `updated`     date,
        `author_id` int,
        `unresolved`    int,
        `commit`        varchar(100),
        `change_message_id` varchar(50) default NULL 
        )ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """
    cursor.execute(sql)


def create_database(cursor, db_name):
    '''新建数据库'''
    sql = f'create database if not exists {db_name};'
    cursor.execute(sql)


def select_one(cursor):
    cursor.execute("select * from test")
    data = cursor.fetchone()
    print("-- 单条记录: {0} ".format(data))


def select_one_by_name(cursor, name):
    sql = 'select * from test where username = %s'
    params = name
    cursor.execute(sql, params)
    data = cursor.fetchone()
    return data


# def update_by_pk(cursor, name, pk):
#     sql = "update test set username = '%s' where id = %d" % (name, pk)
#     cursor.execute(sql)


def create_one(table, ):
    with UsingMysql(log_time=True) as um:
        sql = "insert into {table}(id ,username) values(%s, %s)"
        params = ('6668', 'mxb')
        um.cursor.execute(sql, params)
        # 查看结果
        select_one(um.cursor)

def insert_one_by_one(table, data):
    with UsingMysql(log_time=False) as um:
        val = '%s, ' * (len(data[0]) - 1) + '%s'
        sql = f'insert into {table} values ({val})'
        for d in data:
            try:
                um.cursor.execute(sql, d)
            except Exception:
                continue

def insert_many(table, data):
    '''向全部字段插入数据'''
    if len(data) == 0:
        return
    try:
        with UsingMysql(log_time=False) as um:
            val = '%s, ' * (len(data[0]) - 1) + '%s'
            sql = f'insert into {table} values ({val})'
            if len(data) == 1:
                um.cursor.execute(sql, data[0])
            else:
                um.cursor.executemany(sql, data)
            um.cursor.connection.commit()
            Logger.logi("------database commit to " + table + "-----")
    except pymysql.err.DataError as e:
        # print(str(e))
        # print("--异常符号处理--")
        Logger.logi("--异常符号处理--\t" + table + "\t" + str(data))
        data_list = list(data)
        for d in data_list:
            d[1] = stringutils.delete_emoji(d[1])
            d[3] = stringutils.delete_emoji(d[3])
        insert_many(table, data)
    except Exception as e:
        print(str(e))
        Logger.loge(str(e))
        Logger.loge("instert:\t" + table + "\t" + str(data))
        insert_one_by_one(table, data)
        # with UsingMysql(log_time=False) as um:
        #     for d in data:
        #         um.cursor.execute(sql, d)

# def data_update():
#     with UsingMysql(log_time=True) as um:
#         # 查找一条记录
#         data = select_one_by_name(um.cursor, "mxb")
#         pk = data['id']
#         print('--- 商品{0}: '.format(data))
#         # 修改名字
#         new_name = '单肩包'
#         update_by_pk(um.cursor, new_name, pk)


if __name__ == '__main__':

    # data = [(1,"mxb","1514","daw"),(2,"sgj","dsa","555")]
    # with UsingMysql(log_time=True) as um:
    #     insert_many("test",data)
    # print(type(data))
    # print(type(data[0]))
    # with UsingMysql(log_time=True) as um:
    #     create_table(um.cursor)
    changes_file = os.path.abspath(os.path.dirname(__file__)) + os.sep + "changes"
    changeids = []
    if os.path.isfile(changes_file):
        f = open(changes_file, 'r', encoding='utf-8')
        line = f.readline()
        while line:
            changeids += [line]
            line = f.readline()
        f.close()
        print(changeids[0])
    else:
        url = BASE_URL + "/changes/"
        r = request_data(url)
        content = r.text[5:]
        json_object = json.loads(content)
        for obj in json_object:
            changeids.append(obj["id"])
        while "_more_changes" in json_object[-1].keys() and json_object[-1]["_more_changes"] == True:
            url = BASE_URL + "/changes/" + "?S=" + str(len(changeids))
            r = request_data(url)
            content = r.text[5:]
            json_object = json.loads(content)
            for obj in json_object:
                changeids.append(obj["id"])
        with open(os.path.abspath(os.path.dirname(__file__)) + os.sep + "changes", 'w+', encoding='utf-8') as f:
            for changeid in changeids:
                f.write(changeid + "\n")


    # data = [['6ae52a53d1ddd4823f413c996beb312d6688204c', '😎 Mostafa Emami', 'mostafa.emami@outlook.com', '😎 Mostafa Emami', 'mostafa.emami@outlook.com', 'Enable directload mood for general usage', 'Enable directload mood for general usage\n\n- Setup p2p dbus to get the configuration\n- Load app defined startup plugins before\n  attempt to load the ones defined in configuration\n\nChange-Id: Iffc4546fbae59a3593cec673466f5951ce761709\n']]# insert_many("commit_info", data)
    #
    # for d in data:
    #     print(d[1])
    # insert_many("commit_info", data)
    # print(ord('*'))

