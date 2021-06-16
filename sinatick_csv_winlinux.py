# -*- coding:utf-8 -*-
"""
sinatick下载
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


def get_stock_batch(params):
    return _session.get(stock_api + params,
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
        return [d for d in res if d is not None]
    else:
        return [get_stocks_by_range(param) for param in stocklist]


def formatdata(rep_data):
    """
    将取得的数据格式化为list字典格式方便插入数据库
    :param rep_data: 取得的数据
    :return: 格式化好的数据库
    """
    stocks_detail = "".join(rep_data).split(";")
    stock_list = list()
    for stocki in stocks_detail:
        stock = stocki.split(",")
        if len(stock) <= 30:
            continue
        stockcodenam = stock[0].split("=")
        stock_list.append(
            (stockcodenam[0][-8:], stockcodenam[1].replace('"', ''), stock[1], stock[2], stock[3], stock[4], stock[5],
             stock[6], stock[7], stock[8], stock[9], stock[10], stock[11], stock[12], stock[13], stock[14], stock[15],
             stock[16], stock[17], stock[18], stock[19], stock[20], stock[21], stock[22], stock[23], stock[24],
             stock[25], stock[26], stock[27], stock[28], stock[29], str(stock[30]) + " " + str(stock[31]),
             ))
    return stock_list


_session = requests.session()

stock_api = "http://hq.sinajs.cn/list="

max_num = 800  # 单批次股票数
stocklist, stocklist_split = stocklist_method(max_num)  # 获取股票清单
timeout = 0.65  # 单线程超时时间
threadcnt = min(2, len(stocklist))  # 最大线程数为股票的划分数
# 列名tuple
clname = ("code", "name", "open", "close", "now", "high", "low", "buy", "sell", "turnover", "volume", "bid1_volume",
          "bid1", "bid2_volume", "bid2", "bid3_volume", "bid3", "bid4_volume", "bid4", "bid5_volume", "bid5",
          "ask1_volume",
          "ask1", "ask2_volume", "ask2", "ask3_volume", "ask3", "ask4_volume", "ask4", "ask5_volume", "ask5",
          "datetime")
if __name__ == '__main__':
    print("开始运行，localtime: %s" % datetime.now())

    # 判断交易日历
    if if_trade():
        print("%s 交易日,运行程序" % datetime.now().date())
    else:
        print("%s 非交易日,退出" % datetime.now().date())
        sys.exit(0)

    stktime = {stki: datetime.now() for stki in stocklist_split}  # 用于时间去重的字典生成式
    today_csvname = "%s-sinatick.csv" % datetime.now().date()
    today_zipname = "%s-sinatick.7z" % datetime.now().date()
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
                stkdata = tick_dl(if_thread=True)  # 下载数据
                t3 = datetime.now()
                stkdata = formatdata(stkdata)
                with open(todaycsvpath, mode='a') as file_today:  # 打开文件
                    writecnt = 0
                    for stki in stkdata:
                        if len(stki[31]) > 15:
                            datanowtime = datetime.strptime(stki[31], "%Y-%m-%d %H:%M:%S")
                        else:
                            continue
                        if datanowtime > stktime[stki[0]]:  # 判断该股票的时间大于已经写入的时间
                            # 写入文件
                            file_today.writelines(",".join(stki))
                            file_today.write("\n")
                            stktime[stki[0]] = datanowtime
                            writecnt += 1

                    file_today.close()
                    t4 = datetime.now()
                    print("localtime: %s alltime:%s tocsvtime:%s downloadtime:%s writecnt:%d" % (
                        t4, t4 - t1, t4 - t3, t3 - t1, writecnt))
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
nohup /root/miniconda3/envs/finance/bin/python -u /root/easyqd/new_get_sina.py >/root/easyqd/sina.log 2>&1 &
"""
