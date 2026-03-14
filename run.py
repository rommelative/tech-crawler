# 科技资讯爬虫项目
# 启动文件

import os
from app import create_app

app = create_app()

# Render 会通过环境变量 PORT 提供端口
port = int(os.environ.get('PORT', 5001))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=False)
