"""Process widgets (polls, todos) with strongly-typed submessages."""

import json
from typing import Any, Dict, List, Union, cast

from zulipterminal.api_types import (
    PollOption,
    PollWidgetResult,
    RawPollWidget,
    RawTodoWidget,
    Submessage,
    TodoTask,
    TodoWidgetResult,
)


def find_widget_type(submessages: List[Submessage]) -> str:
    """
    Identify the widget type from the first submessage.

    Parses the content JSON of the first submessage and extracts
    the widget_type field to determine what kind of widget this
    represents (e.g., 'poll', 'todo', etc.).

    Parameters
    ----------
    submessages : List[Submessage]
        List of submessages to inspect. The first submessage's
        content is parsed to determine the widget type.

    Returns
    -------
    str
        A string representing the widget type ('poll', 'todo', etc.),
        or 'unknown' if the widget type cannot be determined.
    """
    if not submessages:
        return "unknown"

    content = submessages[0].get("content")

    if not content or not isinstance(content, str):
        return "unknown"

    try:
        loaded_content = json.loads(content)
        if isinstance(loaded_content, dict):
            return str(loaded_content.get("widget_type", "unknown"))
    except (json.JSONDecodeError, TypeError):
        return "unknown"

    return "unknown"


def process_todo_widget(todo_list: List[Submessage]) -> TodoWidgetResult:
    """
    Process submessages for a todo list widget.

    Extracts and structures todo task information from a list of
    submessages. Handles various todo operations including widget
    creation, task addition, task completion toggling, and title
    updates.

    Parameters
    ----------
    todo_list : List[Submessage]
        List of submessages containing todo widget operations.
        Each submessage has msg_type='widget' with JSON-encoded
        content describing todo operations.

    Returns
    -------
    TodoWidgetResult
        A TypedDict containing:
        - 'title': str - The title of the todo list
        - 'tasks': Dict[str, TodoTask] - Map of task IDs to task details
    """
    title: str = ""
    tasks: Dict[str, TodoTask] = {}

    for entry in todo_list:
        content = entry["content"]
        sender_id = entry["sender_id"]
        msg_type = entry["msg_type"]

        if msg_type == "widget" and isinstance(content, str):
            raw = json.loads(content)
            widget = cast(Union[RawTodoWidget, Dict[str, Any]], raw)

            if widget.get("widget_type") == "todo":
                if "extra_data" in widget and widget["extra_data"] is not None:
                    extra_data = cast(Dict[str, Any], widget["extra_data"])
                    title = cast(str, extra_data.get("task_list_title", ""))
                    if title == "":
                        title = "Task list"
                    for i, task in enumerate(extra_data.get("tasks", [])):
                        task_id = f"{i},canned"
                        # Explicitly cast to TodoTask to satisfy TypedDict requirements
                        tasks[task_id] = cast(
                            TodoTask,
                            {
                                "task": str(task["task"]),
                                "desc": str(task.get("desc", "")),
                                "completed": False,
                            },
                        )

            elif widget.get("type") == "new_task":
                task_id = f"{widget['key']},{sender_id}"
                # Explicitly cast to TodoTask to satisfy TypedDict requirements
                tasks[task_id] = cast(
                    TodoTask,
                    {
                        "task": str(widget["task"]),
                        "desc": str(widget.get("desc", "")),
                        "completed": False,
                    },
                )

            elif widget.get("type") == "strike":
                task_id = str(widget["key"])
                if task_id in tasks:
                    tasks[task_id]["completed"] = not tasks[task_id]["completed"]

            elif widget.get("type") == "new_task_list_title":
                title = cast(str, widget.get("title", ""))

    return {"title": title, "tasks": tasks}


def process_poll_widget(poll_content: List[Submessage]) -> PollWidgetResult:
    """
    Process submessages for a poll widget.

    Extracts and structures poll information from a list of submessages.
    Handles various poll operations including poll creation, option
    addition, and user votes.

    Parameters
    ----------
    poll_content : List[Submessage]
        List of submessages containing poll widget operations.
        Each submessage has msg_type='widget' with JSON-encoded
        content describing poll operations.

    Returns
    -------
    PollWidgetResult
        A TypedDict containing:
        - 'question': str - The poll question text
        - 'options': Dict[str, PollOption] - Map of option IDs to
          poll options with their current vote lists
    """
    poll_question: str = ""
    options: Dict[str, PollOption] = {}

    for entry in poll_content:
        content = entry["content"]
        sender_id = entry["sender_id"]
        msg_type = entry["msg_type"]

        if msg_type == "widget" and isinstance(content, str):
            raw = json.loads(content)
            widget = cast(Union[RawPollWidget, Dict[str, Any]], raw)

            if widget.get("widget_type") == "poll":
                poll_question = widget["extra_data"]["question"]
                for i, option in enumerate(widget["extra_data"].get("options", [])):
                    option_id = f"canned,{i}"
                    options[option_id] = {"option": option, "votes": []}

            elif widget.get("type") == "question":
                poll_question = widget["question"]

            elif widget.get("type") == "vote":
                option_id = widget["key"]
                vote_type = widget["vote"]

                if option_id in options:
                    if vote_type == 1 and sender_id not in options[option_id]["votes"]:
                        options[option_id]["votes"].append(sender_id)
                    elif vote_type == -1 and sender_id in options[option_id]["votes"]:
                        options[option_id]["votes"].remove(sender_id)

            elif widget.get("type") == "new_option":
                idx = widget["idx"]
                new_option = widget["option"]
                option_id = f"{sender_id},{idx}"
                options[option_id] = {"option": new_option, "votes": []}

    return {"question": poll_question, "options": options}
