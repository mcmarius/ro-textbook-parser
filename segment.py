import os
import re

import pymupdf

from config import cfg

MIN_TOC_PAGE = 3
MAX_TOC_PAGE = 10
MIN_SEC_PER_PAGE = 15

DATA_DIR = 'data'
book_list = [book for book in os.listdir(DATA_DIR) if book.endswith('.pdf')]



#pdf01 = pymupdf.open('data/Manual_Cls 8_Lb Ro_3_Corint.pdf')
#pdf02 = pymupdf.open('data/Manual_Cls 8_Lb Ro_1_ArtKlett.pdf')
#pdf03 = pymupdf.open('data/Manual_Cls 8_Lb Ro_2_Artemis.pdf')
#pdf04 = pymupdf.open('data/Manual_Cls 6_Lb Ro_1_EDP.pdf')
#pdf05 = pymupdf.open('data/Manual_Cls 6_Lb Ro_3_Litera.pdf')
#pdf06 = pymupdf.open('data/Manual_Cls 6_Lb Ro_4_CD Press.pdf')
#pdf07 = pymupdf.open('data/Manual_Cls 6_Lb Ro_5_Booklet.pdf')
#pdf08 = pymupdf.open('data/Manual_Cls 6_Lb Ro_7_Paralela 45.pdf')
#pdf09 = pymupdf.open('data/Manual_Cls 6_Lb Ro_8_Intuitext.pdf')
#pdf10 = pymupdf.open('data/Manual_Cls 6_Lb Ro_6_Corint.pdf')
#pdf11 = pymupdf.open('data/Manual_Cls 6_Lb Ro_2_ArtKlett.pdf')
#pdf12 = pymupdf.open('data/Manual_Cls 7_Lb Ro_1_Booklet.pdf')
#pdf13 = pymupdf.open('data/Manual_Cls 7_Lb Ro_2_ArtKlett.pdf')
#pdf14 = pymupdf.open('data/Manual_Cls 7_Lb Ro_3_EDP.pdf')
#pdf15 = pymupdf.open('data/Manual_Cls 7_Lb Ro_4_Litera.pdf')
#pdf16 = pymupdf.open('data/Manual_Cls 7_Lb Ro_5_Intuitext.pdf')
#pdf17 = pymupdf.open('data/Manual_Cls 7_Lb Ro_6_CDPress.pdf')
#pdf18 = pymupdf.open('data/Manual_Cls 7_Lb Ro_7_Paralela45.pdf')
# page_lines = pdf.get_page_text(11).split('\n')

#SORT_NEEDS = {
#    pdf01.name: False, pdf02.name: False, pdf03.name: False,
#    pdf04.name: False, pdf05.name:  True, pdf06.name: False,
#    pdf07.name:  True, pdf08.name: False, pdf09.name: False,
#    pdf10.name: False, pdf11.name: False, pdf12.name: True,
#    pdf13.name: False, pdf14.name: False
#}
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
    # assert(find_chapter(pdf01) == [16, 44, 78, 112, 150, 184])
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
    return
    assert(find_chapter(pdf02) == [1, 10, 50, 92, 126, 158])
    assert(find_chapter(pdf03) == [18, 38, 70, 96, 122, 152])
    assert(find_chapter(pdf04) == [13, 39, 63, 97, 137, 169])
    assert(find_chapter(pdf05) == [11, 51, 83, 113, 141, 167])
    assert(find_chapter(pdf06) == [20, 52, 84, 112, 154])
    assert(find_chapter(pdf07) == [11, 57, 103, 143, 179])
    assert(find_chapter(pdf08) == [13, 49, 93, 127, 159, 185])
    assert(find_chapter(pdf09) == [14, 45, 66, 108, 146, 181, 213])  # good enough
    assert(find_chapter(pdf10) == [12, 48, 88, 131, 164, 192])
    assert(find_chapter(pdf11) == [10, 44, 84, 122, 154])
    assert(find_chapter(pdf12) == [11, 55, 95, 131, 171])
    assert(find_chapter(pdf13) == [10, 48, 88, 124, 166])
    assert(find_chapter(pdf14) == [12, 44, 76, 110, 140, 172])
    assert(find_chapter(pdf15) == [11, 59, 95, 125, 165, 197])
    assert(find_chapter(pdf16) == [8, 16, 60, 90, 132, 162, 204])
    assert(find_chapter(pdf17) == [16, 59, 96, 126, 162])
    assert(find_chapter(pdf18) == [1, 15, 55, 91, 119, 165, 191])

