import scrapy

#写入excel操作模块
import xlsxwriter

class itemSpider(scrapy.Spider):
    # 爬虫名称'itemSpider'  
    #  使用命令：scrapy crawl itemSpider
    name = 'itemSpider'

    # ######################## 基金参数设置区域 ######
    # 我的基金代码
    # 
    myCode = '320007'
    # 初始时间
    timeF = '2019-01-01'
    # 末尾时间
    timeE = '2019-12-26'
    allStr = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=' + myCode + '&page=1&sdate=' + timeF + '&edate=' + timeE + '&per=20'
    
    # 买入的时机 itemSpider.buyValue
    buyValue = -0.012

    # 卖出的时机 itemSpider.sellValue
    sellValue = 0.0665
    
    # 收益最大化
    maxValue = 0

    #开始爬虫
    start_urls = []
    start_urls.append(allStr)

    ######################### 全局变量 #######

    #储存数据
    listBoxAll = [] 

    def parse(self, response):
        
        ########################   将数据迭代放入列表中    ##########
        # 获取数据的所有对象
        data = response.css('table tbody tr')
        
        # 创建 第一级 空列表
        for i in range(len(data)):
            # 创建 第二级 空列表
            listBoxIn = []

            for j in range(4):             
                
                # ------------------- 出现特别小的日增长率 0.000007 时 的解决方案 一 ----
                # -------------------- 想通过自己计算获取 日增长率，但是缺点是，需要前一天的数据 -----
                # --------------------- 如果我爬取100条数据，第前101条数据很难爬取。因为我这是循环页面获取的方式，----
                # if j == 4:
                #     nowValue = data[i].css('td::text')[1].get()
                #     previousValue = data[i].css('td::text')[1].get()
                #     wantValue = 
                # else:
                # -------------------------------------------------
                if data[i].css('td::text')[j].get() == '限制大额申购' or data[i].css('td::text')[j].get() == '开放申购':
                    wantValue = '0%'
                else:
                    # 将 前4个指定数据 迭代进行获取
                    wantValue = data[i].css('td::text')[j].get()
                # print(wantValue)
                # 添加一个一个的添加进入 第二级 列表中
                listBoxIn.append(wantValue)
                
            # 当 第二级列表被填满后，再添加进入 第一级 列表中
            itemSpider.listBoxAll.append(listBoxIn) 
        
        ##############################  迭代全部页面信息 功能  ####################
        # 查找页面中 关于 *总页数 和 当前页数* 的字符串信息
        dataText = response.css('body::text').get()

        # (1)获取 *总页数* 的 字符串索引相关信息
        myAllPageF  = dataText.find('pages:') + 6  # 14 + 6   
        myAllPageE = dataText.find(',curpage:')  # 22       

        # (2)获取 *当前页码* 的 字符串索引相关信息
        nowPageF = dataText.find(',curpage:') + 9 # 22 + 9  想获取当前页
        nowPageE = dataText.find('};')            # 33
        
        # (3)获取所有数据量
        myAllDataF = dataText.find('records:') + 8
        myAllDataE = dataText.find(',pages')

        # 总页数 和 当前页码 和 总数据量 的容器
        myAllPageNum = ''
        nowPageNum = ''
        myAllDataNum = ''

        # 通过（1）获取 总页数
        for i in range(myAllPageF , myAllPageE):
            # print(i)
            myAllPageNum += dataText[i]

        # 通过（2）获取 当前所在的页码数
        for i in range(nowPageF, nowPageE):
            nowPageNum += dataText[i]

        # 通过（3）获取 总数据的数量
        for i in range(myAllDataF, myAllDataE):
            myAllDataNum += dataText[i]

        # （4）查找当前网页中的 *URL的page索引* 的香港信息
        myUrlPageF = itemSpider.allStr.find('&page=') + 6  # 14 + 5  想获取总页数
        myUrlPageE = itemSpider.allStr.find('&sdate')  # 22   
        
        # 通过 （4）的支持，如果当前页面小于 总页数 就 替换网址成下一页 的索引值
        nowPageNum = int(nowPageNum)
        myAllPageNum = int(myAllPageNum)
        if nowPageNum < myAllPageNum:
            next_pageNum = str(nowPageNum + 1)
            next_page_url = itemSpider.allStr[:myUrlPageF] + next_pageNum + itemSpider.allStr[myUrlPageE:]
            # 将得出的下一页URL放入 爬虫中URL 中继续爬取资源。
            next_page = response.urljoin(next_page_url)
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            # 当数据都爬取到后，进行下面的处理，执行一次

            print('----start----')
            # 倒序排列数据(为后期 从更早的日期开始进行数据对比)
            # print(itemSpider.listBoxAll[::-1])
            itemSpider.listBoxAll = itemSpider.listBoxAll[::-1]

            ######## 操作区域 ### 进行策略逻辑 编辑 #########
            #
            # print('----')
            # 交易状态变量
            theSwitch = 0

            # （A）交易初始 单位净值
            saveValue = 0

            # （B）交易比较值
            compareValue = 0

            # 每笔短期最终受益率 B / A - 1
            finallyValueRate = 0

            # 短期累计交易收益率
            shortAllValue = 0

            # 储存每次交易的 买入时间 和 卖出时间
            allTradeTime = []
            
            # 储存 短期内每笔交易的时间 (短期交易时间查询的变量)
            shortTradeTime = []
            # 一共成功进行了几笔交易(正在进行中的交易不算入内)
            succeedTradeNum = 0

            # 长期统计最终收益值
            longTimeFinallyValue = 0

            
            # 总数据中交易第一次开始交易时的值 （便于统计总收益率）
            firstValue = 0
            # 识别是否为第一次开始交易的值的 辅助识别参数 便于统计总收益率）
            firstValueKey = 0

            # 总数据最终的 总收益率
            finallyAllDataValueRate = 0

            # 因为序号是从0开始的，所以往推一格
            newRange = int(myAllDataNum)

            # 将所有数据进行迭代处理
            for i in range(0, newRange):
     
                # 获取 日增长率
                clearValue = itemSpider.listBoxAll[i][3]
                
                # 处理 日增长率 的百分号，便于后期编辑
                clearValue = float(clearValue.replace('%', ''))/100
                # print(i)
                # print('clearValue')
                # print(clearValue)

                # 储存 短期内每笔交易的时间 (短期交易时间查询的变量)
          

                #--------------------------------  负数 区域  #####################
                # 判断出现负数的时候,并识别买入时的 跌百分比
                if clearValue <= itemSpider.buyValue and theSwitch == 0:
                        # 激活正在交易状态
                        theSwitch = 1
                        # 将当日 单位净值 进行保存
                        saveValue = itemSpider.listBoxAll[i][1]

                        
                        # 当第一次交易开始后，保存第一次交易的值 （便于为后期计算总收益率）
                        if firstValueKey == 0:

                            firstValue = itemSpider.listBoxAll[i][1]
                            
                            firstValueKey = 1
                            #短期时间内交易时，买入时间（时间！查询）
                            shortTradeTime.append(itemSpider.listBoxAll[i][0])
                         
                        else:
                            #短期时间内交易时，买入时间（时间！查询）
                            shortTradeTime.append(itemSpider.listBoxAll[i][0])
               
                        # print(saveValue)
                # 交易期间的值 开始累计对比
                elif  theSwitch == 1:
                    # 交易期间每天的值，进行累计收益率计算。
                    compareValue = itemSpider.listBoxAll[i][1]
                    # 短期每笔交易最终受益率 

                    #短期 累计交易 收益率 大于 0.05时 停止交易，进行卖出。【预计到账下次交易日晚上】
                    # shortAllValue += finallyValueRate

                    finallyValueRate = float(compareValue) / float(saveValue) - 1
                    # print(finallyValueRate)

                    # 卖出时的涨幅百分比 指定
                    if finallyValueRate >= itemSpider.sellValue:
                        # 结束交易状态激活
                        theSwitch = 0

                        # 累计成功交易次数
                        succeedTradeNum += 1

                        # 交易终止的时候时间 （卖出时间查询）
                        shortTradeTime.append(itemSpider.listBoxAll[i][0])
                        # 短期每笔交易最终受益值，进行累计（便于后期进行统计总收益率）
                        # 短期交易时间查询迭代输出
                        allTradeTime.append(shortTradeTime)
                        
                        #清空短期每笔交易时间容器
                        shortTradeTime = []
                   
                        longTimeFinallyValue += float(compareValue) - float(saveValue)
                        i = i + 1
                

                
                # for i in range(0,2):
                #     for j in range(0,1):
                #         print(allTradeTime[i][j])
                #     print('-------')
                # ======================
           
            #所有数据最终统计后的总收益率
            # print(longTimeFinallyValue)
            # print(firstValue)
            finallyAllDataValueRate = longTimeFinallyValue / float(firstValue)
            print('总收益率为')
            print(finallyAllDataValueRate)
            print('总交易次数')
            print(succeedTradeNum)
            print('交易时间')
            print(allTradeTime)


                    
                   





            ##############################################  测试 ##################
            # print(itemSpider.allStr)
        
            
            

        

            ############################## 创建excel 文件  将爬到的数据 从列表中迭代出来 并保存文件中 ##############
            # 创建一个新的文件
            # with xlsxwriter.Workbook('new.xlsx') as workbook:
                
            #     # 添加一个工作表
            #     worksheet = workbook.add_worksheet()

            #     # 设置一个加粗的格式
            #     bold = workbook.add_format({"bold": True})

            #     # 设置一个日期的格式
            #     date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})

            #     # 分别设置一下 A 和 B列的宽度
            #     worksheet.set_column('A:A', 10)
            #     worksheet.set_column('B:B', 10)
            #     worksheet.set_column('C:C', 10)
            #     worksheet.set_column('D:D', 10)
            #     worksheet.set_column('E:E', 10)

            #     # 先把表格的抬头写入， 并设置字体加粗
            #     worksheet.write('A1', '序号')
            #     worksheet.write('B1', '日期')
            #     worksheet.write('C1', '单位净值')
            #     worksheet.write('D1', '累计净值')
            #     worksheet.write('E1', '日增长率')
            
            #     # 设置数据写入文件的初始行和列的索引位置
            #     row = 1
            #     col = 0
            #     # 迭代数据并逐行写入文件
            #     for data, value1 ,value2, value3 in(itemSpider.listBoxAll):
            #         worksheet.write(row, col, row)
            #         worksheet.write(row, col + 1, data, date_format)
            #         worksheet.write(row, col + 2, value1)
            #         worksheet.write(row, col + 3, value2)
            #         worksheet.write(row, col + 4, value3)
            #         row += 1
   



   