from array import array
import datetime
import os
import shutil
import glob
from numpy import number
import psutil
import win32com.client as win32
from pathlib import Path
from urllib.parse import unquote
from data_manager import data_manager  # 导入全局数据管理器
from logger import log_info, log_error, log_warning, log_debug
from config_manager import ConfigManager

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

def set_fields_value(table,task, field_config):
    if not field_config or not isinstance(field_config, dict):
        log_warning("无效的字段配置", "WORD")
        return

    for field_name, field_value in field_config.items():
        if not field_name or not field_value:
            log_warning(f"字段 {field_name} 的值无效", "WORD")
            continue

        # 在Word表格中设置字段值
        if field_value is array:
            for i, item in enumerate(field_value):
                cell = table.Cell(item.indexes[0], item.indexes[1])
                if item.type=='image':
                    signature_image = get_engineer_signature_image(task[field_name])
                    if signature_image:
                        insert_image_in_cell(cell, signature_image, width=80, height=20)  # 插入工程师签名图片
                    else:
                        log_warning(f"未找到工程师 {task['engineers']} 的签名图片，使用默认图片", "WORD")
                        default_image_path = Path.cwd() / 'signs' / 'default.jpg'
                        insert_image_in_cell(cell, default_image_path, width=80, height=20)  # 插入默认签名图片
                else:
                    set_text_in_cell(cell, task[field_name])
        else:
            cell = table.Cell(field_value.indexes[0], field_value.indexes[1])
            set_text_in_cell(cell, task[field_name])

def set_option_cells(table, team, folder_status, option_config):
    if not option_config or not isinstance(option_config, dict):
        log_warning("无效的选项配置", "WORD")
        return
    if team == 'ppt':
        set_all_option_cells_for_ppt(table, folder_status, option_config)
    else:
        set_option_cells_for_general(table, folder_status, option_config)


def set_option_cells_for_general(table, folder_status, option_config):
    if not option_config or not isinstance(option_config, dict):
        log_warning("无效的选项配置", "WORD")
        return

    for folder_name, option in option_config.items():
        if folder_name not in folder_status:
            log_warning(f"文件夹 {folder_name} 的状态未定义", "WORD")
            continue

        status = folder_status[folder_name]
        row_index = option.get('row_index')
        column_index = option.get('column_index')

        if row_index is None or column_index is None:
            log_warning(f"选项 {folder_name} 的行列索引未定义", "WORD")
            continue

        try:
            cell = table.Cell(row_index, column_index)
            set_option_cell(cell, status)
        except Exception as e:
            log_error(f"设置选项 {folder_name} 时发生错误: {e}", "WORD")

def set_checklist(task,target_path,team,folder_status, subFolderConfig):
    try:
        # 启动Word应用程序
        word = win32.Dispatch('Word.Application')
        word.Visible = False  # 让Word可见，方便查看操作过程
        checklist_path = get_only_word_file_path(target_path)
        log_debug(f"检查清单路径: {checklist_path}", "WORD")
        # 打开指定的文档
        word_doc = word.Documents.Open(checklist_path)
        # 确保文档有表格
        if word_doc.Tables.Count == 0 or word_doc.Tables.Count < len(subFolderConfig):
            raise ValueError("tables setting in subfolderconfig's not correct")
        for item,i in enumerate(subFolderConfig):
            current_table = word_doc.Tables[i]
            set_fields_value(current_table, task, item.fields)
            set_option_cells(current_table, team, folder_status, item.options)

        # 保存并关闭文档

        word_doc.Save()
        word_doc.Close()
        word.Quit()
    except Exception as e:
        print(f"Error setting checklist: {str(e)}")
        if 'word' in locals():
            word.Quit()  # 确保Word应用程序被关闭
        raise


# 在signs文件夹里获取engineers签名图片
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

# 在word表格某行某列单元格内输入文本
def set_text_in_cell(cell, text):
    """
    在Word表格的指定单元格内输入文本
    :param cell: Word表格单元格对象
    :param text: 要输入的文本
    """
    cell.Range.Text = text

