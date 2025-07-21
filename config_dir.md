# 配置管理器路径解析说明

## 概述
修改后的配置管理器能够智能检测运行环境（开发环境 vs 生产环境），并自动设置正确的配置文件路径。

## 工作原理

### 环境检测
配置管理器使用 `sys.frozen` 属性来检测当前运行环境：

- **开发环境**：`sys.frozen = False`
  - 从源码直接运行 Python 脚本
  - 配置文件位于项目根目录（从 `src/config` 向上两级）
  
- **生产环境**：`sys.frozen = True`
  - PyInstaller 打包后的 exe 文件运行
  - 配置文件位于 exe 文件同级目录

### 路径解析逻辑

```python
def _get_config_directory(self) -> Path:
    if getattr(sys, 'frozen', False):
        # 生产环境：exe 文件同级目录
        executable_dir = Path(sys.executable).parent
        return executable_dir
    else:
        # 开发环境：项目根目录
        project_root = Path(__file__).parent.parent.parent
        return project_root
```

## 部署结构

### 开发环境结构
```
py_checklist/
├── src/
│   ├── config/
│   │   └── config_manager.py
│   └── ...
├── system.json          # 系统配置文件
├── user.json            # 用户配置文件
├── templates/
├── signs/
└── app.py
```

### 生产环境结构
```
部署目录/
├── Check_list.exe       # 主程序
├── system.json          # 系统配置文件（需要手动放置）
├── user.json            # 用户配置文件（需要手动放置）
├── templates/           # 模板文件夹（需要手动放置）
├── signs/               # 签名文件夹（需要手动放置）
└── _internal/           # PyInstaller 生成的内部文件
```

## 配置文件部署

根据 `main.spec` 文件，以下文件/文件夹不会被打包到 exe 中，需要在部署时手动放置到 exe 同级目录：

1. **system.json** - 系统配置文件
2. **user.json** - 用户配置文件
3. **templates/** - 模板文件夹
4. **signs/** - 签名文件夹

## 调试和验证

### 运行时信息获取
可以使用 `get_runtime_info()` 方法获取当前运行环境信息：

```python
from src.config.config_manager import config_manager

runtime_info = config_manager.get_runtime_info()
print(runtime_info)
```

输出示例：
```
{
    'is_frozen': False,
    'executable_path': 'C:/path/to/python.exe',
    'script_path': 'C:/path/to/config_manager.py',
    'config_directory': 'C:/path/to/project',
    'system_config_exists': True,
    'user_config_exists': True,
    'environment_type': 'development'
}
```

### 测试脚本
项目中包含了两个测试脚本：
- `test_production_path.py` - 模拟生产环境测试
- `test_production_real.py` - 使用真实配置文件测试

## 优势

1. **自动环境检测**：无需手动配置，自动识别运行环境
2. **路径智能解析**：开发和生产环境使用不同的路径解析策略
3. **向后兼容**：保持原有 API 不变
4. **调试友好**：提供详细的运行时信息和日志输出
5. **错误处理**：完善的异常处理和错误提示

## 注意事项

1. **部署检查清单**：
   - [ ] 确保 `system.json` 存在于 exe 同级目录
   - [ ] 确保 `user.json` 存在于 exe 同级目录（如不存在会自动创建）
   - [ ] 确保 `templates/` 文件夹存在且包含必要的模板文件
   - [ ] 确保 `signs/` 文件夹存在且包含签名文件

2. **路径要求**：
   - 配置文件必须使用 UTF-8 编码
   - 所有路径都会被转换为绝对路径
   - Windows 环境下支持反斜杠和正斜杠路径

3. **权限要求**：
   - exe 所在目录需要有读写权限（用于创建/修改 user.json）
   - 日志文件目录需要有写权限
