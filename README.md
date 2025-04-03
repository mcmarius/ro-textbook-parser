# Romanian Textbook parser

### Requirements

### Segment files

### Extract exercises

```
python extract.py
```

Extracts text from PDFs based on list heuristics with regexes. Does not work when text is not available. Estimated time: 23 seconds.

### POS tag exercises

### Extract verbs

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

This step takes around 3 minutes.

### Create plots

```
python stats.py
```
