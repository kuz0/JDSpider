# -*- coding: utf-8 -*-
import re
import json
from pprint import pprint
from scrapy.http import Request
from scrapy.spiders import Rule
from scrapy_redis.spiders import CrawlSpider
from scrapy.linkextractors import LinkExtractor


class JDSpider(CrawlSpider):
    name = 'jd_spider'
    allowed_domains = ['jd.com', 'p.3.cn']
    start_urls = ['http://m.jd.com/']

    rules = (
        Rule(LinkExtractor(allow=()),  # 允许所有链接
             callback='parse_item',  # 回调 parse_item 函数
             follow=True),  # 跟进链接，这里最后要跟个逗号
    )

    def parse_item(self, response):
        # 提取出匹配正则的链接
        item_urls = LinkExtractor(allow=r'(http|https)://item.m.jd.com/product/\d+.html').extract_links(response)
        # 正则表达式以拿到 id
        get_id = re.compile(r'(http|https)://item.m.jd.com/product/(\d+).html')
        # 收集 id 的集合
        item_ids = list()

        for url in item_urls:
            item_id = get_id.search(url.url).group(2)  # 取出商品 id
            item_ids.append(item_id)  # 加入 item_ids

        for it in item_ids:
            # 详情页 URL: https://item.m.jd.com/ware/detail.json?wareId={}
            yield Request('https://item.m.jd.com/ware/detail.json?wareId={}'.format(it),
                          callback=self.detail_page,
                          meta={'id': it},
                          priority=5)

    def detail_page(self, response):
        data = json.loads(response.text)
        # 价格页 URL: https://p.3.cn/prices/mgets?type=1&skuIds=J_{}
        yield Request('https://p.3.cn/prices/mgets?type=1&skuIds=J_{}'.format(response.meta['id']),
                      callback=self.price_page,
                      meta={'id': response.meta['id'],
                            'data': data},
                      priority=10)

    def price_page(self, response):
        _ = self
        data = json.loads(response.text)
        detail_data = response.meta['data']
        item_id = response.meta['id']
        item = {'price': data,
                'detail': detail_data,
                'item_id': item_id}
        pprint(item)
        yield item  # 传给管道
