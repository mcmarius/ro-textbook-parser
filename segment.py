import os
import re

import pymupdf

from config import cfg

MIN_TOC_PAGE = 3
MAX_TOC_PAGE = 10
MIN_SEC_PER_PAGE = 15

DATA_DIR = 'data'
book_list = [book for book in os.listdir(DATA_DIR) if book.endswith('.pdf')]


SORT_NEEDS = {
    'data/Manual_Cls 6_Lb Ro_3_Litera.pdf': True,
    'data/Manual_Cls 7_Lb Ro_4_Litera.pdf': True,
    'data/Manual_Cls 7_Lb Ro_5_Intuitext.pdf': True
}
SORT_CHAPTER_NEEDS = {
    'data/Manual_Cls 7_Lb Ro_5_Intuitext.pdf': True
}

def safe_int(nr):
    try:
        return int(nr)
    except ValueError:
        return None


def is_toc_page(pdf_page):
    return len([x for x in re.split('(\d{1,}[^\.][– ]?[\d]?)\n', pdf_page) if x and x[0].isdigit()]) >= MIN_SEC_PER_PAGE and pdf_page.count(';') < 20 and 'Varianta tipărită' not in pdf_page


def find_chapter(pdf):
    chapter_pages = []
    for i in range(MIN_TOC_PAGE, MAX_TOC_PAGE):
        if is_toc_page(pdf.get_page_text(i)):
            fixed_lines = fix_lines(pdf.get_page_text(i, sort=SORT_CHAPTER_NEEDS.get(pdf.name, False)).split('\n'))
            to_skip = 0
            #print(fixed_lines)
            for i, line in enumerate(fixed_lines):
                if 'UNITATEA' in line or 'Unitatea' in line or re.findall('[2-8]\t', line):
                    #print(f'got {i} -> {line}')
                    if '.  . ' in line[-10:]:
                        sep = '\.  \. '
                    elif '. .' in line[-10:]:
                        sep = '\. \.'
                    elif ' / ' in line[-10:]:
                        sep = ' / '
                    elif '/' in line[-10:]:
                        sep = '/'
                    else:
                        sep = ' '
                    if 'DE ÎNVĂȚĂRE' in line:
                        line_lim = 22
                    else:
                        line_lim = 11
                    # page_in_line = line.rsplit(sep, 1)[1].strip()
                    candidates = re.findall(f'{sep}\s*(\d+)', line[line_lim:])
                    if len(candidates) >= 1:
                        page_in_line = candidates[0].strip()
                        if page_in_line[0].isdigit():
                            #print(f'sep {sep}, pg {page_in_line}')
                            chapter_pages.append(page_in_line)
                    else:
                        # skip the pages for the previous found chapter
                        if i < to_skip:
                            continue
                        # we need to find the first section of this chapter
                        for j in range(i + 1, len(fixed_lines)):
                            possible_page = re.findall('\d{2,}$', fixed_lines[j])
                            #print(f"possible: {possible_page}")
                            if possible_page:
                                chapter_pages.append(possible_page[0])
                                to_skip = j
                                break
    return sorted(list({int(x) for x in chapter_pages}))


