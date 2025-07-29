"""
ActiveX控件位置扫描脚本
扫描Word模板文件，找到所有ActiveX控件的位置，并生成配置文件
"""
import os
import json
import win32com.client as win32
from pathlib import Path
import sys

def scan_activex_positions(doc_path, template_name):
    """
    扫描Word文档中的ActiveX控件位置
    :param doc_path: Word文档路径
    :param template_name: 模板名称（用于配置文件）
    :return: 配置字典
    """
    print(f"正在扫描文档: {doc_path}")
    
    if not os.path.exists(doc_path):
        print(f"文件不存在: {doc_path}")
        return None
    
    config = {
        template_name: {
            "description": f"{template_name}模板ActiveX控件位置配置",
            "scanned_from": doc_path
        }
    }
    
    try:
        # 启动Word应用
        word = win32.Dispatch('Word.Application')
        word.Visible = False
        
        # 打开文档
        word_doc = word.Documents.Open(os.path.abspath(doc_path))
        
        print(f"文档包含 {word_doc.Tables.Count} 个表格")
        
        # 扫描每个表格
        for table_index in range(word_doc.Tables.Count):
            table = word_doc.Tables[table_index]
            table_key = f"table_{table_index}"
            config[template_name][table_key] = {}
            
            print(f"扫描表格 {table_index}: {table.Rows.Count} 行 x {table.Columns.Count} 列")
            
            activex_found = 0
            
            # 扫描每行每列
            for row in range(1, table.Rows.Count + 1):
                for col in range(1, table.Columns.Count + 1):
                    try:
                        cell = table.Cell(row, col)
                        
                        # 检查单元格中的ActiveX控件
                        if cell.Range.InlineShapes.Count > 0:
                            for shape_idx in range(1, cell.Range.InlineShapes.Count + 1):
                                try:
                                    shape = cell.Range.InlineShapes(shape_idx)
                                    if hasattr(shape, 'OLEFormat') and shape.OLEFormat is not None:
                                        # 找到ActiveX控件
                                        row_key = str(row)
                                        config[template_name][table_key][row_key] = {
                                            "row": row,
                                            "column": col
                                        }
                                        print(f"  找到ActiveX控件: 行{row}, 列{col}")
                                        activex_found += 1
                                        break  # 每行只记录第一个找到的ActiveX控件
                                except Exception as e:
                                    continue
                            
                            # 如果在这个单元格找到了ActiveX控件，跳到下一行
                            if str(row) in config[template_name][table_key]:
                                break
                                
                    except Exception as e:
                        # 处理合并单元格等情况
                        if "合并" in str(e) or "纵向合并" in str(e):
                            continue
                        else:
                            print(f"  警告: 访问单元格({row},{col})时出错: {str(e)}")
                            continue
            
            print(f"表格 {table_index} 共找到 {activex_found} 个ActiveX控件")
        
        # 关闭文档
        word_doc.Close(False)
        word.Quit()
        
        return config
        
    except Exception as e:
        print(f"扫描过程中出错: {str(e)}")
        if 'word' in locals():
            try:
                word_doc.Close(False)
                word.Quit()
            except:
                pass
        return None

def save_config(config, output_file):
    """保存配置到JSON文件"""
    try:
        # 如果文件已存在，先读取现有配置
        existing_config = {}
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
        
        # 合并配置
        existing_config.update(config)
        
        # 保存配置
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)
        
        print(f"配置已保存到: {output_file}")
        return True
        
    except Exception as e:
        print(f"保存配置文件时出错: {str(e)}")
        return False

def scan_templates():
    """扫描模板文件夹中的所有模板"""
    templates_dir = Path.cwd() / 'templates'
    config_file = Path.cwd() / 'activex_config.json'
    
    if not templates_dir.exists():
        print(f"模板文件夹不存在: {templates_dir}")
        return
    
    print(f"扫描模板文件夹: {templates_dir}")
    
    # 查找所有Word模板文件
    template_files = []
    for ext in ['*.docx', '*.doc']:
        template_files.extend(templates_dir.glob(ext))
    
    if not template_files:
        print("未找到任何Word模板文件")
        return
    
    print(f"找到 {len(template_files)} 个模板文件")
    
    all_config = {}
    
    # 扫描每个模板文件
    for template_file in template_files:
        template_name = template_file.stem  # 文件名（不含扩展名）
        print(f"\n{'='*50}")
        print(f"扫描模板: {template_name}")
        
        config = scan_activex_positions(str(template_file), template_name)
        if config:
            all_config.update(config)
    
    # 保存所有配置
    if all_config:
        if save_config(all_config, str(config_file)):
            print(f"\n✅ 所有模板扫描完成，配置已保存到: {config_file}")
        else:
            print(f"\n❌ 保存配置文件失败")
    else:
        print(f"\n❌ 未扫描到任何有效配置")

def scan_specific_file(file_path, template_name=None):
    """扫描指定的Word文件"""
    if not template_name:
        template_name = Path(file_path).stem
    
    config = scan_activex_positions(file_path, template_name)
    if config:
        config_file = Path.cwd() / 'activex_config.json'
        if save_config(config, str(config_file)):
            print(f"\n✅ 扫描完成，配置已保存到: {config_file}")
            
            # 显示扫描结果
            print(f"\n扫描结果:")
            for template, template_config in config.items():
                print(f"\n模板: {template}")
                for table_key, table_config in template_config.items():
                    if table_key.startswith('table_'):
                        print(f"  {table_key}: {len(table_config)} 个ActiveX控件")
                        for row_key, pos in table_config.items():
                            print(f"    行{row_key}: 第{pos['column']}列")
        else:
            print(f"\n❌ 保存配置文件失败")

def main():
    """主函数"""
    print("ActiveX控件位置扫描工具")
    print("="*50)
    
    if len(sys.argv) > 1:
        # 扫描指定文件
        file_path = sys.argv[1]
        template_name = sys.argv[2] if len(sys.argv) > 2 else None
        scan_specific_file(file_path, template_name)
    else:
        # 扫描模板文件夹
        scan_templates()

if __name__ == "__main__":
    main()
