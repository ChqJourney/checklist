"""
E-filing工具自动化模块
使用pywinauto实现E-filing工具的自动化操作
"""

import time
import re
import os
import psutil
from typing import Dict, Any, Optional, List
from pywinauto import Application, findwindows
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.findwindows import ElementNotFoundError
from src.config.efiling_config import EFILING_CONTROLS_CONFIG


class EFilingAutomation:
    """E-filing工具自动化类"""
    
    def __init__(self, logger_callback=None):
        """
        初始化E-filing自动化
        
        Args:
            logger_callback: 日志回调函数
        """
        self.logger_callback = logger_callback
        self.app = None
        self.main_window = None
        self.config = EFILING_CONTROLS_CONFIG
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        if self.logger_callback:
            self.logger_callback(message)
        else:
            print(f"[{level}] {message}")
    
    def start_and_connect(self, exe_path: str) -> bool:
        """
        启动或连接到E-filing工具
        首先检查该exe是否已经在运行，如果是则直接连接，否则启动新实例
        
        Args:
            exe_path: E-filing工具的可执行文件路径
            
        Returns:
            bool: 启动或连接是否成功
        """
        try:
            exe_name = os.path.basename(exe_path)
            self.log(f"检查E-filing工具是否已运行: {exe_name}")
            
            # 检查是否已有该exe在运行
            running_process = self._find_running_process(exe_name)
            
            if running_process:
                self.log(f"发现已运行的E-filing工具进程 (PID: {running_process.pid})，尝试连接...")
                return self._connect_to_existing_process(running_process.pid)
            else:
                self.log(f"未发现运行中的E-filing工具，启动新实例: {exe_path}")
                return self._start_new_process(exe_path)
                
        except Exception as e:
            self.log(f"启动或连接E-filing工具失败: {e}", "ERROR")
            return False
    
    def _find_running_process(self, exe_name: str) -> Optional[psutil.Process]:
        """
        查找是否有指定的exe正在运行
        
        Args:
            exe_name: 可执行文件名（如 "efiling.exe"）
            
        Returns:
            psutil.Process: 找到的进程对象，如果没有找到则返回None
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    # 比较进程名称
                    if proc.info['name'] and proc.info['name'].lower() == exe_name.lower():
                        self.log(f"找到运行中的进程: {proc.info['name']} (PID: {proc.info['pid']})")
                        return proc
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return None
        except Exception as e:
            self.log(f"查找运行进程时出错: {e}")
            return None
    
    def _connect_to_existing_process(self, process_id: int) -> bool:
        """
        连接到已存在的进程
        
        Args:
            process_id: 进程ID
            
        Returns:
            bool: 连接是否成功
        """
        try:
            self.log(f"连接到已存在的进程: {process_id}")
            
            # 连接到应用程序
            self.app = Application().connect(process=process_id)
            self.log("成功连接到已存在的E-filing工具进程")
            
            # 查找主窗口
            window_found = self._find_main_window()
            
            # 如果找到主窗口，确保其已激活
            if window_found:
                self.log("连接成功，窗口已激活")
            
            return window_found
            
        except Exception as e:
            self.log(f"连接到已存在进程失败: {e}", "ERROR")
            return False
    
    def _start_new_process(self, exe_path: str) -> bool:
        """
        启动新的进程
        
        Args:
            exe_path: 可执行文件路径
            
        Returns:
            bool: 启动是否成功
        """
        try:
            self.log(f"启动新的E-filing工具进程: {exe_path}")
            
            # 使用pywinauto启动应用程序
            self.app = Application().start(exe_path)
            self.log("新进程启动成功")
            
            # 等待应用程序完全启动
            time.sleep(self.config['operation']['window_wait'])
            
            # 查找主窗口
            window_found = self._find_main_window()
            
            # 如果找到主窗口，确保其已激活
            if window_found:
                self.log("新进程启动成功，窗口已激活")
            
            return window_found
            
        except Exception as e:
            self.log(f"启动新进程失败: {e}", "ERROR")
            return False
    
    def connect_to_process(self, process_id: int) -> bool:
        """
        连接到E-filing工具进程
        
        Args:
            process_id: 进程ID
            
        Returns:
            bool: 连接是否成功
        """
        try:
            self.log(f"尝试连接到进程 {process_id}")
            
            # 等待进程启动
            time.sleep(self.config['operation']['window_wait'])
            
            # 连接到应用程序
            self.app = Application().connect(process=process_id)
            self.log("成功连接到E-filing工具进程")
            
            # 获取主窗口
            window_found = self._find_main_window()
            
            # 如果找到主窗口，确保其已激活
            if window_found:
                self.log("连接成功，窗口已激活")
            
            return window_found
            
        except Exception as e:
            self.log(f"连接到进程失败: {e}", "ERROR")
            return False
    
    def _find_main_window(self) -> bool:
        """查找主窗口"""
        try:
            retry_count = self.config['operation']['retry_count']
            retry_delay = self.config['operation']['retry_delay']
            
            for attempt in range(retry_count):
                try:
                    # 尝试获取顶级窗口
                    if self.app:
                        # 方法1: 使用top_window()
                        try:
                            self.main_window = self.app.top_window()
                        except Exception as top_window_error:
                            self.log(f"top_window()失败: {top_window_error}")
                            # 方法2: 使用windows()获取所有窗口
                            try:
                                windows = self.app.windows()
                                if windows:
                                    self.main_window = windows[0]
                                    self.log("使用windows()[0]获取主窗口")
                                else:
                                    raise Exception("未找到任何窗口")
                            except Exception as windows_error:
                                self.log(f"windows()也失败: {windows_error}")
                                raise windows_error
                    else:
                        self.log("应用程序对象为空，无法获取窗口", "ERROR")
                        return False
                    
                    if self.main_window:
                        try:
                            window_text = self.main_window.window_text()
                            self.log(f"找到主窗口: '{window_text}'")
                        except:
                            self.log("找到主窗口，但无法获取窗口标题")
                                        
                        
                        # 等待窗口完全加载
                        time.sleep(self.config['operation']['window_wait'])
                        
                        # 激活窗口
                        self._activate_window()
                        
                        return True
                        
                except Exception as e:
                    self.log(f"第 {attempt + 1} 次查找主窗口失败: {e}")
                    if attempt < retry_count - 1:
                        self.log(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
            
            self.log("无法找到主窗口", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"查找主窗口时发生错误: {e}", "ERROR")
            return False

    def _activate_window(self):
        """激活主窗口，使其处于前台并获得焦点"""
        if not self.main_window:
            self.log("主窗口未找到，无法激活", "WARNING")
            return False
        
        try:
            self.log("正在激活E-filing工具窗口...")
            
            # 方法1: 使用restore()恢复窗口（如果被最小化）
            try:
                if hasattr(self.main_window, 'restore'):
                    self.main_window.restore()
                    self.log("窗口已恢复")
            except Exception as restore_error:
                self.log(f"恢复窗口失败: {restore_error}")
            
            # 方法2: 使用set_focus()设置焦点
            try:
                if hasattr(self.main_window, 'set_focus'):
                    self.main_window.set_focus()
                    self.log("窗口焦点已设置")
            except Exception as focus_error:
                self.log(f"设置窗口焦点失败: {focus_error}")
            
            # 方法3: 使用move_window()将窗口移到前台
            try:
                if hasattr(self.main_window, 'move_window'):
                    # 获取当前窗口位置，然后重新设置（这会将窗口带到前台）
                    rect = self.main_window.rectangle()
                    self.main_window.move_window(rect.left, rect.top, rect.width(), rect.height())
                    self.log("窗口已移到前台")
            except Exception as move_error:
                self.log(f"移动窗口到前台失败: {move_error}")
            
                      
            # 等待一下确保操作生效
            time.sleep(0.5)
            
            self.log("E-filing工具窗口激活完成")
            return True
            
        except Exception as e:
            self.log(f"激活窗口时发生错误: {e}", "ERROR")
            return False

    def fill_information(self, base_dir: str, team: str,filing_dir:str) -> bool:
        """
        自动填入信息到E-filing工具
        
        Args:
            base_dir: 基础目录
            team: 团队名称
        Returns:
            bool: 填入是否成功
        """
        if not self.main_window:
            self.log("主窗口未找到，无法填入信息", "ERROR")
            return False
        
        try:
            self.log("开始自动填入E-filing信息...")
            
            # 打印控件信息用于调试
            self._debug_print_controls()
            
            # 填入ComboBox信息
            team_success = self._fill_combo_boxes(team,1)

            shortcut_success = self._fill_combo_boxes("No",0)
            
            # 填入TextBox信息
            base_dir_success = self._fill_text_boxes(base_dir,1)

            efiling_dir_success = self._fill_text_boxes(filing_dir,0)

            success = team_success and shortcut_success and base_dir_success and efiling_dir_success

            if success:
                self.log("E-filing信息自动填入完成")
            else:
                self.log("E-filing信息填入失败", "WARNING")
            
            return success
            
        except Exception as e:
            self.log(f"自动填入信息时发生错误: {e}", "ERROR")
            return False
    
    def _debug_print_controls(self):
        """打印控件信息用于调试"""
        try:
            self.log("=== 窗口控件信息 ===")
            self.main_window.print_control_identifiers()
            self.log("=== 控件信息结束 ===")
        except Exception as e:
            self.log(f"打印控件信息失败: {e}")

    def _fill_combo_boxes(self, team: str,index:int) -> bool:
        """填入ComboBox信息"""
        try:
            # 查找ComboBox控件
            combo_boxes = self.main_window.descendants(control_type="System.Windows.Forms.ComboBox")
            if not combo_boxes:
                self.log("未找到任何ComboBox控件", "WARNING")
                return False
            for i,combo_box in enumerate(combo_boxes):
                if i==index:
                    combo_box.select(team)
                    self.log(f"已选择ComboBox: {team}")
                    return True
            return False
        except Exception as e:
            self.log(f"填入ComboBox时发生错误: {e}", "ERROR")
            return False

    def _fill_text_boxes(self, dir: str,index:int) -> bool:
        """填入TextBox信息"""
        try:
            # 查找TextBox控件
            text_boxes = self.main_window.descendants(control_type='System.Windows.Forms.TextBox')
            if not text_boxes:
                self.log("未找到任何TextBox控件", "WARNING")
                return False
            for i,text_box in enumerate(text_boxes):
                if i==index:
                    text_box.set_text(dir)
                    return True
            return False
        except Exception as e:
            self.log(f"填入TextBox时发生错误: {e}", "ERROR")
            return False
           
                    
            
    
    def disconnect(self):
        """断开连接"""
        try:
            if self.app:
                self.app = None
            if self.main_window:
                self.main_window = None
            self.log("已断开与E-filing工具的连接")
        except Exception as e:
            self.log(f"断开连接时发生错误: {e}")


def create_efiling_automation(logger_callback=None) -> EFilingAutomation:
    """
    创建E-filing自动化实例
    
    Args:
        logger_callback: 日志回调函数
        
    Returns:
        EFilingAutomation: 自动化实例
    """
    return EFilingAutomation(logger_callback)
