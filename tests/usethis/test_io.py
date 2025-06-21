from pathlib import Path


class TestUsethisFileManager:
    class TestContent:
        def test_setter(self, tmp_path: Path) -> None:
            # Arrange
            from usethis._io import UsethisFileManager
            from usethis._test import change_cwd

            class MyUsethisFileManager(UsethisFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path):
                manager = MyUsethisFileManager()

            # Act
            manager._content = 42

            # Assert
            assert manager._content == 42

    class TestEq:
        def test_example(self) -> None:
            # Arrange
            from usethis._io import UsethisFileManager

            class MyUsethisFileManager(UsethisFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            manager = MyUsethisFileManager()
            other_manager = MyUsethisFileManager()

            # Act
            result = manager == other_manager

            # Assert
            assert result is True

        def test_different_type(self) -> None:
            # Arrange
            from usethis._io import UsethisFileManager

            class MyUsethisFileManager(UsethisFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            manager = MyUsethisFileManager()
            other_manager = object()

            # Act
            result = manager == other_manager

            # Assert
            assert result is False

    class TestRepr:
        def test_example(self, tmp_path: Path) -> None:
            # Arrange
            from usethis._io import UsethisFileManager
            from usethis._test import change_cwd

            class MyUsethisFileManager(UsethisFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path):
                manager = MyUsethisFileManager()

            # Act
            repr_str = repr(manager)

            # Assert
            assert repr_str == "MyUsethisFileManager('pyproject.toml')"
