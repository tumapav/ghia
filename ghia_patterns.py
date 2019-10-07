import re
import click


class Pattern:

    PATTERN_TYPES = ["title", "text", "label", "any"]

    def __init__(self, text):
        self.text = text
        self.regex = None
        self.type = None
        self.parse()

    def parse(self):
        parts = self.text.split(":", 1)

        # Check pattern format type:regex
        if len(parts) != 2:
            raise click.BadParameter(GhiaPatterns.CONFIG_VALIDATION_ERR)

        self.type = parts[0]

        # Check pattern type
        if parts[0] not in self.PATTERN_TYPES:
            raise click.BadParameter(GhiaPatterns.CONFIG_VALIDATION_ERR)

        # Check regex validity
        try:
            self.regex = re.compile(parts[1], flags=re.IGNORECASE)
        except re.error:
            raise click.BadParameter(GhiaPatterns.CONFIG_VALIDATION_ERR)

    def _match_title(self, issue):
        return self.regex.search(issue.title)

    def _match_text(self, issue):
        return self.regex.search(issue.body)

    def _match_label(self, issue):
        for label in issue.labels:
            if self.regex.search(label):
                return True
        return False

    def match(self, issue):
        if self.type == "title":
            return self._match_title(issue)
        elif self.type == "text":
            return self._match_text(issue)
        elif self.type == "label":
            return self._match_label(issue)
        elif self.type == "any":
            return self._match_title(issue) \
                   or self._match_text(issue) \
                   or self._match_label(issue)


class GhiaPatterns:
    CONFIG_VALIDATION_ERR = "incorrect configuration format"

    def __init__(self, config_dict):
        self.conf = config_dict
        self.fallback = None
        self.strategy = None
        self.dry_run = False
        self.patterns = {}

    def set_strategy(self, strategy):
        self.strategy = strategy

    def set_dry_run(self, dry_run):
        self.dry_run = dry_run

    def validate_username(self, username):
        res = re.match('^[A-Za-z0-9\.-_]+$', username)
        if res is None:
            raise click.BadParameter(self.CONFIG_VALIDATION_ERR)

    def parse(self):
        """Initializes the patterns from the configuration dictionary."""

        patterns_conf = self.conf["patterns"]
        for username in patterns_conf:
            self.validate_username(username)
            rules = patterns_conf[username].strip("\n ").split("\n")

            if username not in self.patterns:
                self.patterns[username] = []

            for rule in rules:
                pattern_obj = Pattern(rule)
                self.patterns[username].append(pattern_obj)

        if "fallback" in self.conf and "label" in self.conf["fallback"]:
            self.fallback = self.conf["fallback"]["label"]

    class AssigneeState:

        REMOVED = -1
        KEPT = 0
        ADDED = 1

        def __init__(self, username, state):
            self.username = username
            self.state = state

    def apply_to(self, issue):
        """Applies the saved patterns to the given issue."""

        click.secho("-> ", nl=False)
        click.secho(f"{issue.repo_slug}#{issue.number} ", bold=True, nl=False)
        click.secho(f"({issue.url})")

        to_add = set()
        assignees = {}

        for username in self.patterns:
            patterns = self.patterns[username]

            for pattern in patterns:
                if pattern.match(issue):
                    to_add.add(username)

        # Process users assigned to the issue prior GHIA
        default_state = self.AssigneeState.KEPT if self.strategy == "append" else self.AssigneeState.REMOVED
        for user in issue.assignees:
            assignees[user] = self.AssigneeState(user, default_state)

        # Process users to be added
        if self.strategy != "set" or len(issue.assignees) == 0:
            for user in to_add:
                if user in issue.assignees:
                    # User matched in GHIA and was already assigned => Always keep
                    assignees[user].state = self.AssigneeState.KEPT
                else:
                    # User matched in GHIA and was NOT assigned => Add user
                    assignees[user] = self.AssigneeState(user, self.AssigneeState.ADDED)

        # Get sorted report
        sorted_assignees_report = sorted(list(assignees), key=str.casefold)
        for user in sorted_assignees_report:
            state = assignees[user].state

            if state == self.AssigneeState.REMOVED:
                click.secho("   - ", bold=True, fg='red', nl=False)
            elif state == self.AssigneeState.KEPT:
                click.secho("   = ", bold=True, fg='blue', nl=False)
            elif state == self.AssigneeState.ADDED:
                click.secho("   + ", bold=True, fg='green', nl=False)

            click.echo(f"{user}")

        res = list(filter(lambda x: assignees[x].state >= self.AssigneeState.KEPT, assignees))
        issue.assignees = set(res)

        # Check for FALLBACK label
        if len(issue.assignees) == 0 and self.fallback:
            click.secho("   FALLBACK", bold=True, fg='yellow', nl=False)
            click.echo(":")
            if self.fallback in issue.labels:
                click.echo(f"already has label {self.fallback}")
            else:
                click.echo(f"added label {self.fallback}")
                issue.labels.add(self.fallback)

        return issue
