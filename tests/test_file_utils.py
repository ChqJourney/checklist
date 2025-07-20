import os
from src.funcs.file_utils import detect_folder_has_file, detect_folders_status, folder_name_check
from src.funcs.path_resolver import get_working_folder_path_for_general


def test_get_working_folder_path_for_general():
    base_dir = "test_loads\\lum\\"
    assert get_working_folder_path_for_general(base_dir,"250100032HZH") == f"{base_dir}2025\\250100032HZH_Shangyu Shunhe_Luminaire_ETL"


def test_get_working_folder_path_for_general_with_none_job_no():
    base_dir = "test_loads\\lum\\"
    result = get_working_folder_path_for_general(base_dir, None)
    assert result is None or result == ""

def test_get_working_folder_path_for_general_with_invalid_job_no():
    base_dir = "test_loads\\lum\\"
    result = get_working_folder_path_for_general(base_dir, "invalid_job_no")
    assert result is None or result == ""

def test_folder_name_check():
    target_folder = "test_loads\\lum\\2025\\250100032HZH_Shangyu Shunhe_Luminaire_ETL"
    team = "general"
    
    # 测试文件夹名检查
    assert folder_name_check(target_folder, team) is True

    # 测试不存在的文件夹
    assert folder_name_check("non_existent_folder", team) is False

    # 测试不符合规范的文件夹名
    assert folder_name_check("test_loads\\lum\\2025\\invalid_folder", team) is False

def test_detect_folder_has_file():
    folder_path = "test_loads\\lum\\2025\\250100032HZH_Shangyu Shunhe_Luminaire_ETL\\1 Application documents"
    
    # 测试有文件的文件夹
    assert detect_folder_has_file(folder_path) is True

    # 测试空文件夹
    empty_folder = "test_loads\\lum\\2025\\empty_folder"
    os.makedirs(empty_folder, exist_ok=True)
    assert detect_folder_has_file(empty_folder) is False
    os.rmdir(empty_folder)  # 清理测试创建的空文件夹

def test_detect_folders_status():
    working_folder_path = "test_loads\\lum\\2025\\250100032HZH_Shangyu Shunhe_Luminaire_ETL"
    team = "general"
    options_config = {
        "0 Job sheet & Quotation": {
            "JobSheet": 5,
            "Quotation": 6
        },
        "1 Application documents": {
						"GS": 9,
						"CB": 10,
						"ETL": 11
					},
                    "1 Application documents\\Others service app":12,
					"1 Application documents\\other application documents": 13,
					"2 Certificate": 7,
					"3 Test report": 8,
    }
    # 测试工作文件夹中的子文件夹状态
    status= detect_folders_status(working_folder_path, team, options_config)
    print(status)
    assert status["0 Job sheet & Quotation"]["JobSheet"] is False
    assert status["0 Job sheet & Quotation"]["Quotation"] is False
    assert status["1 Application documents"]["GS"] is True
    assert status["1 Application documents"]["CB"] is True
    assert status["1 Application documents"]["ETL"] is False
    assert status["1 Application documents\\Others service app"]is False
    assert status["1 Application documents\\other application documents"] is False
    assert status["2 Certificate"] is False
    assert status["3 Test report"] is True