"""
配置管理模块
用于管理 system.json（只读）和 user.json（可读写）配置文件
"""

import json
import os
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
import re


class ConfigManager:
    """配置管理器类"""
    
    # 系统配置规范定义
    SYSTEM_CONFIG_SCHEMA = {
        'required_keys': ['subFolderConfig', 'log_config', 'file_map'],
        'subFolderConfig': {
            'required_teams': ['general', 'ppt'],
            'field_schema': {
                'any_of_keys': ['fields', 'options'],  # 只需要其中之一
                'fields': {
                    'required_fields': ['job_no'],
                    'field_types': ['text', 'date', 'image']
                }
            }
        },
        'log_config': {
            'required_keys': ['level', 'log_file_path', 'levels']
        },
        'file_map': {
            'allowed_extensions': ['*.*', '*.pdf', '*.doc', '*.docx', '*.xls', '*.xlsx', 
                                  '*.jpg', '*.jpeg', '*.png', '*.bmp', '*.lnk']
        }
    }
    
    # 用户配置规范定义
    USER_CONFIG_SCHEMA = {
        'required_keys': ['team', 'base_dir','checklist', 'task_list_map'],
        'allowed_keys': ['team', 'base_dir', 'task_list_map', 'checklist'],
        'team': {
            'allowed_values': ['general', 'ppt']
        },
        'base_dir': {
            'type': str,
            'must_exist': False  # 目录可以不存在，但路径格式要正确
        },
        'task_list_map': {
            'type': dict,
            'required_keys': ['job_no']
        },
        'checklist': {
            'type': str,
            'allowed_values': ['cover', 'fill']
        }
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为项目根目录
        """
        if config_dir is None:
            # 检测运行环境并设置配置文件路径
            self.config_dir = self._get_config_directory()
        else:
            self.config_dir = Path(config_dir)
            
        self.system_config_path = self.config_dir / "system.json"
        self.user_config_path = self.config_dir / "user.json"
        
        self._system_config: Optional[Dict[str, Any]] = None
        self._user_config: Optional[Dict[str, Any]] = None
        
        # 加载配置
        self._load_configs()
    
    def _get_config_directory(self) -> Path:
        """
        根据运行环境确定配置文件目录
        
        Returns:
            配置文件目录路径
        """
        if getattr(sys, 'frozen', False):
            # 生产环境：PyInstaller打包后的exe环境
            # sys.executable 指向exe文件路径
            # 配置文件在exe文件同级目录
            executable_dir = Path(sys.executable).parent
            print(f"检测到生产环境，配置文件目录: {executable_dir}")
            return executable_dir
        else:
            # 开发环境：从源码运行
            # 获取项目根目录 (从 src/config 向上两级)
            project_root = Path(__file__).parent.parent.parent
            print(f"检测到开发环境，配置文件目录: {project_root}")
            return project_root
    
    def _load_configs(self):
        """加载配置文件"""
        self._load_system_config()
        self._load_user_config()
        # 验证配置
        self._validate_configs()
    
    def _load_system_config(self):
        """加载系统配置（只读）"""
        try:
            if self.system_config_path.exists():
                with open(self.system_config_path, 'r', encoding='utf-8') as f:
                    self._system_config = json.load(f)
                # 基本格式验证
                self._validate_json_format(self._system_config, "系统配置")
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
                # 基本格式验证
                self._validate_json_format(self._user_config, "用户配置")
            else:
                # 如果用户配置文件不存在，创建默认配置
                self._user_config = self._create_default_user_config()
                self.save_user_config()
        except json.JSONDecodeError as e:
            raise ValueError(f"用户配置文件格式错误: {e}")
        except Exception as e:
            raise RuntimeError(f"加载用户配置失败: {e}")
    
    def _validate_json_format(self, config: Any, config_name: str):
        """验证JSON基本格式"""
        if not isinstance(config, dict):
            raise ValueError(f"{config_name}必须是JSON对象格式")
        
        if not config:
            raise ValueError(f"{config_name}不能为空")
    
    def _validate_configs(self):
        """验证配置内容的规范性"""
        try:
            self._validate_system_config()
            self._validate_user_config()
        except Exception as e:
            raise ValueError(f"配置验证失败: {e}")
    
    def _validate_system_config(self):
        """验证系统配置"""
        if not self._system_config:
            raise ValueError("系统配置为空")
        
        schema = self.SYSTEM_CONFIG_SCHEMA
        
        # 检查必需的顶级键
        for key in schema['required_keys']:
            if key not in self._system_config:
                raise ValueError(f"系统配置缺少必需键: {key}")
        
        # 验证 subFolderConfig
        self._validate_subfolder_config()
        
        # 验证 log_config
        self._validate_log_config()
        
        # 验证 file_map
        self._validate_file_map()
    
    def _validate_subfolder_config(self):
        """验证子文件夹配置"""
        subfolder_config = self._system_config.get('subFolderConfig', {})
        schema = self.SYSTEM_CONFIG_SCHEMA['subFolderConfig']
        
        # 检查必需的团队配置
        for team in schema['required_teams']:
            if team not in subfolder_config:
                raise ValueError(f"系统配置中缺少团队配置: {team}")
            
            team_config = subfolder_config[team]
            if not isinstance(team_config, list) or not team_config:
                raise ValueError(f"团队 {team} 的配置必须是非空列表")
            
            # 验证每个团队配置项
            for i, config_item in enumerate(team_config):
                self._validate_team_config_item(config_item, team, i)
    
    def _validate_team_config_item(self, config_item: Dict, team: str, index: int):
        """验证单个团队配置项"""
        field_schema = self.SYSTEM_CONFIG_SCHEMA['subFolderConfig']['field_schema']
        
        # 检查必需的顶级键（如果存在required_keys）
        if 'required_keys' in field_schema:
            for key in field_schema['required_keys']:
                if key not in config_item:
                    raise ValueError(f"团队 {team}[{index}] 缺少必需键: {key}")
        
        # 检查any_of_keys（只需要其中之一）
        if 'any_of_keys' in field_schema:
            any_keys = field_schema['any_of_keys']
            found_keys = [key for key in any_keys if key in config_item]
            if not found_keys:
                raise ValueError(f"团队 {team}[{index}] 必须包含以下键中的至少一个: {any_keys}")
        
        # 验证 fields（如果存在）
        if 'fields' in config_item:
            fields = config_item.get('fields', {})
            if 'fields' in field_schema and 'required_fields' in field_schema['fields']:
                for required_field in field_schema['fields']['required_fields']:
                    if required_field not in fields:
                        raise ValueError(f"团队 {team}[{index}] 缺少必需字段: {required_field}")
        
        # 验证字段类型（如果存在fields）
        if 'fields' in config_item:
            fields = config_item.get('fields', {})
            for field_name, field_config in fields.items():
                self._validate_field_config(field_config, team, index, field_name)
        
        # 验证 options（如果存在）
        if 'options' in config_item:
            options = config_item.get('options', {})
            if not isinstance(options, dict):
                raise ValueError(f"团队 {team}[{index}] 的 options 必须是字典")
    
    def _validate_field_config(self, field_config: Any, team: str, index: int, field_name: str):
        """验证字段配置"""
        allowed_types = self.SYSTEM_CONFIG_SCHEMA['subFolderConfig']['field_schema']['fields']['field_types']
        
        if isinstance(field_config, dict):
            # 单个字段配置
            field_type = field_config.get('type')
            if field_type not in allowed_types:
                raise ValueError(f"团队 {team}[{index}] 字段 {field_name} 的类型 {field_type} 不被支持")
            
            # 验证 indexes
            indexes = field_config.get('indexes')
            if indexes is not None and not isinstance(indexes, list):
                raise ValueError(f"团队 {team}[{index}] 字段 {field_name} 的 indexes 必须是列表")
                
        elif isinstance(field_config, list):
            # 多个字段配置
            for i, sub_config in enumerate(field_config):
                if isinstance(sub_config, dict):
                    self._validate_field_config(sub_config, team, index, f"{field_name}[{i}]")
        else:
            raise ValueError(f"团队 {team}[{index}] 字段 {field_name} 的配置格式错误")
    
    def _validate_log_config(self):
        """验证日志配置"""
        log_config = self._system_config.get('log_config', {})
        schema = self.SYSTEM_CONFIG_SCHEMA['log_config']
        
        for key in schema['required_keys']:
            if key not in log_config:
                raise ValueError(f"日志配置缺少必需键: {key}")
        
        # 验证日志级别
        level = log_config.get('level', '').upper()
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if level not in valid_levels:
            raise ValueError(f"无效的日志级别: {level}. 支持的级别: {valid_levels}")

        # 验证日志文件路径
        log_file_path = log_config.get('log_file_path')
        if not isinstance(log_file_path, str):
            raise ValueError("log_file_path 必须是字符串")

        if not log_file_path:
            raise ValueError("log_file_path 不能为空")

        # 验证日志级别列表
        levels = log_config.get('levels', [])
        if not isinstance(levels, dict):
            raise ValueError("levels 必须是字典")

        for lvl in levels:
            if lvl not in valid_levels:
                raise ValueError(f"无效的日志级别: {lvl}. 支持的级别: {valid_levels}")

        
    
    def _validate_file_map(self):
        """验证文件映射配置"""
        file_map = self._system_config.get('file_map', {})
        schema = self.SYSTEM_CONFIG_SCHEMA['file_map']
        allowed_extensions = schema['allowed_extensions']
        
        for category, patterns in file_map.items():
            if not isinstance(patterns, list):
                raise ValueError(f"文件映射 {category} 必须是列表")
            
            for pattern in patterns:
                if not isinstance(pattern, str):
                    raise ValueError(f"文件映射 {category} 中的模式必须是字符串")
                
                # 验证文件扩展名模式
                if pattern and not any(self._pattern_matches(pattern, ext) for ext in allowed_extensions):
                    # 这是一个警告而不是错误，因为可能有特殊的文件模式
                    print(f"警告: 文件映射 {category} 中的模式 '{pattern}' 可能不是标准格式")
    
    def _pattern_matches(self, pattern: str, allowed: str) -> bool:
        """检查模式是否匹配允许的扩展名"""
        if allowed == "*.*":
            return True
        if pattern == allowed:
            return True
        # 简单的通配符匹配
        pattern_regex = pattern.replace('*', '.*').replace('.', r'\.')
        allowed_regex = allowed.replace('*', '.*').replace('.', r'\.')
        try:
            return bool(re.match(pattern_regex, allowed) or re.match(allowed_regex, pattern))
        except:
            return False
    
    def _validate_user_config(self):
        """验证用户配置"""
        if not self._user_config:
            raise ValueError("用户配置为空")
        
        schema = self.USER_CONFIG_SCHEMA
        
        # 检查必需键
        for key in schema['required_keys']:
            if key not in self._user_config:
                raise ValueError(f"用户配置缺少必需键: {key}")
        
        # 检查不允许的键
        allowed_keys = schema['allowed_keys']
        for key in self._user_config:
            if key not in allowed_keys:
                raise ValueError(f"用户配置包含未知键: {key}")
        
        # 验证 team
        team = self._user_config.get('team')
        if team not in schema['team']['allowed_values']:
            raise ValueError(f"无效的团队配置: {team}. 允许的值: {schema['team']['allowed_values']}")
        
        # 验证 base_dir
        base_dir = self._user_config.get('base_dir')
        if not isinstance(base_dir, str):
            raise ValueError("base_dir 必须是字符串")
        
        if base_dir:  # 如果不为空，验证路径格式
            try:
                path_obj = Path(base_dir)
                if not path_obj.is_absolute():
                    raise ValueError("base_dir 必须是绝对路径")
            except Exception as e:
                raise ValueError(f"base_dir 路径格式无效: {e}")
        
        # 验证 task_list_map（如果存在）
        if 'task_list_map' in self._user_config:
            task_map = self._user_config['task_list_map']
            if not isinstance(task_map, dict):
                raise ValueError("task_list_map 必须是字典")
            
            # 检查必需的映射
            required_keys = schema['task_list_map']['required_keys']
            for key in required_keys:
                if key not in task_map:
                    raise ValueError(f"task_list_map 缺少必需键: {key}")
                
                # 验证值是整数
                if not isinstance(task_map[key], int):
                    raise ValueError(f"task_list_map[{key}] 必须是整数")
    
    def _create_default_user_config(self) -> Dict[str, Any]:
        """创建默认用户配置"""
        return {
            'team': 'general',
            'base_dir': '',
            'task_list_map': {
                'job_no': 0,
                'job_creator': 1,
                'engineers': 2
            },
            'checklist': 'new'  # 默认值为 'new'
        }
    
    def validate_config_integrity(self) -> Dict[str, Any]:
        """
        验证配置完整性并返回诊断信息
        
        Returns:
            包含验证结果的字典
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'system_config_info': {},
            'user_config_info': {}
        }
        
        try:
            # 验证系统配置
            self._validate_system_config()
            result['system_config_info'] = {
                'teams_count': len(self._system_config.get('subFolderConfig', {})),
                'file_map_categories': len(self._system_config.get('file_map', {})),
                'log_level': self._system_config.get('log_config', {}).get('level', 'N/A')
            }
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"系统配置验证失败: {e}")
        
        try:
            # 验证用户配置
            self._validate_user_config()
            result['user_config_info'] = {
                'team': self._user_config.get('team'),
                'base_dir_exists': Path(self._user_config.get('base_dir', '')).exists() if self._user_config.get('base_dir') else False,
                'has_task_mapping': 'task_list_map' in self._user_config,
                'checklist': self._user_config.get('checklist')
            }
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"用户配置验证失败: {e}")
        
        # 交叉验证
        try:
            self._cross_validate_configs(result)
        except Exception as e:
            result['warnings'].append(f"交叉验证警告: {e}")
        
        return result
    
    def _cross_validate_configs(self, result: Dict[str, Any]):
        """交叉验证配置间的一致性"""
        if not self._system_config or not self._user_config:
            return
        
        # 验证用户选择的团队在系统配置中存在
        user_team = self._user_config.get('team')
        system_teams = list(self._system_config.get('subFolderConfig', {}).keys())
        
        if user_team not in system_teams:
            result['warnings'].append(f"用户配置的团队 '{user_team}' 在系统配置中不存在。可用团队: {system_teams}")
        
        # 验证基础目录路径
        base_dir = self._user_config.get('base_dir', '')
        if base_dir:
            base_path = Path(base_dir)
            if not base_path.exists():
                result['warnings'].append(f"基础目录不存在: {base_dir}")
            elif not base_path.is_dir():
                result['warnings'].append(f"基础目录路径不是目录: {base_dir}")
        
        # 验证任务映射的合理性
        task_map = self._user_config.get('task_list_map', {})
        if task_map:
            max_index = max(task_map.values()) if task_map.values() else -1
            if max_index > 50:  # 假设Excel列数不应该超过50
                result['warnings'].append(f"任务映射索引过大，最大索引: {max_index}")
    
    def get_runtime_info(self) -> Dict[str, Any]:
        """
        获取运行时环境信息
        
        Returns:
            包含运行环境信息的字典
        """
        return {
            'is_frozen': getattr(sys, 'frozen', False),
            'executable_path': sys.executable,
            'script_path': __file__,
            'config_directory': str(self.config_dir),
            'system_config_exists': self.system_config_path.exists(),
            'user_config_exists': self.user_config_path.exists(),
            'environment_type': 'production' if getattr(sys, 'frozen', False) else 'development'
        }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息"""
        summary = {
            'system_config': {
                'path': str(self.system_config_path),
                'exists': self.system_config_path.exists(),
                'size': self.system_config_path.stat().st_size if self.system_config_path.exists() else 0,
                'teams': list(self._system_config.get('subFolderConfig', {}).keys()) if self._system_config else []
            },
            'user_config': {
                'path': str(self.user_config_path),
                'exists': self.user_config_path.exists(),
                'size': self.user_config_path.stat().st_size if self.user_config_path.exists() else 0,
                'team': self._user_config.get('team') if self._user_config else None,
                'base_dir': self._user_config.get('base_dir') if self._user_config else None
            }
        }
        
        return summary
    
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
        print("=== 配置管理器测试 ===")
        
        # 显示运行时环境信息
        print("\n0. 运行时环境信息:")
        runtime_info = config_manager.get_runtime_info()
        for key, value in runtime_info.items():
            print(f"  {key}: {value}")
        
        # 测试配置完整性验证
        print("\n1. 配置完整性验证:")
        integrity = config_manager.validate_config_integrity()
        if integrity['is_valid']:
            print("✓ 配置验证通过")
        else:
            print("✗ 配置验证失败")
            for error in integrity['errors']:
                print(f"  错误: {error}")
        
        for warning in integrity['warnings']:
            print(f"  警告: {warning}")
        
        # 测试配置摘要
        print("\n2. 配置摘要:")
        summary = config_manager.get_config_summary()
        print(f"系统配置: {summary['system_config']['path']} ({summary['system_config']['size']} bytes)")
        print(f"用户配置: {summary['user_config']['path']} ({summary['user_config']['size']} bytes)")
        print(f"当前团队: {summary['user_config']['team']}")
        
        # 测试获取系统配置
        print("\n3. 系统配置测试:")
        print("日志配置:", get_system_config('log_config'))
        print("日志级别:", get_system_config('log_config.level'))
        print("支持的团队:", list(get_system_config('subFolderConfig', {}).keys()))
        
        # 测试用户配置
        print("\n4. 用户配置测试:")
        print("当前团队:", config_manager.get_team())
        print("基础目录:", config_manager.get_base_dir())
        
        print("\n✓ 配置管理器测试完成！")
        
    except Exception as e:
        print(f"✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()