import re
import string

import pymupdf

from copy import deepcopy

from constants import *
from segment import fix_file_lines


# from constants import *
# import pymupdf
# import extract

# pdf = pymupdf.open(DATA_DIR + BOOK_LIST[0])
# extract.exercises_by_chapter(pdf)

# import importlib
# importlib.reload(extract)

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
    if cfg[file_name]['sections']:
        chapters.append(cfg[file_name]['sections'][-1])
    else:
        chapters.append(pdf.page_count)
    regex = '(?:\d{1,2}\.|[a-p]\.)(?:\t| ){1,3}\w+.+[^\n]'
    sub_regex = '(?:\d{1,2}\.|[a-k]\.)(?:\t| ){1,3}\w+.+[^\n]'
    if 'ArtKlett' in file_name and 'Cls 7' not in file_name:
        regex = '(?:\d{1,2}|[a-p])\t ?\w+.+[^\n]'
        sub_regex = '(?:\d{1,2}|[a-k])\t ?\w+.+[^\n]'
    elif 'Artemis' in file_name or 'EDP' in file_name:
        regex = '(?:\d{1,2}\.?|[a-p]\.?)(?:\t| ){1,3}(?:„|…| )*\w+.+[^\n]'
        sub_regex = '(?:\d{1,2}\.?|[a-k]\.?)(?:\t| ){1,3}(?:„|…| )*\w+.+[^\n]'
    # print(f'[DEBUG] chapters: {chapters}')
    for i, chapter in enumerate(chapters[:-1]):
        exercises = []
        chapter_start = chapter
        chapter_end = chapters[i + 1]
        for page in range(chapter_start, chapter_end):
            raw_lines = fix_file_lines(pdf, page)
            for j, line in enumerate(raw_lines):
                if " puncte " in line or (" puncte" in line and len(line) < 15):
                    continue
                # if '\x07' in line:
                #     print(line)
                matching_lines = re.findall(regex, line)
                # remove false positives
                # remove short matches (dictionary definitions)
                # TODO (??): add extra newline between each non-consecutive exercises
                matching_lines = [match_line.strip() for match_line in matching_lines if valid_exercise(match_line) and valid_span(match_line, line)]
                new_lines = []
                for match_line in matching_lines:
                    current_exercise = deepcopy(match_line)
                    while valid_exercise(current_exercise) and valid_span(current_exercise, match_line):
                        start_span = match_line.find(current_exercise)
                        subexercise = re.findall(sub_regex, match_line[start_span + 5:])
                        if subexercise and valid_exercise(subexercise[0]) and valid_span(subexercise[0], match_line):
                            stop_span = current_exercise.find(subexercise[0])
                            new_lines.append(current_exercise[:stop_span].strip())
                            # print(f"subexercise found, stopping at [{new_lines[-1]}]")
                            # print(f"\tsubexercise is {subexercise[0]}")
                            current_exercise = deepcopy(subexercise[0])
                        else:
                            if not new_lines or new_lines[-1] != current_exercise.strip():
                                # print(f"<<<< no more - adding [{current_exercise}]")
                                new_lines.append(current_exercise.strip())
                            break
                #    else:
                #        new_lines.append('\n')
                # exercises += matching_lines
                exercises += new_lines
        with open(f"exercises/{file_name.strip('.pdf')}-{i+1}.txt", 'w') as f:
            f.write('\n'.join(exercises))
