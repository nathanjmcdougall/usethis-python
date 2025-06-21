from collections import OrderedDict
from pathlib import Path

import pytest


class TestEditYaml:
    class TestLiterals:
        """The list of literals is from ruamel/yaml/representer.py near the bottom"""

        def test_none(self, tmp_path: Path):
            # Arrange

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("hello: null")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == {"hello": None}

        def test_str(self, tmp_path: Path):
            # Arrange

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("hello")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == "hello"
                assert type(content) is str

        def test_literal_scalar_string(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.comments import CommentedMap
            from ruamel.yaml.scalarstring import LiteralScalarString

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("""\
hello: |
    world
""")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == {"hello": "world\n"}
                assert isinstance(content, CommentedMap)
                assert type(content["hello"]) is LiteralScalarString

        def test_folded_scalar_string(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.comments import CommentedMap
            from ruamel.yaml.scalarstring import FoldedScalarString

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("""\
hello: >
    world
""")
            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == {"hello": "world\n"}
                assert isinstance(content, CommentedMap)
                assert type(content["hello"]) is FoldedScalarString

        def test_int(self, tmp_path: Path):
            # Arrange

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("3")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == 3
                assert type(content) is int

        def test_float(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.scalarfloat import ScalarFloat

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("3.14")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == 3.14
                assert type(content) is ScalarFloat

        def test_scientific_notation(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.scalarfloat import ScalarFloat

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("3.14e-2")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == 3.14e-2
                assert type(content) is ScalarFloat

        def test_hex(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.scalarint import HexInt

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("0x3")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == 3
                assert type(content) is HexInt

        def test_hex_caps(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.scalarint import HexCapsInt

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("0xE")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == 14
                assert type(content) is HexCapsInt

        def test_octal(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.scalarint import OctalInt

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("0o3")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == 3
                assert type(content) is OctalInt

        def test_binary(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.scalarint import BinaryInt

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("0b11")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == 3
                assert type(content) is BinaryInt

        def test_scalar_int(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.scalarint import ScalarInt

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("&anchor 3")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == 3
                assert type(content) is ScalarInt

        def test_bool(self, tmp_path: Path):
            # Arrange

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("true")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content is True
                assert type(content) is bool

        def test_scalar_bool(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.scalarbool import ScalarBoolean

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("&anchor true")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content
                assert type(content) is ScalarBoolean

        def test_commented_seq(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.comments import CommentedSeq

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("""\
- one
- two
""")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == ["one", "two"]
                assert type(content) is CommentedSeq

        def test_commented_set(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.comments import CommentedSet

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("""\
!!set
  ? one
  ? two
""")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == {"one", "two"}
                assert type(content) is CommentedSet

        def test_commented_map(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.comments import CommentedMap

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("""\
hello: world
""")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == {"hello": "world"}
                assert type(content) is CommentedMap

        def test_commented_ordered_map(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.comments import CommentedOrderedMap

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("""\
!!omap
- hello: world
""")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert content == OrderedDict([("hello", "world")])
                assert type(content) is CommentedOrderedMap

        def test_tagged_scalar(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.comments import TaggedScalar

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("""\
!!custom 3
""")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert type(content) is TaggedScalar

        def test_time_stamp(self, tmp_path: Path):
            # Arrange
            from ruamel.yaml.timestamp import TimeStamp

            from usethis._integrations.file.yaml.io_ import edit_yaml

            path = tmp_path / "test.yaml"
            path.write_text("2001-12-15T02:59:43.1Z")

            with edit_yaml(path) as yaml_document:  # Act
                content = yaml_document.content
                # Assert
                assert type(content) is TimeStamp

    class TestRoundTrip:
        @pytest.mark.xfail(
            reason="Not providing this guarantee yet. ruamel.yaml isn't easily able to cope with perfect round-tripping"
        )
        def test_single_quote_preserved(self, tmp_path: Path):
            # Arrange

            from usethis._integrations.file.yaml.io_ import edit_yaml
            from usethis._test import change_cwd

            path = tmp_path / "x.yml"
            path.write_text(
                """\
x: 'hi'
"""
            )

            # Act
            with change_cwd(tmp_path), edit_yaml(path) as _:
                pass

            # Assert
            contents = path.read_text()
            assert (
                contents
                == """\
x: 'hi'
"""
            )

        @pytest.mark.xfail(
            reason="Not providing this guarantee yet. ruamel.yaml isn't easily able to cope with perfect round-tripping"
        )
        def test_single_quoted_preserved(self, tmp_path: Path):
            # Arrange

            from usethis._integrations.file.yaml.io_ import edit_yaml
            from usethis._test import change_cwd

            path = tmp_path / "x.yml"
            path.write_text(
                """\
x: 'hi'
"""
            )

            # Act
            with change_cwd(tmp_path), edit_yaml(path) as _:
                pass

            # Assert
            contents = path.read_text()
            assert (
                contents
                == """\
x: 'hi'
"""
            )

        def test_unquoted_preserved(self, tmp_path: Path):
            # Arrange

            from usethis._integrations.file.yaml.io_ import edit_yaml
            from usethis._test import change_cwd

            path = tmp_path / "x.yml"
            path.write_text(
                """\
x: hi
"""
            )

            # Act
            with change_cwd(tmp_path), edit_yaml(path) as _:
                pass

            # Assert
            contents = path.read_text()
            assert (
                contents
                == """\
x: hi
"""
            )

        def test_indentation_5_3(self, tmp_path: Path):
            # Arrange

            from usethis._integrations.file.yaml.io_ import edit_yaml
            from usethis._test import change_cwd

            path = tmp_path / "x.yml"
            path.write_text(
                """\
x:
  -  y:
     z:
       -  w
"""
            )

            # Act
            with change_cwd(tmp_path), edit_yaml(path) as _:
                pass

            # Assert
            contents = path.read_text()
            assert (
                contents
                == """\
x:
  -  y:
     z:
       -  w
"""
            )

    def test_no_guess_indent(self, tmp_path: Path):
        # Arrange

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._test import change_cwd

        path = tmp_path / "x.yml"
        path.write_text(
            """\
x:
-    y:
     z:
     -    w
"""
        )

        # Act
        with change_cwd(tmp_path), edit_yaml(path, guess_indent=False) as _:
            pass

        # Assert
        contents = path.read_text()
        assert (
            contents
            == """\
x:
  - y:
    z:
      - w
"""
        )

    def test_invalid_indentation(self, tmp_path: Path):
        # Arrange

        from usethis._integrations.file.yaml.errors import InvalidYAMLError
        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._test import change_cwd

        (tmp_path / "x.yml").write_text(
            """\
repos:
  - repo: local
        hooks:
          - id: placeholder
"""
        )

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pytest.raises(InvalidYAMLError),
            edit_yaml(tmp_path / "x.yml") as _,
        ):
            pass

    def test_incorrect_indentation(self, tmp_path: Path, capfd: pytest.CaptureFixture):
        # Arrange

        from usethis._integrations.file.yaml.errors import InvalidYAMLError
        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._test import change_cwd

        (tmp_path / "x.yml").write_text("""\
- path: / 
    backend: 
      serviceName: <service_name> 
      servicePort: <port> 
""")

        # Act
        with (
            change_cwd(tmp_path),
            pytest.raises(
                InvalidYAMLError, match=r"mapping values are not allowed here"
            ),
            edit_yaml(tmp_path / "x.yml"),
        ):
            pass

        # Assert
        # Should have a hint
        out, err = capfd.readouterr()
        assert "Hint: You may have incorrect indentation the YAML file." in out
        assert not err
