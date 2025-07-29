"""
Word文档处理模块
负责处理Word文档的各种操作，包括表格、图片、ActiveX控件等
"""
import json
from datetime import date
import glob
import os
import shutil
from numpy import number
import win32com.client as win32
from pathlib import Path
from array import array
from src.config import config_manager
from src.funcs.process_manager import kill_all_word_processes
from src.funcs.file_utils import detect_folders_status
from src.funcs.file_utils import detect_folders_status
from src.logger.logger import log_info, log_error, log_warning, log_debug

# 全局变量，用于缓存ActiveX配置
_activex_config_cache = None


def load_activex_config():
    """加载ActiveX控件位置配置文件"""
    global _activex_config_cache
    
    if _activex_config_cache is not None:
        return _activex_config_cache
    
    config_path = Path.cwd() / 'activex_config.json'
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                _activex_config_cache = json.load(f)
                log_debug(f"已加载ActiveX配置文件: {config_path}", "WORD")
                return _activex_config_cache
        else:
            log_warning(f"ActiveX配置文件不存在: {config_path}", "WORD")
            return {}
    except Exception as e:
        log_error(f"加载ActiveX配置文件失败: {str(e)}", "WORD")
        return {}


def get_template_name_from_team(team):
    """根据团队名称获取模板名称"""
    if team.lower() == 'ppt':
        return 'ppt_template'
    else:
        return 'general_template'


def get_cell_with_activeX_by_config(table, row_index, table_index=0, team='general'):
    """
    根据配置文件快速获取指定行中包含ActiveX控件的单元格
    :param table: Word表格对象
    :param row_index: 行索引（从1开始）
    :param table_index: 表格索引（从0开始）
    :param team: 团队名称，用于确定使用哪个模板配置
    :return: 包含ActiveX控件的单元格对象，如果没有找到则返回None
    """
    try:
        # 验证参数
        if row_index < 1 or row_index > table.Rows.Count:
            log_error(f"Invalid row index: {row_index}. Must be between 1 and {table.Rows.Count}", "WORD")
            return None
        
        # 加载配置
        config = load_activex_config()
        if not config:
            log_warning("ActiveX配置为空，回退到原方法", "WORD")
            return get_cell_with_activeX_in_row(table, row_index)
        
        # 获取模板名称
        template_name = get_template_name_from_team(team)
        
        # 检查模板配置是否存在
        if template_name not in config:
            log_warning(f"未找到模板配置: {template_name}，回退到原方法", "WORD")
            return get_cell_with_activeX_in_row(table, row_index)
        
        template_config = config[template_name]
        table_key = f"table_{table_index}"
        
        # 检查表格配置是否存在
        if table_key not in template_config:
            log_warning(f"未找到表格配置: {table_key}，回退到原方法", "WORD")
            return get_cell_with_activeX_in_row(table, row_index)
        
        table_config = template_config[table_key]
        row_key = str(row_index)
        
        # 检查行配置是否存在
        if row_key not in table_config:
            log_debug(f"行 {row_index} 没有ActiveX控件配置", "WORD")
            return None
        
        # 获取配置的位置
        position = table_config[row_key]
        config_row = position['row']
        config_col = position['column']
        
        # 验证配置的位置是否合理
        if config_row != row_index:
            log_warning(f"配置文件中行号不匹配: 期望{row_index}，配置{config_row}", "WORD")
        
        if config_col < 1 or config_col > table.Columns.Count:
            log_error(f"配置的列号无效: {config_col}，表格列数: {table.Columns.Count}", "WORD")
            return get_cell_with_activeX_in_row(table, row_index)
        
        # 直接获取指定位置的单元格
        try:
            cell = table.Cell(config_row, config_col)
            
            # 验证单元格确实包含ActiveX控件
            if cell.Range.InlineShapes.Count > 0:
                for shape in cell.Range.InlineShapes:
                    if hasattr(shape, 'OLEFormat') and shape.OLEFormat is not None:
                        log_debug(f"基于配置找到ActiveX控件: 行{config_row}, 列{config_col}", "WORD")
                        return cell
            
            # 如果配置的位置没有ActiveX控件，记录警告但不回退
            log_warning(f"配置位置({config_row},{config_col})没有ActiveX控件", "WORD")
            return None
            
        except Exception as e:
            log_error(f"访问配置位置({config_row},{config_col})时出错: {str(e)}", "WORD")
            return get_cell_with_activeX_in_row(table, row_index)
    
    except Exception as e:
        log_error(f"基于配置获取ActiveX控件时出错: {str(e)}", "WORD")
        return get_cell_with_activeX_in_row(table, row_index)


