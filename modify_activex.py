import os
import win32com.client as win32
from pathlib import Path

def kill_all_word_processes():
    """
    结束所有Word进程
    """
    import psutil
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'WINWORD.EXE':
            proc.kill()
    print("所有Word进程已被终止。")

def set_checklist(target_path,status,map):
    # 获取当前工作目录
    current_dir = os.getcwd()

    # 启动Word应用程序
    word = win32.Dispatch('Word.Application')
    word.Visible = False  # 让Word可见，方便查看操作过程
    checklist_path = get_only_word_file_path(target_path)
    # 打开指定的文档
    word_doc = word.Documents.Open(checklist_path)

    # 遍历文档中的所有表格
    table=word_doc.Tables[0]
    set_all_option_cells(table,status, map)


    # 保存并关闭文档
    word_doc.Save()
    word_doc.Close()
    word.Quit()

def get_only_word_file_path(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".docx") and "checklist" in file:
            return os.path.join(folder_path, file)
    return None  # Return None if no matching file is found

def set_all_option_cells(table, status,map):
    for row_index, value in map.items():
        cell = table.Cell(map[row_index], 3)
        set_option_cell(cell, status[row_index])

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
        if not os.path.exists(sub_folder_path):
            raise FileNotFoundError(f"{sub_folder_name} folder not found")
        if detect_folder_has_file(sub_folder_path):
            result[sub_folder_name]=True
        else:
            result[sub_folder_name]=False

def get_working_folder_path(shortcuts_path,job_no):
    try:
        shell = win32.Dispatch("WScript.Shell")
    except ImportError:
        return None
   
    with os.scandir(shortcuts_path) as entries:
        for entry in entries:
            try:
                # 检查是否为快捷方式(.lnk文件)
                print(entry.path)
                if entry.name.lower().endswith('.lnk') and entry.name.lower().startswith(job_no.lower()):
                    shortcut = shell.CreateShortCut(str(entry.path))
                    target_path = Path(shortcut.Targetpath)
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
    

if __name__ == "__main__":
    shorts=os.path.join(os.getcwd(), 'shortcuts')
    t_path=get_working_folder_path(shorts,"250100032HZH")
    print(t_path)