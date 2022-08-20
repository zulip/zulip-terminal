#!/usr/bin/env python3
from collections import defaultdict
from pathlib import Path, PurePath
from typing import Dict, List, Tuple

from zulipterminal.config.keys import HELP_CATEGORIES, KEY_BINDINGS


KEYS_FILE = (
    Path(__file__).resolve().parent.parent / "zulipterminal" / "config" / "keys.py"
)
KEYS_FILE_NAME = KEYS_FILE.name
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "docs" / "hotkeys.md"
OUTPUT_FILE_NAME = OUTPUT_FILE.name
SCRIPT_NAME = PurePath(__file__).name


def main() -> None:
    generate_hotkeys_file()


def generate_hotkeys_file() -> None:
    """
    Generate OUTPUT_FILE based on help text description and
    shortcut key combinations in KEYS_FILE
    """
    hotkeys_file_string = get_hotkeys_file_string()
    output_file_matches_string(hotkeys_file_string)
    write_hotkeys_file(hotkeys_file_string)
    print(f"Hot Keys list saved in {OUTPUT_FILE}")


def get_hotkeys_file_string() -> str:
    """
    Construct string in form for output to OUTPUT_FILE based on help text
    description and shortcut key combinations in KEYS_FILE
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


def output_file_matches_string(hotkeys_file_string: str) -> bool:
    if hotkeys_file_string == open(OUTPUT_FILE).read():
        print(f"{OUTPUT_FILE_NAME} file already in sync with config/{KEYS_FILE_NAME}")
        return True
    else:
        print(f"{OUTPUT_FILE_NAME} file not in sync with config/{KEYS_FILE_NAME}")
        return False


def read_help_categories() -> Dict[str, List[Tuple[str, List[str]]]]:
    """
    Get all help categories from KEYS_FILE
    """
    categories = defaultdict(list)
    for item in KEY_BINDINGS.values():
        categories[item["key_category"]].append((item["help_text"], item["keys"]))
    return categories


def write_hotkeys_file(hotkeys_file_string: str) -> None:
    """
    Write hotkeys_file_string variable once to OUTPUT_FILE
    """
    with open(OUTPUT_FILE, "w") as mdFile:
        mdFile.write(hotkeys_file_string)


if __name__ == "__main__":
    main()
