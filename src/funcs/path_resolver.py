"""
路径解析模块
负责解析和获取工作目录路径
"""
import os
import win32com.client as win32
import pythoncom
from win32com.shell import shell, shellcon
from pathlib import Path
from urllib.parse import unquote
from src.logger.logger import log_debug, log_error, log_info


def get_working_folder_path(base_dir, team, job_no):
    """
    获取工作目录路径
    :param base_dir: 基础目录
    :param team: 团队名称
    :param job_no: 工作号
    :return: 工作目录路径，如果未找到则返回None
    """
    if team == 'PPT':
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
    log_info(f"正在PPT快捷方式路径 {shortcuts_path} 中查找工作号 {job_no} 对应的文件夹", "PATH")
    with os.scandir(shortcuts_path) as entries:
        for entry in entries:
            try:
                # 检查是否为快捷方式(.lnk文件)
                if entry.name.lower().endswith('.lnk') and entry.name.lower().startswith(job_no.lower()):
                    log_info(f"找到快捷方式文件: {entry.path}", "PATH")
                    link_info=get_lnk_target_path(entry.path)
                    if not link_info or not link_info.get("target_path"):
                        continue
                    log_info(f"快捷方式目标路径: {link_info.get('target_path')}", "PATH")
                    #shortcut = shell.CreateShortCut(str(entry.path))
                    # Decode URL-encoded characters in the path
                    
                    #decoded_path = unquote(shortcut.Targetpath)
                    #target_path = Path(decoded_path)
                    #log_info(f"找到工作目录: {decoded_path}", "PATH1")
                    target_path = Path(link_info.get("target_path"))
                    return target_path
                # 检查是否为符号链接
                elif entry.is_symlink() and entry.name.lower().startswith(job_no.lower()):
                    target_path = Path(entry.path).readlink()
                    log_info(f"找到工作目录: {target_path}", "PATH2")
                    return target_path
            except Exception as e:
                print("error")
                print(e)
                continue
    print("没有找到对应的文件夹")
    return None

def get_lnk_target_path(lnk_path):
    """
    使用pywin32获取快捷方式的目标路径。
    能处理文件、文件夹、URL等，对于非文件目标，TargetPath可能为空。
    """
    # 确保路径是绝对路径
    lnk_path = os.path.abspath(lnk_path)
    
    try:
        # 初始化COM
        pythoncom.CoInitialize()
        
        # 创建Shell对象
        shell_link = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink,
            None,
            pythoncom.CLSCTX_INPROC_SERVER,
            shell.IID_IShellLink
        )
        
        # 从文件加载快捷方式数据
        persist_file = shell_link.QueryInterface(pythoncom.IID_IPersistFile)
        persist_file.Load(lnk_path)

        # 获取目标路径
        target_path = shell_link.GetPath(shell.SLGP_SHORTPATH)[0]
        
        # 获取其他可能包含目标信息的字段
        # 对于URL或命令，目标通常在这里
        arguments = shell_link.GetArguments()
        
        # 获取ID列表，对于虚拟对象（如“此电脑”）目标在这里
        id_list = shell_link.GetIDList()

        # 清理COM
        shell_link = None
        persist_file = None
        
        return {
            "target_path": target_path,
            "arguments": arguments,
            "has_id_list": id_list is not None
        }

    except Exception as e:
        log_error(f"Error processing {lnk_path}: {e}")
        return None
    finally:
        # 释放COM
        pythoncom.CoUninitialize()

def get_working_folder_path_for_general(base_dir, job_no):
    """
    为通用团队获取工作文件夹路径
    :param base_dir: 基础目录
    :param job_no: 工作号
    :return: 工作目录路径，如果未找到则返回None
    """
    if not job_no or len(job_no) < 8:
        log_debug(f"工作号 {job_no} 无效，无法获取工作目录路径", "PATH")
        return None
    # 构造年份文件夹名称 (假设工作号前两位表示年份，如23表示2023年)
    sub_year_folder = f"20{job_no[:2]}"
    search_dir = os.path.join(base_dir, sub_year_folder)
    
    # 使用 os.scandir() 只查找第一层目录 (最高效)
    try:
        with os.scandir(search_dir) as entries:
            for entry in entries:
                if entry.is_dir() and entry.name.startswith(job_no):
                    log_debug(f"找到工作目录: {entry.path}", "PATH")
                    return entry.path
    except (OSError, FileNotFoundError, PermissionError) as e:
        log_debug(f"无法访问目录 {search_dir}: {e}", "FILE")
    else:
        # 只有在目录可访问但未找到匹配项时才记录此日志
        log_debug(f"在目录 {search_dir} 中未找到以 {job_no} 开头的文件夹", "PATH")
    
    return None
