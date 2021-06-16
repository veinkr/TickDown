# -*- coding:utf-8 -*-
"""
filename : notify-tool.py
createtime : 2020/10/15 20:12
author : Demon Finch
"""
import json
import requests
from datetime import datetime, date


current_day = datetime.now().strftime("%Y-%m-%d")
trd_hour_start_morning = int(datetime.strptime(current_day + ' ' + '09:08:00', '%Y-%m-%d %H:%M:%S').timestamp())
trd_hour_end_morning = int(datetime.strptime(current_day + ' ' + '11:32:00', '%Y-%m-%d %H:%M:%S').timestamp())
trd_hour_start_afternoon = int(datetime.strptime(current_day + ' ' + '12:58:00', '%Y-%m-%d %H:%M:%S').timestamp())
trd_hour_end_afternoon = int(datetime.strptime(current_day + ' ' + '15:12:00', '%Y-%m-%d %H:%M:%S').timestamp())


def neteasy_clean(i):
    return i.replace("sh", "0").replace("sz", "1")


def get_stock_type(stock_code):
    """判断股票ID对应的证券市场
    匹配规则
    ['50', '51', '60', '90', '110'] 为 sh
    ['00', '13', '18', '15', '16', '18', '20', '30', '39', '115'] 为 sz
    ['5', '6', '9'] 开头的为 sh， 其余为 sz
    :param stock_code:股票ID, 若以 'sz', 'sh' 开头直接返回对应类型，否则使用内置规则判断
    :return 'sh' or 'sz'"""
    assert type(stock_code) is str, "stock code need str type"
    sh_head = ("50", "51", "60", "90", "110", "113",
               "132", "204", "5", "6", "9", "7")
    if len(stock_code) < 6:
        return ''
    if stock_code.startswith(("sh", "sz", "zz")):
        return stock_code
    else:
        return "sh" + stock_code if stock_code.startswith(sh_head) else "sz" + stock_code


def stocklist_method(max_num, if_neteasy=False):
    response = requests.get("http://www.shdjt.com/js/lib/astock.js")
    if response.status_code != 200:
        raise Exception("获取股票清单失败，请重试")
    all_text = response.text.replace('var astock_suggest="~', '')
    stock_list = list(set([get_stock_type(i.split("`")[0]) for i in all_text.split("~") if not i.startswith('zz')]))
    if if_neteasy:
        stock_list = list(map(neteasy_clean, stock_list))

    stock_list = [i for i in stock_list if i is not None]
    stock_code = []
    for i in range(0, len(stock_list), max_num):
        request_list = ",".join(stock_list[i: i + max_num])
        stock_code.append(request_list)
    return stock_code, stock_list


def stock_a_hour(current_time):
    """A股时间段判断
    :param current_time:当前时间的时间戳，eg：time.time() 或者 datetime.now().timestamp()
    """
    return (trd_hour_start_morning <= current_time <= trd_hour_end_morning) or (
            trd_hour_start_afternoon <= current_time <= trd_hour_end_afternoon)


def if_trade(selectday: date = datetime.now().date()):
    """判断当日是否交易日"""
    import akshare as ak
    try:
        tool_trade_date_hist_sina_df = ak.tool_trade_date_hist_sina()
        tradedays = tool_trade_date_hist_sina_df.trade_date.to_list()
    except Exception as err:
        print("获取akshare的交易日历失败：", err)
        tradedays = [datetime.now().date()]

    if selectday in tradedays or selectday.strftime("%Y-%m-%d") in tradedays:
        return True
    else:
        return False


if __name__ == "__main__":
    print(if_trade())
    print(stocklist_method(800))
