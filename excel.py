import xlsxwriter


host_ip = (
    ["server1",'192.168.1.101', '2018-06-11'],
    ["server2",'192.168.1.101', '2018-06-11'],
    ["server3",'192.168.1.101', '2018-06-11'],
    ["server4",'192.168.1.101', '2018-06-11']
)

# 创建一个新的文件
with xlsxwriter.Workbook('host_ip2.xlsx') as workbook:
    
    # 添加一个工作表
    worksheet = workbook.add_worksheet()

    # 设置一个加粗的格式
    bold = workbook.add_format({"bold": True})

    # 设置一个日期的格式
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})

    # 分别设置一下 A 和 B列的宽度
    worksheet.set_column('A:A', 10, bold)
    worksheet.set_column('B:B', 10)
    worksheet.set_column('C:C', 10)

    # 先把表格的抬头写入， 并设置字体加粗
    worksheet.write('A1', '主机名')
    worksheet.write('B1', 'IP 地址')
    worksheet.write(0,2, '统计日期')

    # 设置数据写入文件的初始行和列的索引位置
    row = 1
    col = 0

    # 迭代数据并逐行写入文件
    for name, ip ,date in (host_ip):
        worksheet.write(row, col, name)
        worksheet.write(row, col + 1, ip)
        worksheet.write(row, col + 2, date, date_format)
        row += 1
   


# # 创建一个新的 Excel 文件，并添加一个工作表
# workbook = xlsxwriter.Workbook('demo.xlsx')
# worksheet = workbook.add_worksheet()

# # 设置第一列(A) 单元格宽度为 20
# worksheet.set_column('A:A', 20)

# # 定义一个加粗的格式对象
# bold = workbook.add_format({'bold': True})

# # 在 A1 单元格处写入字符串 'Hello'
# worksheet.write('A1', 'Hello')

# # 在 A2 单元格处写入中文字符串，并加粗字体
# worksheet.write('A2', '千锋教育', bold)

# # 利用 行和列的索引号方式，写入数字，索引号是从 0 开始的
# worksheet.write(2, 0, 100)  # 3 行 1列
# worksheet.write(3, 0, 35.8)

# # 计算 A3 到 A4 的结果
# worksheet.write(4, 0, '=SUM(A3:A4)')

# # 在 B5 单元格处插入一个图片
# # worksheet.insert_image('B5', 'logo.png')

# # 关闭 Excel 文件
# workbook.close()