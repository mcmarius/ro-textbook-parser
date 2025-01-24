import re

import pymupdf

MIN_TOC_PAGE = 3
MAX_TOC_PAGE = 10

pdf1 = pymupdf.open('data/Manual_Cls 8_Lb Ro_3_Corint.pdf')
pdf2 = pymupdf.open('data/Manual_Cls 8_Lb Ro_1_ArtKlett.pdf')
pdf3 = pymupdf.open('data/Manual_Cls 8_Lb Ro_2_Artemis.pdf')
pdf4 = pymupdf.open('data/Manual_Cls 6_Lb Ro_1_EDP.pdf')
pdf5 = pymupdf.open('data/Manual_Cls 6_Lb Ro_3_Litera.pdf')
pdf6 = pymupdf.open('data/Manual_Cls 6_Lb Ro_4_CD Press.pdf')
pdf7 = pymupdf.open('data/Manual_Cls 6_Lb Ro_5_Booklet.pdf')
# page_lines = pdf.get_page_text(11).split('\n')


def is_toc_page(pdf_page):
    return len([x for x in re.split('(\d{1,}[^\.][– ]?[\d]?)\n', pdf_page) if x and x[0].isdigit()]) > 20


def find_chapter(pdf):
    chapter_pages = []
    for i in range(MIN_TOC_PAGE, MAX_TOC_PAGE):
        if is_toc_page(pdf.get_page_text(i)):
            fixed_lines = fix_lines(pdf.get_page_text(i).split('\n'))
            to_skip = 0
            for i, line in enumerate(fixed_lines):
                if 'UNITATEA' in line or 'Unitatea' in line:
                    # print(f'got {i} -> {line}')
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
                    # page_in_line = line.rsplit(sep, 1)[1].strip()
                    candidates = re.findall(f'{sep}\s*(\d+)', line[22:])
                    if len(candidates) >= 1:
                        page_in_line = candidates[0].strip()
                        if page_in_line[0].isdigit():
                            # print(f'sep {sep}, pg {page_in_line}')
                            chapter_pages.append(page_in_line)
                    else:
                        # skip the pages for the previous found chapter
                        if i < to_skip:
                            continue
                        # we need to find the first section of this chapter
                        for j in range(i + 1, len(fixed_lines)):
                            possible_page = re.findall('\d{2,}$', fixed_lines[j])
                            if possible_page:
                                chapter_pages.append(possible_page[0])
                                to_skip = j
                                break
    return sorted([int(x) for x in chapter_pages])


def get_toc_pages(lines):
    pages = []
    # / pages
    # pages = [line for line in lines.split('  ') if line and '/' in line]
    page_lines = [line.strip() for line in lines.split('    ') if line and ('/' in line or '...' in line or '. .' in line or ' .   .' in line or ' .  .' in line or ' – ' in line)]
    page_lines = [small_line for line in page_lines for small_line in line.split('\n') if small_line]
    if len(page_lines) < 10:  # only whitespace is the separator; fortunately, no numbers in titles
        return [num for line in lines.split('\n') for num in re.findall('(\d{2,})', line)]
    # print(page_lines)
    for line in page_lines:
        sep = '..'
        if ' .   .' in line:
            sep = ' .   .'
        elif ' .  .' in line:
            sep = ' .  .'
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
                pages.append(''.join(x for x in page_in_line if x.isdigit()))
    # print(page_lines)
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
            toc_page_list = get_toc_pages(pdf.get_page_text(i, sort=True))
            # fixed_lines = fix_lines(pdf.get_page_text(i).split('\n'))
            # toc_page_list = get_toc_pages(fixed_lines) # get_toc_pages(pdf.get_page_text(i))
            if len(toc_page_list) > 20:
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


def chapter_tests():
    assert(find_chapter(pdf1) == [16, 44, 78, 112, 150, 184])
    assert(find_chapter(pdf2) == [10, 50, 92, 126, 158])
    assert(find_chapter(pdf3) == [18, 38, 70, 96, 122, 152])
    assert(find_chapter(pdf4) == [13, 39, 63, 97, 137, 169])
    assert(find_chapter(pdf5) == [11, 51, 83, 113, 141, 167])
    assert(find_chapter(pdf6) == [20, 52, 84, 112, 154])
    assert(find_chapter(pdf7) == [11, 57, 103, 143, 179])