def get_toc_pages(lines):
    pages = []
    # / pages
    # pages = [line for line in lines.split('  ') if line and '/' in line]
    page_lines = [line.strip() for line in lines.split('    ') if line and ('/' in line or '...' in line or '. .' in line or ' .   .' in line or ' .  .' in line or '.  . ' in line or ' – ' in line or re.findall('\d{2,}', line) or re.findall('\d{2,}-\d{2,}', line))]
    #print(page_lines)
    #print('\n----1------\n')
    page_lines = [small_line for line in page_lines for small_line in line.split('\n') if small_line]
    if len(page_lines) < 10:  # only whitespace is the separator; fortunately, no numbers in titles
        return [num for line in lines.split('\n') for num in re.findall('(\d{2,})', line)]
    #print(lines)
    #print('-------2----------\n\n')
    #print(page_lines)
    for line in page_lines:
        if safe_int(line):
            pages.append(line.strip())
            #print(f'got {line}')
            continue
        sep = '..'
        if ' .   .' in line:
            sep = ' .   .'
        elif '.  .' in line:
            sep = '.  .'
        elif ' . ' in line:
            sep = ' . '
        elif ' / ' in line:
            sep = ' / '
        elif '/' in line:
            sep = '/'
        elif '...' in line:
            sep = '...'
        elif ' – ' in line:
            sep = ' – '
        elif re.findall('\d{2,}-\d{2,}', line):
            pages += re.findall('\d{2,}-\d{2,}', line)[0].split('-')
            continue
        elif re.findall('\d{2,}$', line):
            pages += re.findall('\d{2,}$', line)
            continue
        #if len(line.rsplit(sep, 1)) < 2:
        if len(line.rsplit(sep)) < 2:
            continue
        for pg in line.rsplit(sep):
            page_in_line = pg.strip()
            # page_in_line = line.rsplit(sep, 1)[1].strip()
            # print(f'got line {line}')
            if not page_in_line:
                continue
            #print(f'got pg {page_in_line} sep {sep}')
            if page_in_line[0].isdigit():
                #print(f'got > {page_in_line}')
                #print(f"got >> {''.join(x for x in page_in_line if x.isdigit())}")
                if '.' in page_in_line[0:3]:
                    continue
                if '-' in page_in_line:
                    pages += page_in_line.split('-')
                else:
                    pages.append(''.join(x for x in page_in_line if x.isdigit()))
    # print(page_lines)
    # print(len(pages))
    # fix_lines([z for x in pdf4.get_page_text(5, sort=True).split('\n') for z in x.split('  ') if z and '/' in z])
    # for x in re.split('[^L] ?/? ?(\d{2,3})', pdf_page):
    # for x in re.split('[^L] ?/? ?(\d{2,3})', lines):
    # for line in lines:
    #     print(f'got {line}')
    #     if not line or not line[0].isdigit():
    #         continue
    #     pass
    return pages # fix_lines(pages)
    # return [x for x in re.split('[^L] ?/? ?(\d{2,3})', pdf_page) if x and x[0].isdigit()]
    return [x.strip() for x in re.split('(\d{1,}[^\.,][– ]?[\d]?)\n', pdf_page) if x and x[0].isdigit()]

def find_toc(pdf):
    toc_pages = []
    for i in range(MIN_TOC_PAGE, MAX_TOC_PAGE):
        if is_toc_page(pdf.get_page_text(i)):
            toc_page_list = get_toc_pages(pdf.get_page_text(i, sort=SORT_NEEDS.get(pdf.name, False)))
            # fixed_lines = fix_lines(pdf.get_page_text(i).split('\n'))
            # toc_page_list = get_toc_pages(fixed_lines) # get_toc_pages(pdf.get_page_text(i))
            if len(toc_page_list) >= MIN_SEC_PER_PAGE:
                toc_pages += toc_page_list
    return sorted(list(set([int(x) for x in toc_pages if len(x) > 1 and len(x) < 4 and int(x) < len(pdf)])))


def interrupted_line(line):
    if line[-1] == ' ' or\
       line[-1] == '/':
        return True
    return False


def fix_lines(lines):
    fixed_lines = []
    for i, line in enumerate(lines):
        if not line:
            continue
        if i > 0 and (lines[i-1].endswith('\xad') or lines[i-1].endswith('-')):
            fixed_lines[-1] = fixed_lines[-1][:-1] + line
        elif len(fixed_lines) > 0 and interrupted_line(fixed_lines[-1]):
            fixed_lines[-1] += line
        elif len(fixed_lines) > 0 and fixed_lines[-1][-1].isalpha() and line[0].isalpha():
            fixed_lines[-1] += ' ' + line
        else:
            fixed_lines.append(line)
        fixed_lines[-1] = fixed_lines[-1].replace('\xad', '')
    return fixed_lines


pdf_cache = {}
def book_tests(find_func, test_key):
    global pdf_cache
    for book in book_list:
        if not cfg.get(book) or not cfg[book].get(test_key):
            print(f'[WARNING] Missing config for {book} ({test_key} test)')
            continue
        if pdf_cache.get(book):
            pdf = pdf_cache[book]
            # print('[DEBUG] Using pdf book cache')
        else:
            pdf = pymupdf.open(f'{DATA_DIR}/{book}')
            pdf_cache[book] = pdf
        try:
            assert(find_func(pdf) == cfg[book][test_key])
        except AssertionError:
            print(f'[ERROR] Error for {book} ({test_key})')

def chapter_tests():
    book_tests(find_chapter, 'chapters')

def toc_tests():
    book_tests(find_toc, 'sections')
