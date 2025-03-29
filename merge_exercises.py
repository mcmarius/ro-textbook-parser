# import codecs
# import concurrent.futures
import json
import math
import os
import re

import pylcs
# import tqdm
import tqdm.contrib.concurrent
import xlsxwriter

from config import cfg, gemini2cfg
from extract_verbs import read_file


GEMINI_PATH = 'exercises_gemini/json'


def fix_diacritics(text):
    return text.replace('ş', 'ș').replace('Ş', 'Ș').replace('ţ', 'ț').replace('Ţ', 'Ț')


def fix_exercise_diacritics(exercise):
    questions = exercise["questions_list"]
    new_questions = []
    if exercise.get("section_name"):
        exercise["section_name"] = fix_diacritics(exercise["section_name"])
    for question in questions:
        new_question = question
        new_question["text"] = fix_diacritics(question["text"])
        # new_question["text"] = bytes(question["text"]).decode('unicode-escape') # codecs.decode(question["text"], 'unicode-escape')
        new_questions.append(new_question)
    exercise["questions_list"] = new_questions
    return exercise

def merge_gemini_exercises():
    base_path = "Extracted_Gemini_AI"
    for publisher in os.listdir(base_path):
        for klass in os.listdir(f"{base_path}/{publisher}"):
            if not os.path.isdir(f"{base_path}/{publisher}/{klass}"):
                continue
            all_exercises = []
            for page in sorted(os.listdir(f"{base_path}/{publisher}/{klass}"), key=lambda x: int(x.split('_')[-1].strip('.json'))):
                with open(f"{base_path}/{publisher}/{klass}/{page}") as json_file:
                    print(f"processing {base_path}/{publisher}/{klass}/{page}")
                    all_exercises += json.load(json_file)["exercises"]
            chapters = cfg[gemini2cfg[klass]]['chapters']
            if cfg[gemini2cfg[klass]]['sections']:
                chapters.append(cfg[gemini2cfg[klass]]['sections'][-1])
            else:
                chapters.append(999)
            i = 0
            for chapter in chapters[:-1]:
                chapter_end = chapters[i + 1]
                chapter_exercises = [fix_exercise_diacritics(exercise) for exercise in all_exercises if chapter <= exercise["page_number"] < chapter_end]
                texts = [q["text"] for exercise in chapter_exercises for q in exercise["questions_list"]]
                current_chapter = chapter
                i += 1
                with open(f"exercises_gemini/txt/{gemini2cfg[klass].strip('.pdf')}-{i}.txt", "w", encoding="utf-8") as text_file:
                    text_file.write('\n'.join(texts))
                with open(f"exercises_gemini/json/{klass}-{i}.json", "w", encoding="utf-8") as json_file:
                    json.dump(chapter_exercises, json_file, indent=2, ensure_ascii=False)


def deduplicate_exercises():
    exercises_path = 'exercises'
    total = 0
    remaining = 0
    total_gemini = 0
    remaining_gemini = 0
    exercise_files = os.listdir(GEMINI_PATH)
    result = tqdm.contrib.concurrent.process_map(deduplicate_exercise, exercise_files, max_workers=16)
    for rem, totalp, len_gemini, rem_gemini in result:
        remaining += rem
        total += totalp
        total_gemini += len_gemini
        remaining_gemini += rem_gemini
    print(f"{remaining} remaining out of {total}\ngemini: {remaining_gemini} / {total_gemini}")

