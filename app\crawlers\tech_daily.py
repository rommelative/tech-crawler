# 科技日报爬虫 - 改进版
# 网站: https://www.stdaily.com/

import requests
from datetime import datetime
from bs4 import BeautifulSoup
import json
import re


class TechDailyCrawler:
    """科技日报爬虫"""
    
    def __init__(self):
        self.base_url = "https://www.stdaily.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.stdaily.com/'
        }
    
    def fetch_page(self, url, encoding='utf-8'):
        """获取页面内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = encoding
            return response.text
        except Exception as e:
            print(f"获取页面失败 {url}: {e}")
            return ""
    
    def parse_list_page(self, html, source_name):
        """解析列表页面"""
        news_list = []
        if not html:
            return news_list
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尝试多种选择器
        selectors = [
            '.news-list li a',
            '.list-item a',
            '.article-item a',
            '.con-list li a',
            'ul.news-list a',
            '.container a[href*="html"]',
            '.main-content a[href*="html"]',
            'div[class*="list"] a',
            '.index_NoticeList a',
            '.index_NewsList a'
        ]
        
        for selector in selectors:
            articles = soup.select(selector)
            if len(articles) >= 3:
                for article in articles:
                    try:
                        title = article.get_text(strip=True)
                        href = article.get('href', '')
                        
                        if title and len(title) > 8 and not title.startswith('http'):
                            if href and not href.startswith('http'):
                                href = self.base_url + href
                            
                            # 过滤无关链接
                            if any(skip in href.lower() for skip in ['javascript', '#', 'login', 'register', 'about', 'contact']):
                                continue
                                
                            news_list.append({
                                'title': title,
                                'url': href,
                                'source': source_name,
                                'pub_time': '',
                                'summary': ''
                            })
                    except Exception:
                        continue
                
                if news_list:
                    break
        
        # 备选方案：直接查找所有包含.html的链接
        if len(news_list) < 3:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                try:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    # 过滤条件
                    if (title and len(title) > 10 and 
                        '.html' in href and
                        not any(skip in href.lower() for skip in ['javascript', '#', 'login', 'register', 'about', 'contact', 'english', 'web/'])):
                        if not href.startswith('http'):
                            href = self.base_url + href
                        
                        # 避免重复
                        if not any(n['url'] == href for n in news_list):
                            news_list.append({
                                'title': title,
                                'url': href,
                                'source': source_name,
                                'pub_time': '',
                                'summary': ''
                            })
                except Exception:
                    continue
        
        return news_list
    
    def fetch(self):
        """获取所有科技日报新闻"""
        all_news = []
        
        # 尝试多个页面
        pages = [
            ('', '科技日报'),
            ('index/kejixinwen/index.shtml', '科技日报-科技要闻'),
            ('index/yaowen/index.shtml', '科技日报-要闻'),
            ('index/tpxw/index.shtml', '科技日报-图片新闻'),
            ('web/yaowen/', '科技日报-新闻'),
            ('web/zonghe/', '科技日报-综合'),
        ]
        
        for path, name in pages:
            url = self.base_url + '/' + path if path else self.base_url
            html = self.fetch_page(url)
            news = self.parse_list_page(html, name)
            all_news.extend(news)
            print(f"科技日报 {name}: 获取 {len(news)} 条")
        
        # 去重
        seen = set()
        unique_news = []
        for news in all_news:
            if news['title'] not in seen:
                seen.add(news['title'])
                unique_news.append(news)
        
        return unique_news[:30]  # 限制返回数量


def crawl_tech_daily():
    """科技日报爬取入口"""
    crawler = TechDailyCrawler()
    return crawler.fetch()


if __name__ == '__main__':
    news = crawl_tech_daily()
    print(f"\n总计获取到 {len(news)} 条科技日报新闻")
    for item in news[:10]:
        print(f"- {item['title']}")