# 在word表格某行某列单元格内插入图片，并设置图片大小
def insert_image_in_cell(cell, image_path, width=80, height=20):
    """
    在Word表格的指定单元格内插入图片，并设置图片大小
    :param table: Word表格对象
    :param row_index: 行索引（从1开始）
    :param column_index: 列索引（从1开始）
    :param image_path: 图片文件路径
    :param width: 图片宽度（默认100）
    :param height: 图片高度（默认40）
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
            #shape.RelativeHorizontalPosition = 3  # wdRelativeHorizontalPositionColumn
            shape.RelativeVerticalPosition = 3    # wdRelativeVerticalPositionParagraph
            shape.Left = 0   # 水平位置
            shape.Top = 0    # 垂直位置
        else:
            raise Exception("No active shape found in the cell.")
            
    except Exception as e:
        print(f"Error inserting image in cell: {str(e)}")
        raise

def get_only_word_file_path(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".docx") and "checklist" in file:
            return os.path.join(folder_path, file)    # 如果没有找到符合条件的文件，copy the default checklist file to the folder
    default_checklist_path = Path.cwd() / 'E-filing checklist.docx'
    if default_checklist_path.exists():
        # Copy the default checklist file to the target folder
        target_path = Path(folder_path) / 'E-filing checklist.docx'
        shutil.copy2(default_checklist_path, target_path)
        log_info(f"已复制默认检查清单文件到: {target_path}", "WORD")
        return str(target_path)
    else:
        raise FileNotFoundError("Default checklist file not found in the current directory. Please ensure 'E-filing checklist.docx' exists.")

def set_all_option_cells_for_ppt(table, status, map):
    """
    Set values for ActiveX controls in table cells
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
    if cell.Range.InlineShapes[0].OLEFormat.Object.Value == value and cell.Range.InlineShapes[1].OLEFormat.Object.Value != value:
        return
    cell.Range.InlineShapes[0].OLEFormat.Object.Value =  value
    cell.Range.InlineShapes[1].OLEFormat.Object.Value = not value

def detect_folder_has_file(folder_path):
    # 在folder_path以及子文件夹中查找是否有文件，如果有，返回True，否则返回False
    for root, dirs, files in os.walk(folder_path):
        if files:
            return True
def detect_folders(working_folder_path,team,options_config):
    result={}
    if team=='ppt':
        for sub_folder_name in options_config.keys():
            sub_folder_path = os.path.join(working_folder_path, sub_folder_name)
            print(f"检测文件夹: {sub_folder_path}")
            if not os.path.exists(sub_folder_path):
                raise FileNotFoundError(f"{sub_folder_name} folder not found")
            if detect_folder_has_file(sub_folder_path):
                result[sub_folder_name]=True
            else:
                result[sub_folder_name]=False
        if result == {}:
            return None
    else:
        # 遍历optiions_config中的每个属性，见system.json中的subFolderConfig下的options
        for sub_folder_name, option in options_config.items():
            sub_folder_path = os.path.join(working_folder_path, sub_folder_name)
            print(f"检测文件夹: {sub_folder_path}")
            if not os.path.exists(sub_folder_path):
                raise FileNotFoundError(f"{sub_folder_name} folder not found")
            if isinstance(option, number):
                # 如果option是数字，表示需要检测的文件数量
                result[option]= detect_folder_has_file(sub_folder_path)
            elif isinstance(option, dict):
                # 如果option是字典，遍历字典的每个key，在file_map中查找对应的文件名规则
                config_manager = ConfigManager()
                file_map = config_manager.get_file_map()
                
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
                        result[key] = found_file
                    else:
                        log_warning(f"在file_map中未找到键: {key}", "FILE")
                        result[key] = False

    return result

def get_working_folder_path(base_dir, team,job_no):
    """
    获取工作目录路径
    :param base_dir: 基础目录
    :param team: 团队名称
    :param job_no: 工作号
    :return: 工作目录路径，如果未找到则返回None
    """
    if team=='ppt':
        return get_working_folder_path_for_ppt(base_dir, job_no)
    else:
        return get_working_folder_path_for_general(base_dir, job_no)


def get_working_folder_path_for_ppt(shortcuts_path,job_no):
    try:
        shell = win32.Dispatch("WScript.Shell")
    except ImportError:
        return None
   
    with os.scandir(shortcuts_path) as entries:
        for entry in entries:
            try:
                # 检查是否为快捷方式(.lnk文件)
                if entry.name.lower().endswith('.lnk') and entry.name.lower().startswith(job_no.lower()):
                    shortcut = shell.CreateShortCut(str(entry.path))
                    # Decode URL-encoded characters in the path
                    decoded_path = unquote(shortcut.Targetpath)
                    target_path = Path(decoded_path)
                    return target_path
                # 检查是否为符号链接
                elif entry.is_symlink() and entry.name.lower().startswith(job_no.lower()):
                    target_path = Path(entry.path).readlink()
                    return target_path
            except Exception as e:
                print("error")
                print(e)
                continue
    print("没有找到对应的文件夹")
    return None
# 获取Word文档中所有活动的ActiveX控件单元格的行序号和列序号

def get_working_folder_path_for_general(base_dir, job_no):
    sub_year_folder = f"20{job_no[:2]}"
    search_dir = os.path.join(base_dir, sub_year_folder)
    
    # 使用 os.scandir() 只查找第一层目录 (最高效)
    try:
        with os.scandir(search_dir) as entries:
            for entry in entries:
                if entry.is_dir() and entry.name.startswith(job_no):
                    return entry.path
    except (OSError, FileNotFoundError) as e:
        log_debug(f"无法访问目录 {search_dir}: {e}", "FILE")
    
    return None

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

if __name__ == "__main__":
    shorts=os.path.join(os.getcwd(), 'shortcuts')
    t_path=get_working_folder_path(shorts,"250100032HZH")
    print(t_path)