#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Markdown 转换功能
"""

from build_app import convert_markdown_to_html
from pathlib import Path

def test_conversion():
    """测试 markdown 转换"""
    print("测试 Markdown 到 HTML 转换功能...")
    
    # 读取 README.md
    readme_path = Path('README.md')
    if not readme_path.exists():
        print("❌ README.md 文件不存在")
        return False
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        html_content = convert_markdown_to_html(md_content)
        
        # 写入测试 HTML 文件
        test_html_path = Path('test_output.html')
        with open(test_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ 转换成功！测试文件已保存到: {test_html_path.absolute()}")
        print(f"📊 生成的 HTML 文件大小: {test_html_path.stat().st_size} 字节")
        
        # 检查 HTML 内容是否包含基本元素
        if 'h1>' in html_content and '<p>' in html_content and '</body>' in html_content and '</html>' in html_content:
            print("✅ HTML 结构检查通过")
            
            # 检查是否使用了 markdown 库（高级功能）
            if 'id="' in html_content:  # markdown 库会为标题生成 id
                print("✅ 使用 markdown 库转换成功")
            else:
                print("✅ 使用备用方案转换成功")
        else:
            print("⚠️ HTML 结构可能有问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return False

if __name__ == "__main__":
    test_conversion()
