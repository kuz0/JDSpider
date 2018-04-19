from scrapy.conf import settings
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from traceback import format_exc


class JdPipeline(object):
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.client = None
        self.db = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(mongo_uri=crawler.settings.get('MONGODB_URI'),
                   mongo_db=settings.get('MONGODB_DATABASE', 'items'))  # 提取 mongodb 配置

    def open_spider(self, spider):
        _ = spider
        self.client = MongoClient(self.mongo_uri)  # 连接数据库
        self.db = self.client[self.mongo_db]
        self.db['jd_info'].ensure_index('item_id', unique=True)  # 在表 jd_info 中建立索引，并保证索引的唯一性

    def close_spider(self, spider):
        _ = spider
        self.client.close()  # 关闭数据库

    def process_item(self, item, spider):
        try:  # 通过 id 判断，有就更新，没有就插入
            self.db['jd_info'].update({'item_id': item['item_id']}, {'$set': item}, upsert=True)

        except DuplicateKeyError:
            spider.logger.debug('duplicate key error collection')  # 唯一键冲突报错

        except Exception as e:
            _ = e
            spider.logger.error(format_exc())

        return item