def deduplicate_exercise(exercise_file):
    exercises_gemini = []
    exercises_path = 'exercises'
    with open(f"{GEMINI_PATH}/{exercise_file}") as json_file:
        exercises_gemini = json.load(json_file)
    book, chapter = re.findall('(.+)(-\d)', exercise_file)[0]
    chapter_exercise_file = gemini2cfg[book].strip('.pdf') + chapter + '.txt'
    exercises = [fix_diacritics(e) for e in read_file(f"{exercises_path}/{chapter_exercise_file}")]
    all_page_exercises = []
    # search for exercises as substring in gemini exercises
    common_exercises = []
    for page in exercises_gemini:
        page_exercises = [q['text'] for q in page['questions_list']]
        all_page_exercises += page_exercises
        for e1 in page_exercises:
            common_exercises += [exercise for exercise in exercises if exercise in e1]
    # total_gemini += len(all_page_exercises)
    totalp = len(exercises)
    exercises = [exercise for exercise in exercises if exercise not in common_exercises]

    # search for gemini exercises as substring in ours - no such overlaps
    # common_exercises = []
    # for e2 in exercises:
    #     common_exercises += [exercise for exercise in all_page_exercises if exercise in e2]
    # exercises = [exercise for exercise in exercises if exercise not in common_exercises]

    # search for common substring
    common_exercises = []
    common_exercises_gemini = []
    for e1 in all_page_exercises:
        lengths = pylcs.lcs2_of_list(e1, exercises)
        for i, length in enumerate(lengths):
            if length > min(30, min(len(e1), len(exercises[i])) / 2):
                common_exercises.append(exercises[i])
                common_exercises_gemini.append(e1)
    exercises = [exercise for exercise in exercises if exercise not in common_exercises]
    remaining_gemini = [exercise for exercise in all_page_exercises if exercise not in common_exercises_gemini]
    # if exercises and len(exercises) != totalp:
    #     print(f"{len(exercises)} remaining out of {totalp}")
    #     # remaining += len(exercises)
    #     # total += totalp

    # remove quoted text (??)
    if exercises:
        with open(f"exercises/remaining/{chapter_exercise_file}", "w") as f:
            f.write('\n'.join(exercises))
    return len(exercises), totalp, len(all_page_exercises), len(remaining_gemini)


def remove_quotes(texts):
    start_quotes = ['\'', '\"', '„']
    end_quotes = ['\'', '\"', '“']
    regexes = []
    for start_quote in start_quotes:
        for end_quote in end_quotes:
            regexes.append('(' + start_quote + '.+?' + end_quote + ')')
    processed_texts = []
    for text in texts:
        new_text = text
        for regex in regexes:
            new_text = re.sub(regex, '', new_text)
        processed_texts.append(new_text)
    return processed_texts


def write_examples_to_excel(file_name, rows):
    workbook = xlsxwriter.Workbook(file_name)
    worksheet = workbook.add_worksheet()
    cell_format = workbook.add_format({'text_wrap': True, 'font_name': 'Arial', 'font_size': 10})
    cell_format.set_text_wrap()
    worksheet.set_column_pixels('B:B', 100, cell_format)
    worksheet.set_column_pixels('C:C', 70, cell_format)
    worksheet.set_column_pixels('D:D', 70, cell_format)
    worksheet.set_column_pixels('E:E', 100, cell_format)
    worksheet.set_column_pixels('F:F', 1600, cell_format)
    # header row
    worksheet.set_row_pixels(0, 50)
    worksheet.write_row(
        'A1',
        data=['id', 'publisher', 'class', 'chapter', 'bloom_label', 'exercise'],
        cell_format=cell_format
    )
    worksheet.freeze_panes(1, 0)
    for i, exercise in enumerate(rows):
        worksheet.set_row_pixels(i + 1, min(400, max(30, 20 * (exercise[4].count('\n')))))
        worksheet.write_row(f"A{i + 2}", data=[i+1] + exercise, cell_format=cell_format)
    workbook.close()


def merge_exercises():
    all_exercises = []
    for exercise_file in os.listdir(GEMINI_PATH):
        exercises_gemini = []
        book, chapter = re.findall('(.+)-(\d)', exercise_file)[0]
        publisher, klass, _ = book.split('_')
        with open(f"{GEMINI_PATH}/{exercise_file}") as json_file:
            exercises_gemini = json.load(json_file)
        for page in exercises_gemini:
            texts = [q['text'] for q in page['questions_list']]
            processed_texts = remove_quotes(texts)
            all_exercises += [[publisher, klass, chapter, None, text] for text in processed_texts]
        chapter_exercise_file = gemini2cfg[book].strip('.pdf') + '-' + chapter + '.txt'
        remaining_exercises = []
        try:
            remaining_exercises = read_file(f"exercises/remaining/{chapter_exercise_file}")
        except FileNotFoundError:
            print(f"skipping {chapter_exercise_file}")
        processed_texts = remove_quotes(remaining_exercises)
        all_exercises += [[publisher, klass, chapter, None, exercise] for exercise in processed_texts]
    # all_exercises += read_file('exercises/misc/all_remaining_exercises.txt')
    all_exercises = sorted(all_exercises, key=lambda x: (x[1], x[0], x[2]))
    write_examples_to_excel('all_exercises_merged.xlsx', all_exercises)


if __name__ == "__main__":
    # merge_gemini_exercises()
    # deduplicate_exercises()
    merge_exercises()
