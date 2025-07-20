"""
任务工具模块
负责任务状态更新和进度记录
"""
import datetime
from src.data.data_manager import data_manager


def update_task_status(job_no: str, status: str):
    """更新任务状态"""
    result = data_manager.get_result_by_job_no(job_no)
    if result:
        result['status'] = status
        print(f"更新任务 {job_no} 状态为: {status}")


def log_task_progress(job_no: str, message: str):
    """记录任务进度"""
    result = data_manager.get_result_by_job_no(job_no)
    if result:
        if 'logs' not in result:
            result['logs'] = []
        result['logs'].append({
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': message
        })
        print(f"任务 {job_no}: {message}")
