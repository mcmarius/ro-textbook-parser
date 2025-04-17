import json
import re

# from stats import read_book
from constants import *
# from copy import deepcopy
from collections import defaultdict, Counter
# from collections import Counter

from openpyxl import load_workbook

import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt


sns.set_theme()
sns.set_context('paper', font_scale=2)
# aa = books_stats()
# df = pd.DataFrame.from_dict(aa)
# # g = sns.FacetGrid(df, col="grade", row="publisher", height=3.5, aspect=.65)

# aaa = read_book(BOOK_LIST[0], 1)
# www = [w for line in aaa for w in line.split() if w[-1] in ['ă', 'i', 'e'] and len(w) > 4]



def books_plots(allow_ties='ties', by_chapter=False, with_colors=False, split_examples=True):
    # duplicates_values = [False, True]
    # allow_ties_values = [False, True]
    # for duplicates in duplicates_values:
    # for allow_ties in allow_ties_values:
    # by_chapter = False
    stats = books_stats(True, allow_ties, by_chapter=by_chapter, with_colors=with_colors, split_examples=split_examples)
    if by_chapter:
        id_vars = ['grade', 'publisher', 'chapter']
    else:
        id_vars = ['grade', 'publisher']
    df = pd.DataFrame.from_dict(stats)
    if allow_ties == 'multitask':
        var_name = 'Bloom categories'
    else:
        var_name = 'Bloom category'
    dfm = df.melt(id_vars=id_vars, var_name=var_name, value_name='count')
    if by_chapter:
        sns.catplot(row='publisher', col='grade', x='chapter', y='count', data=dfm, hue=var_name, kind='bar') # , col_wrap=2)
    else:
        sns.catplot(col='publisher', x='grade', y='count', data=dfm, hue=var_name, kind='bar', col_wrap=4)
    file_name = 'counts'
    if by_chapter:
        file_name += '_by_chapter'
    if allow_ties == 'ties':
        file_name += '_ties'
    elif allow_ties == 'break':
        file_name += '_break_ties'
    elif allow_ties == 'multitask':
        file_name += '_multitask'
    else:
        file_name += '_no_ties'
    if with_colors:
        file_name += '_colored'
    if not split_examples:
        file_name += '_full_exercises'
    plt.savefig(f"plots/{file_name}.pdf", bbox_inches='tight', pad_inches=0.1)


