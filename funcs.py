import datetime
import os
import win32com.client as win32
from pathlib import Path
from urllib.parse import unquote
from data_manager import data_manager  # 导入全局数据管理器

def kill_all_word_processes():
    """
    结束所有Word进程
    """
    import psutil
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'WINWORD.EXE':
            proc.kill()
    print("所有Word进程已被终止。")

def set_checklist(task,target_path,status,map):
    current_dir = os.getcwd()
    # 启动Word应用程序
    word = win32.Dispatch('Word.Application')
    word.Visible = False  # 让Word可见，方便查看操作过程
    checklist_path = get_only_word_file_path(target_path)
    print(f"检查清单路径: {checklist_path}")
    # 打开指定的文档
    word_doc = word.Documents.Open(checklist_path)
    # 确保文档有表格
    if word_doc.Tables.Count == 0:
        raise ValueError("No tables found in the document")
    # 填写基本信息
    table_info = word_doc.Tables[0]
    #清空单元格
    table_info.Cell(1,2).Range.Text=""
    table_info.Cell(2,4).Range.Text=""
    table_info.Cell(2,2).Range.Text=""
    set_text_in_cell(table_info, 1, 2, task['job_no'])  # 工作号
    set_text_in_cell(table_info, 2, 4, task['job_creator'])  # 工作创建人
    set_text_in_cell(table_info, 1, 4, task['engineers'])  # 工程师
    # 获取工程师签名图片路径
    engineer_signature_image = get_engineer_signature_image(task['engineers'])
    if engineer_signature_image:
        insert_image_in_cell(table_info, 1, 4, engineer_signature_image, width=80, height=20)  # 插入工程师签名图片
    else:
        print(f"Signature image for {task['engineers']} not found. Using default logo.")
        image_path=os.path.join(os.getcwd(), 'signs\\default.jpg')
        insert_image_in_cell(table_info, 1, 4, image_path, width=80, height=20)  # 插入默认签名图片
    set_text_in_cell(table_info, 2, 2, datetime.datetime.now().strftime('%Y-%m-%d'))  # 当前日期
    # 填写文件夹状态，activieX控件设置
    table=word_doc.Tables[1]
    
    set_all_option_cells(table,status, map)


    # 保存并关闭文档
    word_doc.Save()
    word_doc.Close()
    word.Quit()


# 在signs文件夹里获取engineers签名图片
def get_engineer_signature_image(engineer_name):
    """
    获取指定工程师的签名图片路径
    :param engineer_name: 工程师姓名
    :return: 签名图片的完整路径，如果不存在则返回None
    """
    signs_folder = os.path.join(os.getcwd(), 'signs')
    image_path = os.path.join(signs_folder, f"{engineer_name}.jpg")
    if os.path.exists(image_path):
        return image_path
    else:
        print(f"Signature image for {engineer_name} not found.")
        return None
# 在word表格某行某列单元格内输入文本
def set_text_in_cell(table, row_index, column_index, text):
    """
    在Word表格的指定单元格内输入文本
    :param table: Word表格对象
    :param row_index: 行索引（从1开始）
    :param column_index: 列索引（从1开始）
    :param text: 要输入的文本
    """
    cell = table.Cell(row_index, column_index)
    cell.Range.Text = text
# 在word表格某行某列单元格内插入图片，并设置图片大小
def insert_image_in_cell(table, row_index, column_index, image_path, width=80, height=20):
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
            
        # Get cell
        cell = table.Cell(row_index, column_index)
        
        
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
            raise Exception("Failed to insert image")
            
    except Exception as e:
        print(f"Error inserting image in cell ({row_index}, {column_index}): {str(e)}")
        raise
def get_only_word_file_path(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".docx") and "checklist" in file:
            return os.path.join(folder_path, file)
    return None  # Return None if no matching file is found

def set_all_option_cells(table, status, map):
    """
    Set values for ActiveX controls in table cells
    :param table: Word表格对象
    :param status: 状态字典
    :param map: 行映射字典
    """
    try:
        for folder_name, row_num in map.items():
            if not isinstance(row_num, int):
                print(f"Warning: Invalid row number for {folder_name}: {row_num}")
                continue
                
            cell = get_cell_with_activeX_in_row(table, row_num)
            if cell is None:
                print(f"No ActiveX control found in row {row_num}")
                continue
                
            if folder_name in status:
                set_option_cell(cell, status[folder_name])
            else:
                print(f"No status found for folder: {folder_name}")
    except Exception as e:
        print(f"Error in set_all_option_cells: {str(e)}")

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
        print(f"Error in get_cell_with_activeX_in_row: {str(e)}")
        return None

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
def detect_folders(working_folder_path,sub_folder_names):
    result={}
    for sub_folder_name in sub_folder_names:
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
    return result

def get_working_folder_path(shortcuts_path,job_no):
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