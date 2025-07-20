"""
功能函数模块 - 重构后的兼容性接口
为了保持向后兼容性，此模块导入所有拆分后的功能模块
"""
# 导入所有拆分后的模块功能
from src.funcs.process_manager import kill_all_word_processes
from src.funcs.word_processor import (
    get_engineer_signature_image,
    set_text_in_cell,
    insert_image_in_cell,
    get_only_word_file_path,
    get_cell_with_activeX_in_row,
    set_option_cell,
    set_fields_value,
    set_all_option_cells_for_ppt,
    set_option_cells_for_general,
    set_option_cells,
    set_checklist,
    get_activeX_cells
)
from src.funcs.file_utils import (
    detect_folder_has_file,
    detect_folders,
    folder_precheck
)
from src.funcs.path_resolver import (
    get_working_folder_path,
    get_working_folder_path_for_ppt,
    get_working_folder_path_for_general
)
from src.funcs.task_utils import (
    update_task_status,
    log_task_progress
)


# 保持原有的测试代码
if __name__ == "__main__":
    import os
    shorts = os.path.join(os.getcwd(), 'shortcuts')
    t_path = get_working_folder_path(shorts, "ppt", "250100032HZH")
    print(t_path)