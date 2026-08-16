"""
Process widgets (submessages) like polls, todo lists, etc.
"""

import json
from typing import Any, Dict, List, Tuple, cast

from zulipterminal.api_types import (
    PollNewOptionEvent,
    PollOption,
    PollQuestionEvent,
    PollVoteEvent,
    PollWidgetInit,
    Submessage,
    TodoNewTaskEvent,
    TodoNewTitleEvent,
    TodoStrikeEvent,
    TodoTask,
    TodoWidgetInit,
)


def find_widget_type(submessages: List[Submessage]) -> str:
    if submessages and "content" in submessages[0]:
        content = submessages[0]["content"]
        try:
            loaded_content: Dict[str, Any] = json.loads(content)
            return loaded_content.get("widget_type", "unknown")
        except json.JSONDecodeError:
            return "unknown"
    else:
        return "unknown"


def process_todo_widget(
    todo_list: List[Submessage],
) -> Tuple[str, Dict[str, TodoTask]]:
    title = ""
    tasks: Dict[str, TodoTask] = {}

    for entry in todo_list:
        content = entry["content"]
        sender_id = entry["sender_id"]
        msg_type = entry["msg_type"]

        if msg_type == "widget":
            widget: Dict[str, Any] = json.loads(content)

            if widget.get("widget_type") == "todo":
                todo_init = cast(TodoWidgetInit, widget)
                extra_data = todo_init.get("extra_data")
                if extra_data is not None:
                    title = extra_data.get("task_list_title", "")
                    if title == "":
                        # Webapp uses "Task list" as default title
                        title = "Task list"
                    # Process initial tasks
                    for i, task in enumerate(extra_data.get("tasks", [])):
                        # Initial tasks get  ID as "index,canned"
                        task_id = f"{i},canned"
                        tasks[task_id] = {
                            "task": task["task"],
                            "desc": task.get("desc", ""),
                            "completed": False,
                        }

            elif widget.get("type") == "new_task":
                new_task = cast(TodoNewTaskEvent, widget)
                # New tasks get ID as "key,sender_id"
                task_id = f"{new_task['key']},{sender_id}"
                tasks[task_id] = {
                    "task": new_task["task"],
                    "desc": new_task.get("desc", ""),
                    "completed": False,
                }

            elif widget.get("type") == "strike":
                strike = cast(TodoStrikeEvent, widget)
                # Strike event - toggle task completion state
                task_id = strike["key"]
                if task_id in tasks:
                    tasks[task_id]["completed"] = not tasks[task_id]["completed"]

            elif widget.get("type") == "new_task_list_title":
                new_title = cast(TodoNewTitleEvent, widget)
                title = new_title["title"]

    return title, tasks


def process_poll_widget(
    poll_content: List[Submessage],
) -> Tuple[str, Dict[str, PollOption]]:
    poll_question = ""
    options: Dict[str, PollOption] = {}

    for entry in poll_content:
        content = entry["content"]
        sender_id = entry["sender_id"]
        msg_type = entry["msg_type"]

        if msg_type == "widget":
            widget: Dict[str, Any] = json.loads(content)

            if widget.get("widget_type") == "poll":
                poll_init = cast(PollWidgetInit, widget)
                extra_data = poll_init["extra_data"]
                poll_question = extra_data["question"]
                for i, option in enumerate(extra_data["options"]):
                    option_id = f"canned,{i}"
                    options[option_id] = {"option": option, "votes": []}

            elif widget.get("type") == "question":
                question_event = cast(PollQuestionEvent, widget)
                poll_question = question_event["question"]

            elif widget.get("type") == "vote":
                vote_event = cast(PollVoteEvent, widget)
                option_id = vote_event["key"]
                vote_type = vote_event["vote"]

                if option_id in options:
                    if vote_type == 1 and sender_id not in options[option_id]["votes"]:
                        options[option_id]["votes"].append(sender_id)
                    elif vote_type == -1 and sender_id in options[option_id]["votes"]:
                        options[option_id]["votes"].remove(sender_id)

            elif widget.get("type") == "new_option":
                new_option_event = cast(PollNewOptionEvent, widget)
                idx = new_option_event["idx"]
                new_option = new_option_event["option"]
                option_id = f"{sender_id},{idx}"
                options[option_id] = {"option": new_option, "votes": []}

    return poll_question, options
