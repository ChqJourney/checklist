import os
import json
import pandas as pd
from funcs import get_working_folder_path,detect_folders, kill_all_word_processes,set_checklist 
# 用pandas读取excel文件，返回tasks列表,忽略第一行标题,task数据格式为{job_no:str,job_creator:str,engineers:str}
def get_tasks_from_task_list_excel(excel_file_path, map):
    tasks = []
    try:
        df = pd.read_excel(excel_file_path)
        # Skip the first row (header) and map columns according to 'map'
        for _, row in df.iloc[0:].iterrows():
            task = {key: str(row.iloc[value]) for key, value in map.items()}
            tasks.append(task)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
    return tasks



def main():
    global shortcuts_path, subFolderNames, subFolder_map, task_list_map, tasks
    # 检查当前目录是否存在config.json文件
    if not os.path.exists('config.json'):
        print("配置文件config.json不存在，请检查当前目录。")
        return
    # 读取配置文件config.json
    with open('config.json', 'r') as f:
        config = json.load(f)
        shortcuts_path = config['shortcuts_path']
        subFolderNames = config['subFolderNames']
        subFolder_map = config['subFolder_map']
        task_list_map=config['task_list_map']
    # 基于task_list_map读取task list.xlsx,按行读取数据，数据格式为{job_no:str,job_creator:str,engineers:str}
    print(task_list_map)
    tasks = get_tasks_from_task_list_excel('task list.xlsx',task_list_map)
    print(f'任务: {len(tasks)}')
    if not tasks:
        print("没有任务数据，请检查task list.xlsx文件。")
        return
    for task in tasks:
        target_path = get_working_folder_path(shortcuts_path, task['job_no'])
        if target_path is not None:
            print(f"{task['job_no']}的目录是: {target_path}")
        else:
            print(f"{task['job_no']}的目录不存在")
        folder_status=detect_folders(target_path, subFolderNames)
        kill_all_word_processes()
        set_checklist(task,target_path,folder_status, subFolder_map)

if __name__ == "__main__":
    main()
