# -*- coding:utf-8 -*-
"""
neteasytick下载
filename : jqdata_api.py
createtime : 2020/10/24 8:14
author : Demon Finch
"""
import os
import sys
import requests
from time import sleep
from datetime import datetime
from multiprocessing.pool import ThreadPool
from func_timeout import FunctionTimedOut, func_timeout
from some_tool import stocklist_method, if_trade, stock_a_hour, trd_hour_end_afternoon
import json


def get_stock_batch(params):
    return _session.get(stock_api + params + ',money.api',
                        headers={"Accept-Encoding": "gzip, deflate, sdch",
                                 "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                                "(KHTML, like Gecko) Chrome/54.0.2840.100 "
                                                "Safari/537.36")}
                        )


def get_stocks_by_range(params):
    try:
        r = func_timeout(timeout, get_stock_batch, args=(params,))
        return r.text
    except FunctionTimedOut:
        print("batch timeout,localtime:%s" % datetime.now())
        return ''
    except Exception as e:
        print("something wrong,tell author please\n", e)
        return ''


def tick_dl(if_thread=False):
    if if_thread:
        pool = ThreadPool(threadcnt)
        try:
            res = pool.map(get_stocks_by_range, stocklist)
        finally:
            pool.close()
        return [d.lstrip("_ntes_quote_callback(").rstrip(");") for d in res if d is not None]
    else:
        return [get_stocks_by_range(param) for param in stocklist]


def formatdata(rep_data):
    """
    将取得的数据格式化为list字典格式方便插入数据库
    :param rep_data: 取得的数据
    :return: 格式化好的数据库
    """
    stock_dict = []
    for repi in rep_data:
        if repi is not None and repi != "":
            for stockidats in json.loads(repi).values():
                # stockidats["time"] = datetime.strptime(stockidats["time"], "%Y/%m/%d %H:%M:%S")
                if len(stockidats.keys()) > 30:
                    stock_dict.append(stockidats)
    return stock_dict


_session = requests.session()

stock_api = "http://api.money.126.net/data/feed/"

max_num = 800  # 单批次股票数
stocklist, stocklist_split = stocklist_method(max_num, if_neteasy=True)  # 获取股票清单
stocklist = [stocki.replace("sz", "1").replace("sh", "0") for stocki in stocklist]
timeout = 1.0  # 单线程超时时间
threadcnt = min(4, len(stocklist))  # 最大线程数为股票的划分数

clname = ('code', 'time', 'name', 'percent', 'price', 'open', 'high', 'low',
          'ask1', 'ask2', 'ask3', 'ask4', 'ask5', 'askvol1', 'askvol2', 'askvol3', 'askvol4', 'askvol5',
          'bid1', 'bid2', 'bid3', 'bid4', 'bid5', 'bidvol1', 'bidvol2', 'bidvol3', 'bidvol4', 'bidvol5',
          'updown', 'type', 'status', 'symbol', 'update', 'volume', 'arrow', 'yestclose', 'turnover',)

if __name__ == '__main__':
    print("开始运行，localtime: %s" % datetime.now())

    # 判断交易日历
    if if_trade():
        print("%s 交易日,运行程序" % datetime.now().date())
    else:
        print("%s 非交易日,退出" % datetime.now().date())
        sys.exit(0)

    stktime = {stki: datetime.now() for stki in stocklist_split}  # 用于时间去重的字典生成式
    today_csvname = "%s-neteasycsvtick.csv" % datetime.now().date()
    today_zipname = "%s-neteasycsvtick.7z" % datetime.now().date()
    todaycsvpath = os.path.join(os.path.dirname(__file__), today_csvname)  # csv文件名称
    todayzippath = os.path.join(os.path.dirname(__file__), today_zipname)  # 压缩文件名称

    if not os.path.exists(todaycsvpath):
        # 如果没有这个文件，则创建这个文件并写入列名
        with open(todaycsvpath, mode='w') as file_today:
            file_today.writelines(",".join(clname))
            file_today.write("\n")
            file_today.close()

    while True:
        t1 = datetime.now()
        if stock_a_hour(t1.timestamp()):  # 判断A股时间段
            try:
                stkdata = formatdata(tick_dl(if_thread=True))
                t2 = datetime.now()
                with open(todaycsvpath, mode='a') as file_today:  # 打开文件
                    writecnt = 0
                    for stki in stkdata:
                        datanowtime = datetime.strptime(stki["time"], "%Y/%m/%d %H:%M:%S")
                        if datanowtime > stktime[stki['code']]:
                            # 写入文件
                            file_today.writelines(",".join([str(stki[keysel]) for keysel in clname]))
                            file_today.write("\n")
                            stktime[stki['code']] = datanowtime
                            writecnt += 1
                    file_today.close()
                t4 = datetime.now()
                print(f"localtime: {t4} alltime:{t4 - t1} tocsvtime:{t4 - t2}  downloadtime:{t2 - t1} ")
            except Exception as erre:
                print(erre)
        elif datetime.now().timestamp() > trd_hour_end_afternoon:  # 下午3：02退出循环
            print("download complete -> %s" % todaycsvpath)
            break
        else:
            print("relax 10s , localtime: %s" % datetime.now())  # 未退出前休息
            sleep(10)

    print("运行结束：%s" % datetime.now())
    print("\n\n-----------------------------------------\n\n")

    """
    linux 后台运行命令：
    nohup /root/miniconda3/envs/finance/bin/python -u /root/easyqd/new_get_qq.py >/root/easyqd/qq.log 2>&1 &
    """
