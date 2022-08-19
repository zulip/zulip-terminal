#!/usr/bin/env python3
from collections import defaultdict
from pathlib import Path, PurePath

from zulipterminal.config.keys import HELP_CATEGORIES, KEY_BINDINGS


categories = defaultdict(list)
for item in KEY_BINDINGS.values():
    categories[item["key_category"]].append((item["help_text"], item["keys"]))

OUTPUT_FILE = Path(__file__).resolve().parent.parent / "docs" / "hotkeys.md"
SCRIPT_NAME = PurePath(__file__).name

with open(OUTPUT_FILE, "w") as mdFile:
    mdFile.write(
        f"<!--- Generated automatically by tools/{SCRIPT_NAME} -->\n"
        "<!--- Do not modify -->\n\n# Hot Keys\n"
    )
    for action in HELP_CATEGORIES.keys():
        mdFile.write(
            f"## {HELP_CATEGORIES[action]}\n"
            "|Command|Key Combination|\n"
            "| :--- | :---: |\n"
        )
        for help_text, key_combinations_list in categories[action]:
            various_key_combinations = " / ".join(
                [
                    " + ".join([f"<kbd>{key}</kbd>" for key in key_combination.split()])
                    for key_combination in key_combinations_list
                ]
            )
            mdFile.write(f"|{help_text}|{various_key_combinations}|\n")
        mdFile.write("\n")

print(f"Hot Keys list saved in {OUTPUT_FILE}")
