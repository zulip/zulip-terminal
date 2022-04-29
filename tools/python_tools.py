#!/usr/bin/env python3

import glob


tools_exclusions = {
    f"tools/{name}"
    for name in {
        "fetch-pull-request",
        "fetch-rebase-pull-request",
        "push-to-pull-request",
        "release",
        "__pycache__",
    }
}

lintable_tools_files = set(glob.glob("tools/*")).difference(tools_exclusions)


if __name__ == "__main__":
    for f in lintable_tools_files:
        print(f)
