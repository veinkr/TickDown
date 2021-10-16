from .tick_down import TickDown
from time import sleep
from datetime import datetime
import json


class NetTickDown(TickDown):
    # 列名tuple
    clname = ('code', 'time', 'name', 'percent', 'price', 'open', 'high', 'low',
              'ask1', 'ask2', 'ask3', 'ask4', 'ask5', 'askvol1', 'askvol2', 'askvol3', 'askvol4', 'askvol5',
              'bid1', 'bid2', 'bid3', 'bid4', 'bid5', 'bidvol1', 'bidvol2', 'bidvol3', 'bidvol4', 'bidvol5',
              'updown', 'type', 'status', 'symbol', 'update', 'volume', 'arrow', 'yestclose', 'turnover',)
    tick_source = "neteasy"
    stock_api = 'http://api.money.126.net/data/feed/{params},money.api'

    def neteasy_stock_clean(self):
        self.stock_code = [stocki.replace("sz", "1").replace("sh", "0") for stocki in self.stock_code]
        self.stock_list = [stocki.replace("sz", "1").replace("sh", "0") for stocki in self.stock_list]
        self.stktime = {k.replace("sz", "1").replace("sh", "0"): v for k, v in self.stktime.items()}

    @staticmethod
    def formatdata(rep_data):
        for repi in rep_data:
            if repi is not None and repi != "":
                for stockidats in json.loads(repi.lstrip("_ntes_quote_callback(").rstrip(");")).values():
                    if len(stockidats.keys()) > 30:
                        yield stockidats

    def run(self):
        self.neteasy_stock_clean()
        self.check_file()
        while True:
            t1 = datetime.now()
            if self.stock_a_hour(t1):  # 判断A股时间段
                # try:
                stkdata = self.formatdata(self.tick_dl(if_thread=True))
                with open(self.todaycsvpath, mode='a') as file_today:  # 打开文件
                    writecnt = 0
                    t3 = datetime.now()
                    for stki in stkdata:
                        datanowtime = datetime.strptime(stki["time"], "%Y/%m/%d %H:%M:%S")
                        if datanowtime > self.stktime[stki['code']]:
                            # 写入文件
                            file_today.writelines(
                                ",".join([str(stki[keysel]) for keysel in self.clname]))
                            file_today.write("\n")
                            self.stktime[stki['code']] = datanowtime
                            writecnt += 1
                    file_today.close()
                    t4 = datetime.now()
                    print(f"localtime: {t4} all:{t4 - t1} tocsv:{t4 - t3} download:{t3 - t1} cnt:{writecnt}")
                # except Exception as error_downdata:
                #     print(f"error_downdata: {error_downdata}")
            elif datetime.now() > self.trd_hour_end_afternoon:  # 下午3：02退出循环
                print("download complete -> %s" % self.todaycsvpath)
                break
            else:
                print("relax 10s , localtime: %s" % datetime.now())  # 未退出前休息
                sleep(10)

        self.send_message(f"下载{self.tick_source}数据 -> 完成")  # 发送完成消息
