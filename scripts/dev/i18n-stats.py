#!/usr/bin/python3
#
# Print a simple summary of translation coverage and completeness.
# Make sure to run ./scripts/create_locales.sh beforehand.
#
import glob
import os

import polib

os.chdir(os.path.join(os.path.dirname(__file__), "..", "..", "locale"))

results = {}

for filename in glob.glob("*.po"):
    with open(filename, "r", encoding="utf-8") as f:
        po = polib.pofile(filename)
        lang = filename[:-3]

        total_entries = len(po)
        translated_entries = sum(1 for entry in po if entry.translated())
        fuzzy_entries = sum(1 for entry in po if entry.fuzzy)
        percent_done = (translated_entries / total_entries) * 100
        results[lang] = [percent_done, translated_entries, total_entries, fuzzy_entries]

print("Locale".ljust(8), "Completed".rjust(10), "Translated".rjust(12), "Fuzzy".rjust(6))
for lang, stats in sorted(results.items(), key=lambda x: x[1][0], reverse=True):
    percent_done, translated_entries, total_entries, fuzzy_entries = stats
    print(lang.ljust(8), f"{percent_done:.1f}%".rjust(10), f"{translated_entries}/{total_entries}".rjust(12), str(fuzzy_entries).rjust(6))
