import json
import re


class Issue:
    """Issue representation for the purposes of GHIA"""

    def __init__(self, data):
        self.data = data
        self.number = None
        self.body = None
        self.title = None
        self.repo_slug = None
        self.url = None
        self.assignees = set()
        self.labels = set()
        self.parse(data)

    def parse(self, data):
        """Initialize issue instance from the API data"""
        self.number = data["number"]
        self.title = data["title"]
        self.body = data["body"]

        for label in data["labels"]:
            self.labels.add(label["name"])

        for user in data["assignees"]:
            self.assignees.add(user["login"])

        self.url = data["html_url"]
        self.repo_slug = re.match("^.*/([^/]+/[^/]+)$", data["repository_url"]).group(1)

    def __str__(self):
        """Debug string representation of issue"""
        res = ""
        res += f"RepoSlug: {self.repo_slug}\n"
        res += f"Title: {self.title} (#{self.number})\n"
        res += f"Body: {self.body}\n"
        res += f"Labels: {self.labels}\n"
        res += f"Assigned: {self.assignees}\n"
        return res

    def get_update_json(self):
        """Returns json to send to Github API to update labels, assignees"""
        res = {
            "assignees": list(self.assignees),
            "labels": list(self.labels),
        }
        return json.dumps(res)
