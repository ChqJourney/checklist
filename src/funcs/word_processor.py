"""
Word文档处理模块
负责处理Word文档的各种操作，包括表格、图片、ActiveX控件等
"""
from datetime import date
import glob
import os
import shutil
from numpy import number
import win32com.client as win32
from pathlib import Path
from array import array
from src.funcs.file_utils import detect_folders_status
from src.funcs.file_utils import detect_folders_status
from src.logger.logger import log_info, log_error, log_warning, log_debug


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

    checklist_files = glob.glob(os.path.join(folder_path, '*checklist*.doc*'))
    checklist_files = [f for f in checklist_files if not os.path.basename(f).startswith(('~$', '.', '__'))]
    if checklist_files:
        if len(checklist_files) > 1:
            raise ValueError(f"在文件夹 {folder_path} 中找到多个检查清单文件，请确保只有一个符合条件的文件。")
        return checklist_files[0]
    # 如果没有找到符合条件的文件，copy the default checklist file to the folder
    default_checklist_path = Path.cwd() / 'E-filing checklist.docx'
    if default_checklist_path.exists():
        # Copy the default checklist file to the target folder
        target_path = Path(folder_path) / 'E-filing checklist.docx'
        shutil.copy2(default_checklist_path, target_path)
        log_info(f"已复制默认检查清单文件到: {target_path}", "WORD")
        return str(target_path)
    else:
        raise FileNotFoundError("Default checklist file not found in the current directory. Please ensure 'E-filing checklist.docx' exists.")


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
            print(f"Invalid row index: {row_index}. Must be between 1 and {table.Rows.Count}")
            return None

        for column_index in range(1, table.Columns.Count + 1):
            try:
                cell = table.Cell(row_index, column_index)
                if cell.Range.InlineShapes.Count > 0:
                    for shape in cell.Range.InlineShapes:
                        if hasattr(shape, 'OLEFormat') and shape.OLEFormat is not None:
                            return cell
            except Exception as e:
                print(f"Error accessing cell at row {row_index}, column {column_index}: {str(e)}")
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


def set_all_option_cells_for_ppt(table, status, map):
    """
    Set values for ActiveX controls in table cells for PPT team
    :param table: Word表格对象
    :param status: 状态字典
    :param map: 行映射字典
    """
    try:
        for folder_name, row_num in map.items():
            if not isinstance(row_num, int):
                log_debug(f"Warning: Invalid row number for {folder_name}: {row_num}")
                continue
                
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


def set_option_cells_for_general(table, folder_status, option_config):
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

        if isinstance(option, int):
            try:
                opt_cell = get_cell_with_activeX_in_row(table, option)
                set_option_cell(opt_cell, status)
            except Exception as e:
                log_error(f"设置选项 {folder_name} 时发生错误: {e}", "WORD")

        else:
            for key, value in option.items():
                row_index = value
                opt_cell=get_cell_with_activeX_in_row(table, row_index)
                if not opt_cell:
                    log_warning(f"未找到文件夹 {folder_name} 的选项单元格", "WORD")
                    continue
                try:

                    set_option_cell(opt_cell, status[key])
                except Exception as e:
                    log_error(f"设置选项 {folder_name} 时发生错误: {e}", "WORD")


def set_option_cells(table, team, folder_status, option_config):
    """设置选项单元格"""
    if not option_config or not isinstance(option_config, dict):
        log_warning("无效的选项配置", "WORD")
        return
    if team == 'ppt':
        set_all_option_cells_for_ppt(table, folder_status, option_config)
    else:
        set_option_cells_for_general(table, folder_status, option_config)


def set_checklist(task, target_path, team, subFolderConfig):
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
        for i,item in enumerate(subFolderConfig):
            print(f"正在处理表格索引: {i}, 配置项: {item}")
            current_table = word_doc.Tables[i]
            print(f"当前表格索引: {i}, 表格行数: {current_table.Rows.Count}, 列数: {current_table.Columns.Count}")
            set_fields_value(current_table, task, item["fields"])
            print(f"设置字段值完成: {item['fields']}")
            folder_status = detect_folders_status(target_path, team, item["options"])
            print(f"检测文件夹状态: {folder_status}")
            # 设置选项单元格
            set_option_cells(current_table, team, folder_status, item["options"])

        # 保存并关闭文档
        word_doc.Save()
        word_doc.Close()
        word.Quit()
    except Exception as e:
        print(f"Error setting checklist: {str(e)}")
        if 'word' in locals():
            word.Quit()  # 确保Word应用程序被关闭
        raise


def get_activeX_cells(doc_path):
    """
    获取Word文档中所有包含ActiveX控件的单元格信息
    
    Args:
        doc_path (str): Word文档的路径
        
    Returns:
        list: 包含字典的列表，每个字典包含 {'row': row_index, 'column': column_index, 'table_index': table_index}
    """
    
    try:
        # 启动Word应用程序
        word = win32.Dispatch('Word.Application')
        word.Visible = False  # 隐藏Word窗口
        
        # 打开文档
        doc = word.Documents.Open(doc_path)
        
        # 遍历文档中的所有表格
        for table_index, table in enumerate(doc.Tables, 1):
            # 遍历表格中的所有行
            for row_index in range(1, table.Rows.Count + 1):
                # 遍历表格中的所有列
                for column_index in range(1, table.Columns.Count + 1):
                    try:
                        # 获取单元格
                        cell = table.Cell(row_index, column_index)
                        
                        # 检查单元格中是否有InlineShapes（ActiveX控件通常以InlineShapes的形式存在）
                        if cell.Range.InlineShapes.Count > 0:
                            # 检查InlineShapes是否为ActiveX控件
                            for shape_index in range(1, cell.Range.InlineShapes.Count + 1):
                                shape = cell.Range.InlineShapes[shape_index]
                                # 检查是否为OLE对象（ActiveX控件）
                                if hasattr(shape, 'OLEFormat') and shape.OLEFormat is not None:
                                    try:
                                        # 尝试访问OLE对象，确认它是一个有效的ActiveX控件
                                        ole_object = shape.OLEFormat.Object
                                        if ole_object is not None:
                                            print(f"Found ActiveX control at Row: {row_index}, Column: {column_index}, Table: {table_index}, Shape: {shape_index}")
                                            break  # 找到一个ActiveX控件就跳出循环
                                    except Exception:
                                        # 如果无法访问OLE对象，继续检查下一个
                                        continue
                    except Exception:
                        # 如果无法访问某个单元格，跳过它
                        continue
        
        # 关闭文档和Word应用程序
        doc.Close()
        word.Quit()
        
    except Exception as e:
        print(f"处理文档时出错: {e}")
        # 确保Word应用程序被关闭
        try:
            if 'word' in locals():
                word.Quit()
        except:
            pass
