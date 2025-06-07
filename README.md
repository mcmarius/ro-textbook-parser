# Romanian Textbook parser

### Textbooks

Download the textbooks from https://manuale.edu.ro and place the PDFs in a folder called `data`.

### Labeled exercises

The labeled exercises can be found inside the `Bloom_level_exercises` folder:
- `all_exercises_labeled` contains only full exercises with a single label
- `all_exercises_labeled_break_ties_split` contains exercises with a single label, but if the initial exercise contains two Bloom verbs, we (1) split by sentence and create multiple sub-exercises and (2) if a sentence still contains two or more Bloom verbs, we assign the label of the first verb
- `all_exercises_labeled_with_ties` contains full exercises with multiple labels

### Requirements

Python version: 3.10

- matplotlib==3.10.0
- openpyxl==3.1.5
- pandas==2.2.3
- pylcs==0.1.1
- PyMuPDF==1.25.2
- seaborn==0.13.2
- spacy==3.8.4
- tqdm==4.67.1
- XlsxWriter==3.2.2

For the `ro_udv25_romanianrrt_trf` spaCy model, you will need:
- Python 3.10 (newer versions will **NOT** work)
- numpy==1.26.4
- pip==24.0
- spacy==3.2.5

### Segment files

```
python segment.py
```

This script extracts the table of contents from PDFs. For now, we do not use the sections. It is faster to manually enter the chapter pages in the `config.py` script.

### Extract exercises

```
python extract.py
```

Extracts text from PDFs based on list heuristics with regexes. Does not work when text is not available. Estimated time: 23 seconds.

### POS tag exercises, extract verbs

This step saves POS tagging for each text in order to find verbs.

```
python pos_tag.py
```
Change paths in script to run with different models since we get different results and no model is necessarily better than the others (i.e. even the small model is helpful).


```
python extract_verbs.py
```

Using the POS tags from before, we extract verbs that are either second person or third person in a question context.

NOTE (possible limitation): verbs tagged with POS tag `AUX` are not extracted.

### Merge exercises

```
python merge_exercises.py
```

Merge exercises extracted directly from PDFs with exercises extracted by Gemini, ensuring no duplicates are included.

Deduplication is the most time-consuming step since we need to compute all longest common substring pairs.

Extimated time with 16 threads: 36 seconds.

### Label exercises

```
python label.py
```

Label exercises based on keywords. For now, this step performs POS tagging again instead of relying on the cached entries.

This step takes around 1.5-2 minutes for each configuration.

### Create plots

```
python stats.py
```
