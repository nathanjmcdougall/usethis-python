import os
from pathlib import Path

import pytest
import requests

from usethis._integrations.ci.bitbucket.schema import Script, Step, Step2, StepBase
from usethis._test import is_offline


class TestStep2:
    def test_shared_parent(self):
        assert isinstance(Step2(script=Script(["hi"])), StepBase)
        assert isinstance(Step(script=Script(["hi"])), StepBase)

    def test_field_subset(self):
        assert set(Step2.model_fields.keys()) == set(Step.model_fields.keys())


class TestSchemaJSON:
    def test_matches_schema_store(self):
        if is_offline():
            pytest.skip("Cannot fetch JSON schema when offline")

        local_schema_json = (Path(__file__).parent / "schema.json").read_text()
        try:
            online_schema_json = requests.get(
                "https://api.bitbucket.org/schemas/pipelines-configuration", timeout=5
            ).text
        except requests.exceptions.ConnectionError as err:
            if os.getenv("CI"):
                pytest.skip(
                    "Failed to fetch JSON schema (connection issues); skipping test"
                )
            raise err

        # Compare the JSON
        # TIP: go into debug mode to copy-and-paste into updated schema.json
        assert local_schema_json == online_schema_json

    def test_target_python_version(self, usethis_dev_dir: Path):
        # If this test fails, we should bump the version in the command in schema.py
        assert (usethis_dev_dir / ".python-version").read_text().startswith("3.10")
