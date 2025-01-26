import re
import string

import pymupdf

from copy import deepcopy

from constants import *
from segment import fix_file_lines


# pdf = pymupdf.open(DATA_DIR + BOOK_LIST[0])

def valid_exercise(line):
    if 'MANUAL' in line:
        return False
    return len(line) > 1 and (\
        (line[1].isspace() or line[1] in string.punctuation or line[1].isdigit()) and line[2].isspace())

def valid_span(match_line, line):
    start = line.find(match_line)
    if 4 < line[start:].find('.') < 20:
        return False
    if start == 0:
        return True
    if (line[start].isdigit() or line[start].isalpha()) and not (line[start - 1].isalpha() or line[start - 1] in string.punctuation):
        return True
    return False

def exercises_by_chapter(pdf):
    file_name = pdf.name.strip(DATA_DIR)
    chapters = deepcopy(cfg[file_name]['chapters'])
    # assume the limit for the last chapter is the last section
    chapters.append(cfg[file_name]['sections'][-1])
    regex = '(?:\d{1,2}\.?|[a-p]\.?)(?:\t| ){1,3}\w+.+[^\n]'
    if 'ArtKlett' in file_name:
        regex = '(?:\d{1,2}|[a-p])\t ?\w+.+[^\n]'
    elif 'Artemis' in file_name:
        regex = '(?:\d{1,2}\.?|[a-p]\.?)(?:\t| ){1,3}(?:„|…| )*\w+.+[^\n]'
    # print(f'[DEBUG] chapters: {chapters}')
    for i, chapter in enumerate(chapters[:-1]):
        exercises = []
        chapter_start = chapter
        chapter_end = chapters[i + 1]
        for page in range(chapter_start, chapter_end):
            raw_lines = fix_file_lines(pdf, page).split('\n')
            for j, line in enumerate(raw_lines):
                if '\x07' in line:
                    print(line)
                matching_lines = re.findall(regex, line)
                # remove false positives
                # remove short matches (dictionary definitions)
                # TODO (??): add extra newline between each non-consecutive exercises
                matching_lines = [match_line.strip() for match_line in matching_lines if valid_exercise(match_line) and valid_span(match_line, line)]
                exercises += matching_lines
        with open(f"exercises/{file_name.strip('.pdf')}-{i+1}.txt", 'w') as f:
            f.write('\n'.join(exercises))
