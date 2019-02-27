import gitlint
from gitlint.rules import CommitRule, RuleViolation
from gitlint.options import ListOption

from typing import List, Any, Optional


class EndsWithDot(CommitRule):
    name = "title-doesn't-end-with-dot"
    id = "ZT1"

    def validate(self, commit: Any) -> Optional[List[RuleViolation]]:
        error = "Title does not end with a '.' character"
        if not commit.message.title.endswith("."):
            return [RuleViolation(self.id, error, line_nr=1)]


class StartsWithAreaColonOrMore(CommitRule):
    name = "title-missing-area-and-colon"
    id = "ZT2"

    def validate(self, commit: Any) -> Optional[List[RuleViolation]]:
        error = ("Title should start with at least one area "
                 "followed by a colon and space")
        title_components = commit.message.title.split(": ")

        if len(title_components) < 2:
            return [RuleViolation(self.id, error, line_nr=1)]


class AreaConstraints(CommitRule):
    name = "area-constraints"
    id = "ZT3"

    options_spec = [ListOption("exclusions", ["WIP"],
                               "Exclusions to area lower-case rule")]

    def validate(self, commit: Any) -> Optional[List[RuleViolation]]:
        exclusions = self.options['exclusions'].value
        exclusions_text = ", or ".join(exclusions)
        if exclusions_text:
            exclusions_text = " (or {})".format(exclusions_text)

        error = ("Areas at start of title should be lower case{}, "
                 "followed by ': '".format(exclusions_text))

        title_components = commit.message.title.split(": ")

        violations = []

        for area in title_components[:-1]:
            if not (area.islower() or area in exclusions) or ' ' in area:
                violations += [RuleViolation(self.id, error, line_nr=1)]

        return violations


class ChangeCapitalized(CommitRule):
    name = "capitalized-change"
    id = "ZT4"

    def validate(self, commit: Any) -> Optional[List[RuleViolation]]:
        error = "Summary of change, after areas, should be capitalized"
        title_components = commit.message.title.split(": ")

        if not title_components[-1][0].isupper():
            return [RuleViolation(self.id, error, line_nr=1)]
