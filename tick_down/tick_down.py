import os
import sys
import shutil

from multiprocessing.pool import ThreadPool
from func_timeout import FunctionTimedOut, func_timeout
import requests
from datetime import datetime, date, time
from abc import ABCMeta, abstractmethod

headers = {"Accept-Encoding": "gzip, deflate, sdch",
           "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/54.0.2840.100 "
                          "Safari/537.36")}


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


class TickDown(metaclass=ABCMeta):
    clname = None
    tick_source = ""
    stock_api = ""

    def __init__(self,
                 max_num=800,
                 timeout=1,
                 threadcnt=3,
                 save_path=os.path.dirname(sys.argv[0]),
                 msg_callback=None,
                 stock_list=None,
                 trade_date_bypass: bool = False):
        """
        tick下载基类
        :param max_num: 单次请求的股票数量
        :param timeout: 单次请求超时时间
        :param threadcnt: 请求线程数
        :param save_path: tick csv保存路径
        :param msg_callback: 发送信息的callback function
        :param stock_list:自定义股票清单
        :param trade_date_bypass: 旁通交易日历,即不判断交易日历
        """

        self.request_session = requests.session()
        self.msg_callback = msg_callback
        self.max_num = max_num
        self.timeout = timeout
        self.threadcnt = min(threadcnt, 8)
        # 股票清单
        self.stock_list = [] if stock_list is None else stock_list
        self.stocklist()

        # 时间部分信息
        self.current_day = date.today()
        self.trd_hour_start_morning = datetime.combine(self.current_day, time(9, 8))
        self.trd_hour_end_morning = datetime.combine(self.current_day, time(11, 32))
        self.trd_hour_start_afternoon = datetime.combine(self.current_day, time(12, 58))
        self.trd_hour_end_afternoon = datetime.combine(self.current_day, time(15, 2))
        # csv文件名称
        self.todaycsvname = f"{self.current_day}-{self.tick_source}tick.csv"
        self.todaycsvpath = os.path.join(save_path, self.todaycsvname)
        # 压缩文件名称
        self.today7zname = f"{self.current_day}-{self.tick_source}tick.7z"
        self.today7zpath = os.path.join(save_path, self.today7zname)
        print(f"file save path: {save_path}")
        # run before
        self.if_trade(trade_date_bypass=trade_date_bypass)
        # 发送启动信息
        self.send_message(f"下载{self.tick_source}数据 -> 启动")  # 发送启动消息

    def compress(self, zip_loc='7za', password='1234'):
        """7z压缩"""
        os.system(f"""{zip_loc} a -t7z {self.today7zpath} {self.todaycsvpath} -p{password}""")

    def move_to_path(self, path):
        """移动到数据文件目录去"""
        if not os.path.exists(path):
            os.makedirs(path)
        shutil.move(self.todaycsvpath, os.path.join(path, self.todaycsvname))
        if os.path.exists(self.today7zpath):
            shutil.move(self.today7zpath, os.path.join(path, self.today7zname))

    def stocklist(self):
        """查询所有方法获取到股票清单"""
        if len(self.stock_list) == 0:
            for method in [self.stocklist_astock, self.stocklist_akshare, self.stocklist_from_file]:  #
                try:
                    self.stock_list += method()
                    break
                except Exception as err:
                    self.send_message(f"获取{method.__name__}股票清单失败，请查看原因，{err}"[:100])
        self.stock_list = list(set(self.stock_list))
        self.stock_code = [",".join(self.stock_list[i: i + self.max_num]) for i in
                           range(0, len(self.stock_list) + 1, self.max_num)]
        self.stock_code = [i for i in self.stock_code if i != '' and i is not None]
        self.stktime = {stki: datetime.now() for stki in self.stock_list}  # 用于时间去重的字典生成式
        self.stocklist_to_file()

    def stocklist_to_file(self):
        stock_list_file = os.path.join(os.path.dirname(__file__), "stock_list.txt")
        with open(stock_list_file, 'w') as stock_list_file:
            stock_list_file.writelines('\n'.join(self.stock_list))  # todo
            stock_list_file.close()

    @classmethod
    def stocklist_from_file(cls):
        stock_list_file = os.path.join(os.path.dirname(__file__), "stock_list.txt")
        with open(stock_list_file, 'r') as stock_list_file:
            return [i.strip() for i in stock_list_file.readlines()]

    @classmethod
    def stocklist_akshare(cls):
        pass

    @classmethod
    def stocklist_astock(cls):
        response = requests.get("http://www.shdjt.com/js/lib/astock.js")
        if response.status_code == 200:
            all_text = response.text.replace('var astock_suggest="~', '')
            stock_list = list(
                set([get_stock_type(i.split("`")[0]) for i in all_text.split("~") if not i.startswith('zz')]))
            return [i for i in stock_list if i is not None and i != '']

    def get_stock_batch(self, params):
        return self.request_session.get(self.stock_api.format(params=params), headers=headers)

    def get_stocks_by_range(self, params):
        try:
            r = func_timeout(self.timeout, self.get_stock_batch, args=(params,))
            return r.text
        except FunctionTimedOut:
            print("batch timeout,localtime:%s" % datetime.now())
            return ''
        except Exception as e:
            print("something wrong,tell author please\n", e)
            return ''

    def tick_dl(self, if_thread=False):
        if if_thread:
            pool = ThreadPool(self.threadcnt)
            try:
                res = pool.map(self.get_stocks_by_range, self.stock_code)
            finally:
                pool.close()
            return [d for d in res if d is not None]
        else:
            return [self.get_stocks_by_range(param) for param in self.stock_code]

    def send_message(self, msg):
        if self.msg_callback:
            self.msg_callback(msg)

    def check_file(self):
        if not os.path.exists(self.todaycsvpath):
            # 如果没有这个文件，则创建这个文件并写入列名
            with open(self.todaycsvpath, mode='w') as file_today:
                file_today.writelines(",".join(self.clname))
                file_today.write("\n")
                file_today.close()

    def stock_a_hour(self, current_time=datetime.now()) -> bool:
        """A股时间段判断
        :param current_time:当前时间的时间戳，eg：time.time() 或者 datetime.now().timestamp()
        """
        return (self.trd_hour_start_morning <= current_time <= self.trd_hour_end_morning) or (
                self.trd_hour_start_afternoon <= current_time <= self.trd_hour_end_afternoon)

    def if_trade(self, selectday: date = datetime.now().date(), trade_date_bypass: bool = False):
        """判断当日是否交易日"""
        if trade_date_bypass:
            print("bypass 交易日历检查")
            return
        from akshare import tool_trade_date_hist_sina as ak_trade_date
        try:
            trade_days = ak_trade_date().trade_date.to_list()
            if selectday in trade_days or selectday.strftime("%Y-%m-%d") in trade_days:
                print("%s 交易日,运行程序" % datetime.now().date())
            else:
                print("%s 非交易日,退出" % datetime.now().date())
                sys.exit(0)
        except Exception as err:
            print("获取akshare的交易日历失败：", err)
            self.send_message(f"获取akshare的交易日历失败,下载程序继续启动:{err}"[:50])

    @staticmethod
    def formatdata(rep_data):
        pass

    @abstractmethod
    def run(self):
        self.check_file()
        pass
