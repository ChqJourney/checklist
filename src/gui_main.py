import webview
import threading
import json
import os
import sys
import pandas as pd
from datetime import datetime
from src.funcs.file_utils import folder_precheck
from src.funcs.path_resolver import get_working_folder_path
from src.funcs.process_manager import kill_all_word_processes
from src.funcs.word_processor import get_only_word_file_path, set_checklist
from src.data.data_manager import data_manager
from src.logger.logger import global_logger, log_info, log_error, log_warning, log_debug, log_critical
from src.config.config_manager import config_manager, get_system_config, set_user_config

class ProjectFileChecker:
    def __init__(self):
        self.task_file_path = ""
        self.tasks = []
        self.is_running = False
        self.log_callback = "None"
        
        try:
            print("=== 初始化ProjectFileChecker ===")
            
            # 加载配置
            print("正在加载配置...")
            # 获取系统配置
            self.log_level = get_system_config('log_config.level')
            self.file_map = get_system_config('file_map')
            self.subFolderConfig = get_system_config('subFolderConfig', {}).get(config_manager.get_team(), {})
            
            print(f"当前团队配置: {self.subFolderConfig}")
            # 获取用户配置
            self.team = config_manager.get_team()
            print(f"当前团队: {self.team}")
            
            self.base_dir = config_manager.get_base_dir()
            print(f"初始化时的基础目录: '{self.base_dir}'")
            
            self.task_list_map = config_manager.get_user_config('task_list_map', {})
            print(f"任务列表映射: {self.task_list_map}")
            
            # 设置全局日志的前端回调
            global_logger.set_frontend_callback(self._frontend_log_callback)
            print("=== ProjectFileChecker 初始化完成 ===")
            
        except Exception as e:
            print(f"初始化过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
    
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
    
    
    def log(self, message):
        """输出日志信息 - 兼容旧接口，现在使用全局日志系统"""
        # 为了向后兼容，保留原有接口
        if self.log_level.upper() == "DEBUG":
            log_debug(message, "GUI")
        elif self.log_level.upper() == "WARNING":
            log_warning(message, "GUI")
        elif self.log_level.upper() == "ERROR":
            log_error(message, "GUI")
        elif self.log_level.upper() == "CRITICAL":
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
                    target_path = get_working_folder_path(self.base_dir,self.team, task['job_no'])
                    
                    result = {
                        'job_no': task['job_no'],
                        'job_creator': task['job_creator'],
                        'engineers': task['engineers'],
                        'target_path': str(target_path) if target_path is not None else None,
                        'status': '未找到目录' if target_path is None else '已处理',
                        'folders': {}
                    }
                    self.log(f"找到目录: {target_path}")
                    if not folder_precheck(target_path, self.team):
                        self.log(f"任务 {task['job_no']} 的文件夹预检查失败")
                        result['status'] = '文件夹预检查失败'
                        data_manager.add_result(result)
                        continue
                    # 检测文件夹
                    self.log("开始检查子文件夹...")
                    
                    
                    # 结束所有Word进程
                    self.log("确保文件夹检查不受干扰,结束所有Word进程...")
                    kill_all_word_processes()
                    # 设置检查列表
                    self.log(f"{task['job_no']}开始写入检查列表...")
                    try:
                        set_checklist(task, target_path, self.team, self.subFolderConfig)
                        self.log(f"{task['job_no']}检查列表写入完成")
                        result['status'] = '完成'
                    except Exception as e:
                        self.log(f"{task['job_no']}设置检查列表失败: {e}")
                        result['status'] = '失败'
                            
                    self.log(f"任务 {task['job_no']} 处理完成:结果为：{result['status']}")
                    
                    
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
                self.task_file_path = ""
                webview.windows[0].evaluate_js('deSelectedTaskFile()')
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
    
    def get_base_dir(self):
        """获取当前基础目录"""
        try:
            # 从配置管理器获取最新的base_dir值
            config_base_dir = config_manager.get_base_dir()
            instance_base_dir = self.base_dir
            
            print(f"配置管理器中的base_dir: '{config_base_dir}'")
            print(f"实例中的base_dir: '{instance_base_dir}'")
            
            # 使用配置管理器中的值，因为它是最新的
            base_dir = config_base_dir
            
            # 更新实例变量
            self.base_dir = base_dir
            
            return {
                'success': True,
                'base_dir': base_dir
            }
        except Exception as e:
            print(f"获取基础目录异常: {e}")
            self.log(f"获取基础目录失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def set_base_dir(self, base_dir):
        """设置基础目录"""
        try:
            # 验证路径
            if base_dir and not os.path.isabs(base_dir):
                return {'success': False, 'message': '基础目录必须是绝对路径'}
            
            if base_dir and not os.path.exists(base_dir):
                return {'success': False, 'message': '指定的目录不存在'}
            
            if base_dir and not os.path.isdir(base_dir):
                return {'success': False, 'message': '指定的路径不是目录'}
            
            # 保存配置
            config_manager.set_base_dir(base_dir)
            self.base_dir = base_dir  # 更新本地变量
            self.log(f"基础目录已更新: {base_dir}")
            
            return {
                'success': True,
                'base_dir': base_dir
            }
        except Exception as e:
            self.log(f"设置基础目录失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def select_folder(self):
        """选择文件夹"""
        try:
            result = webview.windows[0].create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=self.base_dir if self.base_dir and os.path.exists(self.base_dir) else os.getcwd()
            )
            
            if result and len(result) > 0:
                folder_path = result[0] if isinstance(result, list) else result
                self.log(f"已选择文件夹: {folder_path}")
                return {
                    'success': True,
                    'path': folder_path
                }
            else:
                return {'success': False, 'message': '未选择文件夹'}
        except Exception as e:
            self.log(f"文件夹选择失败: {e}")
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
    webview.start(debug=True, icon=icon_path)
