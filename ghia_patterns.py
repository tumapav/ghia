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
            self.regex = re.compile(parts[1])
        except re.error:
            raise click.BadParameter(GhiaPatterns.CONFIG_VALIDATION_ERR)


class GhiaPatterns:
    CONFIG_VALIDATION_ERR = "incorrect configuration format"

    def __init__(self, config_dict):
        self.conf = config_dict
        self.fallback = None
        self.patterns = {}

    def validate_username(self, username):
        res = re.match('^[A-Za-z0-9\.-_]+$', username)
        if res is None:
            raise click.BadParameter(self.CONFIG_VALIDATION_ERR)

    def parse(self):
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