def get_engineer_signature_image(engineer_name):
    """获取指定工程师的签名图片路径"""
    if not engineer_name or not engineer_name.strip():
        return None
    
    signs_folder = Path.cwd() / 'signs'
    if not signs_folder.exists():
        print(f"签名文件夹不存在: {signs_folder}")
        return None
    
    # 支持多种图片格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    
    for ext in image_extensions:
        image_path = signs_folder / f"{engineer_name.strip()}{ext}"
        if image_path.exists():
            return str(image_path)
    
    print(f"未找到工程师 {engineer_name} 的签名图片")
    return None


def set_text_in_cell(cell, text):
    """
    在Word表格的指定单元格内输入文本
    :param cell: Word表格单元格对象
    :param text: 要输入的文本
    """
    cell.Range.Text = text


def insert_image_in_cell(cell, image_path, width=80, height=20):
    """
    在Word表格的指定单元格内插入图片，并设置图片大小
    :param cell: Word表格单元格对象
    :param image_path: 图片文件路径
    :param width: 图片宽度（默认80）
    :param height: 图片高度（默认20）
    """
    try:
        # Validate parameters
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        # Set cell alignment properties
        cell.VerticalAlignment = 1  # 1 = wdAlignVerticalCenter
        cell.Range.ParagraphFormat.Alignment = 1  # 1 = wdAlignParagraphCenter
        
        # Add picture
        shape = cell.Range.InlineShapes.AddPicture(
            FileName=image_path,
            LinkToFile=False,
            SaveWithDocument=True
        )
        
        # Set dimensions
        if shape:
            shape.Width = width
            shape.Height = height
            # Convert to floating shape for more position control
            shape = shape.ConvertToShape()
            
            # Set position relative to cell
            shape.RelativeVerticalPosition = 3    # wdRelativeVerticalPositionParagraph
            shape.Left = 0   # 水平位置
            shape.Top = 0    # 垂直位置
        else:
            raise Exception("No active shape found in the cell.")
            
    except Exception as e:
        print(f"Error inserting image in cell: {str(e)}")
        raise


def get_only_word_file_path(folder_path):
    """获取文件夹中的Word检查清单文件路径"""
    user_config = config_manager.get_user_config()
    if not user_config.get('checklist', None):
        raise ValueError("User configuration for checklist not found. Please ensure the user config is set up correctly.")
    checklist_files = glob.glob(os.path.join(folder_path, '*checklist*.doc*'))
    checklist_files = [f for f in checklist_files if not os.path.basename(f).startswith(('~$', '.', '__'))]
    if user_config['checklist']=='cover':
        if len(checklist_files)>0:
            #删除找到的第一个checklist文件
            os.remove(checklist_files[0])
            log_info(f"已删除现有的检查清单文件: {checklist_files[0]}", "WORD")
        team_category = user_config['team'].lower() if user_config['team'] == 'PPT' else 'general'
        template_name=f"{team_category}_template.docx"
        template_path = Path.cwd() / 'templates' / template_name
        if template_path.exists():
            # Copy the default checklist file to the target folder
            target_path = Path(folder_path) / 'E-filing checklist.docx'
            shutil.copy2(template_path, target_path)
            log_info(f"已复制默认检查清单文件到: {target_path}", "WORD")
            return str(target_path)
        else:
            raise FileNotFoundError("Checklist template's not found in the 'templates' directory of program folder. Please ensure 'E-filing checklist.docx' exists.")

    if checklist_files:
        if len(checklist_files) > 1 and user_config['checklist'] != 'cover':
            log_error(f"在文件夹 {folder_path} 中找到多个检查清单文件，只有第一个会被填写。")
        return checklist_files[0]
    else:
        # 如果既不符合复制默认文件的条件，又没有找到检查清单文件
        raise FileNotFoundError(f"在文件夹 {folder_path} 中未找到检查清单文件，且不符合使用默认文件的条件。")


