# -*- coding:utf-8 -*-
"""
qqtick下载
filename : jqdata_api.py
createtime : 2020/10/24 8:14
author : Demon Finch
"""
import re
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
    stock_details = "".join(rep_data).split(";")
    stock_dict = list()
    for stock_detail in stock_details:
        stock = stock_detail.split("~")
        if len(stock) < 53:
            continue
        stock_dict.append(
            (stock[1], re.compile(r"(?<=_)\w+").search(stock[0]).group(), stock[3],
             stock[4], stock[5], stock[6],
             stock[7], stock[8], stock[9], stock[10], stock[11], stock[12],
             stock[13], stock[14], stock[15], stock[16], stock[17], stock[18],
             stock[19], stock[20], stock[21], stock[22], stock[23], stock[24],
             stock[25], stock[26], stock[27], stock[28], stock[29],
             stock[30],
             stock[31], stock[32], stock[33], stock[34], stock[35], stock[36],
             stock[37], stock[38], stock[39], stock[43], stock[44], stock[45],
             stock[46], stock[47], stock[48], stock[49], stock[50], stock[51],
             stock[52], stock[53]))
    return stock_dict


_session = requests.session()

stock_api = "http://qt.gtimg.cn/q="

max_num = 800  # 单批次股票数
stocklist, stocklist_split = stocklist_method(max_num)  # 获取股票清单
timeout = 0.65  # 单线程超时时间
threadcnt = min(3, len(stocklist))  # 最大线程数为股票的划分数
# 列名tuple
clname = ("name", "code", "now", "close", "open", "volume", "bid_volume", "ask_volume", "bid1",
          "bid1_volume", "bid2", "bid2_volume", "bid3", "bid3_volume", "bid4", "bid4_volume",
          "bid5", "bid5_volume", "ask1", "ask1_volume", "ask2", "ask2_volume", "ask3", "ask3_volume",
          "ask4", "ask4_volume", "ask5", "ask5_volume", "last_deal", "datetime", "phg", "phg_percent",
          "high", "low", "price_volumn_turnover", "deal_column", "deal_turnover", "turnover", "PE", "amplitude",
          "fluent_market_value", "all_market_value", "PB", "price_limit_s", "price_limit_x", "quant_ratio",
          "commission", "avg", "market_earning_d", "market_earning_j")

if __name__ == '__main__':
    print("开始运行，localtime: %s" % datetime.now())

    # 判断交易日历
    if if_trade():
        print("%s 交易日,运行程序" % datetime.now().date())
    else:
        print("%s 非交易日,退出" % datetime.now().date())
        sys.exit(0)

    stktime = {stki: datetime.now() for stki in stocklist_split}  # 用于时间去重的字典生成式
    today_csvname = "%s-qqtick.csv" % datetime.now().date()
    todaycsvpath = os.path.join(os.path.dirname(__file__), today_csvname)  # csv文件名称

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
                        datanowtime = datetime.strptime(stki[29], "%Y%m%d%H%M%S")
                        if datanowtime > stktime[stki[1]]:  # 判断该股票的时间大于已经写入的时间
                            # 写入文件
                            file_today.writelines(",".join(stki))
                            file_today.write("\n")
                            stktime[stki[1]] = datanowtime
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

    # 转换为hdf5格式

    print("运行结束：%s" % datetime.now())
    print("\n\n-----------------------------------------\n\n")

"""
linux 后台运行命令：
nohup /root/miniconda3/envs/finance/bin/python -u /root/easyqd/new_get_qq.py >/root/easyqd/qq.log 2>&1 &
"""
