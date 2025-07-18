"""
全局日志管理器
支持分级日志、前端显示、文件输出和控制台输出
"""
import json
import os
import threading
from datetime import datetime
from typing import Callable, Optional
from config_manager import get_system_config

class GlobalLogger:
    """全局日志管理器"""
    
    # 日志级别
    LEVELS = {
        'DEBUG': 10,
        'INFO': 20,
        'WARNING': 30,
        'ERROR': 40,
        'CRITICAL': 50
    }

    def __init__(self):
        # 设置默认配置
        config = get_system_config()
        if config is None:
            self.config = {
            "level": "INFO",
            "log_to_console": True,
                "log_to_file": True,
                "log_file_path": "app.log",
                "log_format": "[{timestamp}] [{level}] {message}",
                "max_frontend_logs": 1000,
                "levels": {
                    "DEBUG": {"color": "#6c757d", "icon": "🔍"},
                    "INFO": {"color": "#17a2b8", "icon": "ℹ️"},
                    "WARNING": {"color": "#ffc107", "icon": "⚠️"},
                    "ERROR": {"color": "#dc3545", "icon": "❌"},
                    "CRITICAL": {"color": "#6f42c1", "icon": "🚨"}
                }
            }
        else:
            self.config = config
        self.frontend_callback: Optional[Callable] = None
        self._lock = threading.Lock()
        self.frontend_logs = []  # 存储前端显示的日志

    
    
    def set_frontend_callback(self, callback: Callable):
        """设置前端回调函数"""
        self.frontend_callback = callback
    
    def _should_log(self, level: str) -> bool:
        """判断是否应该记录该级别的日志"""
        current_level = self.LEVELS.get(self.config.get('level', 'INFO'), 20)
        message_level = self.LEVELS.get(level, 20)
        return message_level >= current_level
    
    def _format_message(self, message: str, level: str, module: str = "") -> str:
        """格式化日志消息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        format_template = self.config.get('log_format', '[{timestamp}] [{level}] {message}')
        
        if module:
            message = f"[{module}] {message}"
        
        return format_template.format(
            timestamp=timestamp,
            level=level,
            message=message
        )
    
    def _log_to_file(self, formatted_message: str):
        """写入日志文件"""
        if not self.config.get('log_to_file', False):
            return
        
        try:
            log_file = self.config.get('log_file_path', 'app.log')
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(formatted_message + '\n')
        except Exception as e:
            print(f"写入日志文件失败: {e}")
    
    def _log_to_console(self, formatted_message: str):
        """输出到控制台"""
        if self.config.get('log_to_console', True):
            print(formatted_message)
    
    def _log_to_frontend(self, formatted_message: str, level: str):
        """发送日志到前端"""
        with self._lock:
            # 添加到前端日志列表
            self.frontend_logs.append({
                'message': formatted_message,
                'level': level,
                'timestamp': datetime.now().isoformat()
            })
            
            # 限制前端日志数量
            max_logs = self.config.get('max_frontend_logs', 1000)
            if len(self.frontend_logs) > max_logs:
                self.frontend_logs = self.frontend_logs[-max_logs:]
            
            # 调用前端回调
            if self.frontend_callback:
                try:
                    self.frontend_callback(formatted_message, level)
                except Exception as e:
                    print(f"前端日志回调失败: {e}")
    
    def _escape_for_js(self, text: str) -> str:
        """转义文本以便在JavaScript中安全使用"""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
    
    def log(self, message: str, level: str = 'INFO', module: str = ""):
        """记录日志"""
        level = level.upper()
        
        if not self._should_log(level):
            return
        
        formatted_message = self._format_message(message, level, module)
        
        # 输出到各个目标
        self._log_to_console(formatted_message)
        self._log_to_file(formatted_message)
        self._log_to_frontend(formatted_message, level)
    
    def debug(self, message: str, module: str = ""):
        """记录DEBUG级别日志"""
        self.log(message, 'DEBUG', module)
    
    def info(self, message: str, module: str = ""):
        """记录INFO级别日志"""
        self.log(message, 'INFO', module)
    
    def warning(self, message: str, module: str = ""):
        """记录WARNING级别日志"""
        self.log(message, 'WARNING', module)
    
    def error(self, message: str, module: str = ""):
        """记录ERROR级别日志"""
        self.log(message, 'ERROR', module)
    
    def critical(self, message: str, module: str = ""):
        """记录CRITICAL级别日志"""
        self.log(message, 'CRITICAL', module)
    
    def get_frontend_logs(self) -> list:
        """获取前端日志列表"""
        with self._lock:
            return self.frontend_logs.copy()
    
    def clear_frontend_logs(self):
        """清空前端日志"""
        with self._lock:
            self.frontend_logs.clear()

# 创建全局日志实例
global_logger = GlobalLogger()

# 便捷函数
def log_debug(message: str, module: str = ""):
    global_logger.debug(message, module)

def log_info(message: str, module: str = ""):
    global_logger.info(message, module)

def log_warning(message: str, module: str = ""):
    global_logger.warning(message, module)

def log_error(message: str, module: str = ""):
    global_logger.error(message, module)

def log_critical(message: str, module: str = ""):
    global_logger.critical(message, module)
