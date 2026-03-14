# 爬虫模块初始化文件

from .tech_daily import crawl_tech_daily
from .beijing_kw import crawl_beijing_kw
from .miit import crawl_miit

__all__ = [
    'crawl_tech_daily',
    'crawl_beijing_kw',
    'crawl_miit'
]
