import webview
import threading
import json
import os
import sys
import pandas as pd
from datetime import datetime
from funcs import get_working_folder_path, detect_folders, kill_all_word_processes, set_checklist
from data_manager import data_manager
from logger import global_logger, log_info, log_error, log_warning, log_debug, log_critical

class ProjectFileChecker:
    def __init__(self):
        self.task_file_path = ""
        self.tasks = []
        self.is_running = False
        self.log_callback = "None"
        
        # 设置全局日志的前端回调
        global_logger.set_frontend_callback(self._frontend_log_callback)
        
        # 加载配置
        self.load_config()
    
    def _frontend_log_callback(self, formatted_message: str, level: str):
        """全局日志的前端回调函数"""
        try:
            if webview.windows and len(webview.windows) > 0:
                escaped_message = global_logger._escape_for_js(formatted_message)
                webview.windows[0].evaluate_js(f'addLogWithLevel("{escaped_message}", "{level}")')
        except Exception as e:
            print(f"前端日志显示失败: {e}")
            if webview.windows and len(webview.windows) > 0:
                escaped_message = global_logger._escape_for_js(formatted_message)
                webview.windows[0].evaluate_js(f'addLogWithLevel("{escaped_message}", "{level}")')
        except Exception as e:
            print(f"前端日志显示失败: {e}")
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.shortcuts_path = config.get('shortcuts_path', '')
                self.subFolderNames = config.get('subFolderNames', [])
                self.subFolder_map = config.get('subFolder_map', {})
                self.task_list_map = config.get('task_list_map', {})
                print(f"配置加载成功: shortcuts_path={self.shortcuts_path}")
        except Exception as e:
            print(f"配置文件加载失败: {e}")            # 设置默认值
            self.shortcuts_path = ""
            self.subFolderNames = []
            self.subFolder_map = {}
            self.task_list_map = {}
    
    def log(self, message, level="INFO"):
        """输出日志信息 - 兼容旧接口，现在使用全局日志系统"""
        # 为了向后兼容，保留原有接口
        if level.upper() == "DEBUG":
            log_debug(message, "GUI")
        elif level.upper() == "WARNING":
            log_warning(message, "GUI")
        elif level.upper() == "ERROR":
            log_error(message, "GUI")
        elif level.upper() == "CRITICAL":
            log_critical(message, "GUI")
        else:
            log_info(message, "GUI")
    
    def select_file(self):
        """选择Excel文件"""
        try:
            file_types = ('Excel Files (*.xlsx;*.xls)', 'All files (*.*)')
            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                directory=os.getcwd(),
                allow_multiple=False,
                file_types=file_types
            )
            
            if result and len(result) > 0:
                self.task_file_path = result[0]
                self.log(f"已选择文件: {os.path.basename(self.task_file_path)}")
                return {
                    'success': True,
                    'filename': os.path.basename(self.task_file_path),
                    'path': self.task_file_path
                }
            else:
                return {'success': False, 'message': '未选择文件'}
        except Exception as e:
            self.log(f"文件选择失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def get_tasks_from_excel(self, excel_file_path):
        """从Excel文件读取任务列表"""
        tasks = []
        try:
            df = pd.read_excel(excel_file_path)
            for _, row in df.iloc[0:].iterrows():
                task = {key: str(row.iloc[value]) for key, value in self.task_list_map.items()}
                tasks.append(task)
            self.log(f"成功读取 {len(tasks)} 个任务")
        except Exception as e:
            self.log(f"读取Excel文件失败: {e}")
        return tasks
    
    def process_tasks(self):
        """处理任务"""
        if not self.task_file_path:
            self.log("请先选择任务列表文件")
            return {'success': False, 'message': '请先选择任务列表文件'}
        
        if self.is_running:
            self.log("程序正在运行中...")
            return {'success': False, 'message': '程序正在运行中'}
        
        def run_process():
            try:
                self.is_running = True

                data_manager.clear_results()  # 清空之前的结果
                data_manager.set_processing_status(True)
                
                # 更新按钮状态
                webview.windows[0].evaluate_js('setRunning(true)')
                
                self.log("开始处理任务...")
                
                # 读取任务列表
                self.tasks = self.get_tasks_from_excel(self.task_file_path)
                data_manager.set_tasks(self.tasks)
                
                if not self.tasks:
                    self.log("没有找到任务数据")
                    return
                self.log(f"共计 {len(self.tasks)} 个任务")
                # 处理每个任务
                for i, task in enumerate(self.tasks):
                    self.log(f"处理任务 {i+1}/{len(self.tasks)}: {task['job_no']}")
                    
                    # 获取工作目录
                    target_path = get_working_folder_path(self.shortcuts_path, task['job_no'])
                    
                    result = {
                        'job_no': task['job_no'],
                        'job_creator': task['job_creator'],
                        'engineers': task['engineers'],
                        'target_path': str(target_path) if target_path is not None else None,
                        'status': '未找到目录' if target_path is None else '已处理',
                        'folders': {}
                    }
                    
                    if target_path is not None:
                        self.log(f"找到目录: {target_path}")
                        # 检测文件夹
                        self.log("开始检查子文件夹...")
                        folder_status = detect_folders(target_path, self.subFolderNames)
                        if  not folder_status:
                            self.log(f"子文件夹检查失败: {task['job_no']}")
                            result['status'] = '子文件夹检查失败'
                            break
                        else:
                            self.log(f"子文件夹检查结果: {folder_status}")
                            result['folders'] = folder_status
                        # 结束所有Word进程
                        self.log("确保文件夹检查不受干扰,结束所有Word进程...")
                        kill_all_word_processes()
                        # 设置检查列表
                        self.log(f"{task['job_no']}开始写入检查列表...")
                        try:
                            set_checklist(task, target_path, folder_status, self.subFolder_map)
                            self.log(f"{task['job_no']}检查列表写入完成")
                            result['status'] = '完成'
                        except Exception as e:
                            self.log(f"{task['job_no']}设置检查列表失败: {e}")
                            result['status'] = '失败'
                            
                        self.log(f"任务 {task['job_no']} 处理完成:结果为：{result['status']}")
                    else:
                        self.log(f"未找到目录: {task['job_no']}")
                    
                    # 使用数据管理器添加结果
                    data_manager.add_result(result)
                    
                    # 更新表格
                    webview.windows[0].evaluate_js(f'updateResults({json.dumps(data_manager.get_results())})')
                
                self.log(f"所有任务处理完成，共处理 {len(self.tasks)} 个任务")
                
                # 保存结果到文件
                #data_manager.save_to_file()
                
            except Exception as e:
                self.log(f"处理过程中发生错误: {e}")
            finally:
                self.is_running = False
                data_manager.set_processing_status(False)
                webview.windows[0].evaluate_js('setRunning(false)')
        
        # 在新线程中运行处理过程
        thread = threading.Thread(target=run_process)
        thread.daemon = True
        thread.start()
        
        return {'success': True, 'message': '开始处理任务'}
    
    def get_results(self):
        """获取结果数据"""
        return data_manager.get_results()
    
    def open_target_file(self, target_path):
        """打开target_path对应的文件"""
        try:
            if not target_path:
                return {'success': False, 'message': '路径为空'}
            
            # 查找checklist文件
            from funcs import get_only_word_file_path
            checklist_file = get_only_word_file_path(target_path)
            
            if checklist_file and os.path.exists(checklist_file):
                os.startfile(checklist_file)
                self.log(f"已打开文件: {checklist_file}")
                return {'success': True, 'message': f'已打开文件: {os.path.basename(checklist_file)}'}
            else:
                self.log(f"在路径 {target_path} 中未找到checklist文件")
                return {'success': False, 'message': '未找到checklist文件'}
                
        except Exception as e:
            self.log(f"打开文件失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def open_target_folder(self, target_path):
        """打开target_path所在的目录"""
        try:
            if not target_path:
                return {'success': False, 'message': '路径为空'}
            
            if os.path.exists(target_path):
                # 使用Windows资源管理器打开目录
                os.startfile(target_path)
                self.log(f"已打开目录: {target_path}")
                return {'success': True, 'message': f'已打开目录: {target_path}'}
            else:
                self.log(f"目录不存在: {target_path}")
                return {'success': False, 'message': '目录不存在'}
                
        except Exception as e:
            self.log(f"打开目录失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def clear_logs(self):
        """清除前端日志"""
        try:
            global_logger.clear_frontend_logs()
            self.log("日志已清除")
            return {'success': True, 'message': '日志已清除'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_log_config(self):
        """获取日志配置信息"""
        try:
            return {
                'success': True,
                'config': global_logger.config
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

# 创建API实例
api = ProjectFileChecker()

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 设置当前工作目录为脚本所在目录
    # 构建前端HTML文件的绝对路径
    html_path = os.path.join(current_dir, 'static', 'index.html')
    
    # 将文件路径转换为url格式
    html_url = 'file:///' + html_path.replace('\\', '/')
    
    # 获取图标路径
    icon_path = os.path.join(current_dir, 'check.ico')
    # 创建窗口
    window = webview.create_window(
        'Project File Checker',
        url=html_url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(1000, 600),
        resizable=True
    )
    
    # 启动应用
    webview.start(debug=False, icon=icon_path)
