# 导入 GUI 模块并启动 GUI 应用
import sys
import os

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入并启动 GUI
from gui_main import api
import webview

def main():
    """启动 GUI 应用"""
    # 构建前端HTML文件的绝对路径
    html_path = os.path.join(current_dir, 'static', 'index.html')
    
    # 将文件路径转换为url格式
    html_url = 'file:///' + html_path.replace('\\', '/')
    
    # 获取图标路径
    icon_path = os.path.join(current_dir, 'check.ico')
    
    # 创建窗口
    window = webview.create_window(
        'Project File Checker',
        url=html_url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(1000, 600),
        resizable=True
    )
    
    # 启动应用
    webview.start(debug=False, icon=icon_path)

if __name__ == "__main__":
    main()