def get_cell_with_activeX_in_row(table, row_index):
    """
    获取指定行中包含ActiveX控件的单元格
    :param table: Word表格对象
    :param row_index: 行索引（从1开始）
    :return: 包含ActiveX控件的单元格对象，如果没有找到则返回None
    """
    try:
        # Validate row_index
        if row_index < 1 or row_index > table.Rows.Count:
            log_error(f"Invalid row index: {row_index}. Must be between 1 and {table.Rows.Count}")
            return None


        for column_index in range(1, table.Columns.Count + 1):
            try:
                cell = table.Cell(row_index, column_index)
                if cell.Range.InlineShapes.Count > 0:
                    for shape in cell.Range.InlineShapes:
                        if hasattr(shape, 'OLEFormat') and shape.OLEFormat is not None:
                            return cell
            except Exception as e:
                log_debug(f"Error accessing cell at row {row_index}, column {column_index}: {str(e)}", "WORD")
                continue
                
        return None
    except Exception as e:
        raise Exception(f"Error in get_cell_with_activeX_in_row: {str(e)}")


def set_option_cell(cell, value):
    """设置选项单元格的值"""
    if cell.Range.InlineShapes[0].OLEFormat.Object.Value == value and cell.Range.InlineShapes[1].OLEFormat.Object.Value != value:
        return
    cell.Range.InlineShapes[0].OLEFormat.Object.Value = value
    cell.Range.InlineShapes[1].OLEFormat.Object.Value = not value


def set_fields_value(table, task, field_config):
    """设置表格字段值"""
    if not field_config or not isinstance(field_config, dict):
        log_warning("无效的字段配置", "WORD")
        return

    for field_name, field_value in field_config.items():
        if not field_name or not field_value:
            log_warning(f"字段 {field_name} 的值无效", "WORD")
            continue

        # 在Word表格中设置字段值
        if isinstance(field_value, list):
            # 如果field_value是列表，遍历每个项目
            for i, item in enumerate(field_value):
                cell = table.Cell(item["indexes"][0], item["indexes"][1])
                if item["type"] == 'image':
                    signature_image = get_engineer_signature_image(task[field_name])
                    if signature_image:
                        insert_image_in_cell(cell, signature_image, width=80, height=20)  # 插入工程师签名图片
                    else:
                        log_warning(f"未找到工程师 {task['engineers']} 的签名图片，使用默认图片", "WORD")
                        default_image_path = Path.cwd() / 'signs' / 'default.jpg'
                        insert_image_in_cell(cell, default_image_path, width=80, height=20)  # 插入默认签名图片
                elif item["type"] == 'date':
                    set_text_in_cell(cell, date.today().strftime("%Y-%m-%d"))  # 设置当前日期
                else:
                    set_text_in_cell(cell, task[field_name])
        else:
            # 如果field_value是单个字典
            cell = table.Cell(field_value["indexes"][0], field_value["indexes"][1])
            if field_name == 'date':
                set_text_in_cell(cell, date.today().strftime("%Y-%m-%d"))  # 设置当前日期
            else:
                set_text_in_cell(cell, task[field_name])


def set_all_option_cells_for_ppt(table, status, map, table_index=0, use_config=True):
    """
    Set values for ActiveX controls in table cells for PPT team
    :param table: Word表格对象
    :param status: 状态字典
    :param map: 行映射字典
    :param table_index: 表格索引
    :param use_config: 是否使用配置文件方法
    """
    try:
        for folder_name, row_num in map.items():
            if not isinstance(row_num, int):
                log_debug(f"Warning: Invalid row number for {folder_name}: {row_num}")
                continue
            
            # 选择使用配置方法还是原方法
            if use_config:
                cell = get_cell_with_activeX_by_config(table, row_num, table_index, 'ppt')
            else:
                cell = get_cell_with_activeX_in_row(table, row_num)
                
            if cell is None:
                log_error(f"No ActiveX control found in row {row_num}")
                raise Exception(f"No ActiveX control found in row {row_num} for folder: {folder_name}, please check if the row setting is correct or if the file is damaged.")
                
            if folder_name in status:
                set_option_cell(cell, status[folder_name])
            else:
                log_debug(f"No status found for folder: {folder_name}")
    except Exception as e:
        raise Exception(f"Error in set_all_option_cells: {str(e)}")


