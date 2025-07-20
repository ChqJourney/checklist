"""
配置管理模块
用于管理 system.json（只读）和 user.json（可读写）配置文件
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为当前脚本所在目录
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent
        else:
            self.config_dir = Path(config_dir)
            
        self.system_config_path = self.config_dir / "system.json"
        self.user_config_path = self.config_dir / "user.json"
        
        self._system_config: Optional[Dict[str, Any]] = None
        self._user_config: Optional[Dict[str, Any]] = None
        
        # 加载配置
        self._load_configs()
    
    def _load_configs(self):
        """加载配置文件"""
        self._load_system_config()
        self._load_user_config()
    
    def _load_system_config(self):
        """加载系统配置（只读）"""
        try:
            if self.system_config_path.exists():
                with open(self.system_config_path, 'r', encoding='utf-8') as f:
                    self._system_config = json.load(f)
            else:
                raise FileNotFoundError(f"系统配置文件不存在: {self.system_config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"系统配置文件格式错误: {e}")
        except Exception as e:
            raise RuntimeError(f"加载系统配置失败: {e}")
    
    def _load_user_config(self):
        """加载用户配置（可读写）"""
        try:
            if self.user_config_path.exists():
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    self._user_config = json.load(f)
            else:
                # 如果用户配置文件不存在，创建默认配置
                self._user_config = {}
                self.save_user_config()
        except json.JSONDecodeError as e:
            raise ValueError(f"用户配置文件格式错误: {e}")
        except Exception as e:
            raise RuntimeError(f"加载用户配置失败: {e}")
    
    def reload_configs(self):
        """重新加载所有配置文件"""
        self._load_configs()
    
    def get_system_config(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        获取系统配置
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'log_config.level'
            default: 默认值
            
        Returns:
            配置值
        """
        if self._system_config is None:
            return default
            
        if key is None:
            return self._system_config
            
        return self._get_nested_value(self._system_config, key, default)
    
    def get_user_config(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        获取用户配置
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        if self._user_config is None:
            return default
            
        if key is None:
            return self._user_config
            
        return self._get_nested_value(self._user_config, key, default)
    
    def set_user_config(self, key: str, value: Any):
        """
        设置用户配置
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        if self._user_config is None:
            self._user_config = {}
            
        self._set_nested_value(self._user_config, key, value)
    
    def save_user_config(self):
        """保存用户配置到文件"""
        try:
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                json.dump(self._user_config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise RuntimeError(f"保存用户配置失败: {e}")
    
    def _get_nested_value(self, config: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        获取嵌套配置值
        
        Args:
            config: 配置字典
            key: 配置键，支持点号分隔
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        current = config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
                
        return current
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """
        设置嵌套配置值
        
        Args:
            config: 配置字典
            key: 配置键，支持点号分隔
            value: 配置值
        """
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
            
        current[keys[-1]] = value
    
    # 便捷方法：获取常用配置
    
    def get_subfolder_config(self, team: str = None) -> Dict[str, Any]:
        """获取子文件夹配置"""
        if team is None:
            team = self.get_user_config('team', 'general')
        return self.get_system_config(f'subFolderConfig.{team}', [])
    
    def get_log_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get_system_config('log_config', {})
    
    def get_file_map(self) -> Dict[str, Any]:
        """获取文件映射配置"""
        return self.get_system_config('file_map', {})
    
    def get_base_dir(self) -> str:
        """获取基础目录"""
        return self.get_user_config('base_dir', '')
    
    def set_base_dir(self, base_dir: str):
        """设置基础目录"""
        self.set_user_config('base_dir', base_dir)
        self.save_user_config()
    
    def get_team(self) -> str:
        """获取团队配置"""
        return self.get_user_config('team', 'general')
    
    def set_team(self, team: str):
        """设置团队配置"""
        self.set_user_config('team', team)
        self.save_user_config()


# 全局配置管理器实例
config_manager = ConfigManager()


def get_system_config(key: Optional[str] = None, default: Any = None) -> Any:
    """获取系统配置的便捷函数"""
    return config_manager.get_system_config(key, default)


def get_user_config(key: Optional[str] = None, default: Any = None) -> Any:
    """获取用户配置的便捷函数"""
    return config_manager.get_user_config(key, default)


def set_user_config(key: str, value: Any):
    """设置用户配置的便捷函数"""
    config_manager.set_user_config(key, value)
    config_manager.save_user_config()


def reload_configs():
    """重新加载配置的便捷函数"""
    config_manager.reload_configs()


if __name__ == "__main__":
    # 测试代码
    try:
        # 测试获取系统配置
        print("=== 系统配置测试 ===")
        print("日志配置:", get_system_config('log_config'))
        print("日志级别:", get_system_config('log_config.level'))
        print("子文件夹配置:", config_manager.get_subfolder_config())
        
        # 测试用户配置
        print("\n=== 用户配置测试 ===")
        print("当前团队:", config_manager.get_team())
        print("基础目录:", config_manager.get_base_dir())
        print("用户配置:", config_manager.get_subfolder_config())
        
        # 测试设置用户配置
        # print("\n=== 设置用户配置测试 ===")
        # set_user_config('test_key', 'test_value')
        # print("测试键值:", get_user_config('test_key'))
        
        print("\n配置管理器测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")