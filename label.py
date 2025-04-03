# import csv

# from suffix_trees import STree

# from constants import *
import json

import spacy

from collections import defaultdict

from openpyxl import load_workbook
from tqdm import tqdm

from merge_exercises import write_examples_to_excel

nlp = spacy.load("ro_core_news_lg")
TOKENIZED_EXERCISES = {}


def read_labels(file_name, include_colored_labels, skip_ambiguous_labels):
    DEFAULT_COLOR = '00000000'
    wb_labels = load_workbook(file_name, read_only=True)
    ws_labels = wb_labels.worksheets[0]
    labeled_verbs = {}
    for i, row in enumerate(ws_labels.iter_rows(min_row=2)):
        # if i == 0:
        #     continue
        if len(row) < 2:
            continue
        verb, label = row
        if verb.fill.bgColor.rgb != DEFAULT_COLOR and not include_colored_labels:
            continue
        if not label or not label.value:
            continue
        if '/' in label.value and skip_ambiguous_labels:
            continue
        fixed_label = label.value.strip()
        if fixed_label in ['undertand', 'undesrstand', 'undestand']:
            fixed_label = 'understand'
        labeled_verbs[verb.value] = fixed_label
    wb_labels.close()
    return labeled_verbs


def label_examples(include_colored_labels=False, skip_ambiguous_labels=True, skip_ambiguous_exercises=True):
    labeled_verbs1 = read_labels('Verbe-cu-etichetă-p1.xlsx', include_colored_labels, skip_ambiguous_labels)
    labels = defaultdict(lambda: [])
    for verb, label in labeled_verbs1.items():
        labels[label].append(verb)
    labeled_verbs2 = read_labels('Verbe-cu-etichetă-p2.xlsx', include_colored_labels, skip_ambiguous_labels)
    for verb, label in labeled_verbs2.items():
        labels[label].append(verb)
    labeled_verbs = {}
    labeled_verbs.update(labeled_verbs1)
    labeled_verbs.update(labeled_verbs2)
    suffix = ''
    if include_colored_labels:
        suffix += '_colored'
    kw_file = f"keywords{suffix}.json"
    with open(kw_file, "w", encoding='utf-8') as f:
        json.dump(labels, f, ensure_ascii=False)
    # print(labeled_verbs)
    # return
    if not skip_ambiguous_exercises:
        suffix += '_with_ties'
    ambiguous_exercises_count = 0
    labeled_examples = []
    wb_examples = load_workbook('all_exercises_merged.xlsx')
    ws_examples = wb_examples.worksheets[0]
    skipped_exercises = 0
    total_exercises = 0
    for i, row in tqdm(list(enumerate(ws_examples.values))):
        id_, publisher, klass, chapter, bloom_label, exercise = row
        # tokenize example
        if not exercise:
            # print("Empty exercise")
            continue
        total_exercises += 1
        doc = TOKENIZED_EXERCISES.get(i)
        if not doc:
            doc = nlp(exercise)
            TOKENIZED_EXERCISES[i] = doc
        local_tally = defaultdict(lambda: 0)
        # count verb tokens
        for token in doc:
            label = labeled_verbs.get(str(token).lower())
            if label:
                local_tally[label] += 1
        if not local_tally:
            skipped_exercises += 1
            continue
        max_cat = max(local_tally, key=lambda cat: local_tally[cat])
        max_cats = [cat for cat in local_tally if local_tally[cat] == local_tally[max_cat]]
        if len(max_cats) > 1:
            ambiguous_exercises_count += 1
            if skip_ambiguous_exercises:
                continue
            bloom_label = '/'.join(max_cats)
        else:
            bloom_label = max_cat
        labeled_examples.append([publisher, klass, chapter, bloom_label, exercise])
    print(f"Exercises skipped (no verbs): {skipped_exercises} / {total_exercises}")
    print(f"Ambiguous examples: {ambiguous_exercises_count}")
    out_file = f"all_exercises_labeled{suffix}.xlsx"
    write_examples_to_excel(out_file, labeled_examples)
    wb_examples.close()


if __name__ == "__main__":
    label_examples(include_colored_labels=False, skip_ambiguous_exercises=True)
    label_examples(include_colored_labels=True, skip_ambiguous_exercises=True)
    label_examples(include_colored_labels=True, skip_ambiguous_exercises=False)
    label_examples(include_colored_labels=False, skip_ambiguous_exercises=False)

"""
def read_csv(file_name):
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        lines = []
        for row in reader:
            row['text'] = row['text'].strip()
            lines.append(row)
        return lines

def write_csv(file_name, rows):
    with open(file_name, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys(), delimiter=',', quotechar='"')
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def read_chapter(book, chapter):
    with open(f"exercises/{book.strip('.pdf')}-{chapter}.txt") as f:
        return [line.strip() for line in f.readlines()]

def read_book(book, num_chapters):
    lines = []
    for chapter in range(1, num_chapters + 1):
        lines += read_chapter(book, chapter)
    return lines


def label_text():
    labeled_examples = read_csv('misc/texts_labeled.csv')
    lines = [example['text'] for example in labeled_examples]
    current_book = BOOK_LIST[4]
    num_chapters = len(cfg[current_book]['chapters'])
    book_lines = read_book(current_book, num_chapters)

    labeled_book_lines = []
    for book_line in tqdm.tqdm(book_lines):
        max_len = 0
        max_example = None
        max_lcs = ''
        for example in labeled_examples:
            lcs = STree.STree([example['text'], book_line]).lcs()
            if len(lcs) > max_len:
                max_len = len(lcs)
                max_example = example
                max_lcs = lcs
        if max_example and max_len > 15:
            # print(f'max lcs: {max_lcs}')
            labeled_book_lines.append({'text': book_line, 'label': max_example['label']})
    return labeled_book_lines
"""
