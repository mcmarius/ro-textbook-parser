# https://huggingface.co/explosion/ro_udv25_romanianrrt_trf

import os
import json

from tqdm import tqdm

import spacy

from config import cfg, gemini2cfg


# nlp = spacy.load("ro_udv25_romanianrrt_trf")
# nlp = spacy.load("ro_core_news_sm")
nlp = spacy.load("ro_core_news_lg")


EXERCISES_DIR = 'exercises'
# EXERCISES_DIR = 'exercises_gemini/txt'
BOOK_EXERCISES_LIST = [item for item in os.listdir(EXERCISES_DIR) if os.path.isfile(f'{EXERCISES_DIR}/{item}')]


def process_text(lines):
    result = []
    for line in lines:
        doc = nlp(line)
        # for sent in doc.sents:
        sents = [{'start': sent.start_char, 'end': sent.end_char} for sent in doc.sents]
        tokens = [{'text': token.text, 'idx': token.idx, 'pos': token.pos_, 'tag': token.tag_} | token.morph.to_dict() for token in doc]
        result.append({'sents': sents, 'tokens': tokens})
    return result


def read_chapter(chapter_file):
    with open(f"{EXERCISES_DIR}/{chapter_file}", encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]


def process_books():
    for chapter_file in tqdm(BOOK_EXERCISES_LIST):
        dest_file = f"parsed_exercises/lg/{chapter_file.replace('.txt', '.json')}"
        if os.path.exists(dest_file):
            continue
        chapter_lines = read_chapter(chapter_file)
        parsed_data = process_text(chapter_lines)
        with open(dest_file, "w", encoding='utf-8') as f:
            json.dump(parsed_data, f)


if __name__ == "__main__":
    process_books()
