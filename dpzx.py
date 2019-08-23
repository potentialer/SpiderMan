# -*-coding:utf-8 -*-
# 冻品在线-成都
# 1163348088061034498-1163348088140726273

import datetime
import re
import math
import pymysql
import scrapy, time, json
import requests
from ..functions.check_spider import *
from ..functions.get_batchid import get_time_stamp
from ..items import TaskspiderItem

header = {
    "User-Agent": "okhttp/3.6.0",
}


class Spider(scrapy.Spider):
    batch_id = get_time_stamp()
    name = "dpzx"
    id = 1163348088140726273
    error_dict = {}

    # 数据库获取自定义字段，初始化
    def set_config(self, items):
        item = items[0]
        self.batch_id = get_time_stamp()
        self.mcht_id = item[0]
        self.zone_id = item[1]
        self.channel = item[2]
        self.username = item[4]
        self.password = item[5]

    # 登录接口
    def start_requests(self):
        print("登录接口尝试")
        data = {
            "account": "13388031120",
            "password": "hqq654321",
            "imei": "355757010667430",
        }
        url = "https://app.dpzaixian.com/api/v5/customer/login?time=" + str(int(time.time()))
        yield scrapy.FormRequest(
            url=url,
            headers=header,
            formdata=data,
            callback=self.Login
        )

    # 接入分类页面
    # 速冻米面、调理美食
    def Login(self, response):
        html = json.loads(response.text)
        if html['code'] == '200':
            print("登录成功")
            token = html['datas']['token']
            print(token)
            gate_url = "https://app.dpzaixian.com/api/v5/goods_category/tree/1?token=" + token + "&time=" + str(
                int(time.time()))
            request = scrapy.Request(
                url=gate_url,
                callback=self.get_gate
            )
            request.meta['token'] = token
            yield request
        else:
            print("登陆失败")
            print("尝试重试登录")
            self.start_requests()

    # 获取分类信息，构建分类URL
    def get_gate(self, response):
        html = json.loads(response.text)
        token = response.meta['token']
        if html['code'] == '200':
            print("分类获取成功")
            for i, text in enumerate(html['datas']):
                print(i)
                if i == 3 or i == 4:
                    g1_id = text['id']
                    g1_name = text['name']
                    for j, text2 in enumerate(text['children']):
                        g2_id = text2['id']
                        g2_name = text2['name']
                        print(g2_id,g2_name)
                        if g2_id == '5':
                            g2_id = str(int(g2_id) + 20)
                            data = {"activityId": "", "activityType": "", "brandIds": [],
                                    "customerRedPacketId": "", "excludeOutOfStock": False,
                                    "keyword": "", "largeCategoryId": "", "mediumCategoryId": g2_id,
                                    "smallCategoryId": "", "citySearchHotId": ""}
                        else:
                            data = {"activityId": "", "activityType": "", "brandIds": [],
                                    "customerRedPacketId": "", "excludeOutOfStock": False,
                                    "keyword": "", "largeCategoryId": "", "mediumCategoryId": g2_id,
                                    "smallCategoryId": "", "citySearchHotId": ""}
                            sku_list_url = "https://app.dpzaixian.com/api/v5/goods/search/result/566974/567017/0/20/1?token=" + token + "&time=" + str(
                                int(time.time()))
                            print(sku_list_url)
                            request = scrapy.FormRequest(
                                url=sku_list_url,
                                formdata=data,
                                headers=header,
                                callback=self.get_sku_list
                            )
                            request.meta['cat1_id'] = g1_id
                            request.meta['cat1_name'] = g1_name
                            request.meta['cat2_id'] = g2_name
                            request.meta['cat2_name'] = g2_name
                            request.meta['token'] = token
                            yield request
        else:
            print("分类获取失败")

    def get_sku_list(self, response):
        print("进入分类列表")
        token = response.meta['token']
        g1_id = response.meta['cat1_id']
        g1_name = response.meta['cat1_name']
        g2_id = response.meta['cat2_id']
        g2_name = response.meta['cat2_name']
        html = json.loads(response.text)
        for text in html['datas']:
            sku_id = text['id']
            sku_name = text['name']
            sku_url = "https://app.dpzaixian.com/api/v5/goods/detail/1/566974/567017/"+sku_id+"?token="+token+"&time="+str(int(time.time()))
            request = scrapy.Request(
                url=sku_url,
                headers=header,
                callback=self.sku
            )
            request.meta['cat1_id'] = g1_id
            request.meta['cat1_name'] = g1_name
            request.meta['cat2_id'] = g2_id
            request.meta['cat2_name'] = g2_name
            request.meta['url'] = sku_url
            request.meta['ids'] = sku_id
            yield request
    def sku(self,response):
        print("商品详情页")
        cat_id = response.meta['cat2_id']
        cat_name = response.meta['cat2_name']
        cat_parents_id = response.meta['cat1_id']
        cat_parents_name = response.meta['cat1_name']
        html = json.loads(response.text)
        text = html['datas']

        brand = text['brand']['name']
        unique_id = text['id'] # unique ID
        name = text['name'] # 商品名
        barcode = text['code'] # 条形码
        exp = text['sheLife']+"天" # 保质期
        img = text['picList']# 图片（List）
        # 大件小件价格区分
        big_price = text['priceList'][0]['taxSalePrice']
        small_price = text['priceList'][1]['taxSalePrice']
        big_spec = text['priceList'][0]['spec']
        small_spec = text['priceList'][1]['spec']
        big_unit = text['priceList'][0]['unitName']
        small_unit = text['priceList'][1]['unitName']

        item = TaskspiderItem()
        item["batch_id"] = self.batch_id
        item["mcht_id"] = self.mcht_id
        item["zone_id"] = self.zone_id
        item["channel"] = self.channel
        item["cat_id"] = cat_id
        item["cat_name"] = cat_name
        item["cat_parents_id"] = cat_parents_id
        item["cat_parents_name"] = cat_parents_name
        item["name"] = name
        item["limit_order"] = 9999
        item["limit_day"] = 9999
        item["moq"] = 1
        item["step"] = 1
        item["inventory"] = -1
        item["barcode"] = barcode
        item["brand"] = brand
        item["brand_first"] = ''
        item["img_url"] = str(img)
        item["is_shelved"] = 1
        item["ea_retail_price"] = '0'
        item["cs_retail_price"] = '0'#
        item["country"] = "中国"
        item["imported"] = 0
        item["actives"] = 0
        item['attrs'] = ''
        item["data_type"] = 1
        item["url"] = response.meta['url']
        item["exp"] = exp
        item["activity_id"] = ''
        item["unique_id"] = unique_id+'1'  #
        item["price"] = small_price#
        item["price_org"] = small_price#
        item["ea_spec"] = small_price.strip()  #
        # 单品单位 —— 无问题
        item["ea_unit"] = small_unit  #
        item["ea_price"] = small_price  #
        item["cs_num"] = ""  # 包装内个数#
        # 售卖单位
        item["cs_unit"] = small_unit#
        item["cs_spec"] = small_spec # 售卖规格#



        big_item = TaskspiderItem()
        big_item["batch_id"] = self.batch_id
        big_item["mcht_id"] = self.mcht_id
        big_item["zone_id"] = self.zone_id
        big_item["channel"] = self.channel
        big_item["cat_id"] = cat_id
        big_item["cat_name"] = cat_name
        big_item["cat_parents_id"] = cat_parents_id
        big_item["cat_parents_name"] = cat_parents_name
        big_item["name"] = name
        big_item["limit_order"] = 9999
        big_item["limit_day"] = 9999
        big_item["moq"] = 1
        big_item["step"] = 1
        big_item["inventory"] = -1
        big_item["barcode"] = barcode
        big_item["brand"] = brand
        big_item["brand_first"] = ''
        big_item["img_url"] = str(img)
        big_item["is_shelved"] = 1
        big_item["ea_retail_price"] = '0'
        big_item["cs_retail_price"] = '0'
        big_item["country"] = "中国"
        big_item["imported"] = 0
        big_item["actives"] = 0
        big_item['attrs'] = ''
        big_item["data_type"] = 1
        big_item["url"] = response.meta['url']
        big_item["exp"] = exp
        big_item["activity_id"] = ''
        big_item["unique_id"] = unique_id+'0'  #
        big_item["price"] = big_unit  #
        big_item["price_org"] = big_price  #
        big_item["ea_spec"] =  big_spec#
        # 单品单位 —— 无问题
        big_item["ea_unit"] = big_unit  #
        big_item["ea_price"] = 0  #
        big_re = re.compile(r'\*[0-9]+')
        try:
            big_item["cs_num"] = big_re.findall(big_spec)[0]  # 包装内个数#
        except:
            big_item['cs_num'] = '1'
        # 售卖单位
        big_item["cs_unit"] = big_unit #
        big_item["cs_spec"] = big_spec  # 售卖规格#

        yield item
        yield big_item