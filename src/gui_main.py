import glob
import webview
import threading
import json
import os
import sys
import pandas as pd
import subprocess
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
        self.cancel_requested = False
        self.current_thread = None
        
        try:
            print("=== 初始化ProjectFileChecker ===")
            
            # 加载配置
            print("正在加载配置...")
            # 获取系统配置
            self.log_level = get_system_config('log_config.level')
            self.file_map = get_system_config('file_map')
            # 获取用户配置
            self.team = config_manager.get_team()
            print(f"当前团队: {self.team}")
            
            # 获取子文件夹配置
            team_category = self.team.lower() if self.team=='PPT' else 'general'
            self.subFolderConfig = get_system_config('subFolderConfig', {}).get(team_category, {})

            print(f"当前团队配置: {self.subFolderConfig}")
            
            self.base_dir = config_manager.get_base_dir()
            print(f"初始化时的基础目录: '{self.base_dir}'")

            self.archive_path = config_manager.get_user_config('archive_path', {})
            print(f"初始化时归档目录: '{self.archive_path}'")
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
        finally:
            pass

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
            # 如果正在运行，则请求取消
            self.log("请求取消任务处理...")
            self.cancel_requested = True
            return {'success': True, 'message': '已请求取消'}
        
        def run_process():
            try:
                self.is_running = True
                self.cancel_requested = False

                data_manager.clear_results()  # 清空之前的结果
                data_manager.set_processing_status(True)
                # 更新表格
                webview.windows[0].evaluate_js(f'updateResults({json.dumps(data_manager.get_results())})')
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
                    # 检查是否请求取消
                    if self.cancel_requested:
                        self.log("用户请求取消，停止处理任务")
                        break
                    
                    self.log(f"处理任务 {i+1}/{len(self.tasks)}: {task['job_no']}")
                    
                    # 获取工作目录
                    target_path = get_working_folder_path(self.base_dir,self.team, task['job_no'].strip())
                    log_info(f"target_path: {target_path}", "GUI")
                    s_status = '未找到目录' if target_path is None else ('快捷方式已损坏' if str(target_path).strip() == "." else '已处理')
                    result = {
                        'job_no': task['job_no'],
                        'job_creator': task['job_creator'],
                        'engineers': task['engineers'],
                        'target_path': str(target_path) if target_path is not None else None,
                        'status': s_status,
                        'folders': {}
                    }
                    if target_path is None or str(target_path).strip() == ".":
                        log_error(f"任务 {task['job_no']} 的工作目录未找到")
                        data_manager.add_result(result)
                        webview.windows[0].evaluate_js(f'updateResults({json.dumps(data_manager.get_results())})')
                        continue
                    self.log(f"找到目录: {target_path}")
                    if not folder_precheck(target_path, self.team):
                        log_error(f"任务 {task['job_no']} 的文件夹预检查失败")
                        result['status'] = '文件夹预检查失败'
                        data_manager.add_result(result)
                        webview.windows[0].evaluate_js(f'updateResults({json.dumps(data_manager.get_results())})')
                        continue
                    # 检测文件夹
                    self.log("开始检查子文件夹...")
                    
                    # 再次检查是否请求取消
                    if self.cancel_requested:
                        self.log("用户请求取消，停止处理任务")
                        break
                    
                    # 结束所有Word进程
                    self.log("确保文件夹检查不受干扰,结束所有Word进程...")
                    kill_all_word_processes()
                    
                    # 再次检查是否请求取消
                    if self.cancel_requested:
                        self.log("用户请求取消，停止处理任务")
                        break
                    
                    # 设置检查列表
                    self.log(f"{task['job_no']}开始写入检查列表...")
                    try:
                        set_checklist(task, target_path, self.team, self.subFolderConfig)
                        self.log(f"{task['job_no']}检查列表写入完成")
                        result['status'] = '完成'
                    except Exception as e:
                        log_error(f"{task['job_no']}设置检查列表失败: {e}")
                        if isinstance(e,PermissionError):
                            result['status']='无写入权限'
                        else:
                            result['status'] = '失败'
                            
                    self.log(f"任务 {task['job_no']} 处理完成:结果为：{result['status']}")
                    
                    
                    # 使用数据管理器添加结果
                    data_manager.add_result(result)
                    
                    # 更新表格
                    webview.windows[0].evaluate_js(f'updateResults({json.dumps(data_manager.get_results())})')
                
                if self.cancel_requested:
                    self.log(f"任务处理已取消，已处理 {len(data_manager.get_results())} 个任务")
                else:
                    self.log(f"所有任务处理完成，共处理 {len(self.tasks)} 个任务")
              
                
                # 保存结果到文件
                #data_manager.save_to_file()
                
            except Exception as e:
                log_error(f"处理过程中发生错误: {e}")
            finally:
                self.is_running = False
                self.cancel_requested = False
                self.task_file_path = ""
                webview.windows[0].evaluate_js('deSelectedTaskFile()')
                data_manager.set_processing_status(False)
                webview.windows[0].evaluate_js('setRunning(false)')
        
        # 在新线程中运行处理过程
        thread = threading.Thread(target=run_process)
        thread.daemon = True
        self.current_thread = thread
        thread.start()
        
        return {'success': True, 'message': '开始处理任务'}

    def rerun_task(self, job_no):
        """重新运行单个任务"""
        if self.is_running:
            return {'success': False, 'message': '有任务正在运行，请等待完成或取消后再试'}

        # 查找指定的任务
        task_to_rerun = None
        if self.tasks:
            for task in self.tasks:
                if task['job_no'] == job_no:
                    task_to_rerun = task
                    break
        
        if not task_to_rerun:
            self.log(f"未找到任务 {job_no}")
            return {'success': False, 'message': f'未找到任务 {job_no}'}

        def run_single_task():
            try:
                self.is_running = True
                self.cancel_requested = False
                
                data_manager.set_processing_status(True)
                webview.windows[0].evaluate_js('setRunning(true)')
                
                self.log(f"开始重新运行任务: {job_no}")
                
                # 获取工作目录
                target_path = get_working_folder_path(self.base_dir, self.team, task_to_rerun['job_no'])
                result = {
                    'job_no': task_to_rerun['job_no'],
                    'job_creator': task_to_rerun['job_creator'],
                    'engineers': task_to_rerun['engineers'],
                    'target_path': str(target_path) if target_path is not None else None,
                    'status': '未找到目录' if target_path is None else '处理中',
                    'folders': {}
                }
                
                # 更新现有结果中的这一项为处理中状态
                data_manager.update_result_by_job_no(job_no, result)
                webview.windows[0].evaluate_js(f'updateResults({json.dumps(data_manager.get_results())})')
                
                if target_path is None:
                    self.log(f"任务 {task_to_rerun['job_no']} 的工作目录未找到")
                    result['status'] = '未找到目录'
                    data_manager.update_result_by_job_no(job_no, result)
                    webview.windows[0].evaluate_js(f'updateResults({json.dumps(data_manager.get_results())})')
                    return
                
                self.log(f"找到目录: {target_path}")
                
                if not folder_precheck(target_path, self.team):
                    self.log(f"任务 {task_to_rerun['job_no']} 的文件夹预检查失败")
                    result['status'] = '文件夹预检查失败'
                    data_manager.update_result_by_job_no(job_no, result)
                    webview.windows[0].evaluate_js(f'updateResults({json.dumps(data_manager.get_results())})')
                    return
                
                # 结束所有Word进程
                self.log("确保文件夹检查不受干扰,结束所有Word进程...")
                kill_all_word_processes()
                
                # 设置检查列表
                self.log(f"{task_to_rerun['job_no']}开始写入检查列表...")
                try:
                    set_checklist(task_to_rerun, target_path, self.team, self.subFolderConfig)
                    self.log(f"{task_to_rerun['job_no']}检查列表写入完成")
                    result['status'] = '完成'
                except Exception as e:
                    self.log(f"{task_to_rerun['job_no']}设置检查列表失败: {e}")
                    result['status'] = '失败'
                
                self.log(f"任务 {task_to_rerun['job_no']} 处理完成: 结果为：{result['status']}")
                
                # 更新结果
                data_manager.update_result_by_job_no(job_no, result)
                webview.windows[0].evaluate_js(f'updateResults({json.dumps(data_manager.get_results())})')
                
            except Exception as e:
                self.log(f"处理过程中发生错误: {e}")
                # 确保即使出错也更新状态
                result = {
                    'job_no': task_to_rerun['job_no'],
                    'job_creator': task_to_rerun['job_creator'],
                    'engineers': task_to_rerun['engineers'],
                    'target_path': str(target_path) if 'target_path' in locals() else None,
                    'status': f'错误: {str(e)}',
                    'folders': {}
                }
                data_manager.update_result_by_job_no(job_no, result)
                webview.windows[0].evaluate_js(f'updateResults({json.dumps(data_manager.get_results())})')
            finally:
                self.is_running = False
                data_manager.set_processing_status(False)
                webview.windows[0].evaluate_js('setRunning(false)')
        
        # 在新线程中运行处理过程
        thread = threading.Thread(target=run_single_task)
        thread.daemon = True
        self.current_thread = thread
        thread.start()
        
        return {'success': True, 'message': f'开始重新运行任务 {job_no}'}
    
    def get_results(self):
        """获取结果数据"""
        return data_manager.get_results()
    
    def open_target_file(self, target_path):
        """打开target_path对应的文件"""
        try:
            if not target_path:
                return {'success': False, 'message': '路径为空'}
            
            # 查找checklist文件
            checklist_files = glob.glob(os.path.join(target_path, '*checklist*.doc*'))
            checklist_files = [f for f in checklist_files if not os.path.basename(f).startswith(('~$', '.', '__'))]

            if checklist_files and os.path.exists(checklist_files[0]):
                os.startfile(checklist_files[0])
                self.log(f"已打开文件: {checklist_files[0]}")
                return {'success': True, 'message': f'已打开文件: {os.path.basename(checklist_files[0])}'}
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
    
    def get_all_config(self):
        """获取所有配置"""
        try:
            config = {
                'team': config_manager.get_team(),
                'base_dir': config_manager.get_base_dir(),
                'archive_path': config_manager.get_user_config('archive_path', ''),
                'checklist': config_manager.get_user_config('checklist', 'cover'),
                'task_list_map': config_manager.get_user_config('task_list_map', {
                    'job_no': 0,
                    'job_creator': 1,
                    'engineers': 2
                }),
                'efilling_tool_path': config_manager.get_user_config('efilling_tool_path', '')
            }
            return {'success': True, 'config': config}
        except Exception as e:
            self.log(f"获取配置失败: {e}")
            return {'success': False, 'message': str(e)}

    def save_all_config(self, new_config):
        """保存所有配置"""
        try:
            # 验证配置
            if not isinstance(new_config, dict):
                raise ValueError("配置必须是字典格式")
            
            # 保存各项配置
            config_manager.set_user_config('team', new_config.get('team', 'LUM'))
            config_manager.set_user_config('base_dir', new_config.get('base_dir', ''))
            config_manager.set_user_config('archive_path', new_config.get('archive_path', ''))
            config_manager.set_user_config('checklist', new_config.get('checklist', 'cover'))
            config_manager.set_user_config('task_list_map', new_config.get('task_list_map', {
                'job_no': 0,
                'job_creator': 1,
                'engineers': 2
            }))
            config_manager.set_user_config('efilling_tool_path', new_config.get('efilling_tool_path', ''))
            
            # 保存到文件
            config_manager.save_user_config()
            
            # 更新当前实例的配置
            self.team = new_config.get('team', 'LUM')
            self.base_dir = new_config.get('base_dir', '')
            self.task_list_map = new_config.get('task_list_map', {
                'job_no': 0,
                'job_creator': 1,
                'engineers': 2
            })
             # 获取子文件夹配置
            team_category = self.team.lower() if self.team=='PPT' else 'general'
            self.subFolderConfig = get_system_config('subFolderConfig', {}).get(team_category, {})
            
            
            self.log("配置保存成功")
            return {'success': True, 'message': '配置保存成功'}
            
        except Exception as e:
            self.log(f"保存配置失败: {e}")
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
        """选择基础目录"""
        try:
            result = webview.windows[0].create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=os.getcwd(),
                allow_multiple=False
            )
            
            if result:
                return {'success': True, 'path': result}
            else:
                return {'success': False, 'message': '未选择目录'}
                
        except Exception as e:
            self.log(f"选择文件夹时发生错误: {e}")
            return {'success': False, 'message': str(e)}

    def select_archive_folder(self):
        """选择归档目录"""
        try:
            result = webview.windows[0].create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=os.getcwd(),
                allow_multiple=False
            )
            
            if result:
                return {'success': True, 'path': result}
            else:
                return {'success': False, 'message': '未选择目录'}
                
        except Exception as e:
            self.log(f"选择归档文件夹时发生错误: {e}")
            return {'success': False, 'message': str(e)}
    
    def select_exe_file(self):
        """选择exe文件"""
        try:
            file_types = ('Executable Files (*.exe)', 'All files (*.*)')
            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                directory=os.getcwd(),
                allow_multiple=False,
                file_types=file_types
            )
            
            if result and len(result) > 0:
                exe_path = result[0]
                if not exe_path.lower().endswith('.exe'):
                    return {'success': False, 'message': '请选择.exe文件'}
                
                self.log(f"已选择E-filing工具: {os.path.basename(exe_path)}")
                return {
                    'success': True,
                    'path': exe_path
                }
            else:
                return {'success': False, 'message': '未选择文件'}
        except Exception as e:
            self.log(f"文件选择失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def open_efiling_tool(self):
        """打开E-filing工具并自动填入信息"""
        try:
            efilling_tool_path = config_manager.get_user_config('efilling_tool_path', '')
            
            if not efilling_tool_path:
                return {'success': False, 'message': '未配置E-filing工具路径'}
            
            if not os.path.exists(efilling_tool_path):
                return {'success': False, 'message': 'E-filing工具文件不存在'}
            
            if not efilling_tool_path.lower().endswith('.exe'):
                return {'success': False, 'message': 'E-filing工具路径必须指向.exe文件'}
            
            # 使用pywinauto启动并自动化E-filing工具
            try:
                from src.funcs.efiling_automation import create_efiling_automation
                
                self.log(f"正在启动E-filing工具: {os.path.basename(efilling_tool_path)}")
                
                # 创建自动化实例
                automation = create_efiling_automation(logger_callback=self.log)
                
                # 使用pywinauto启动应用程序并连接
                if automation.start_and_connect(efilling_tool_path):
                    
                    #print("E-filing工具启动成功，正在自动填入信息...")
                    #fill_success = automation.fill_information(self.base_dir,self.team,self.archive_path)
                    # 断开连接
                    automation.disconnect()
                    
                    #if fill_success:
                        #return {'success': True, 'message': 'E-filing工具启动成功并已自动填入信息'}
                    #else:
                        #return {'success': True, 'message': 'E-filing工具启动成功，但自动填入信息时遇到问题'}
                else:
                    return {'success': False, 'message': 'E-filing工具启动失败或无法连接'}
                        
            except ImportError as import_error:
                self.log(f"导入pywinauto模块失败: {import_error}")
                return {'success': False, 'message': 'pywinauto未安装，无法启动E-filing工具'}
            except Exception as auto_error:
                self.log(f"启动E-filing工具失败: {auto_error}")
                return {'success': False, 'message': f'启动E-filing工具失败: {auto_error}'}
            
        except Exception as e:
            self.log(f"启动E-filing工具失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def _get_current_task_info(self):
        """获取当前任务信息用于自动填入"""
        try:
            # 如果有当前处理的任务，返回其信息
            if hasattr(self, 'current_task') and self.current_task:
                return self.current_task
            
            # 如果有任务列表，返回第一个任务的信息
            if self.tasks and len(self.tasks) > 0:
                return self.tasks[0]
            
            # 返回默认信息
            return {
                'job_no': 'DEFAULT_JOB',
                'job_creator': 'DEFAULT_CREATOR', 
                'engineers': 'DEFAULT_ENGINEER'
            }
            
        except Exception as e:
            self.log(f"获取当前任务信息失败: {e}")
            return {
                'job_no': 'ERROR_JOB',
                'job_creator': 'ERROR_CREATOR',
                'engineers': 'ERROR_ENGINEER'
            }

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
