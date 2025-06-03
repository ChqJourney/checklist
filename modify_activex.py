import os
import win32com.client as win32
from pathlib import Path

def set_checklist(target_path,map):
    # 获取当前工作目录
    current_dir = os.getcwd()

    # 启动Word应用程序
    word = win32.Dispatch('Word.Application')
    word.Visible = False  # 让Word可见，方便查看操作过程
    checklist_path = get_only_word_file_path(current_dir)
    # 打开指定的文档
    word_doc = word.Documents.Open(checklist_path)

    # 遍历文档中的所有表格
    table=word_doc.Tables[0]
    set_all_option_cells(table, map)


    # 保存并关闭文档
    word_doc.Save()
    word_doc.Close()
    word.Quit()

def get_only_word_file_path(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".docx") and "checklist" in file:
            return os.path.join(folder_path, file)
    return None  # Return None if no matching file is found

def set_all_option_cells(table, dictionary):
    # dictionary格式为{row_index:number, value:value},然后在table中查找row_index行，将columun 3 cell的option buuton设置为value（使用def set_option_cell)
    for row_index, value in dictionary.items():
        cell = table.Cell(row_index, 3)
        set_option_cell(cell, value)

def set_option_cell(cell, value):
    if cell.Range.InlineShapes[0].OLEFormat.Object.Value == value and cell.Range.InlineShapes[1].OLEFormat.Object.Value != value:
        return
    cell.Range.InlineShapes[0].OLEFormat.Object.Value =  value
    cell.Range.InlineShapes[1].OLEFormat.Object.Value != value
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
        log_service.error("未安装pywin32模块，无法处理快捷方式")
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
                    log_service.debug(f"符号链接指向: {target_path}")
                    return target_path
            except Exception as e:
                print("error")
                print(e)
                continue
    print("没有找到对应的文件夹")
    return None


        