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
from pathlib import Path


def print_step(step_name):
    """打印步骤信息"""
    print(f"\n{'='*50}")
    print(f"步骤: {step_name}")
    print(f"{'='*50}")


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
    required_items = ['templates', 'signs', 'user.json', 'system.json','task_list_sample.xlsx']
    
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
