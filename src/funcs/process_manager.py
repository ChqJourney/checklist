"""
进程管理模块
负责管理系统进程，特别是Word进程
"""
import psutil
from src.logger.logger import log_info, log_error, log_debug


def kill_all_word_processes():
    """
    结束所有Word进程
    """
    try:
        killed_count = 0
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'WINWORD.EXE':
                proc.kill()
                killed_count += 1
        
        if killed_count > 0:
            log_info(f"已终止 {killed_count} 个Word进程", "WORD")
        else:
            log_debug("没有发现运行中的Word进程", "WORD")
    except Exception as e:
        log_error(f"终止Word进程时发生错误: {e}", "WORD")
