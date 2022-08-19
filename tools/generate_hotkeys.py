#!/usr/bin/env python3
from collections import defaultdict
from pathlib import Path, PurePath
from typing import Dict, List, Tuple

from zulipterminal.config.keys import HELP_CATEGORIES, KEY_BINDINGS


def read_help_categories() -> Dict[str, List[Tuple[str, List[str]]]]:
    """
    Get all help categories from keys.py
    """
    categories = defaultdict(list)
    for item in KEY_BINDINGS.values():
        categories[item["key_category"]].append((item["help_text"], item["keys"]))
    return categories


OUTPUT_FILE = Path(__file__).resolve().parent.parent / "docs" / "hotkeys.md"
SCRIPT_NAME = PurePath(__file__).name


def generate_hotkeys_file() -> None:
    """
    Generate hotkeys.md in docs folder based on help text description and
    shortcut key combinations in config/keys.py file
    """
    hotkeys_file_string = get_hotkeys_file_string()
    write_hotkeys_file(hotkeys_file_string)
    print(f"Hot Keys list saved in {OUTPUT_FILE}")


def get_hotkeys_file_string() -> str:
    """
    Construct string in form for output to hotkeys.md in docs folder based on help text
    description and shortcut key combinations in config/keys.py file
    """
    categories = read_help_categories()
    hotkeys_file_string = (
        f"<!--- Generated automatically by tools/{SCRIPT_NAME} -->\n"
        "<!--- Do not modify -->\n\n# Hot Keys\n"
    )
    for action in HELP_CATEGORIES.keys():
        hotkeys_file_string += (
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
            hotkeys_file_string += f"|{help_text}|{various_key_combinations}|\n"
        hotkeys_file_string += "\n"
    return hotkeys_file_string


def write_hotkeys_file(hotkeys_file_string: str) -> None:
    """
    Write hotkeys_file_string variable once to hotkeys.md file
    """
    with open(OUTPUT_FILE, "w") as mdFile:
        mdFile.write(hotkeys_file_string)


def main() -> None:
    generate_hotkeys_file()


if __name__ == "__main__":
    main()
