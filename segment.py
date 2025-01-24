import pymupdf

MAX_TOC_PAGE = 10

pdf = pymupdf.open('data/Manual_Cls 8_Lb Ro_3_Corint.pdf')
pdf2 = pymupdf.open('data/Manual_Cls 8_Lb Ro_1_ArtKlett.pdf')
pdf3 = pymupdf.open('data/Manual_Cls 8_Lb Ro_2_Artemis.pdf')

page_lines = pdf.get_page_text(11).split('\n')


def is_toc_page(pdf_page):
    return len([x for x in re.split('(\d{1,}[^\.][– ]?[\d]?)\n', pdf_page) if x and x[0].isdigit()]) > 20


def find_chapter(pdf):
    chapter_pages = []
    for i in range(MAX_TOC_PAGE):
        if is_toc_page(pdf.get_page_text(i)):
            fixed_lines = fix_lines(pdf.get_page_text(i).split('\n'))
            to_skip = 0
            for i, line in enumerate(fixed_lines):
                if 'UNITATEA' in line:
                    page_in_line = line.rsplit(' ', 1)[1]
                    if page_in_line[0].isdigit():
                        chapter_pages.append(page_in_line)
                    else:
                        # we need to find the first section of this chapter
                        if i < to_skip:
                            continue
                        for j in range(i + 1, len(fixed_lines)):
                            possible_page = re.findall('\d{2,}$', fixed_lines[j])
                            if possible_page:
                                chapter_pages.append(possible_page[0])
                                to_skip = j
                                break
    return [int(x) for x in chapter_pages]


def get_toc_pages(pdf_page):
    return [x for x in re.split('[^L] ?/? ?(\d{2,3})', pdf_page) if x and x[0].isdigit()]
    return [x.strip() for x in re.split('(\d{1,}[^\.,][– ]?[\d]?)\n', pdf_page) if x and x[0].isdigit()]

def find_toc(pdf):
    toc_pages = []
    for i in range(MAX_TOC_PAGE):
        toc_page_list = get_toc_pages(pdf.get_page_text(i))
        if is_toc_page(pdf.get_page_text(i)) and len(toc_page_list) > 20:
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
