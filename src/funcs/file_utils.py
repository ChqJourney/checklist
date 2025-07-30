"""
文件和文件夹工具模块
负责文件夹检测、文件查找等操作
"""
import os
import glob
from numpy import number
from src.config.config_manager import ConfigManager, get_system_config, config_manager
from src.logger.logger import log_warning

def folder_precheck(target_folder:str,team:str)-> bool:
    """
    检查目标文件夹是否符合规则
    :param target_folder: 目标文件夹路径
    :param team: 团队名称
    :return: 如果符合规则返回True，否则返回False
    """
    # 检查目标文件夹是否存在,检查目标文件夹是否为目录
    if not os.path.exists(target_folder) and not os.path.isdir(target_folder):
        log_warning(f"目标文件夹 {target_folder} 不存在，或该文件夹不是目录", "FOLDER")
        return False
    # 检查目标文件夹下是否有文件名包含checklist的word文档
    checklist_files = glob.glob(os.path.join(target_folder, '*checklist*.doc*'))
    # 过滤掉隐藏文件和缓存文件
    checklist_files = [f for f in checklist_files if not os.path.basename(f).startswith(('~$', '.', '__'))]
    # if not checklist_files:
    #     log_warning(f"目标文件夹 {target_folder} 下没有找到包含 'checklist' 的 Word 文档", "FOLDER")
    #     return False
    if len(checklist_files) > 1:
        for file in checklist_files:
            log_warning(f"找到的文件: {file}", "FOLDER")
        log_warning(f"目标文件夹 {target_folder} 下找到多个包含 'checklist' 的 Word 文档，请确保只有一个", "FOLDER")
        return False
    # 检查文件夹命名是否满足规范
    folder_name_check_result=folder_name_check(target_folder, team)
    if not folder_name_check_result:
        log_warning(f"目标文件夹 {target_folder} 中的子文件夹的命名不符合规范", "FOLDER")
        return False

    return True

def folder_name_check(target_folder:str, team:str)-> bool:
    folder_configs = config_manager.get_subfolder_config(team)
    return _folder_name_check(target_folder, team, folder_configs)

def _folder_name_check(target_folder:str, team:str,folder_configs:dict)-> bool:
    """
    从配置获取文件夹名列表，如果文件夹全部存在（包含大小写也一致），则返回True
    :param target_folder: 目标文件夹路径
    :param team: 团队名称
    :return: 如果符合规则返回True，否则返回False
    """   
    
    # 获取配置中的所有文件夹名
    if not folder_configs or not isinstance(folder_configs, list) or not folder_configs:
        log_warning(f"未找到团队 {team} 的文件夹配置", "FOLDER")
        return False
    
    # 假设配置结构中有options字段包含文件夹名
    options_config = None
    for config_item in folder_configs:
        if isinstance(config_item, dict) and 'options' in config_item:
            options_config = config_item['options']
            break
    
    if not options_config:
        log_warning(f"团队 {team} 的配置中未找到 options 字段", "FOLDER")
        return False
    
    # 检查每个配置的文件夹是否都存在（大小写敏感）
    for folder_name in options_config.keys():
        folder_path = os.path.join(target_folder, folder_name)
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            log_warning(f"必需文件夹 {folder_name} 在路径 {target_folder} 中不存在", "FOLDER")
            return False
    
    return True

def detect_folder_has_file(folder_path):
    """
    在folder_path以及子文件夹中查找是否有文件，如果有，返回True，否则返回False
    """
    for root, dirs, files in os.walk(folder_path):
        if files:
            return True
    return False


def detect_folders_status(working_folder_path, team, options_config):
    """
    检测工作文件夹中的子文件夹状态
    :param working_folder_path: 工作文件夹路径
    :param team: 团队名称
    :param options_config: 选项配置
    :return: 文件夹状态字典
    """
    result = {}
    if team == 'PPT':
        for sub_folder_name in options_config.keys():
            sub_folder_path = os.path.join(working_folder_path, sub_folder_name)
            print(f"检测文件夹: {sub_folder_path}")
            if not os.path.exists(sub_folder_path):
                raise FileNotFoundError(f"{sub_folder_name} folder not found")
            if detect_folder_has_file(sub_folder_path):
                result[sub_folder_name] = True
            else:
                result[sub_folder_name] = False
        if result == {}:
            return None
    else:
        # 遍历options_config中的每个属性，见system.json中的subFolderConfig下的options
        for sub_folder_name, option in options_config.items():
            sub_folder_path = os.path.join(working_folder_path, sub_folder_name)
            print(f"检测文件夹: {sub_folder_path}: {option}")
            if not os.path.exists(sub_folder_path):
                print(f"{sub_folder_name} folder not found")
                result[sub_folder_name] = False
            if isinstance(option, int):
                # 如果option是数字，表示需要检测的文件数量
                print(f"当前option是数字: {option}")
                result[sub_folder_name] = detect_folder_has_file(sub_folder_path)
            elif isinstance(option, dict):
                print(f"当前option是字典: {option}")
                # 如果option是字典，遍历字典的每个key，在file_map中查找对应的文件名规则
                file_map = get_system_config('file_map')
                
                for key, value in option.items():
                    if key in file_map:
                        file_patterns = file_map[key]
                        found_file = False
                        
                        # 遍历file_map中的文件名规则列表
                        for pattern in file_patterns:
                            if not pattern:  # 跳过空字符串
                                continue
                            # 使用glob模块查找符合规则的文件
                            matching_files = glob.glob(os.path.join(sub_folder_path, pattern))
                            if matching_files:
                                found_file = True
                                break
                        if result.get(sub_folder_name) is None:
                            result[sub_folder_name] = {}
                            result[sub_folder_name][key] = found_file
                        else:
                            result[sub_folder_name][key] = found_file
                    else:
                        log_warning(f"在file_map中未找到键: {key}", "FILE")
                        if result.get(sub_folder_name) is None:
                            result[sub_folder_name] = {}
                            result[sub_folder_name][key] = False
                        else:
                            result[sub_folder_name][key] = False
            else:
                # 如果option是其他类型，直接设置为False
                print(f"当前option不是数字或字典: {option}")
                result[sub_folder_name] = False
    print(f"检测结果: {result}")
    return result