def books_stats(duplicates=True, allow_ties='ties', by_chapter=False, with_colors=False, split_examples=True):
    all_stats = defaultdict(lambda: [])
    kw_file = 'keywords.json'
    suffix = ''
    if with_colors:
        suffix += '_colored'
        kw_file = 'keywords_colored.json'
    if allow_ties in ['ties', 'multitask']:
        suffix += '_with_ties'
    elif allow_ties == 'break':
        suffix += '_break_ties'
    if split_examples:
        suffix += '_split'
    in_file = f"all_exercises_labeled{suffix}.xlsx"
    exercises_wb = load_workbook(in_file, read_only=True)
    # discard id
    exercises = [exercise[1:] for exercise in exercises_wb.worksheets[0].values]
    # discard header
    exercises = exercises[1:]
    # TODO: decide how to handle "with ties"
    if allow_ties == 'task':
        exercises = count_in_all_categories(exercises)
    elif allow_ties == 'multitask':
        exercises = count_multitask(exercises)
    all_books = BOOK_LIST
    selected_books = []
    for book in all_books:
        for publisher in ['ArtKlett', 'Booklet', 'Corint', 'Litera', 'CDPress', 'EDP', 'Intuitext', 'Paralela45', 'ArsLibri', 'Aramis']:
            if publisher in book:
                selected_books.append(book)
    all_stats = defaultdict(lambda: [])
    if allow_ties == 'multitask':
        default_labels = {'L1,L2 + L5,L6': 0, 'L1,L2 + L3,L4': 0, 'L3,L4 + L5,L6': 0, 'other': 0}
        sort_idx = {'L1,L2 + L5,L6': 1, 'L1,L2 + L3,L4': 2, 'L3,L4 + L5,L6': 3, 'other': 4}
    else:
        default_labels = {'apply': 0, 'analyze': 0, 'create': 0, 'evaluate': 0, 'remember': 0, 'understand': 0}
        sort_idx = {'remember': 1, 'understand': 2, 'apply': 3, 'analyze': 4, 'evaluate': 5, 'create': 6}
    for book in selected_books:
        grade, _subject, _idx, publisher = re.findall('Manual_Cls (\d{1,2})_([\w| ]+)_(\d{1,2})_(\w+)\.pdf', book)[0]
        if by_chapter:
            num_chapters = len(cfg[book]['chapters'])
            for chapter in range(1, num_chapters + 1):
                labels = [exercise[4] for exercise in exercises if exercise[0] == publisher.lower() and exercise[1] == grade and int(exercise[2]) == chapter]
                tally = Counter(labels)
                if not tally:
                    continue
                all_stats['grade'].append(grade)
                all_stats['publisher'].append(publisher)
                all_stats['chapter'].append(chapter)
                for stat, value in sorted(tally.items(), key=lambda x: sort_idx[x[0]]):
                    all_stats[stat].append(value)
                # handle missing levels
                for stat, value in sorted(default_labels.items(), key=lambda x: sort_idx[x[0]]):
                    if stat not in tally:
                        all_stats[stat].append(value)
        else:
            labels = [exercise[4] for exercise in exercises if exercise[0] == publisher.lower() and exercise[1] == grade]
            tally = Counter(labels)
            if not tally:
                continue
            all_stats['grade'].append(grade)
            all_stats['publisher'].append(publisher)
            for stat, value in sorted(tally.items(), key=lambda x: sort_idx[x[0]]):
                all_stats[stat].append(value)
        # print(f"stats for {book}: {tally}")
        # stats = stats_for_lines(selected_exercises, duplicates, allow_ties, kw_file)
    return all_stats


def count_in_all_categories(exercises):
    new_exercises = []
    for exercise in exercises:
        new_exercise = list(exercise)
        if '/' in exercise[4]:
            for label in exercise[4].split('/'):
                new_exercise[4] = label
                new_exercises.append(new_exercise)
        else:
            new_exercises.append(new_exercise)
    return new_exercises


def count_multitask(exercises):
    new_exercises = []
    for exercise in exercises:
        if '/' not in exercise[4]:
            continue
        labels = exercise[4].split('/')
        new_exercise = list(exercise)
        if ('remember' in labels or 'understand' in labels) and ('evaluate' in labels or 'create' in labels) and ('apply' not in labels and 'analyze' not in labels):
            new_exercise[4] = 'L1,L2 + L5,L6'
        elif ('remember' in labels or 'understand' in labels) and ('evaluate' not in labels and 'create' not in labels) and ('apply' in labels or 'analyze' in labels):
            new_exercise[4] = 'L1,L2 + L3,L4'
        elif ('remember' not in labels and 'understand' not in labels) and ('evaluate' in labels or 'create' in labels) and ('apply' in labels or 'analyze' in labels):
            new_exercise[4] = 'L3,L4 + L5,L6'
        else:
            new_exercise[4] = 'other'
        new_exercises.append(new_exercise)
    return new_exercises


