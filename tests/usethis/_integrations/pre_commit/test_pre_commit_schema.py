import os
from pathlib import Path

import pytest
import requests

from usethis._integrations.pre_commit.schema import HookDefinition, LocalRepo
from usethis._test import is_offline


def test_multiple_per_repo():
    # There was a suspicion this wasn't possible, but it is.
    LocalRepo(
        repo="local",
        hooks=[
            HookDefinition(id="black"),
            HookDefinition(id="isort"),
        ],
    )


class TestSchemaJSON:
    def test_matches_schema_store(self):
        if is_offline():
            pytest.skip("Cannot fetch JSON schema when offline")

        local_schema_json = (Path(__file__).parent / "schema.json").read_text()
        online_schema_json = requests.get(
            "https://json.schemastore.org/pre-commit-config.json"
        ).text

        # Compare the JSON
        assert local_schema_json == online_schema_json.replace("\r\n", "\n\n")

    @pytest.mark.skipif(
        bool(os.getenv("CI")),
        reason=".python-version re-pinned in CI for test matrix",
    )
    def test_target_python_version(self):
        # If this test fails, we should bump the version in the command in schema.py
        assert Path(".python-version").read_text().startswith("3.10")