def toc_tests():
    assert(find_toc(pdf1) == [14, 16, 22, 24, 27, 29, 31, 34, 35, 36, 37, 38, 39, 41, 42, 44, 53, 55, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78, 80, 81, 83, 84, 86, 89, 92, 94, 96, 97, 99, 101, 103, 105, 106, 108, 110, 112, 117, 118, 120, 124, 127, 128, 130, 133, 136, 138, 139, 141, 142, 143, 144, 146, 148, 150, 156, 157, 161, 163, 165, 168, 169, 172, 173, 176, 177, 180, 182, 184, 189, 195, 197, 199, 201, 203, 205, 207, 209, 211, 214, 218, 220, 221, 224])
    assert(find_toc(pdf2) == [10, 15, 17, 20, 22, 23, 25, 26, 28, 31, 34, 36, 38, 40, 42, 44, 48, 50, 56, 58, 61, 63, 66, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86, 90, 92, 94, 95, 96, 98, 100, 101, 103, 104, 105, 107, 109, 111, 113, 115, 118, 120, 124, 126, 130, 132, 138, 140, 141, 143, 144, 146, 147, 149, 150, 152, 156, 158, 164, 166, 168, 170, 172, 174, 176, 179, 181, 182, 184, 185, 187, 188, 190, 191, 193, 194, 196, 198, 200, 204, 205, 207])
    assert(find_toc(pdf3) == [13, 18, 19, 21, 22, 23, 27, 29, 31, 33, 35, 38, 39, 48, 49, 54, 57, 59, 61, 63, 66, 70, 71, 72, 77, 79, 81, 85, 87, 91, 92, 96, 97, 101, 102, 104, 107, 109, 112, 114, 117, 119, 122, 124, 128, 129, 131, 133, 136, 139, 144, 148, 152, 154, 161, 163, 166, 170, 175, 177, 181, 184, 187, 189, 190, 192])
    assert(find_toc(pdf4) == [11, 13, 14, 16, 22, 24, 26, 30, 33, 35, 37, 39, 40, 42, 44, 46, 49, 51, 54, 57, 60, 62, 63, 64, 66, 69, 71, 73, 76, 80, 83, 84, 88, 93, 95, 97, 98, 100, 106, 108, 110, 112, 116, 117, 119, 123, 128, 131, 135, 137, 138, 140, 144, 149, 152, 157, 158, 161, 164, 167, 169, 170, 172, 178, 181, 184, 186, 188, 189, 191, 192, 193, 196, 200, 202, 205, 207])
    assert(find_toc(pdf5) == [11, 12, 15, 16, 18, 21, 24, 26, 28, 31, 34, 35, 37, 39, 40, 45, 47, 49, 51, 52, 55, 57, 58, 60, 63, 65, 66, 68, 70, 71, 73, 75, 78, 80, 82, 83, 84, 85, 86, 87, 88, 90, 91, 93, 94, 95, 96, 99, 100, 103, 104, 106, 108, 109, 110, 112, 113, 114, 115, 116, 118, 120, 121, 123, 125, 127, 128, 130, 133, 135, 137, 139, 140, 141, 142, 144, 145, 146, 149, 151, 152, 154, 157, 160, 162, 164, 166, 167, 168, 169, 171, 173, 175, 178, 180, 182, 184, 185, 190, 192])
    assert(find_toc(pdf6) == [14, 20, 22, 24, 26, 27, 30, 32, 40, 44, 52, 54, 56, 58, 60, 62, 64, 68, 76, 80, 84, 88, 90, 92, 93, 95, 96, 98, 100, 102, 106, 112, 114, 116, 118, 122, 124, 126, 128, 131, 133, 136, 139, 140, 144, 154, 156, 158, 160, 162, 168, 169, 171, 176, 178, 180, 184, 188])
    assert(find_toc(pdf7) == [11, 12, 24, 28, 33, 35, 38, 40, 43, 46, 49, 53, 55, 57, 58, 70, 74, 77, 83, 86, 89, 91, 93, 96, 98, 101, 103, 104, 110, 113, 117, 119, 123, 124, 126, 127, 131, 133, 136, 138, 141, 143, 144, 156, 160, 162, 167, 169, 171, 174, 176, 178, 179, 180, 187, 192, 195, 199, 203, 205, 210, 212, 214, 216, 219, 220, 221, 222, 223, 224])

