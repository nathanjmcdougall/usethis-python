import pytest
import requests

from usethis._integrations.github.tags import (
    GitHubTagError,
    NoGitHubTagsFoundError,
    get_github_latest_tag,
)


class TestGetGitHubLatestTag:
    def test_mock(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            class MockResponse:
                def json(self):
                    return [{"name": "v1.0.0"}]

                def raise_for_status(self):
                    pass

            return MockResponse()

        monkeypatch.setattr("requests.get", mock_get)

        assert get_github_latest_tag(owner="foo", repo="bar") == "v1.0.0"

    def test_http_error(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            class MockResponse:
                def raise_for_status(self):
                    raise requests.exceptions.HTTPError("Failed to fetch tags")

            return MockResponse()

        monkeypatch.setattr("requests.get", mock_get)

        with pytest.raises(GitHubTagError, match="Failed to fetch tags"):
            get_github_latest_tag(owner="foo", repo="bar")

    def test_no_tags(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            class MockResponse:
                def json(self):
                    return []

                def raise_for_status(self):
                    pass

            return MockResponse()

        monkeypatch.setattr("requests.get", mock_get)

        with pytest.raises(NoGitHubTagsFoundError):
            get_github_latest_tag(owner="foo", repo="bar")