import requests
import click
from .ghia_issue import Issue


class GhiaRequests:
    CONFIG_VALIDATION_ERR = "incorrect configuration format"
    HTTP_OK = 200
    EXIT_CODE_ISSUES_NA = 10

    def __init__(self, token, slug=None):
        self.token = token
        self.slug = slug

        # Init the requests Session
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'GHIA-Python v0.1'}
        self.session.auth = self.token_auth

    def token_auth(self, req):
        req.headers['Authorization'] = f'token {self.token}'
        return req

    def get_user(self):
        success = True
        try:
            r = self.session.get(f'https://api.github.com/user')
        except requests.exceptions.RequestException:
            success = False

        if not success or r.status_code != self.HTTP_OK:
            raise RuntimeError("Could not fetch Github user identity.")

        user_data = r.json()
        return user_data

    def get_issues(self, issues=[], url=None):
        success = True
        try:
            r = self.session.get(f'https://api.github.com/repos/{self.slug}/issues' if url is None else url)
        except requests.exceptions.RequestException:
            success = False

        if not success or r.status_code != self.HTTP_OK:
            click.secho("ERROR", fg="red", bold=True, nl=False, err=True)
            click.echo(f": Could not list issues for repository {self.slug}", err=True)
            exit(self.EXIT_CODE_ISSUES_NA)

        raw_issues = r.json()
        for raw_issue in raw_issues:
            if raw_issue["state"] == "closed":
                continue
            issue = Issue(raw_issue)
            issues.append(issue)

        if "next" in r.links:
            url = r.links["next"]["url"]
            return self.get_issues(issues, url)
        else:
            return issues

    def update_issue(self, issue):
        data = issue.get_update_json()
        success = True
        try:
            r = self.session.patch(f'https://api.github.com/repos/{self.slug}/issues/{issue.number}', data)
        except requests.exceptions.RequestException:
            success = False

        if not success or r.status_code != self.HTTP_OK:
            click.secho("   ERROR", fg="red", bold=True, nl=False, err=True)
            click.echo(f": Could not update issue {self.slug}#{issue.number}", err=True)
            return None

        raw_issue = r.json()
        return Issue(raw_issue)

