import requests


class GitHubTagError(Exception):
    """Custom exception for GitHub tag-related errors."""


class NoGitHubTagsFoundError(GitHubTagError):
    """Custom exception raised when no tags are found."""


def get_github_latest_tag(owner: str, repo: str) -> str:
    """Get the name of the most recent tag on the default branch of a GitHub repository.

    Args:
        owner: GitHub repository owner (username or organization).
        repo: GitHub repository name.

    Returns:
        The name of most recent tag of the repository.

    Raises:
        GitHubTagError: If there's an issue fetching the tags from the GitHub API.
        NoTagsFoundError: If the repository has no tags.
    """

    # GitHub API URL for repository tags
    api_url = f"https://api.github.com/repos/{owner}/{repo}/tags"

    # Fetch the tags using the GitHub API
    try:
        response = requests.get(api_url, timeout=1)
        response.raise_for_status()  # Raise an error for HTTP issues
    except requests.exceptions.HTTPError as err:
        raise GitHubTagError(f"Failed to fetch tags from GitHub API: {err}")

    tags = response.json()

    if not tags:
        raise NoGitHubTagsFoundError(f"No tags found for repository '{owner}/{repo}'")

    # Most recent tag's name
    return tags[0]["name"]