#!/usr/bin/python
# encoding: utf-8
# -*- coding: utf8 -*-
"""
Created by PyCharm.
File:        OrderBook.py
User:        ZhaoPeng
Create Date:    2019/10/16
Create Time:    14:51
System Version: ubuntu 18.0
 """
import logging
import os
import time


class Order_Book(object):
    def __init__(self):
        self.path = './info/'
        self.path_snapshot = './info/snapshot/'

    def is_folder_exists(self):
        '''
        创建self.path与self.path_snapshot目录
        :return:
        '''
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if not os.path.exists(self.path_snapshot):
            os.makedirs(self.path_snapshot)

    def init_log(self):
        '''
        初始化日志，调用self.logging写日志
        :return:
        '''
        LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"  # 日志格式化输出
        DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"  # 日期格式
        fp = logging.FileHandler(os.path.join(self.path, 'logs.txt'), encoding='utf-8')
        fs = logging.StreamHandler()
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT, handlers=[fp, fs])  # 调用
        self.logging = logging
        self.logging.info("日志初始化成功")

    def init_order(self, all_orders):
        '''
        记录收到的每个订单
        :param all_orders: 收到的订单
        :return:
        '''
        with open(os.path.join(self.path, 'order.txt'), 'a') as f:
            orders = map(lambda x: [x[0], str(x[1]), str(x[2]), x[3]], all_orders)
            for order in orders:
                f.write(','.join(order) + '\n')
            self.logging.info("订单记录添加成功")

    def get_snapshot(self, all_orders):
        '''
        每次改变订单，生成快照(txt文件)
        :param all_orders: 改变后的订单
        :return:
        '''
        name = str(int(time.time() * 10 ** 7)) + '.txt'  # 快照名为当前时间戳
        orders = map(lambda x: [x[0], str(x[1]), str(x[2]), x[3]], all_orders)
        pwd = os.path.join(self.path_snapshot, name)
        isExists = os.path.exists(pwd)
        if not isExists:
            with open(pwd, 'w') as f:
                for order in orders:
                    if order[2] != '0':
                        f.write(','.join(order) + '\n')
            self.logging.info(name + "快照已生成")
        else:
            self.get_snapshot(all_orders)

    def add_trade(self, info):
        '''
        添加交易合同
        :param info: 每次交易后的撮合记录
        :return:
        '''
        with open(os.path.join(self.path, 'trade.txt'), 'a') as f:
            f.write(info + '\n')
        self.logging.info("交易合同已添加")

    def init_data(self, name):
        '''
        加载文件数据返回数据与列表
        :param name: 文件名
        :return: 数据列表
        '''
        with open(name) as f:
            orders = [line.strip('\n').split(',') for line in f.readlines()]
        self.logging.info("数据初始化成功")
        return list(map(lambda x: [x[0], int(x[1]), int(x[2]), x[3]], orders))

    def best_choice(self, current_index, all_orders):
        '''
        遍历当前索引之前的数据，选出最适合撮合成交顺序
        :param current_index: all_orders列表的当前索引
        :param all_orders: 所有数据
        :return: 最适合交易的数据
        '''
        result = []
        for i in range(current_index):
            if all_orders[current_index][0] == all_orders[i][0] and all_orders[current_index][3] == '1' and \
                    all_orders[i][3] == '2' and all_orders[i][2] != 0 and all_orders[current_index][1]>=all_orders[i][1]:
                result.append(all_orders[i])
            elif all_orders[current_index][0] == all_orders[i][0] and all_orders[current_index][3] == '2' and \
                    all_orders[i][3] == '1' and all_orders[i][2] != 0 and all_orders[current_index][1]<=all_orders[i][1]:
                result.append(all_orders[i])
        if not result:
            return None
        if all_orders[current_index][3] == '1':
            return min(result, key=lambda x: x[1])
        elif all_orders[current_index][3] == '2':
            return max(result, key=lambda x: x[1])
        else:
            self.logging.error('用户数据异常')
            raise KeyError("数据异常!")

    def match_up_orders(self, all_orders):
        '''
        撮合交易
        :param all_orders: 所有数据
        :return:
        '''
        nums = len(all_orders)
        for i in range(nums):
            best = self.best_choice(i, all_orders)
            count = 1
            while best and all_orders[i][2] != 0:
                index = all_orders.index(best)
                if all_orders[i][2] >= all_orders[index][2]:
                    all_orders[i][2] -= all_orders[index][2]
                    trade="{}.Order {} - Order {}：以{}的价格成交{}手".\
                        format(count, i + 1, index + 1, all_orders[index][1], all_orders[index][2])
                    self.add_trade(trade)
                    self.logging.info(trade)
                    all_orders[index][2] = 0
                    self.get_snapshot(all_orders)
                    count += 1
                elif all_orders[i][2] < all_orders[index][2]:
                    all_orders[index][2] -= all_orders[i][2]
                    trade="{}.Order {} - Order {}：以{}的价格成交{}手".format(count, i + 1, index + 1, all_orders[index][1], all_orders[i][2])
                    self.add_trade(trade)
                    self.logging.info(trade)
                    all_orders[i][2] = 0
                    self.get_snapshot(all_orders)
                    count += 1
                best = self.best_choice(i, all_orders)

    def change_order_book(self, file, all_orders):
        '''
        撮合交易成功后，修改原数据文件，保留剩下需要交易的内容
        :param file: 原数据文件地址
        :param all_orders: 所有数据
        :return:
        '''
        orders = map(lambda x: [x[0], str(x[1]), str(x[2]), x[3]], all_orders)
        with open(file, 'w') as f:
            for order in orders:
                if order[2] != '0':
                    f.write(','.join(order) + '\n')
            self.logging.info('交易委托账本修改成功')

    def run(self):
        file = './Orders.txt'
        self.is_folder_exists()
        self.init_log()
        all_orders = self.init_data(file)
        self.init_order(all_orders)
        self.match_up_orders(all_orders)
        self.change_order_book(file, all_orders)


if __name__ == '__main__':
    order = Order_Book()
    order.run()
