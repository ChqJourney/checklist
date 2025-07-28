"""
E-filing工具自动化配置
用于配置pywinauto控件查找和操作的参数
"""

# E-filing工具控件配置
EFILING_CONTROLS_CONFIG = {
    # 窗口识别配置
    'window': {
        'title_regex': r'.*E.?filing.*|.*电子.*归档.*',  # 窗口标题正则表达式
        'class_name': None,  # 窗口类名，如果知道的话
        'timeout': 10,  # 等待窗口出现的超时时间(秒)
    },
    
    # ComboBox配置
    'combo_boxes': [
        {
            'name': 'project_type',  # 项目类型选择框
            'auto_id': None,  # 自动化ID，如果知道的话
            'control_type': 'ComboBox',
            'index': 0,  # 第几个ComboBox(从0开始)
            'fill_with': 'job_no',  # 要填入的数据字段
        },
        # 可以添加更多ComboBox配置
    ],
    
    # TextBox配置
    'text_boxes': [
        {
            'name': 'job_number',  # 项目编号输入框
            'auto_id': None,
            'control_type': 'Edit',
            'index': 0,  # 第几个TextBox(从0开始)
            'fill_with': 'job_no',  # 要填入的数据字段
        },
        {
            'name': 'creator',  # 客服输入框
            'auto_id': None,
            'control_type': 'Edit', 
            'index': 1,
            'fill_with': 'job_creator',
        },
        {
            'name': 'engineer',  # 工程师输入框
            'auto_id': None,
            'control_type': 'Edit',
            'index': 2,
            'fill_with': 'engineers',
        },
        # 可以添加更多TextBox配置
    ],
    
    # 其他控件配置
    'buttons': [
        # 如果需要点击特定按钮，可以在这里配置
    ],
    
    # 操作配置
    'operation': {
        'fill_delay': 0.5,  # 每次填入操作之间的延迟(秒)
        'window_wait': 3,   # 等待窗口加载的时间(秒)
        'retry_count': 3,   # 查找控件的重试次数
        'retry_delay': 1,   # 重试之间的延迟(秒)
    }
}

