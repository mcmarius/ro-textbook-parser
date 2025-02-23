import csv

import tqdm
from suffix_trees import STree

from constants import *

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