def toc_tests():
    book_tests(find_toc, 'sections')
    return
    assert(find_toc(pdf01) == [14, 16, 22, 24, 27, 29, 31, 34, 35, 36, 37, 38, 39, 41, 42, 44, 53, 55, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78, 80, 81, 83, 84, 86, 89, 92, 94, 96, 97, 99, 101, 103, 105, 106, 108, 110, 112, 117, 118, 120, 124, 127, 128, 130, 133, 136, 138, 139, 141, 142, 143, 144, 146, 148, 150, 156, 157, 161, 163, 165, 168, 169, 172, 173, 176, 177, 180, 182, 184, 189, 195, 197, 199, 201, 203, 205, 207, 209, 211, 214, 218, 220, 221, 224])
    assert(find_toc(pdf02) == [10, 15, 17, 20, 22, 23, 25, 26, 28, 31, 34, 36, 38, 40, 42, 44, 48, 50, 56, 58, 61, 63, 66, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86, 90, 92, 94, 95, 96, 98, 100, 101, 103, 104, 105, 107, 109, 111, 113, 115, 118, 120, 124, 126, 130, 132, 134, 136, 138, 140, 141, 143, 144, 146, 147, 149, 150, 152, 156, 158, 164, 166, 168, 170, 172, 174, 176, 179, 181, 182, 184, 185, 187, 188, 190, 191, 193, 194, 196, 198, 200, 204, 205, 207])
    assert(find_toc(pdf03) == [13, 18, 19, 21, 22, 23, 27, 29, 31, 33, 35, 38, 39, 48, 49, 54, 57, 59, 61, 63, 66, 70, 71, 72, 77, 79, 81, 85, 87, 91, 92, 96, 97, 101, 102, 104, 107, 109, 112, 114, 117, 119, 122, 124, 128, 129, 131, 133, 136, 139, 144, 148, 152, 154, 161, 163, 166, 170, 175, 177, 181, 184, 187, 189, 190, 192])
    assert(find_toc(pdf04) == [11, 13, 14, 16, 22, 24, 26, 30, 33, 35, 37, 39, 40, 42, 44, 46, 49, 51, 54, 57, 60, 62, 63, 64, 66, 69, 71, 73, 76, 80, 83, 84, 88, 93, 95, 97, 98, 100, 106, 108, 110, 112, 116, 117, 119, 123, 128, 131, 135, 137, 138, 140, 144, 149, 152, 157, 158, 161, 164, 167, 169, 170, 172, 178, 181, 184, 186, 188, 189, 191, 192, 193, 196, 200, 202, 205, 207])
    assert(find_toc(pdf05) == [11, 12, 15, 16, 18, 21, 24, 26, 28, 31, 34, 35, 37, 39, 40, 45, 47, 49, 51, 52, 55, 57, 58, 60, 63, 65, 66, 68, 70, 71, 73, 75, 78, 80, 82, 83, 84, 85, 86, 87, 88, 90, 91, 93, 94, 95, 96, 99, 100, 103, 104, 106, 108, 109, 110, 112, 113, 114, 115, 116, 118, 120, 121, 123, 125, 127, 128, 130, 133, 135, 137, 139, 140, 141, 142, 144, 145, 146, 149, 151, 152, 154, 157, 160, 162, 164, 166, 167, 168, 169, 171, 173, 175, 178, 180, 182, 184, 185, 190, 192])
    assert(find_toc(pdf06) == [14, 20, 22, 24, 26, 27, 30, 32, 40, 44, 52, 54, 56, 58, 60, 62, 64, 68, 76, 80, 84, 88, 90, 92, 93, 95, 96, 98, 100, 102, 106, 112, 114, 116, 118, 122, 124, 126, 128, 131, 133, 136, 139, 140, 144, 154, 156, 158, 160, 162, 168, 169, 171, 176, 178, 180, 184, 188])
    assert(find_toc(pdf07) == [11, 12, 24, 28, 33, 35, 38, 40, 43, 46, 49, 53, 55, 57, 58, 70, 74, 77, 83, 86, 89, 91, 93, 96, 98, 101, 103, 104, 110, 113, 117, 119, 123, 124, 126, 127, 131, 133, 136, 138, 141, 143, 144, 156, 160, 162, 167, 169, 171, 174, 176, 178, 179, 180, 187, 192, 195, 199, 203, 205, 210, 212, 214, 216, 219, 220, 221, 222, 223, 224])
    assert(find_toc(pdf08) == [13, 14, 17, 18, 21, 29, 31, 34, 36, 38, 40, 41, 42, 43, 46, 47, 48, 49, 50, 53, 54, 57, 64, 67, 69, 71, 73, 75, 77, 81, 85, 88, 90, 91, 92, 93, 94, 97, 98, 100, 108, 111, 117, 119, 121, 124, 125, 126, 127, 128, 131, 132, 134, 135, 136, 144, 147, 149, 151, 154, 155, 156, 157, 158, 159, 160, 163, 167, 169, 173, 177, 180, 181, 183, 184, 185, 186, 190, 192, 198, 201, 204, 206, 207, 208, 210, 211, 212, 215])
    assert(find_toc(pdf09) == [10, 11, 13, 14, 19, 21, 24, 26, 28, 29, 31, 33, 35, 37, 38, 39, 40, 43, 45, 46, 49, 51, 53, 55, 56, 58, 59, 60, 61, 64, 66, 67, 70, 74, 76, 78, 81, 83, 88, 90, 92, 93, 94, 97, 99, 100, 105, 107, 108, 116, 118, 119, 121, 123, 126, 128, 131, 133, 134, 136, 137, 139, 143, 145, 146, 149, 151, 153, 155, 158, 162, 164, 166, 168, 171, 173, 175, 176, 179, 181, 182, 186, 188, 189, 191, 194, 195, 196, 198, 200, 201, 202, 204, 206, 207, 210, 212, 213, 215, 218, 220, 221, 223])
    assert(find_toc(pdf10) == [12, 13, 16, 18, 19, 20, 22, 26, 28, 31, 41, 42, 46, 48, 49, 53, 54, 56, 58, 61, 63, 66, 83, 84, 86, 88, 89, 92, 94, 96, 98, 100, 103, 105, 107, 110, 126, 127, 130, 131, 133, 134, 136, 137, 139, 141, 142, 144, 146, 148, 150, 158, 160, 162, 164, 165, 168, 171, 173, 175, 177, 179, 181, 187, 188, 190, 192, 194, 198, 200, 202, 203, 205, 208, 213, 215, 218, 219, 221, 222])
    assert(find_toc(pdf11) == [10, 13, 14, 16, 17, 19, 20, 21, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 47, 49, 52, 54, 56, 58, 60, 62, 64, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86, 88, 91, 92, 95, 96, 98, 100, 102, 105, 106, 109, 112, 113, 115, 116, 118, 120, 122, 124, 126, 128, 129, 132, 134, 136, 140, 142, 144, 146, 148, 150, 152, 154, 158, 160, 162, 164, 166, 168, 170, 172, 175, 176, 178, 180, 182, 184, 186, 188, 190, 192])
    assert(find_toc(pdf12) == [11, 12, 16, 18, 20, 22, 24, 27, 29, 30, 32, 34, 37, 40, 42, 44, 46, 48, 50, 52, 54, 55, 56, 62, 64, 65, 67, 68, 69, 70, 73, 75, 77, 79, 83, 86, 88, 90, 92, 94, 95, 96, 99, 100, 102, 103, 105, 106, 108, 110, 112, 116, 118, 121, 123, 125, 128, 130, 131, 132, 137, 138, 139, 144, 145, 148, 149, 151, 153, 155, 157, 159, 161, 163, 164, 166, 167, 168, 170, 171, 172, 178, 180, 182, 183, 187, 189, 191, 192, 193, 194, 196, 197, 200, 202, 204, 205, 207, 208, 211, 212])
    assert(find_toc(pdf13) == [10, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 37, 38, 39, 40, 42, 44, 46, 48, 53, 55, 57, 59, 60, 62, 63, 65, 67, 70, 74, 76, 78, 81, 82, 84, 86, 88, 90, 92, 93, 94, 97, 99, 100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 119, 120, 122, 124, 130, 132, 135, 136, 140, 142, 144, 145, 146, 148, 150, 152, 153, 154, 156, 157, 158, 160, 162, 164, 166, 172, 173, 175, 177, 178, 181, 183, 184, 186, 188, 190, 192, 194, 196, 198])
    assert(find_toc(pdf14) == [12, 14, 16, 17, 22, 23, 24, 25, 26, 27, 31, 32, 33, 34, 35, 36, 38, 42, 44, 46, 48, 49, 56, 58, 59, 61, 62, 63, 65, 66, 67, 72, 74, 76, 77, 78, 79, 84, 86, 87, 88, 90, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 107, 108, 110, 112, 114, 115, 117, 118, 119, 120, 121, 122, 123, 125, 127, 128, 130, 131, 132, 133, 134, 135, 136, 138, 140, 144, 145, 148, 149, 150, 153, 154, 155, 156, 160, 161, 162, 164, 165, 166, 168, 170, 172, 174, 176, 177, 181, 182, 183, 184, 185, 187, 188, 189, 190, 191, 192, 193, 196, 197])
    assert(find_toc(pdf15) == [11, 12, 17, 18, 20, 23, 24, 26, 30, 32, 33, 35, 37, 39, 40, 42, 43, 45, 47, 48, 49, 50, 51, 53, 55, 57, 59, 60, 64, 66, 67, 69, 72, 76, 77, 78, 79, 80, 82, 83, 85, 87, 89, 90, 92, 94, 95, 96, 99, 101, 103, 104, 107, 108, 109, 111, 113, 114, 115, 118, 119, 122, 123, 124, 125, 126, 130, 131, 132, 134, 135, 136, 139, 141, 142, 144, 146, 148, 150, 152, 153, 154, 155, 157, 158, 159, 161, 162, 164, 165, 166, 170, 172, 173, 177, 179, 181, 183, 185, 187, 188, 190, 191, 192, 193, 194, 196, 197, 198, 206, 207, 209, 211, 213, 217, 218, 220, 221, 222, 223])
    assert(find_toc(pdf16) == [10, 16, 20, 22, 24, 25, 27, 28, 29, 30, 32, 33, 34, 35, 36, 37, 38, 40, 44, 46, 47, 48, 51, 53, 54, 55, 58, 60, 64, 66, 67, 69, 71, 73, 75, 79, 81, 82, 85, 88, 90, 95, 97, 99, 101, 102, 105, 106, 108, 110, 112, 115, 117, 119, 122, 124, 125, 126, 130, 132, 133, 134, 136, 139, 141, 144, 147, 148, 150, 152, 154, 156, 158, 160, 162, 164, 167, 170, 172, 174, 175, 177, 179, 181, 183, 185, 187, 190, 191, 192, 194, 195, 196, 199, 202, 204, 209, 211])
    assert(find_toc(pdf17) == [13, 16, 22, 28, 33, 43, 47, 51, 54, 55, 59, 66, 70, 72, 80, 84, 86, 91, 92, 96, 101, 105, 107, 111, 114, 117, 122, 123, 126, 130, 136, 138, 142, 148, 152, 156, 158, 159, 162, 166, 169, 170, 172, 180, 182, 184, 186, 187, 188, 189])
    #assert(find_toc(pdf18) == [])
