from .tick_down import TickDown
import re
from time import sleep
from datetime import datetime


class QQTickDown(TickDown):
    # 列名tuple
    clname = ("name", "code", "now", "close", "open", "volume", "bid_volume", "ask_volume", "bid1",
              "bid1_volume", "bid2", "bid2_volume", "bid3", "bid3_volume", "bid4", "bid4_volume",
              "bid5", "bid5_volume", "ask1", "ask1_volume", "ask2", "ask2_volume", "ask3", "ask3_volume",
              "ask4", "ask4_volume", "ask5", "ask5_volume", "last_deal", "datetime", "phg", "phg_percent",
              "high", "low", "price_volumn_turnover", "deal_column", "deal_turnover", "turnover", "PE", "amplitude",
              "fluent_market_value", "all_market_value", "PB", "price_limit_s", "price_limit_x", "quant_ratio",
              "commission", "avg", "market_earning_d", "market_earning_j")
    tick_source = "qq"
    stock_api = "http://qt.gtimg.cn/q={params}"

    @staticmethod
    def formatdata(rep_data):
        stock_details = "".join(rep_data).split(";")
        for stock_detail in stock_details:
            stock = stock_detail.split("~")
            if len(stock) > 53:
                yield (stock[1], re.compile(r"(?<=_)\w+").search(stock[0]).group(), stock[3], stock[4],
                       stock[5], stock[6], stock[7], stock[8], stock[9], stock[10], stock[11], stock[12],
                       stock[13], stock[14], stock[15], stock[16], stock[17], stock[18], stock[19], stock[20],
                       stock[21], stock[22], stock[23], stock[24], stock[25], stock[26], stock[27], stock[28],
                       stock[29], stock[30], stock[31], stock[32], stock[33], stock[34], stock[35], stock[36],
                       stock[37], stock[38], stock[39], stock[43], stock[44], stock[45], stock[46], stock[47],
                       stock[48], stock[49], stock[50], stock[51], stock[52], stock[53])

    def run(self):
        self.check_file()  # 创建下载文件
        while True:
            t1 = datetime.now()
            if self.stock_a_hour(t1):  # 判断A股时间段
                try:
                    stkdata = self.formatdata(self.tick_dl(if_thread=True))  # 下载数据
                    with open(self.todaycsvpath, mode='a') as file_today:  # 打开文件
                        t3 = datetime.now()
                        writecnt = 0
                        for stki in stkdata:
                            datanowtime = datetime.strptime(stki[29], "%Y%m%d%H%M%S")
                            if datanowtime > self.stktime[stki[1]]:  # 判断该股票的时间大于已经写入的时间
                                # 写入文件
                                file_today.writelines(",".join(stki) + "\n")
                                self.stktime[stki[1]] = datanowtime
                                writecnt += 1

                        file_today.close()
                        t4 = datetime.now()
                        print(f"localtime: {t4} all:{t4 - t1} tocsv:{t4 - t3} download:{t3 - t1} cnt:{writecnt}")

                except Exception as error_downdata:
                    print(f"error_downdata: {error_downdata}")
            elif datetime.now() > self.trd_hour_end_afternoon:  # 下午3：02退出循环
                print("download complete -> %s" % self.todaycsvpath)
                break
            else:
                print("relax 10s , localtime: %s" % datetime.now())  # 未退出前休息
                sleep(10)
        self.send_message(f"下载{self.tick_source}数据 -> 完成")  # 发送完成消息
