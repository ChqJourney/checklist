
from funcs.word_processor import get_cell_with_activeX_in_row
import win32com.client as win32

def test_get_activeX_cell():
    doc_path = "test_loads\\lum\\2025\\250100032HZH_Shangyu Shunhe_Luminaire_ETL\\project No._E-filing checklist.docx"
    word = win32.Dispatch('Word.Application')
    word.Visible = False  # 设置为True可以看到Word界面
    word_doc = word.Documents.Open(doc_path)
    
    # 获取包含ActiveX控件的单元格
    cell = get_cell_with_activeX_in_row(word_doc.Tables[0], 15)
    
    assert cell is not None, "ActiveX cell should not be None"
    
    # 清理
    word_doc.Close(False)
    word.Quit()