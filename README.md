# TickDown
A股tick下载，自动判断交易日历，获取全市场level1数据

### 依赖项
1. func_timeout
2. requests
3. some_tool(仓库里)
4. akshare

### 使用
定时任务在上午 09:07开始运行

### 参数调节
1. max_num 单批次提交的股票数，当前为800，可以自行尝试多个数值
2. timeout 单个线程的超时时间，网络不好的同学可以调大一些，1.5s内都是可以接受的
3. threadcnt = min(3, len(stocklist)) 线程数，默认开启多线程，最大线程不超过股票的分组数量（大约为8），3个线程大约最合适，视具体情况而定，可多次尝试

### 下载逻辑
1. 多线程下载数据
2. 下载的数据合并清洗
3. 用判断时间大于的方式来判定当前下载到的股票tick数据是更新的数据
4. 对提取到的更新的数据集合写入到csv中
5. 循环以上行为

### 数据来源
1. 股票清单：http://www.shdjt.com/js/lib/astock.js
2. 交易日历：akshare（原始来源sina）
3. tick的api：



### 交流群
[![2OuaWV.jpg](https://z3.ax1x.com/2021/06/16/2OuaWV.jpg)](https://imgtu.com/i/2OuaWV)
