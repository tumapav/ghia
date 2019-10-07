import requests
import click
import json
import re


class Issue:

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
        self.number = data["number"]
        self.title = data["title"]
        self.body = data["body"]

        for label in data["labels"]:
            self.labels.add(label["name"])

        for user in data["assignees"]:
            self.assignees.add(user["login"])

        self.url = data["url"]
        self.repo_slug = re.match("^.*/([^/]+/[^/]+)$", data["repository_url"]).group(1)

    def __str__(self):
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


class GhiaRequests:
    CONFIG_VALIDATION_ERR = "incorrect configuration format"

    def __init__(self, token, slug):
        self.token = token
        self.slug = slug

        # Init the requests Session
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'GHIA-Python v0.1'}
        self.session.auth = self.token_auth

    def token_auth(self, req):
        req.headers['Authorization'] = f'token {self.token}'
        return req

    def get_issues(self):
        r = self.session.get(f'https://api.github.com/repos/{self.slug}/issues')
        raw_issues = r.json()

        issues = []
        for raw_issue in raw_issues:
            issue = Issue(raw_issue)
            issues.append(issue)
            print(issue)
        return issues

    def update_issue(self, issue):
        data = issue.get_update_json()
        r = self.session.patch(f'https://api.github.com/repos/{self.slug}/issues/{issue.number}', data)
        raw_issue = r.json()
        #print(raw_issue)
        issue = Issue(raw_issue)
        return issue


