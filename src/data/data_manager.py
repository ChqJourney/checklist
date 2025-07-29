"""
全局数据管理器 - 使用单例模式管理共享数据
"""
import threading
import json
from typing import List, Dict, Any

class DataManager:
    """单例模式的数据管理器"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.results = []
            self.tasks = []
            self.current_task_index = 0
            self.is_processing = False
            self._lock = threading.Lock()
            self.initialized = True
    
    def add_result(self, result: Dict[str, Any]) -> None:
        """添加一个结果记录"""
        with self._lock:
            self.results.append(result)
    
    def update_result(self, index: int, result: Dict[str, Any]) -> None:
        """更新指定索引的结果记录"""
        with self._lock:
            if 0 <= index < len(self.results):
                self.results[index] = result
    
    def update_result_by_job_no(self, job_no: str, result: Dict[str, Any]) -> bool:
        """根据工作号更新结果记录，成功返回True，未找到返回False"""
        with self._lock:
            for i, existing_result in enumerate(self.results):
                if existing_result.get('job_no') == job_no:
                    self.results[i] = result
                    return True
            return False
    
    def get_results(self) -> List[Dict[str, Any]]:
        """获取所有结果记录"""
        with self._lock:
            return self.results.copy()
    
    def get_result_by_job_no(self, job_no: str) -> Dict[str, Any]:
        """根据工作号获取结果记录"""
        with self._lock:
            for result in self.results:
                if result.get('job_no') == job_no:
                    return result
        return None
    
    def clear_results(self) -> None:
        """清空所有结果记录"""
        with self._lock:
            self.results.clear()
    
    def set_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """设置任务列表"""
        with self._lock:
            self.tasks = tasks
            self.current_task_index = 0
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取任务列表"""
        with self._lock:
            return self.tasks.copy()
    
    def get_current_task(self) -> Dict[str, Any]:
        """获取当前任务"""
        with self._lock:
            if 0 <= self.current_task_index < len(self.tasks):
                return self.tasks[self.current_task_index]
        return None
    
    def next_task(self) -> bool:
        """移动到下一个任务，返回是否成功"""
        with self._lock:
            if self.current_task_index < len(self.tasks) - 1:
                self.current_task_index += 1
                return True
        return False
    
    def set_processing_status(self, status: bool) -> None:
        """设置处理状态"""
        with self._lock:
            self.is_processing = status
    
    def get_processing_status(self) -> bool:
        """获取处理状态"""
        with self._lock:
            return self.is_processing
    
    def save_to_file(self, filename: str = "results.json") -> None:
        """保存结果到文件"""
        with self._lock:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.results, f, ensure_ascii=False, indent=2)
                print(f"结果已保存到 {filename}")
            except Exception as e:
                print(f"保存结果失败: {e}")
    
    def load_from_file(self, filename: str = "results.json") -> bool:
        """从文件加载结果"""
        with self._lock:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.results = json.load(f)
                print(f"从 {filename} 加载了 {len(self.results)} 条结果")
                return True
            except Exception as e:
                print(f"加载结果失败: {e}")
                return False

# 创建全局实例
data_manager = DataManager()