def books_stats_old(duplicates=True, allow_ties=True, by_chapter=False):
    all_books = BOOK_LIST
    selected_books = []
    for book in all_books:
        for publisher in ['ArtKlett', 'Booklet', 'Corint', 'Litera']:
            if publisher in book:
                selected_books.append(book)
    all_stats = defaultdict(lambda: [])
    for book in selected_books:
        grade, subject, idx, publisher = re.findall('Manual_Cls (\d{1,2})_([\w| ]+)_(\d{1,2})_(\w+)\.pdf', book)[0]
        if by_chapter:
            stats = book_stats_chapter_old(book, duplicates=duplicates, allow_ties=allow_ties)
            for chapter_stats in stats:
                all_stats['grade'].append(grade)
                all_stats['publisher'].append(publisher)
                for stat in chapter_stats:
                    all_stats[stat].append(chapter_stats[stat])
        else:
            stats = book_stats_old(book, duplicates=duplicates, allow_ties=allow_ties)
            all_stats['grade'].append(grade)
            all_stats['publisher'].append(publisher)
            for stat in stats:
                all_stats[stat].append(stats[stat])
            # all_stats['kind'].append(stat)
            # all_stats['count'].append(stats[stat])
    return all_stats


def read_chapter(book, chapter):
    with open(f"exercises/{book.strip('.pdf')}-{chapter}.txt") as f:
        return [line.strip() for line in f.readlines()]


def read_book(book, num_chapters):
    lines = []
    for chapter in range(1, num_chapters + 1):
        lines += read_chapter(book, chapter)
    return lines


def read_kw(kw_file='keywords.json', duplicates=False):
    kws = {}
    idx = {}
    with open(kw_file) as f:
        kws = json.load(f)
    for kw in kws:
        words = kws[kw]
        for word in words:
            if duplicates:
                idx[word] = kw.split("/")
            else:
                idx[word] = [kw]
    # verify we do not have duplicate words
    assert(len([w for wl in kws.values() for w in wl]) == len({w for wl in kws.values() for w in wl}))
    return kws, idx


def book_stats_chapter_old(book, duplicates=False, allow_ties=False):
    num_chapters = len(cfg[book]['chapters'])
    stats = []
    for chapter in range(1, num_chapters + 1):
        book_lines = read_chapter(book, chapter)
        chapter_stats = stats_for_lines_old(book_lines, duplicates, allow_ties)
        chapter_stats.update({'chapter': chapter})
        stats.append(chapter_stats)
    return stats


def book_stats_old(book, duplicates=False, allow_ties=False):
    num_chapters = len(cfg[book]['chapters'])
    book_lines = read_book(book, num_chapters)
    return stats_for_lines_old(book_lines, duplicates, allow_ties)


def stats_for_lines_old(lines, duplicates, allow_ties, kw_file='keywords.json'):
    kws, idx = read_kw(kw_file, duplicates)
    if duplicates:
        categories = [key for key in kws.keys() if '/' not in key]
    else:
        categories = list(kws.keys())
    tally = defaultdict(lambda: 0)
    ambiguous_count = 0
    for line in lines:
        exercise = line.lower().replace('ş', 'ș').replace('ţ', 'ț')
        local_tally = defaultdict(lambda: 0)
        for word in idx:
            if word in exercise:
                for cat in idx[word]:
                    local_tally[cat] += 1
        if not local_tally:
            continue
        max_cat = max(local_tally, key=lambda cat: local_tally[cat])
        max_cats = [cat for cat in local_tally if local_tally[cat] == local_tally[max_cat]]
        if allow_ties:
            for cat in max_cats:
                tally[cat] += 1
        else:
            if len(max_cats) > 1:
                # print(f'skipping due to ambiguous labels: {max_cats}')
                ambiguous_count += 1
                continue
            tally[max_cat] += 1
    for cat in categories:
        if tally[cat] == 0:
            pass
    if ambiguous_count > 0:
        print(f'skipped {ambiguous_count} ambiguous exercises')
    return dict(sorted(tally.items(), key=lambda cat_data: categories.index(cat_data[0])))


if __name__ == "__main__":
    for chapter in [False, True]:
        for tie in ['multitask']: # ['break']: # [False, True]:
            for color in [False, True]:
                for split in [False, True]:
                    print(f"chapter: {chapter}, color: {color}, split examples: {split}")
                    books_plots(tie, chapter, color, split)
