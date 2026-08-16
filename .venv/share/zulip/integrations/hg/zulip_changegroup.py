#!/usr/bin/env python3

# Zulip hook for Mercurial changeset pushes.
#
# This hook is called when changesets are pushed to the default repository (ie
# `hg push`). See https://zulip.com/integrations for installation instructions.

import sys

from mercurial import repository as repo
from mercurial import ui

import zulip

VERSION = "0.9"


def format_summary_line(
    web_url: str, user: str, base: int, tip: int, branch: str, node: str
) -> str:
    """
    Format the first line of the message, which contains summary
    information about the changeset and links to the changelog if a
    web URL has been configured:

    Jane Doe <jane@example.com> pushed 1 commit to default (170:e494a5be3393):
    """
    revcount = tip - base
    plural = "s" if revcount > 1 else ""

    if web_url:
        shortlog_base_url = web_url.rstrip("/") + "/shortlog/"
        summary_url = f"{shortlog_base_url}{tip - 1}?revcount={revcount}"
        formatted_commit_count = f"[{revcount} commit{plural}]({summary_url})"
    else:
        formatted_commit_count = f"{revcount} commit{plural}"

    return f"**{user}** pushed {formatted_commit_count} to **{branch}** (`{tip}:{node[:12]}`):\n\n"


def format_commit_lines(web_url: str, repo: repo, base: int, tip: int) -> str:
    """
    Format the per-commit information for the message, including the one-line
    commit summary and a link to the diff if a web URL has been configured:
    """
    if web_url:
        rev_base_url = web_url.rstrip("/") + "/rev/"

    commit_summaries = []
    for rev in range(base, tip):
        rev_node = repo.changelog.node(rev)
        rev_ctx = repo[rev_node]
        one_liner = rev_ctx.description().split("\n")[0]

        if web_url:
            summary_url = rev_base_url + str(rev_ctx)
            summary = f"* [{one_liner}]({summary_url})"
        else:
            summary = f"* {one_liner}"

        commit_summaries.append(summary)

    return "\n".join(summary for summary in commit_summaries)


def send_zulip(
    email: str, api_key: str, site: str, stream: str, subject: str, content: str
) -> None:
    """
    Send a message to Zulip using the provided credentials, which should be for
    a bot in most cases.
    """
    client = zulip.Client(
        email=email, api_key=api_key, site=site, client="ZulipMercurial/" + VERSION
    )

    message_data = {
        "type": "stream",
        "to": stream,
        "subject": subject,
        "content": content,
    }

    client.send_message(message_data)


def get_config(ui: ui, item: str) -> str:
    try:
        # config returns configuration value.
        return ui.config("zulip", item)
    except IndexError:
        ui.warn(f"Zulip: Could not find required item {item} in hg config.")
        sys.exit(1)


def hook(ui: ui, repo: repo, **kwargs: str) -> None:
    """
    Invoked by configuring a [hook] entry in .hg/hgrc.
    """
    hooktype = kwargs["hooktype"]
    node = kwargs["node"]

    ui.debug(f"Zulip: received {hooktype} event\n")

    if hooktype != "changegroup":
        ui.warn(f"Zulip: {hooktype} not supported\n")
        sys.exit(1)

    ctx = repo[node]
    branch = ctx.branch()

    # If `branches` isn't specified, notify on all branches.
    branch_whitelist = get_config(ui, "branches")
    branch_blacklist = get_config(ui, "ignore_branches")

    if branch_whitelist:
        # Only send notifications on branches we are watching.
        watched_branches = [b.lower().strip() for b in branch_whitelist.split(",")]
        if branch.lower() not in watched_branches:
            ui.debug(f"Zulip: ignoring event for {branch}\n")
            sys.exit(0)

    if branch_blacklist:
        # Don't send notifications for branches we've ignored.
        ignored_branches = [b.lower().strip() for b in branch_blacklist.split(",")]
        if branch.lower() in ignored_branches:
            ui.debug(f"Zulip: ignoring event for {branch}\n")
            sys.exit(0)

    # The first and final commits in the changeset.
    base = repo[node].rev()
    tip = len(repo)

    email = get_config(ui, "email")
    api_key = get_config(ui, "api_key")
    site = get_config(ui, "site")

    if not (email and api_key):
        ui.warn("Zulip: missing email or api_key configurations\n")
        ui.warn("in the [zulip] section of your .hg/hgrc.\n")
        sys.exit(1)

    stream = get_config(ui, "stream")
    # Give a default stream if one isn't provided.
    if not stream:
        stream = "commits"

    web_url = get_config(ui, "web_url")
    user = ctx.user()
    content = format_summary_line(web_url, user, base, tip, branch, node)
    content += format_commit_lines(web_url, repo, base, tip)

    subject = branch

    ui.debug("Sending to Zulip:\n")
    ui.debug(content + "\n")

    send_zulip(email, api_key, site, stream, subject, content)
