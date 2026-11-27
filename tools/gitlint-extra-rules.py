from typing import Any, List, Optional
from gitlint.options import ListOption
from gitlint.rules import CommitRule, RuleViolation

class EndsWithDot(CommitRule):
    """
    Rule to ensure that the commit message title ends with a period ('.').
    """
    name = "title-doesn't-end-with-dot"
    id = "ZT1"

    def validate(self, commit: Any) -> Optional[List[RuleViolation]]:
        if not commit.message.title.endswith("."):
            return [RuleViolation(self.id, "Title must end with a '.'", line_nr=1)]
        return None

class AreaFormatting(CommitRule):
    """
    Rule to enforce a structured format for commit message titles:
    - The title must start with an area (lowercase, followed by ': ')
    - Certain exclusions (e.g., 'WIP') are allowed in uppercase.
    - The summary (after the colon) must start with an uppercase letter.
    """
    name = "area-formatting"
    id = "ZT2"
    options_spec = [ListOption("exclusions", ["WIP"], "Allowed uppercase exclusions")]

    def validate(self, commit: Any) -> Optional[List[RuleViolation]]:
        title_parts = commit.message.title.split(": ")
        violations = []
        
        # Ensure the title contains at least an area and a summary
        if len(title_parts) < 2:
            return [RuleViolation(self.id, "Title must start with an area, followed by ': '", line_nr=1)]
        
        exclusions = self.options["exclusions"].value
        area_part = title_parts[0]
        summary_part = title_parts[1]
        
        # Check if the area part is correctly formatted
        if area_part not in exclusions and not area_part.islower():
            violations.append(RuleViolation(self.id, "Area must be lowercase unless excluded", line_nr=1))
        
        # Ensure the summary starts with an uppercase letter
        if not summary_part[0].isupper():
            violations.append(RuleViolation(self.id, "Summary must start with an uppercase letter", line_nr=1))
        
        return violations if violations else None
