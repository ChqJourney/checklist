# Checklist 自动填写工具

这是一个自动化工具，用于批量处理项目的checklist.docx文件。程序会读取Excel任务列表，扫描对应的项目文件夹，并自动填写checklist文档。

## 工作流程

1. **准备工作**
   - 在工作目录下准备 `task list.xlsx` 文件，包含项目列表信息
   - 确保 `config.json` 配置文件正确配置
   - 准备签名图片文件夹 `signs`

2. **自动化处理流程**
   - 根据 `config.json` 中的 `task_list_map` 读取 `task list.xlsx`，获取项目信息（项目号、创建人、负责工程师）
   - 遍历每个项目，执行以下操作：
     1. 根据项目号（job_no）在 `shortcuts_path` 中查找对应的项目文件夹快捷方式
     2. 扫描项目文件夹下的子文件夹，检测是否包含文件
     3. 根据扫描结果，自动设置 checklist.docx 中表格的 ActiveX 控件状态
     4. 从 `signs` 文件夹获取签名图片，插入到 checklist.docx 的指定位置
     5. 填写项目基本信息（项目号、创建人、工程师、当前日期）
     6. 保存并关闭文档

## 配置说明

### config.json 配置项
- `subFolderNames`: 需要检测的子文件夹列表
- `shortcuts_path`: 项目快捷方式存放路径
- `task_list_map`: Excel文件列映射（列索引对应字段）
- `subFolder_map`: 子文件夹与checklist表格行号的映射关系

### 文件结构要求
- `task list.xlsx`: 项目任务列表
- `config.json`: 配置文件
- `signs/`: 签名图片文件夹
- 项目文件夹需要包含名为 "checklist" 的 Word 文档

## 功能特点
- 自动终止现有Word进程，避免冲突
- 支持快捷方式和符号链接的项目文件夹定位
- 自动检测文件夹内容并设置对应的复选框状态
- 自动插入签名图片并调整尺寸
- 批量处理多个项目
