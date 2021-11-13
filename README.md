# gerritdata
获取Gerrit的数据，目前是qt项目的数据，链接: [QT Code Review](https://codereview.qt-project.org/)。
## 运行方法
### change相关的信息
首次运行请运行database.py，填写数据库信息，运行：
```python
with UsingMysql(log_time=True) as um:
    create_table(um.cursor)
```
除了QT的其他项目在changes.py更换BASE_URL
运行changes.py
### account相关的信息
运行account.py
## 异常处理
如果发生异常导致退出，可以在changes.py第229行指定从哪个继续获取，从25的倍数重新开始获取即可。
例如执行第1140个change发生了异常，继续从第1125个开始获取即可。
也可以从文档中查看异常数据，进行手动处理。
