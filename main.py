import os
from datetime import datetime
from time import sleep

from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from pydantic import BaseModel, ValidationError
import click
from pathlib import Path
import pandas as pd

QUERY_WAIT = 3  # [s]


class Milestone(BaseModel):
    name: str
    begin: datetime
    end: datetime


class Team(BaseModel):
    slug: str
    repo_path: str


class InputData(BaseModel):
    milestone: Milestone
    teams: list[Team]


class Api:
    def __init__(self, token):
        self.token = token

        self._transport = RequestsHTTPTransport(
            url="https://api.github.com/graphql",
            verify=True,
            retries=3,
            headers={"Authorization": f"bearer {self.token}"},
        )
        self._client = Client(transport=self._transport,
                              fetch_schema_from_transport=True)

        self.rate_limiting: dict | None = None

    def get_team_info(self, org_name: str, team_slug: str):
        """Get team information."""
        query = gql(
            """
            query($orgName: String!, $teamSlug: String!) {
                organization(login: $orgName) {
                    team(slug: $teamSlug) {
                        id
                        members {
                            nodes {
                                login
                                name
                                id
                                url
                            }
                        }
                    }
                }
                rateLimit {
                    limit
                    cost
                    remaining
                    resetAt
                }
            }
            """
        )

        params = {"orgName": org_name, "teamSlug": team_slug}

        result: dict = self._client.execute(query, variable_values=params)
        members = result["organization"]["team"]["members"]["nodes"]
        self.rate_limiting = result["rateLimit"]
        return members

    def get_commits_during_timeperiod(self, repo_path: str, since: str, until: str):
        """Get commits of a user during the time period."""
        tokens = repo_path.split("/")
        if len(tokens) != 2:
            raise ValueError("expect the repo_path to be in a format of 'ower/repo_name'")
        repo_owner = tokens[0]
        repo_name = tokens[1]

        query = gql(
            """
            query ($repoOwner: String!, $repoName: String!, $since: GitTimestamp!, $until: GitTimestamp!) {
                repository(owner: $repoOwner, name: $repoName) {
                    defaultBranchRef {
                        target {
                            ... on Commit {
                                history(since: $since, until: $until) {
                                    edges {
                                        node {
                                            ... on Commit {
                                                committedDate
                                            }
                                            author {
                                                name
                                                user {
                                                    login
                                                    id
                                                }
                                                email
                                            }
                                            commitUrl
                                            committedViaWeb
                                            messageHeadline
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                rateLimit {
                    limit
                    cost
                    remaining
                    resetAt
                }
            }
            """
        )

        params = {
            "repoOwner": repo_owner,
            "repoName": repo_name,
            "since": since,
            "until": until
        }

        result: dict = self._client.execute(query, variable_values=params)
        raw_commits = result["repository"]["defaultBranchRef"]["target"]["history"]["edges"]
        self.rate_limiting = result["rateLimit"]

        commits = []
        for raw_commit in raw_commits:
            commit = dict()
            raw_commit = raw_commit["node"]
            
            commit["committedDate"] = raw_commit["committedDate"]
            if raw_commit["author"]["user"] is None:
                name = raw_commit["author"]["name"]
                email = raw_commit["author"]["email"]
                commit["login"] = f"{name} ({email})"
            else:
                commit["login"] = raw_commit["author"]["user"]["login"]
            commits.append(commit)
        
        return commits


def filter_team_members(ta_logins: list[str], members: list[dict]):
    return [member for member in members if not (member["login"] in ta_logins)]


def filter_commits(commits):
    """Does not filter yet."""
    return commits


@click.command()
@click.argument("input-file-path", type=click.Path("r"))
def main(input_file_path: str | Path):
    token = os.environ["GH_TOKEN"]

    try:
        input_data = InputData.parse_file(input_file_path)
    except ValidationError as e:
        print(e)
        click.fail()

    api = Api(token)

    for team in input_data.teams:
        commits = api.get_commits_during_timeperiod(
            team.repo_path, input_data.milestone.begin.isoformat(), input_data.milestone.end.isoformat())
        # idx = pd.date_range(input_data.milestone.begin, input_data.milestone.end)
        df = pd.DataFrame(data=commits)
        df["committedDate"] = pd.to_datetime(df["committedDate"]).dt.floor("d")
        df = df.groupby(by=["login", "committedDate"]).size()
        print(team.slug)
        print(df, end="\n\n")

        sleep(QUERY_WAIT)


if __name__ == "__main__":
    load_dotenv()
    main()
