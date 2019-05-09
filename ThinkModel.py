#!/usr/bin/python
# -*- coding: utf-8 -*-
import pymysql
import traceback
import logging
import time
import os

# 日志路径
if os.path.exists("./logs"):
    pass
else:
    os.mkdir("./logs")

logging_path="./logs/{}.logs".format(time.strftime("%Y%m%d", time.localtime()))

# 日志配置
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    filename=logging_path,
                    filemode='a+')

# 定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# mysql配置
mysql = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'db': 'ygwfc',
    'charset': 'utf8',
}

class model():
    """
    数据库实例化
    """

    def __init__(self, table):
        self.table = table
        self.connection = pymysql.connect(**mysql)
        self.cursor = self.connection.cursor()
        self.sql_where = ""
        self.sql_limit = ""
        self.sql_order = ""
        self.sql_group = ""
        self.sql_field = ""

    def where(self, field, *arg):
        """
        where 查询
        :param field:查询字段
        :param condition: 逻辑符号
        :param value: 查询添加
        :return:
        """
        if len(arg) == 1:
            condition = "="
            value = arg[0]
        elif len(arg) == 2:
            condition = arg[0]
            value = arg[1]
        else:
            raise NameError('where 参数不合法!')

        if condition == "":
            condition = "="

        if condition in ["<", ">", "=", "<>", "!="]:
            if self.sql_where:
                self.sql_where = self.sql_where + " AND `{}`{}{}".format(field, condition, value)
            else:
                self.sql_where = self.sql_where + "`{}`{}{}".format(field, condition, value)
        elif condition.upper() in ["IS", "IS NOT", "IS NULL", "IS NOT NULL", "IN"]:
            if value is not None:
                if type(value) == "str":
                    if self.sql_where:
                        self.sql_where = self.sql_where + " AND `{}`{}{}".format(field, condition, value)
                    else:
                        self.sql_where = self.sql_where + "`{}`{}{}".format(field, condition, value)
                if type(value) == "list":
                    if self.sql_where:
                        self.sql_where = self.sql_where + " AND `{}` {} {}".format(field, condition, str(set(value)))
                    else:
                        self.sql_where = self.sql_where + "`{}` {} {}".format(field, condition, str(set(value)))
            else:
                if self.sql_where:
                    self.sql_where = self.sql_where + " AND `{}` {}".format(field, condition)
                else:
                    self.sql_where = self.sql_where + "`{}` {}".format(field, condition)

        return self

    def update(self, data: dict):
        """
        更新操作
        :param data:更新数据字典
        :return:
        """
        if self.sql_where:
            if len(data.keys()):
                update_str = []
                for key in data.keys():
                    if "'" in data[key]:
                        data[key] = data[key].replace("'", "\'")

                    update_str.append("`{}`='{}'", format(key, data[key]))
                update_str = ",".join(update_str)
                sql = "UPDATE {} SET {} WHERE {}".format(self.table, update_str, self.sql_where)
                self.execute(sql)
                self.commit()
                self.close()
            else:
                raise NameError('update 更新数据为空!')
        else:
            raise NameError('update 必须要有where条件限制!')

    def delete(self):
        """
        删除数据
        :return:
        """
        if self.sql_where:
            sql = "DELETE FROM {} WHERE {}".format(self.table, self.sql_where)
            self.execute(sql)
            self.commit()
            self.close()
        else:
            raise NameError('delete 必须要有where条件限制!')

    def like(self, field, like_str):
        """
        like查询
        :param field:字段
        :param like_str: LIKE
        :return:
        """
        if field is None or field == "":
            raise NameError('like 匹配字段为空!')
        if like_str is None or like_str == "":
            raise NameError('like 匹配条件为空!')
        if self.sql_where:
            self.sql_where = self.sql_where + " AND `{}` LIKE \"{}\"".format(field, like_str)
        else:
            self.sql_where = self.sql_where + "`{}` LIKE \"{}\"".format(field, like_str)

        return self

    def order(self, order_str: str):
        """
        排序
        :param order_str:排序条件
        :return:
        """
        if self.sql_order:
            raise NameError('order 条件已存在!')
        if order_str:
            self.sql_order = order_str
        else:
            raise NameError('order 添加为空!')

    def group(self, field: str):
        """
        分组
        :param field:
        :return:
        """
        if self.sql_group:
            raise NameError('group 已存在!')
        if field:
            self.sql_group = field
        else:
            raise NameError('group 为空!')

        return self

    def limit(self, start: int, end: int):
        """
        查询限制
        :param start:起始位置
        :param end: 结束为止
        :return:
        """
        if start is None:
            raise NameError('limit 参数缺失!')
        if self.sql_limit:
            raise NameError('limit 条件已经存在!')
        if start and end:
            self.sql_limit = "LIMIT {},{}".format(start, end)
        if start and end is None:
            self.sql_limit = "LIMIT {}".format(start)

        return self

    def select(self):
        """
        获取查询数据集
        :param limit:
        :return:
        """
        if self.sql_field:
            pass
        else:
            self.sql_field = "*"

        sql = "select {} from {}".format(self.sql_field, self.table)
        if self.sql_where:
            sql = sql + " WHERE {}".format(self.sql_where)
        if self.sql_order:
            sql = sql + " ORDER BY {}".format(self.sql_where)
        if self.sql_group:
            sql = sql + " GROUP BY {}".format(self.sql_group)
        if self.sql_limit:
            sql = sql + "{}".format(self.sql_limit)

        logging.info(sql)
        try:
            t1=time.time()
            self.execute(sql)
            self.commit()
            results = self.cursor.fetchall()
            t2=time.time()-t1
            logging.info("耗时:{} 毫秒".format(round(t2,6)))
            self.close()
            return results
        except:
            logging.error(traceback.format_exc())

    def find(self):
        """
        获取单挑查询数据
        :param limit:
        :return:
        """
        if self.sql_field:
            pass
        else:
            self.sql_field = "*"

        sql = "select {} from {}".format(self.sql_field, self.table)
        if self.sql_where:
            sql = sql + " WHERE {}".format(self.sql_where)
        if self.sql_order:
            sql = sql + " ORDER BY {}".format(self.sql_where)
        if self.sql_group:
            sql = sql + " GROUP BY {}".format(self.sql_group)
        sql = sql + " LIMIT 1"
        logging.info(sql)
        try:
            t1 = time.time()
            self.execute(sql)
            self.commit()
            results = self.cursor.fetchall()
            t2 = time.time() - t1
            logging.info("耗时:{} 毫秒".format(round(t2, 6)))
            self.close()
            return results
        except:
            logging.error(traceback.format_exc())

    def close(self):
        """
        关闭connection对象
        :return:
        """
        self.connection.close()

    def commit(self):
        """
        提交操作
        :return:
        """
        self.connection.commit()

    def field(self, field_str):
        """
        获取字段
        :param field_str:
        :return:
        """
        if self.sql_field:
            raise NameError('field 已存在!')
        if field_str:
            self.sql_field = field_str
        else:
            self.sql_field = "*"

    def execute(self, sql):
        """
        执行sql
        :param sql:
        :return:
        """
        self.cursor.execute(sql)

    def filter(self,strs):
        """
        sql过滤
        :param strs:
        :return:
        """
        pass


if __name__ == "__main__":
    userModel = model("zxyl_user")
    query = userModel.find()
