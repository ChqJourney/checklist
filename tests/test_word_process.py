
from src.funcs.word_processor import get_cell_with_activeX_in_row,get_cell_with_activeX_by_config,load_activex_config
import win32com.client as win32
from contextlib import contextmanager
import pythoncom
@contextmanager
def word_context(doc_path):
    word = win32.Dispatch('Word.Application')
    word.Visible = False
    word_doc = word.Documents.Open(doc_path)
    try:
        yield word, word_doc
    finally:
        word_doc.Close(False)
        word.Quit()


def test_activeX_config_okay():
    config=load_activex_config()
    general_config=config['general_template']
    assert general_config['table_0']["5"]["column"]==3
    assert general_config['table_0']["5"]["row"]==5