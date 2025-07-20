
import os

import webview
from src.gui_main import ProjectFileChecker


if __name__ == "__main__":
    # 创建API实例
    api = ProjectFileChecker()

    if __name__ == '__main__':
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 设置当前工作目录为脚本所在目录
        # 构建前端HTML文件的绝对路径
        html_path = os.path.join(current_dir,'src', 'static', 'index.html')
    
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