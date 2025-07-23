#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序构建脚本
自动编译生成 Check list.exe 并复制必要的文件到同级目录
"""

import os
import shutil
import subprocess
import sys
import re
from pathlib import Path

try:
    import markdown
    from markdown.extensions import toc, tables, fenced_code, codehilite
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


def print_step(step_name):
    """打印步骤信息"""
    print(f"\n{'='*50}")
    print(f"步骤: {step_name}")
    print(f"{'='*50}")


def convert_markdown_to_html(md_content):
    """
    使用 markdown 库进行高质量的 Markdown 到 HTML 转换
    如果 markdown 库不可用，则使用简单的正则转换作为备用
    """
    if MARKDOWN_AVAILABLE:
        try:
            # 使用 markdown 库进行转换
            md = markdown.Markdown(
                extensions=[
                    'toc',          # 目录支持
                    'tables',       # 表格支持
                    'fenced_code',  # 代码块支持
                    'codehilite',   # 代码高亮
                    'nl2br',        # 换行转换
                    'sane_lists',   # 更好的列表处理
                ],
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight',
                        'use_pygments': False,
                    }
                }
            )
            
            html_body = md.convert(md_content)
            
            # 创建完整的HTML文档
            full_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Check List 使用说明</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px;
            background-color: #fff;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 0.8em;
            font-weight: 600;
        }}
        h1 {{
            font-size: 2.5em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
        }}
        h2 {{
            font-size: 2em;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }}
        h3 {{
            font-size: 1.6em;
            color: #34495e;
        }}
        p {{
            margin-bottom: 1.2em;
            text-align: justify;
        }}
        ul, ol {{
            margin-bottom: 1.5em;
            padding-left: 2em;
        }}
        li {{
            margin-bottom: 0.8em;
            line-height: 1.6;
        }}
        code {{
            background-color: #f8f9fa;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            color: #e74c3c;
            border: 1px solid #e1e8ed;
        }}
        pre {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            border: 1px solid #e1e8ed;
            margin: 1.5em 0;
        }}
        pre code {{
            background: none;
            padding: 0;
            border: none;
            color: #333;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 1.5em 0;
            padding: 1em 1.5em;
            background-color: #f9f9f9;
            color: #666;
            font-style: italic;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1.5em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px 15px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: 600;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 15px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}
        em {{
            color: #7f8c8d;
            font-style: italic;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: all 0.3s ease;
        }}
        a:hover {{
            color: #2980b9;
            border-bottom-color: #2980b9;
        }}
        .toc {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 2em 0;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 1em;
        }}
        .toc > ul {{
            padding-left: 0;
        }}
        .toc a {{
            color: #495057;
            font-weight: 500;
        }}
        .highlight {{
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        @media (max-width: 768px) {{
            body {{
                padding: 20px 15px;
            }}
            h1 {{
                font-size: 2em;
            }}
            h2 {{
                font-size: 1.6em;
            }}
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>'''
            
            return full_html
            
        except Exception as e:
            print(f"⚠ 使用 markdown 库转换失败，使用备用方案: {e}")
    
    # 备用的简单转换（如果 markdown 库不可用）
    return _simple_markdown_to_html(md_content)


def _simple_markdown_to_html(md_content):
    """
    简单的 Markdown 到 HTML 转换（备用方案）
    """
    html = md_content
    
    # 转换标题
    html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # 转换粗体和斜体
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    html = re.sub(r'<bold>(.*?)</bold>', r'<strong>\1</strong>', html)
    
    # 转换链接和图片
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\s+"([^"]+)"\s+width="(\d+)"\s+height="(\d+)"\)', 
                  r'<img src="\2" alt="\1" title="\3" width="\4" height="\5">', html)
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', html)
    html = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # 转换代码块
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # 转换列表
    lines = html.split('\n')
    in_list = False
    result_lines = []
    
    for line in lines:
        if re.match(r'^\s*[\d]+\.\s', line):  # 有序列表
            if not in_list:
                result_lines.append('<ol>')
                in_list = 'ol'
            item = re.sub(r'^\s*[\d]+\.\s*(.*)$', r'<li>\1</li>', line)
            result_lines.append(item)
        elif re.match(r'^\s*[-*]\s', line):  # 无序列表
            if not in_list:
                result_lines.append('<ul>')
                in_list = 'ul'
            elif in_list == 'ol':
                result_lines.append('</ol>')
                result_lines.append('<ul>')
                in_list = 'ul'
            item = re.sub(r'^\s*[-*]\s*(.*)$', r'<li>\1</li>', line)
            result_lines.append(item)
        else:
            if in_list:
                result_lines.append(f'</{in_list}>')
                in_list = False
            if line.strip():
                result_lines.append(f'<p>{line}</p>')
            else:
                result_lines.append('')
    
    if in_list:
        result_lines.append(f'</{in_list}>')
    
    html = '\n'.join(result_lines)
    
    # 创建完整的HTML文档
    full_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Check List 使用说明</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }}
        h1 {{ font-size: 2.2em; }}
        h2 {{ font-size: 1.8em; }}
        h3 {{ font-size: 1.4em; }}
        p {{ margin-bottom: 1em; }}
        ul, ol {{ margin-bottom: 1em; padding-left: 30px; }}
        li {{ margin-bottom: 0.5em; }}
        code {{
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            color: #e74c3c;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin: 10px 0;
        }}
        strong {{ color: #2c3e50; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
{html}
</body>
</html>'''
    
    return full_html


def run_command(command, description):
    """运行命令并处理错误"""
    print(f"\n执行: {description}")
    print(f"命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            print("输出:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: {e}")
        if e.stdout:
            print(f"标准输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False


def copy_files_and_folders():
    """复制必要的文件和文件夹到dist目录"""
    print_step("复制必要文件到输出目录")
    
    # 获取当前目录和dist目录路径
    current_dir = Path(__file__).parent
    dist_dir = current_dir / 'dist'
    
    if not dist_dir.exists():
        print(f"错误: dist目录不存在: {dist_dir}")
        return False
    
    # 需要复制的文件和文件夹
    items_to_copy = [
        ('templates', '模板文件夹'),
        ('signs', '签名图片文件夹'),
        ('user.json', '用户配置文件'),
        ('system.json', '系统配置文件'),
        ('task_list_sample.xlsx', '任务列表示例文件'),
        ('docs', '图片文件夹'),
    ]
    
    success = True
    
    for item, description in items_to_copy:
        source = current_dir / item
        dest = dist_dir / item
        
        if source.exists():
            try:
                if source.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(source, dest)
                    print(f"✓ 复制文件夹: {item} -> {dest}")
                else:
                    shutil.copy2(source, dest)
                    print(f"✓ 复制文件: {item} -> {dest}")
            except Exception as e:
                print(f"✗ 复制 {description} 失败: {e}")
                success = False
        else:
            print(f"⚠ 跳过不存在的项目: {item}")
    
    # 转换 README.md 为 HTML 并复制
    readme_md = current_dir / 'README.md'
    if readme_md.exists():
        try:
            with open(readme_md, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            html_content = convert_markdown_to_html(md_content)
            readme_html = dist_dir / 'README.html'
            
            with open(readme_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✓ 转换并复制文件: README.md -> {readme_html}")
        except Exception as e:
            print(f"✗ 转换 README.md 失败: {e}")
            success = False
    else:
        print(f"⚠ README.md 不存在，跳过转换")
    
    return success


def clean_build_dirs():
    """清理构建目录"""
    print_step("清理旧的构建文件")
    
    dirs_to_clean = ['build', 'dist']
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"✓ 删除目录: {dir_name}")
            except Exception as e:
                print(f"✗ 删除目录 {dir_name} 失败: {e}")
                return False
        else:
            print(f"○ 目录不存在: {dir_name}")
    
    return True


def build_executable():
    """使用PyInstaller构建可执行文件"""
    print_step("使用PyInstaller构建可执行文件")
    
    # 检查main.spec文件是否存在
    if not Path('main.spec').exists():
        print("错误: main.spec 文件不存在")
        return False
    
    # 运行PyInstaller
    command = "pyinstaller main.spec"
    return run_command(command, "构建可执行文件")


def verify_build():
    """验证构建结果"""
    print_step("验证构建结果")
    
    dist_dir = Path('dist')
    exe_file = dist_dir / 'Check list.exe'
    
    if not exe_file.exists():
        print(f"✗ 可执行文件不存在: {exe_file}")
        return False
    
    print(f"✓ 可执行文件已生成: {exe_file}")
    
    # 检查文件大小
    file_size = exe_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"文件大小: {size_mb:.2f} MB")
    
    # 检查必要文件是否存在
    required_items = ['templates', 'signs', 'user.json', 'system.json','task_list_sample.xlsx', 'docs', 'README.html']

    for item in required_items:
        item_path = dist_dir / item
        if item_path.exists():
            if item_path.is_dir():
                file_count = len(list(item_path.iterdir()))
                print(f"✓ {item} 文件夹存在 (包含 {file_count} 个项目)")
            else:
                print(f"✓ {item} 文件存在")
        else:
            print(f"⚠ {item} 不存在")
    
    return True


def main():
    """主函数"""
    print("Check list 应用程序构建脚本")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查必要工具
    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
        print("✓ PyInstaller 已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ PyInstaller 未安装，请运行: pip install pyinstaller")
        return False
    
    # 构建步骤
    steps = [
        ("清理构建目录", clean_build_dirs),
        ("构建可执行文件", build_executable),
        ("复制必要文件", copy_files_and_folders),
        ("验证构建结果", verify_build),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n✗ 构建失败于步骤: {step_name}")
            return False
    
    print_step("构建完成")
    print("✓ Check list.exe 构建成功！")
    print(f"输出目录: {Path('dist').absolute()}")
    print("\n您可以在 dist 目录中找到完整的应用程序文件。")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
