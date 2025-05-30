import os
import re

import pymupdf

from config import cfg
from constants import *

def safe_int(nr):
    try:
        return int(nr)
    except ValueError:
        return None


def is_toc_page(pdf_page, min_sec):
    return len([x for x in re.split('(\d{1,}[^\.][– ]?[\d]?)\n', pdf_page) if x and x[0].isdigit()]) >= min_sec and pdf_page.count(';') < 20 and 'Varianta tipărită' not in pdf_page and 'TIPĂRIT' not in pdf_page


def unit_offset(line):
    kws = ['UNITATEA ', 'Unitatea ', 'CAPITOLUL ']
    for kw in kws:
        if kw in line:
            return line.find(kw)
    return 0


def find_chapter(pdf):
    chapter_pages = []
    min_sec = cfg[pdf.name.strip(DATA_DIR)].get('min_sec', MIN_SEC_PER_PAGE)
    for i in range(MIN_TOC_PAGE, MAX_TOC_PAGE):
        if is_toc_page(pdf.get_page_text(i), min_sec):
            fixed_lines = fix_lines(pdf.get_page_text(i, sort=SORT_CHAPTER_NEEDS.get(pdf.name, False)).split('\n'))
            to_skip = 0
            # print(fixed_lines)
            for i, line in enumerate(fixed_lines):
                if 'UNITATEA' in line or 'Unitatea' in line or 'CAPITOLUL' in line or (re.findall('[2-8]\t', line) and re.findall('([2-8]\t)', line)[0][:-1] == line.split('\t')[0]):
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
                        line_lim = 22 + unit_offset(line)
                    else:
                        line_lim = 11 + unit_offset(line)
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
                            if not possible_page:
                                possible_page = re.findall('^(\d{2,}) (?:L\d{1,2}|\t)', fixed_lines[j])
                            # print(f"possible: {possible_page}")
                            if possible_page:
                                chapter_pages.append(possible_page[0])
                                to_skip = j
                                break
    return sorted(list({int(x) for x in chapter_pages}))


def get_toc_pages(lines):
    pages = []
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
        elif '...' in line:
            sep = '...'
        elif '/' in line:
            sep = '/'
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
    min_sec = cfg[pdf.name.strip(DATA_DIR)].get('min_sec', MIN_SEC_PER_PAGE)
    for i in range(MIN_TOC_PAGE, MAX_TOC_PAGE):
        if is_toc_page(pdf.get_page_text(i), min_sec):
            # print(f'{i} is toc page')
            toc_page_list = get_toc_pages(pdf.get_page_text(i, sort=SORT_NEEDS.get(pdf.name, False)))
            # fixed_lines = fix_lines(pdf.get_page_text(i).split('\n'))
            # toc_page_list = get_toc_pages(fixed_lines) # get_toc_pages(pdf.get_page_text(i))
            if len(toc_page_list) >= min_sec:
                toc_pages += toc_page_list
    return sorted(list(set([int(x) for x in toc_pages if len(x) > 1 and len(x) < 4 and int(x) < len(pdf)])))


def interrupted_line(line):
    #if line == '':
    #    return False
    # print(f'line is {type(line)}')
    if not line:
        return False
    if line[-1] == ' ' or\
       line[-1] == '/':
        return True
    return False


def fix_lines(lines):
    fixed_lines = []
    for i, line in enumerate(lines):
        if not line:
            continue
        #print(f'line: {fixed_lines}')
        if i > 0 and (lines[i-1].endswith('\xad') or lines[i-1].endswith('-')):
            fixed_lines[-1] = fixed_lines[-1].strip('-') + line
        elif len(fixed_lines) > 0 and interrupted_line(fixed_lines[-1]):
            fixed_lines[-1] += line
        elif len(fixed_lines) > 0 and fixed_lines[-1][-1].isalpha() and (line[0].isalpha() or line[0].isspace()):
            fixed_lines[-1] += ' ' + line
        else:
            fixed_lines.append(line)
        fixed_lines[-1] = re.sub(' {4,}', ' ', fixed_lines[-1])
        fixed_lines[-1] = fixed_lines[-1].replace('\xad', '').replace('\x07', '')
        if fixed_lines[-1] == '':
            fixed_lines.pop()
    return fixed_lines


def fix_file_lines(pdf, page):
    return fix_lines(pdf.get_page_text(page, sort=SORT_EXTRACT_NEEDS.get(pdf.name, False)).split('\n'))


def join_fix_file_lines(pdf, page):
    return '\n'.join(fix_file_lines(pdf, page))


pdf_cache = {}
def book_tests(find_func, test_key):
    global pdf_cache
    for book in BOOK_LIST:
        if not cfg.get(book) or not cfg[book].get(test_key):
            print(f'[WARNING] Missing config for {book} ({test_key} test)')
            continue
        if pdf_cache.get(book):
            pdf = pdf_cache[book]
            # print('[DEBUG] Using pdf book cache')
        else:
            pdf = pymupdf.open(os.path.join(DATA_DIR, book))
            pdf_cache[book] = pdf
        try:
            elems = find_func(pdf)
            #print(len(elems))
            #print(f'book {book}')
            assert(elems == cfg[book][test_key])
        except AssertionError:
            print(f'[ERROR] Error for {book} ({test_key})')
            # print(f'expected {cfg[book][test_key]}')
            # print(f'got {elems}')
            print(f'missing: {[x for x in cfg[book][test_key] if x not in elems]}')
            print(f'extra: {[x for x in elems if x not in cfg[book][test_key]]}')

def chapter_tests():
    book_tests(find_chapter, 'chapters')

def toc_tests():
    book_tests(find_toc, 'sections')
