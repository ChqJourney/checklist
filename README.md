# Checklist 自动填写工具

这是一个自动化工具，用于批量处理项目的checklist.docx文件。程序会读取Excel任务列表，扫描对应的项目文件夹，并自动填写checklist文档。

## 工作流程

1. **准备工作**
   - 用户自行在工作目录下准备 `task list.xlsx` 文件，包含项目列表信息
   - 用户确保配置文件`user.json`和`system.json` 正确配置
   - 用户准备签名图片文件夹 `signs`

2. **自动化处理流程**
   - 根据 `user.json` 中的 `task_list_map` 读取 `task list.xlsx`，获取项目信息（项目号、创建人、负责工程师）
   - 遍历每个项目，执行以下操作：
     1. 根据项目号（job_no）在 `base_dir` 中, 根据`user.json`中的`team`使用不同方式去查找对应的项目文件夹，`team`为`general`或`ppt`,
     2. 根据`system.json`中的`subFolderConfig`的配置，填写`fields`，再根据`options`配置，扫描对应文件夹的情况来设置项目根目录下word文档中的activeX控件
     3. 大部分fields是填写文本信息部分（项目号、创建人、工程师、当前日期），部分fields需要从 `signs` 文件夹获取签名图片并插入
     4. options对应文件情况，根据`team`的不同,有不同的方式扫描
     5. 保存并关闭文档
     6. 记录
   

## 配置说明

### user.json 配置项
- `team`: 组别
- `base_dir`: 目标文件夹，项目文件夹在其子目录中
- `task_list_map`: Excel文件列映射（列索引对应字段）存在，就返回true
### system.json 配置项
- `subFolderConfig`: 子文件夹与checklist表格行号的映射关系
- `file_map`: 当`team`为`general`时，搜索文件的方式，只要这些命名规则的文件存在，就返回true
### 文件结构要求
- `task list.xlsx`: 项目任务列表
- `user.json`: 用户配置文件，用户可更改
- `sytem.json`: 系统配置文件，用户不可更改
- `signs/`: 签名图片文件夹
- 项目文件夹需要包含名为 "checklist" 的 Word 文档

## 功能特点
- 自动终止现有Word进程，避免冲突
- 支持快捷方式和符号链接的项目文件夹定位
- 自动检测文件夹内容并设置对应的复选框状态
- 自动插入签名图片并调整尺寸
- 批量处理多个项目

## 当前进度
- 在测试环境中功能已实现
- ui中选择task list的逻辑还需优化，二次选择以及任务完成后的task list初始化
- 所有文件项检查逻辑detect_folders_status还需斟酌
- 核心方法set_checklist还需梳理优化
