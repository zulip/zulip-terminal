#!/usr/bin/env python3

# Script to capture screenshot, and save them to screenshots/

import os
from datetime import datetime

import pyscreenshot as ImageGrab


DIR = "screenshots"


def stdout(cmd: str) -> str:
    output = str(os.popen(cmd).read())
    # Truncate the output string (original: '<output>\n')
    return output[:-1]


def capture_curr_screen() -> None:
    # Getting the active window id
    win_id = stdout("xprop -root 32x '\t$0' _NET_ACTIVE_WINDOW | cut -f 2")
    win_info = f"xwininfo -id {win_id} | grep "

    # Get window dimensions
    left_x = int(stdout(f"{win_info}'Absolute upper-left X'")[26:])
    top_y = int(stdout(f"{win_info}'Absolute upper-left Y'")[26:])
    right_x = int(stdout(f"{win_info}Width")[9:]) + left_x
    bottom_y = int(stdout(f"{win_info}Height")[9:]) + top_y

    dimensions = (left_x, top_y, right_x, bottom_y)

    # If the directory doesn't exists, create it
    if not os.path.isdir(DIR):
        os.mkdir(DIR)

    # Set filename as the timestamp of capture
    date = datetime.now().replace(microsecond=0)
    path = f"{DIR}/Screenshot from {date}.png"

    # Capture and save the screenshot
    ImageGrab.grab(bbox=dimensions).save(path)


if __name__ == "__main__":
    capture_curr_screen()
