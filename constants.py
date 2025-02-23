import os

from config import cfg

MIN_TOC_PAGE = 3
MAX_TOC_PAGE = 10
MIN_SEC_PER_PAGE = 15

DATA_DIR = 'data/'
BOOK_LIST = sorted(
    [book for book in os.listdir(DATA_DIR) if book.endswith('.pdf')],
    key=lambda book: list(cfg.keys()).index(book))

SORT_NEEDS = {
    'data/Manual_Cls 6_Lb Ro_3_Litera.pdf': True,
    'data/Manual_Cls 7_Lb Ro_4_Litera.pdf': True,
    'data/Manual_Cls 7_Lb Ro_5_Intuitext.pdf': True
}
SORT_CHAPTER_NEEDS = {
    'data/Manual_Cls 7_Lb Ro_5_Intuitext.pdf': True
}

SORT_EXTRACT_NEEDS = {
    'data/Manual_Cls 6_Lb Ro_1_EDP.pdf': True
}