def set_option_cells_for_general(table, folder_status, option_config, table_index=0, use_config=True):
    """设置通用团队的选项单元格"""
    if not option_config or not isinstance(option_config, dict):
        log_warning("无效的选项配置", "WORD")
        return

    for folder_name, option in option_config.items():
        if folder_name not in folder_status.keys():
            print(f"folder {folder_name} not in folder_status {folder_status}")
            log_warning(f"文件夹 {folder_name} 的状态未定义", "WORD")
            continue

        status = folder_status[folder_name]

        if not isinstance(option, dict):
            raise Exception(f"选项配置 {folder_name} 的格式不正确，应该是字典类型")

        for key, value in option.items():
            row_index = value
            
            # 选择使用配置方法还是原方法
            if use_config:
                opt_cell = get_cell_with_activeX_by_config(table, row_index, table_index, 'general')
            else:
                opt_cell = get_cell_with_activeX_in_row(table, row_index)
                
            if not opt_cell:
                log_warning(f"未找到文件夹 {folder_name} 的选项单元格", "WORD")
                continue
                
            try:
                set_option_cell(opt_cell, status[key])
            except Exception as e:
                log_error(f"设置选项 {folder_name} 时发生错误: {e}", "WORD")


def set_option_cells(table, team, folder_status, option_config, table_index=0, use_config=True):
    """设置选项单元格"""
    if not option_config or not isinstance(option_config, dict):
        log_warning("无效的选项配置", "WORD")
        return
    if team == 'PPT':
        set_all_option_cells_for_ppt(table, folder_status, option_config, table_index, use_config)
    else:
        set_option_cells_for_general(table, folder_status, option_config, table_index, use_config)


def set_checklist(task, target_path, team, subFolderConfig, use_config=True):
    """设置检查清单"""
    try:
        # 启动Word应用程序
        print(f"{subFolderConfig}")
        word = win32.Dispatch('Word.Application')
        word.Visible = False  # 让Word可见，方便查看操作过程
        checklist_path = get_only_word_file_path(target_path)
        log_debug(f"检查清单路径: {checklist_path}", "WORD")
        
        # 打开指定的文档
        word_doc = word.Documents.Open(checklist_path)
        # 确保文档有表格
        if word_doc.Tables.Count == 0 or word_doc.Tables.Count < len(subFolderConfig):
            raise ValueError("tables setting in subfolderconfig's not correct")
        
        # 记录使用的方法
        method_name = "配置文件方法" if use_config else "原始搜索方法"
        log_info(f"使用{method_name}处理ActiveX控件", "WORD")
        
        for i, item in enumerate(subFolderConfig):
            log_debug(f"正在处理表格索引: {i}, 配置项: {item}", "WORD")
            current_table = word_doc.Tables[i]
            log_debug(f"当前表格索引: {i}, 表格行数: {current_table.Rows.Count}, 列数: {current_table.Columns.Count}", "WORD")
            log_debug(f"fields: {item.get('fields')}, options: {item.get('options')}", "WORD")
            
            if 'fields' in item and item['fields'] is not None:
                set_fields_value(current_table, task, item["fields"])
                log_debug(f"设置字段值完成: {item['fields']}", "WORD")
                
            if 'options' in item and item["options"] is not None:
                folder_status = detect_folders_status(target_path, team, item["options"])
                log_debug(f"检测文件夹状态: {folder_status}", "WORD")
                # 设置选项单元格，传递表格索引和配置方法选择
                set_option_cells(current_table, team, folder_status, item["options"], i, use_config)

        # 保存并关闭文档
        word_doc.Save()
        word_doc.Close()
        word.Quit()
    except Exception as e:
        log_error(f"Error setting checklist: {str(e)}", "WORD")
        if 'word' in locals():
            kill_all_word_processes()
        raise


