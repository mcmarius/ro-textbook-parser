import json
import os

# PARSED_EXERCISES_DIR = 'parsed_exercises'
PARSED_EXERCISES_DIR = 'parsed_exercises/trf'
PARSED_EXERCISES_LIST = sorted([item for item in os.listdir(PARSED_EXERCISES_DIR) if os.path.isfile(f'{PARSED_EXERCISES_DIR}/{item}')])
MIN_SENT_LEN = 5


def read_file(file_name):
    with open(file_name) as f:
        return [line.strip() for line in f.readlines()]


def merge_verbs():
    new_files = ['verbs_selected-gem-trf-skip-quote.txt', 'verbs_selected-gem-lg-skip-quote.txt', 'verbs_selected-gem-sm-skip-quote.txt',
                 'verbs_selected-trf-skip-quote.txt', 'verbs_selected-lg-skip-quote.txt', 'verbs_selected-sm-skip-quote.txt']
    old_files = ['verbs_selected.txt']
    new_verbs = set()
    for new_file in new_files:
        verbs = set(read_file(new_file))
        new_verbs.update(verbs)
    for old_file in old_files:
        old_verbs = set(read_file(old_file))
        new_verbs.difference_update(old_verbs)
    with open('verbs-diff-all-skip-quote.txt', 'w') as f:
        f.write('\n'.join(sorted(new_verbs)))
    # return sorted(new_verbs)

# f1 = set(read_file('verbs_selected.txt'))
# f2 = set(read_file('verbs_selected-gem.txt'))
# sorted({x for x in f2 if x not in f1})
# with open('verbs-diff-gem.txt', 'w') as f: f.write('\n'.join(sorted({x for x in f2 if x not in f1})))


def find_verbs(file_name):
    with open(f'{PARSED_EXERCISES_DIR}/{file_name}') as f:
        text_data = json.load(f)
    all_verbs = set()
    selected_verbs = set()
    quote_count = 0
    for i, exercise in enumerate(text_data):
        # if i != 117:
        #     continue
        all_tokens_raw = exercise['tokens']
        all_tokens = []
        in_quote = False
        #quote = []
        for token in all_tokens_raw:
            #if in_quote:
            #    quote.append(token['text'])
            if not in_quote and token['text'] in ['\'', '\"', '„']:
                in_quote = True
                continue
            elif in_quote and token['text'] in ['\'', '\"', '“']:
                in_quote = False
                #print(' '.join(quote))
                #quote = []
                quote_count += 1
                continue
            if not in_quote:
                all_tokens.append(token)
        verb_tokens = [token for token in all_tokens if token['pos'] == 'VERB']
        all_verbs.update({token['text'].lower() for token in verb_tokens})
        for sent in exercise['sents']:
            if sent['end'] - sent['start'] < MIN_SENT_LEN:
                continue
            sent_tokens = [token for token in all_tokens if sent['start'] <= token['idx'] <= sent['end']]
            verb_tokens = [token for token in sent_tokens if token['pos'] == 'VERB' and token.get('Tense') == 'Pres' and token.get('Person') in ('2', '3') and token.get('Mood') in ('Ind', 'Imp')]
            # print(f"sent toks: {[token for token in sent_tokens]}")
            selected_verbs.update({token['text'].lower() for token in verb_tokens if token['Person'] == '2' or (token['Person'] == '3' and sent_tokens[-1]['tag'] == 'QUEST')})
    return all_verbs, selected_verbs, quote_count


def process_files():
    all_quote_count = 0
    all_verbs = set()
    selected_verbs = set()
    for chapter_file in PARSED_EXERCISES_LIST:
        extracted = find_verbs(chapter_file)
        all_verbs.update(extracted[0])
        selected_verbs.update(extracted[1])
        all_quote_count += extracted[2]
    if all_quote_count > 0:
        print(f"skipped {all_quote_count} quotes")
    with open('verbs_all-trf-skip-quote.txt', "w", encoding='utf-8') as f:
        f.write('\n'.join(sorted(all_verbs)))
    with open('verbs_selected-trf-skip-quote.txt', "w", encoding='utf-8') as f:
        f.write('\n'.join(sorted(selected_verbs)))


if __name__ == "__main__":
    process_files()
