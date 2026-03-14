# Flask API 路由

from flask import Blueprint, jsonify, render_template, request
from app.crawlers import crawl_tech_daily, crawl_beijing_kw, crawl_miit
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import logging
import os
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 判断是否在云端运行
RENDER_MODE = os.environ.get('RENDER', 'false').lower() == 'true'

# 收藏文件路径 - 云端使用 /tmp
if RENDER_MODE:
    COLLECTED_FILE = '/tmp/collected.txt'
else:
    COLLECTED_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'collected.txt')

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 全局缓存
news_cache = {
    'tech_daily': [],
    'beijing_kw': [],
    'miit': [],
    'all': [],
    'last_update': None
}

# 缓存有效期（秒）
CACHE_EXPIRE_SECONDS = 300  # 5分钟


def refresh_all_news():
    """刷新所有新闻数据"""
    logger.info("开始刷新新闻数据...")
    
    try:
        news_cache['tech_daily'] = crawl_tech_daily()
        logger.info(f"科技日报: 获取到 {len(news_cache['tech_daily'])} 条")
    except Exception as e:
        logger.error(f"科技日报爬取失败: {e}")
        news_cache['tech_daily'] = []
    
    try:
        news_cache['beijing_kw'] = crawl_beijing_kw()
        logger.info(f"北京市科委: 获取到 {len(news_cache['beijing_kw'])} 条")
    except Exception as e:
        logger.error(f"北京市科委爬取失败: {e}")
        news_cache['beijing_kw'] = []
    
    try:
        news_cache['miit'] = crawl_miit()
        logger.info(f"工信部: 获取到 {len(news_cache['miit'])} 条")
    except Exception as e:
        logger.error(f"工信部爬取失败: {e}")
        news_cache['miit'] = []
    
    # 合并所有新闻
    news_cache['all'] = (
        news_cache['tech_daily'] + 
        news_cache['beijing_kw'] + 
        news_cache['miit']
    )
    
    from datetime import datetime
    news_cache['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    logger.info(f"新闻数据刷新完成，总计 {len(news_cache['all'])} 条")


# 初始化调度器
scheduler = BackgroundScheduler()
scheduler.add_job(func=refresh_all_news, trigger="interval", seconds=CACHE_EXPIRE_SECONDS, id='refresh_news')

# 在云端可能不需要自动刷新，或者使用更简单的策略
if not RENDER_MODE:
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

# 初始加载数据
refresh_all_news()


@api_bp.route('/')
def index():
    """主页"""
    return render_template('index.html')


@api_bp.route('/api/news')
def get_all_news():
    """获取所有新闻"""
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'news': news_cache['all'],
            'total': len(news_cache['all']),
            'last_update': news_cache['last_update']
        }
    })


@api_bp.route('/api/tech-daily')
def get_tech_daily():
    """获取科技日报新闻"""
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'news': news_cache['tech_daily'],
            'total': len(news_cache['tech_daily']),
            'source': '科技日报'
        }
    })


@api_bp.route('/api/beijing-kw')
def get_beijing_kw():
    """获取北京市科委新闻"""
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'news': news_cache['beijing_kw'],
            'total': len(news_cache['beijing_kw']),
            'source': '北京市科委'
        }
    })


@api_bp.route('/api/miit')
def get_miit():
    """获取工信部新闻"""
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'news': news_cache['miit'],
            'total': len(news_cache['miit']),
            'source': '工信部'
        }
    })


@api_bp.route('/api/refresh')
def refresh_news():
    """手动刷新新闻"""
    refresh_all_news()
    return jsonify({
        'code': 200,
        'message': '新闻刷新成功',
        'data': {
            'total': len(news_cache['all']),
            'last_update': news_cache['last_update']
        }
    })


@api_bp.route('/api/collect', methods=['POST'])
def collect_news():
    """收录新闻到txt文件"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        url = data.get('url', '')

        if not title or not url:
            return jsonify({
                'code': 400,
                'message': '标题和网址不能为空'
            })

        # 读取现有收藏
        collected = []
        if os.path.exists(COLLECTED_FILE):
            with open(COLLECTED_FILE, 'r', encoding='utf-8') as f:
                collected = [line.strip() for line in f if line.strip()]

        # 检查是否已收藏（通过URL判断）
        for line in collected:
            if url in line:
                return jsonify({
                    'code': 400,
                    'message': '该链接已收录'
                })

        # 添加收藏记录
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        record = f"{title} | {url} | {timestamp}\n"

        with open(COLLECTED_FILE, 'a', encoding='utf-8') as f:
            f.write(record)

        logger.info(f"收录新闻: {title}")

        return jsonify({
            'code': 200,
            'message': '收录成功'
        })

    except Exception as e:
        logger.error(f"收录失败: {e}")
        return jsonify({
            'code': 500,
            'message': '收录失败'
        })


@api_bp.route('/api/collected')
def get_collected():
    """获取所有已收录的新闻"""
    try:
        collected = []
        if os.path.exists(COLLECTED_FILE):
            with open(COLLECTED_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split(' | ')
                        if len(parts) >= 3:
                            collected.append({
                                'title': parts[0],
                                'url': parts[1],
                                'time': parts[2]
                            })
                        elif len(parts) == 2:
                            collected.append({
                                'title': parts[0],
                                'url': parts[1],
                                'time': ''
                            })

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'collected': collected,
                'total': len(collected)
            }
        })

    except Exception as e:
        logger.error(f"获取已收录失败: {e}")
        return jsonify({
            'code': 500,
            'message': '获取失败'
        })


@api_bp.route('/api/remove', methods=['POST'])
def remove_collected():
    """取消收录"""
    try:
        data = request.get_json()
        url = data.get('url', '')

        if not url:
            return jsonify({
                'code': 400,
                'message': '网址不能为空'
            })

        # 读取现有收藏
        if not os.path.exists(COLLECTED_FILE):
            return jsonify({
                'code': 400,
                'message': '没有已收录的内容'
            })

        with open(COLLECTED_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 过滤掉包含该URL的行
        new_lines = [line for line in lines if url not in line]

        # 写回文件
        with open(COLLECTED_FILE, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        logger.info(f"取消收录: {url}")

        return jsonify({
            'code': 200,
            'message': '取消成功'
        })

    except Exception as e:
        logger.error(f"取消收录失败: {e}")
        return jsonify({
            'code': 500,
            'message': '取消失败'
        })
