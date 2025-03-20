import codecs
import json
import os

from config import cfg, gemini2cfg

def fix_exercise_diacritics(exercise):
    fix_diacritics = lambda x: x.replace('ş', 'ș').replace('Ş', 'Ș').replace('ţ', 'ț').replace('Ţ', 'Ț')
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

def merge_exercises():
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


merge_exercises()
