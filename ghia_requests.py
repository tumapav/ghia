import requests
import click
from ghia_issue import Issue


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

    def get_issues(self, issues=[], url=None):
        r = self.session.get(f'https://api.github.com/repos/{self.slug}/issues' if url is None else url)

        if r.status_code != 200:
            click.secho("ERROR", fg="red", bold=True, nl=False, err=True)
            click.echo(f": Could not list issues for repository {self.slug}", err=True)
            exit(10)

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
        r = self.session.patch(f'https://api.github.com/repos/{self.slug}/issues/{issue.number}', data)
        if r.status_code != 200:
            click.secho("   ERROR", fg="red", bold=True, nl=False, err=True)
            click.echo(f": Could not update issue {self.slug}#{issue.number}", err=True)
            return



