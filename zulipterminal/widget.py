"""
Process widgets (submessages) like polls, todo lists, etc.
"""

import json
from typing import Any, Dict, List, Union, cast

from typing_extensions import Literal, TypedDict

from zulipterminal.api_types import Submessage


class TodoItem(TypedDict):
    task: str
    desc: str
    completed: bool


class ProcessedTodoWidget(TypedDict):
    title: str
    tasks: Dict[str, TodoItem]


class PollOption(TypedDict):
    option: str
    votes: List[int]


class ProcessedPollWidget(TypedDict):
    question: str
    options: Dict[str, PollOption]


class TodoTaskInput(TypedDict, total=False):
    task: str
    desc: str


class TodoExtraData(TypedDict):
    task_list_title: str
    tasks: List[TodoTaskInput]


class TodoWidgetInitial(TypedDict):
    widget_type: Literal["todo"]
    extra_data: TodoExtraData


class TodoNewTaskEvent(TypedDict):
    type: Literal["new_task"]
    key: int
    task: str
    desc: str
    completed: bool


class TodoStrikeEvent(TypedDict):
    type: Literal["strike"]
    key: str


class TodoTitleChangeEvent(TypedDict):
    type: Literal["new_task_list_title"]
    title: str


TodoWidgetJSON = Union[
    TodoWidgetInitial,
    TodoNewTaskEvent,
    TodoStrikeEvent,
    TodoTitleChangeEvent,
]


class PollExtraData(TypedDict):
    question: str
    options: List[str]


class PollWidgetInitial(TypedDict):
    widget_type: Literal["poll"]
    extra_data: PollExtraData


class PollNewOptionEvent(TypedDict):
    type: Literal["new_option"]
    idx: int
    option: str


class PollQuestionChangeEvent(TypedDict):
    type: Literal["question"]
    question: str


class PollVoteEvent(TypedDict):
    type: Literal["vote"]
    key: str
    vote: int


PollWidgetJSON = Union[
    PollWidgetInitial,
    PollNewOptionEvent,
    PollQuestionChangeEvent,
    PollVoteEvent,
]


def find_widget_type(submessages: List[Submessage]) -> str:
    if not submessages or "content" not in submessages[0]:
        return "unknown"

    content = submessages[0]["content"]

    try:
        loaded_content = json.loads(content)
        return loaded_content.get("widget_type", "unknown")
    except json.JSONDecodeError:
        return "unknown"


def process_todo_widget(
    todo_list: List[Submessage],
) -> ProcessedTodoWidget:
    title = ""
    tasks: Dict[str, TodoItem] = {}

    for entry in todo_list:
        content = entry.get("content")
        sender_id = entry.get("sender_id")
        msg_type = entry.get("msg_type")

        if msg_type == "widget" and isinstance(content, str):
            widget: TodoWidgetJSON = json.loads(content)

            if cast(Dict[str, Any], widget).get("widget_type") == "todo":
                todo_widget = cast(TodoWidgetInitial, widget)
                title = todo_widget["extra_data"].get("task_list_title", "")
                if title == "":
                    # Webapp uses "Task list" as default title
                    title = "Task list"
                # Process initial tasks
                for i, task in enumerate(todo_widget["extra_data"]["tasks"]):
                    # Initial tasks get  ID as "index,canned"
                    task_id = f"{i},canned"
                    tasks[task_id] = {
                        "task": task["task"],
                        "desc": task.get("desc", ""),
                        "completed": False,
                    }

            elif cast(Dict[str, Any], widget).get("type") == "new_task":
                new_task_event = cast(TodoNewTaskEvent, widget)
                # New tasks get ID as "key,sender_id"
                task_id = f"{new_task_event['key']},{sender_id}"
                tasks[task_id] = {
                    "task": new_task_event["task"],
                    "desc": new_task_event.get("desc", ""),
                    "completed": False,
                }

            elif cast(Dict[str, Any], widget).get("type") == "strike":
                strike_event = cast(TodoStrikeEvent, widget)
                # Strike event - toggle task completion state
                task_id = strike_event["key"]
                if task_id in tasks:
                    tasks[task_id]["completed"] = not tasks[task_id]["completed"]

            elif cast(Dict[str, Any], widget).get("type") == "new_task_list_title":
                title_event = cast(TodoTitleChangeEvent, widget)
                title = title_event["title"]

    return ProcessedTodoWidget(title=title, tasks=tasks)


def process_poll_widget(
    poll_content: List[Submessage],
) -> ProcessedPollWidget:
    poll_question = ""
    options: Dict[str, PollOption] = {}

    for entry in poll_content:
        content = entry["content"]
        sender_id = entry["sender_id"]
        msg_type = entry["msg_type"]

        if msg_type == "widget" and isinstance(content, str):
            widget: PollWidgetJSON = json.loads(content)

            if cast(Dict[str, Any], widget).get("widget_type") == "poll":
                poll_widget = cast(PollWidgetInitial, widget)
                poll_question = poll_widget["extra_data"]["question"]
                for i, option in enumerate(poll_widget["extra_data"]["options"]):
                    option_id = f"canned,{i}"
                    options[option_id] = {"option": option, "votes": []}

            elif cast(Dict[str, Any], widget).get("type") == "question":
                question_event = cast(PollQuestionChangeEvent, widget)
                poll_question = question_event["question"]

            elif cast(Dict[str, Any], widget).get("type") == "vote":
                vote_event = cast(PollVoteEvent, widget)
                option_id = vote_event["key"]
                vote_type = vote_event["vote"]

                if option_id in options:
                    if vote_type == 1 and sender_id not in options[option_id]["votes"]:
                        options[option_id]["votes"].append(sender_id)
                    elif vote_type == -1 and sender_id in options[option_id]["votes"]:
                        options[option_id]["votes"].remove(sender_id)

            elif cast(Dict[str, Any], widget).get("type") == "new_option":
                new_option_event = cast(PollNewOptionEvent, widget)
                idx = new_option_event["idx"]
                new_option = new_option_event["option"]
                option_id = f"{sender_id},{idx}"
                options[option_id] = {"option": new_option, "votes": []}

    return ProcessedPollWidget(question=poll_question, options=options)
