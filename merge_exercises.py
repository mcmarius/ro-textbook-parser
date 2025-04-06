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
    os.makedirs('exercises_gemini/txt', exist_ok=True)
    os.makedirs('exercises_gemini/json', exist_ok=True)
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
    os.makedirs('exercises/remaining', exist_ok=True)
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
    exercises_path = 'exercises/json'
    with open(f"{GEMINI_PATH}/{exercise_file}") as json_file:
        exercises_gemini = json.load(json_file)
    book, chapter = re.findall('(.+)(-\d)', exercise_file)[0]
    chapter_exercise_file = gemini2cfg[book].strip('.pdf') + chapter + '.json'
    # exercises = [fix_diacritics(e) for e in read_file(f"{exercises_path}/{chapter_exercise_file}")]
    with open(f"{exercises_path}/{chapter_exercise_file}") as json_file:
        exercises_json = json.load(json_file)
    all_page_exercises = []
    # search for exercises as substring in gemini exercises
    common_exercises = []
    for page in exercises_gemini:
        page_exercises = [q['text'] for q in page['questions_list']]
        all_page_exercises += page_exercises
        for e1 in page_exercises:
            for exercise_group in exercises_json:
                for exercise in exercise_group['questions_list']:
                    if exercise['text'] in e1:
                        common_exercises.append(exercise['text'])
            # we use this convoluted logic to ensure we do not accidentally include an exercise that would be found somewhere else
            # common_exercises += [exercise for exercise in exercises if exercise in e1]
    # total_gemini += len(all_page_exercises)
    totalp = sum(len(exercises['questions_list']) for exercises in exercises_json)
    # exercises = [exercise for exercise in exercises if exercise not in common_exercises]
    exercises = []
    exercises_txt = []
    for exercise_group in exercises_json:
        remaining_exercises = []
        for exercise in exercise_group['questions_list']:
            if exercise['text'] not in common_exercises:
                remaining_exercises.append(exercise)
                exercises_txt.append(exercise['text'])
        if remaining_exercises:
            exercises.append({"page_number": exercise_group['page_number'], "questions_list": remaining_exercises})

    # search for gemini exercises as substring in ours - no such overlaps
    # common_exercises = []
    # for e2 in exercises:
    #     common_exercises += [exercise for exercise in all_page_exercises if exercise in e2]
    # exercises = [exercise for exercise in exercises if exercise not in common_exercises]

    # search for common substring
    common_exercises = []
    common_exercises_gemini = []
    for e1 in all_page_exercises:
        lengths = pylcs.lcs2_of_list(e1, exercises_txt)
        for i, length in enumerate(lengths):
            if length > min(30, min(len(e1), len(exercises_txt[i])) / 2):
                common_exercises.append(exercises_txt[i])
                common_exercises_gemini.append(e1)
    exercises_txt = [exercise for exercise in exercises_txt if exercise not in common_exercises]
    remaining_gemini = [exercise for exercise in all_page_exercises if exercise not in common_exercises_gemini]

    exercises_to_write = []
    for exercise_group in exercises:
        remaining_exercises = []
        for exercise in exercise_group['questions_list']:
            if exercise['text'] not in common_exercises:
                remaining_exercises.append(exercise)
        if remaining_exercises:
            exercises_to_write.append({"page_number": exercise_group['page_number'], "questions_list": remaining_exercises})

    # if exercises and len(exercises) != totalp:
    #     print(f"{len(exercises)} remaining out of {totalp}")
    #     # remaining += len(exercises)
    #     # total += totalp

    # remove quoted text (??)
    if exercises_to_write:
        with open(f"exercises/remaining/{chapter_exercise_file}", "w") as f:
            json.dump(exercises_to_write, f, ensure_ascii=False, indent=2)
            # f.write('\n'.join(exercises))
    return len(exercises_txt), totalp, len(all_page_exercises), len(remaining_gemini)


def remove_quotes(text):
    start_quotes = ['\'', '\"', '„']
    end_quotes = ['\'', '\"', '“']
    regexes = []
    for start_quote in start_quotes:
        for end_quote in end_quotes:
            regexes.append('(' + start_quote + '.+?' + end_quote + ')')
    #processed_texts = []
    #for text in texts:
    new_text = text
    for regex in regexes:
        new_text = re.sub(regex, '', new_text)
    #    processed_texts.append(new_text)
    #return processed_texts
    return new_text


def write_examples_to_excel(file_name, rows, include_raw_exercise=False):
    workbook = xlsxwriter.Workbook(file_name)
    worksheet = workbook.add_worksheet()
    cell_format = workbook.add_format({'text_wrap': True, 'font_name': 'Arial', 'font_size': 10})
    cell_format.set_text_wrap()
    worksheet.set_column_pixels('B:B', 100, cell_format)
    worksheet.set_column_pixels('C:C', 70, cell_format)
    worksheet.set_column_pixels('D:D', 70, cell_format)
    worksheet.set_column_pixels('E:E', 70, cell_format)
    worksheet.set_column_pixels('F:F', 100, cell_format)
    worksheet.set_column_pixels('G:G', 1600, cell_format)
    if include_raw_exercise:
        worksheet.set_column_pixels('H:H', 1600, cell_format)
    # header row
    worksheet.set_row_pixels(0, 50)
    header = ['id', 'publisher', 'class', 'chapter', 'page', 'bloom_label', 'exercise']
    if include_raw_exercise:
        header.append('raw_exercise')
    worksheet.write_row(
        'A1',
        data=header,
        cell_format=cell_format
    )
    worksheet.freeze_panes(1, 0)
    for i, exercise in enumerate(rows):
        worksheet.set_row_pixels(i + 1, min(400, max(30, 20 * (exercise[5].count('\n')))))
        if include_raw_exercise:
            worksheet.set_row_pixels(i + 1, min(400, max(30, 20 * (exercise[6].count('\n')))))
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
            texts = [{"text": remove_quotes(q['text']), "page": page["page_number"]} for q in page['questions_list']]
            # processed_texts = remove_quotes(texts)
            all_exercises += [[publisher, klass, chapter, entry['page'], None, entry['text']] for entry in texts]
        chapter_exercise_file = gemini2cfg[book].strip('.pdf') + '-' + chapter + '.json'
        remaining_exercises = []
        try:
            with open(f"exercises/remaining/{chapter_exercise_file}") as json_file:
                remaining_exercises = json.load(json_file)
        except FileNotFoundError:
            print(f"skipping {chapter_exercise_file}")
        for page in remaining_exercises:
            texts = [{"text": remove_quotes(q['text']), "page": page["page_number"]} for q in page['questions_list']]
            all_exercises += [[publisher, klass, chapter, entry['page'], None, entry['text']] for entry in texts]
    all_exercises = sorted(all_exercises, key=lambda x: (x[1], x[0], x[2], x[3]))
    write_examples_to_excel('all_exercises_merged.xlsx', all_exercises)


if __name__ == "__main__":
    # merge_gemini_exercises()
    deduplicate_exercises()
    merge_exercises()
