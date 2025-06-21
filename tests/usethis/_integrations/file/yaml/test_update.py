from pathlib import Path


class TestUpdateRuamelYamlMap:
    def test_no_change(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedMap

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("""\
hello: world # comment
""")

        # Act
        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedMap)  # Help pyright
            update_ruamel_yaml_map(
                yaml_document.content,
                {"hello": "world"},
                preserve_comments=True,
            )

        # Assert
        assert (
            path.read_text()
            == """\
hello: world # comment
"""
        )

    def test_map(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedMap

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("""\
hello: world # comment
""")

        # Act
        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedMap)  # Help pyright
            update_ruamel_yaml_map(
                yaml_document.content,
                {"hello": "universe"},
                preserve_comments=True,
            )

        # Assert
        assert (
            path.read_text()
            == """\
hello: universe # comment
"""
        )

    def test_list(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedMap

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("""\
key:
    - 1 # comment
    - 2
    - 3 # another comment
""")

        # Act
        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedMap)  # Help pyright
            update_ruamel_yaml_map(
                yaml_document.content,
                {"key": [1, 2, 4]},
                preserve_comments=True,
            )

        # Assert
        assert (
            path.read_text()
            == """\
key:
    - 1 # comment
    - 2
    - 4 # another comment
"""
        )

    def test_remove_key(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedMap

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("""\
key: value
other: value
""")

        # Act
        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedMap)  # Help pyright
            update_ruamel_yaml_map(
                yaml_document.content,
                {"key": "new value"},
                preserve_comments=True,
            )

        # Assert
        assert (
            path.read_text()
            == """\
key: new value
"""
        )

    def test_nested_map(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedMap

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("""\
key: # comment1
    hello: world # comment2
this: willberemoved                  
""")

        # Act
        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedMap)  # Help pyright
            update_ruamel_yaml_map(
                yaml_document.content,
                {"key": {"hello": "universe"}, "banana": "yummy"},
                preserve_comments=True,
            )

        # Assert
        assert (
            path.read_text()
            == """\
key: # comment1
    hello: universe # comment2
banana: yummy
"""
        )

    def test_reuse_ref(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedMap

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("""\
key:
    - 1 # comment
    - 2
    - 3 # another comment
""")
        another_path = tmp_path / "another.yaml"
        another_path.write_text("""\
hello: 4 # yet another
""")
        with edit_yaml(another_path) as yaml_document:
            another_yaml_doc = yaml_document

        # Act
        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedMap)  # Help pyright
            assert isinstance(another_yaml_doc.content, CommentedMap)  # Help pyright
            update_ruamel_yaml_map(
                yaml_document.content,
                {"key": [1, another_yaml_doc.content, another_yaml_doc.content.copy()]},
                preserve_comments=True,
            )

        # Assert
        assert (
            path.read_text()
            == """\
key:
    - 1 # comment
    - hello: 4 # yet another
    -   # another comment
      hello: 4 # yet another
"""
        )

    def test_remove_list_element(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedMap

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("""\
key:
    - 1 # comment
    - 2
    - 3 # another comment
""")

        # Act
        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedMap)

            update_ruamel_yaml_map(
                yaml_document.content,
                {"key": [1, 3]},
                preserve_comments=True,
            )

        # Assert
        assert (
            path.read_text()
            == """\
key:
    - 1 # comment
    - 3 # another comment
"""
        )

    def test_remove_nested_list(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedMap

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("""\
key:
    - lookup: 1
      value: 2
    - lookup: 3
      value: 4
""")
        # Act
        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedMap)

            update_ruamel_yaml_map(
                yaml_document.content,
                {"key": [{"lookup": 1, "value": 2}]},
                preserve_comments=True,
            )

        # Assert
        assert (
            path.read_text()
            == """\
key:
    - lookup: 1
      value: 2
"""
        )

    def test_anchor_with_ref(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedMap

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("""\
key: &anchor
    - 1
    - 2
""")
        # Act
        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedMap)

            update_ruamel_yaml_map(
                yaml_document.content,
                {
                    "key": yaml_document.content["key"],
                    "new_key": yaml_document.content["key"],
                },
                preserve_comments=True,
            )

        # Assert
        assert (
            path.read_text()
            == """\
key: &anchor
    - 1
    - 2
new_key: *anchor
"""
        )

    def test_anchor_without_ref(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedMap, CommentedSeq

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("""\
key:
    - 1
    - 2
""")
        # Act
        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedMap)

            key = yaml_document.content["key"]
            assert isinstance(key, CommentedSeq)

            update_ruamel_yaml_map(
                yaml_document.content,
                {
                    "key": key,
                    "new_key": key,
                },
                preserve_comments=True,
            )
            key.yaml_set_anchor("banana")

        # Assert
        assert (
            path.read_text()
            == """\
key: &banana
    - 1
    - 2
new_key: *banana
"""
        )

    def test_new_anchor(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedSeq

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import update_ruamel_yaml_map

        path = tmp_path / "test.yaml"
        path.write_text("{}")

        # Act
        with edit_yaml(path, guess_indent=False) as yaml_document:
            key = CommentedSeq([1, 2])

            update_ruamel_yaml_map(
                yaml_document.content,
                {
                    "key": key,
                    "new_key": key,
                },
                preserve_comments=True,
            )
            key.yaml_set_anchor("banana")

        # Assert
        assert (
            path.read_text()
            == """\
key: &banana
  - 1
  - 2
new_key: *banana
"""
        )


class TestLCSListUpdate:
    def test_identical(self):
        # Arrange

        from usethis._integrations.file.yaml.update import lcs_list_update

        x = [1, 2, 3, 4]
        new = [1, 2, 3, 4]

        # Act
        lcs_list_update(x, new)

        # Assert
        assert x == [1, 2, 3, 4]

    def test_addition(self):
        # Arrange
        from usethis._integrations.file.yaml.update import lcs_list_update

        x = [1, 2, 3, 4]
        new = [1, 2, 3, 4, 5]

        # Act
        lcs_list_update(x, new)

        # Assert
        assert x == [1, 2, 3, 4, 5]

    def test_deletion(self):
        # Arrange
        from usethis._integrations.file.yaml.update import lcs_list_update

        x = [1, 2, 3, 4]
        new = [1, 2, 4]

        # Act
        lcs_list_update(x, new)

        # Assert
        assert x == [1, 2, 4]

    def test_ruamel_yaml_file(self, tmp_path: Path):
        # Arrange
        from ruamel.yaml.comments import CommentedSeq

        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._integrations.file.yaml.update import lcs_list_update

        path = tmp_path / "test.yaml"
        path.write_text("""\
- 1 # comment
- 2
- 3 # another comment
""")

        with edit_yaml(path) as yaml_document:
            assert isinstance(yaml_document.content, CommentedSeq)  # Help pyright
            # Act
            lcs_list_update(yaml_document.content, [1, 2, 4])

        # Assert
        assert (
            path.read_text()
            == """\
- 1 # comment
- 2
- 4 # another comment
"""
        )
