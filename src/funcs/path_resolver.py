"""
路径解析模块
负责解析和获取工作目录路径
"""
import os
import win32com.client as win32
from pathlib import Path
from urllib.parse import unquote
from src.logger.logger import log_debug


def get_working_folder_path(base_dir, team, job_no):
    """
    获取工作目录路径
    :param base_dir: 基础目录
    :param team: 团队名称
    :param job_no: 工作号
    :return: 工作目录路径，如果未找到则返回None
    """
    if team == 'ppt':
        return get_working_folder_path_for_ppt(base_dir, job_no)
    else:
        return get_working_folder_path_for_general(base_dir, job_no)


def get_working_folder_path_for_ppt(shortcuts_path, job_no):
    """
    为PPT团队获取工作文件夹路径（通过快捷方式）
    :param shortcuts_path: 快捷方式文件夹路径
    :param job_no: 工作号
    :return: 工作目录路径，如果未找到则返回None
    """
    try:
        shell = win32.Dispatch("WScript.Shell")
    except ImportError:
        return None
   
    with os.scandir(shortcuts_path) as entries:
        for entry in entries:
            try:
                # 检查是否为快捷方式(.lnk文件)
                if entry.name.lower().endswith('.lnk') and entry.name.lower().startswith(job_no.lower()):
                    shortcut = shell.CreateShortCut(str(entry.path))
                    # Decode URL-encoded characters in the path
                    decoded_path = unquote(shortcut.Targetpath)
                    target_path = Path(decoded_path)
                    return target_path
                # 检查是否为符号链接
                elif entry.is_symlink() and entry.name.lower().startswith(job_no.lower()):
                    target_path = Path(entry.path).readlink()
                    return target_path
            except Exception as e:
                print("error")
                print(e)
                continue
    print("没有找到对应的文件夹")
    return None


def get_working_folder_path_for_general(base_dir, job_no):
    """
    为通用团队获取工作文件夹路径
    :param base_dir: 基础目录
    :param job_no: 工作号
    :return: 工作目录路径，如果未找到则返回None
    """
    sub_year_folder = f"20{job_no[:2]}"
    search_dir = os.path.join(base_dir, sub_year_folder)
    
    # 使用 os.scandir() 只查找第一层目录 (最高效)
    try:
        with os.scandir(search_dir) as entries:
            for entry in entries:
                if entry.is_dir() and entry.name.startswith(job_no):
                    return entry.path
    except (OSError, FileNotFoundError) as e:
        log_debug(f"无法访问目录 {search_dir}: {e}", "FILE")
    
    return None
