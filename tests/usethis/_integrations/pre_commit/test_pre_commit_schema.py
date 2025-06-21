import os
from pathlib import Path

import pytest


def test_multiple_per_repo():
    # There was a suspicion this wasn't possible, but it is.
    from usethis._integrations.pre_commit.schema import HookDefinition, LocalRepo

    LocalRepo(
        repo="local",
        hooks=[
            HookDefinition(id="black"),
            HookDefinition(id="isort"),
        ],
    )


class TestSchemaJSON:
    def test_matches_schema_store(self):
        import requests

        from usethis._test import is_offline

        if is_offline():
            pytest.skip("Cannot fetch JSON schema when offline")

        local_schema_json = (Path(__file__).parent / "schema.json").read_text()
        try:
            online_schema_json = requests.get(
                "https://json.schemastore.org/pre-commit-config.json", timeout=5
            ).text
        except requests.exceptions.ConnectionError as err:
            if os.getenv("CI"):
                pytest.skip(
                    "Failed to fetch JSON schema (connection issues); skipping test"
                )
            raise err

        # Compare the JSON
        # TIP: go into debug mode to copy-and-paste into updated schema.json
        assert local_schema_json == online_schema_json.replace("\r\n", "\n\n")

    def test_target_python_version(self):
        # If this test fails, we should bump the version in the command in schema.py
        assert Path(".python-version").read_text().startswith("3.10")
