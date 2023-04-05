import os

from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


def get_team_info(org_name: str, team_slug: str):
    """Get team information."""
    transport = RequestsHTTPTransport(
        url="https://api.github.com/graphql",
        verify=True,
        retries=3,
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}"},
    )

    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Provide a GraphQL query
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

    result: dict = client.execute(query, variable_values=params)
    members = result["organization"]["team"]["members"]["nodes"]
    rate_limiting = result["rateLimit"]
    return members, rate_limiting


def get_commits_during_timeperiod(
    name: str, owner: str, since: str, until: str, uid: str
):
    """Get commits of a user during the time period."""
    transport = RequestsHTTPTransport(
        url="https://api.github.com/graphql",
        verify=True,
        retries=3,
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}"},
    )

    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Provide a GraphQL query
    query = gql(
        """
query ($name: String!, $owner: String!, $since: GitTimestamp!, $until: GitTimestamp!, $uid: ID) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      name
      target {
        ... on Commit {
          history(author: {id: $uid}, since: $since, until: $until) {
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
            totalCount
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
        "name": name,
        "owner": owner,
        "since": since,
        "until": until,
        "uid": uid,
    }

    result: dict = client.execute(query, variable_values=params)
    commits = result["repository"]["defaultBranchRef"]["target"]["history"]["edges"]
    total_commit_count = result["repository"]["defaultBranchRef"]["target"]["history"][
        "totalCount"
    ]
    rate_limiting = result["rateLimit"]
    return commits, total_commit_count, rate_limiting


if __name__ == "__main__":
    load_dotenv()

    members = get_team_info("OU-CS3560", "team-name")
    print(members)

    commits = get_commits_during_timeperiod(
        "team-name",
        "OU-CS3560",
        "2023-03-19T00:00:00+00:00",
        "2023-04-04T23:59:00+00:00",
        "uid",
    )
    print(commits)
