import json
import os

PARSED_EXERCISES_LIST = sorted([item for item in os.listdir('parsed_exercises') if os.path.isfile(f'parsed_exercises/{item}')])
MIN_SENT_LEN = 5

def find_verbs(file_name):
    with open(f'parsed_exercises/{file_name}') as f:
        text_data = json.load(f)
    all_verbs = set()
    selected_verbs = set()
    for i, exercise in enumerate(text_data):
        # if i != 117:
        #     continue
        all_tokens = exercise['tokens']
        verb_tokens = [token for token in all_tokens if token['pos'] == 'VERB']
        all_verbs.update({token['text'].lower() for token in verb_tokens})
        for sent in exercise['sents']:
            if sent['end'] - sent['start'] < MIN_SENT_LEN:
                continue
            sent_tokens = [token for token in all_tokens if sent['start'] <= token['idx'] <= sent['end']]
            verb_tokens = [token for token in sent_tokens if token['pos'] == 'VERB' and token.get('Tense') == 'Pres' and token.get('Person') in ('2', '3') and token.get('Mood') in ('Ind', 'Imp')]
            # print(f"sent toks: {[token for token in sent_tokens]}")
            selected_verbs.update({token['text'].lower() for token in verb_tokens if token['Person'] == '2' or (token['Person'] == '3' and sent_tokens[-1]['tag'] == 'QUEST')})
    return all_verbs, selected_verbs


def process_files():
    all_verbs = set()
    selected_verbs = set()
    for chapter_file in PARSED_EXERCISES_LIST:
        extracted = find_verbs(chapter_file)
        all_verbs.update(extracted[0])
        selected_verbs.update(extracted[1])
    with open('verbs_all.txt', "w", encoding='utf-8') as f:
        f.write('\n'.join(sorted(all_verbs)))
    with open('verbs_selected.txt', "w", encoding='utf-8') as f:
        f.write('\n'.join(sorted(selected_verbs)))


if __name__ == "__main__":
    process_files()
