from pathlib import Path

import pytest


class TestAddRepo:
    def test_unregistered_id(self, tmp_path: Path):
        from usethis._integrations.pre_commit.hooks import add_repo
        from usethis._integrations.pre_commit.schema import HookDefinition, UriRepo
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text("""\
repos:
  - repo: foo
    hooks:
    - id: bar
""")
        with (
            change_cwd(tmp_path),
            pytest.raises(NotImplementedError, match="Hook 'foo' not recognized"),
        ):
            add_repo(
                UriRepo(
                    repo="foo", rev="foo", hooks=[HookDefinition(id="foo", name="foo")]
                )
            )

    def test_adding_to_existing(
        self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        from usethis._integrations.pre_commit.hooks import add_repo
        from usethis._integrations.pre_commit.schema import (
            HookDefinition,
            Language,
            LocalRepo,
        )
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text("""\
repos:
  - repo: foo
    hooks:
    - id: bar
""")

        # Act
        with change_cwd(tmp_path):
            add_repo(
                LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="deptry",
                            name="deptry",
                            entry="uv run --frozen deptry src",
                            language=Language("system"),
                            always_run=True,
                        )
                    ],
                )
            )

        # Assert
        assert (
            (tmp_path / ".pre-commit-config.yaml").read_text()
            == """\
repos:
  - repo: foo
    hooks:
      - id: bar
  - repo: local
    hooks:
      - id: deptry
        name: deptry
        always_run: true
        entry: uv run --frozen deptry src
        language: system
"""
        )
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Adding hook 'deptry' to '.pre-commit-config.yaml'.\n"

    def test_placeholder(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.pre_commit.hooks import (
            _get_placeholder_repo_config,
            add_repo,
        )
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path):
            add_repo(_get_placeholder_repo_config())

        # Assert
        assert (
            (tmp_path / ".pre-commit-config.yaml").read_text()
            == """\
repos:
  - repo: local
    hooks:
      - id: placeholder
        name: Placeholder - add your own hooks!
        entry: uv run --isolated --frozen --offline python -c "print('hello world!')"
        language: system
"""
        )
        out, err = capfd.readouterr()
        assert not err
        assert out == (
            "✔ Writing '.pre-commit-config.yaml'.\n"
            "✔ Adding placeholder hook to '.pre-commit-config.yaml'.\n"
        )

    def test_hook_order_constant_is_respected(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pre_commit.hooks import add_repo, get_hook_ids
        from usethis._integrations.pre_commit.schema import (
            HookDefinition,
            Language,
            LocalRepo,
        )
        from usethis._test import change_cwd

        with change_cwd(tmp_path):
            # Add 'codespell' first (later in _HOOK_ORDER)
            add_repo(
                LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="codespell",
                            name="codespell",
                            entry="codespell .",
                            language=Language("system"),
                        )
                    ],
                )
            )

            # Now add 'pyproject-fmt' (earlier in _HOOK_ORDER)
            add_repo(
                LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="pyproject-fmt",
                            name="pyproject-fmt",
                            entry="uv run --frozen pyproject-fmt .",
                            language=Language("system"),
                        )
                    ],
                )
            )

            # Assert: pyproject-fmt should appear before codespell
            assert get_hook_ids() == [
                "pyproject-fmt",
                "codespell",
            ]

    def test_hooks_added_in_standard_order(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pre_commit.hooks import add_repo, get_hook_ids
        from usethis._integrations.pre_commit.schema import (
            HookDefinition,
            Language,
            LocalRepo,
        )
        from usethis._test import change_cwd

        with change_cwd(tmp_path):
            add_repo(
                LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="pyproject-fmt",
                            name="pyproject-fmt",
                            entry="uv run --frozen pyproject-fmt .",
                            language=Language("system"),
                        )
                    ],
                )
            )

            # Act
            add_repo(
                LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="codespell",
                            name="codespell",
                            entry="codespell .",
                            language=Language("system"),
                        )
                    ],
                )
            )
            # Assert
            assert get_hook_ids() == [
                "pyproject-fmt",
                "codespell",
            ]

    def test_hook_order_constant_is_respected_multi(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pre_commit.hooks import add_repo, get_hook_ids
        from usethis._integrations.pre_commit.schema import (
            HookDefinition,
            Language,
            LocalRepo,
        )
        from usethis._test import change_cwd

        with change_cwd(tmp_path):
            # Act
            add_repo(
                LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="foo",
                            name="foo",
                            entry="foo .",
                            language=Language("system"),
                        )
                    ],
                ),
            )
            add_repo(
                LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="codespell",
                            name="codespell",
                            entry="codespell .",
                            language=Language("system"),
                        )
                    ],
                )
            )
            add_repo(
                LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="pyproject-fmt",
                            name="pyproject-fmt",
                            entry="uv run --frozen pyproject-fmt .",
                            language=Language("system"),
                        )
                    ],
                )
            )

            # Assert
            assert get_hook_ids() == [
                "foo",
                "pyproject-fmt",
                "codespell",
            ]


class TestInsertRepo:
    def test_predecessor_is_none(
        self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        from usethis._integrations.pre_commit.hooks import insert_repo
        from usethis._integrations.pre_commit.io_ import edit_pre_commit_config_yaml
        from usethis._integrations.pre_commit.schema import (
            HookDefinition,
            Language,
            LocalRepo,
        )
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text("""\
repos:
    - repo: codespell
      hooks:
      - id: codespell
""")

        # Act
        with change_cwd(tmp_path), edit_pre_commit_config_yaml() as doc:
            repos = insert_repo(
                repo_to_insert=LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="pyproject-fmt",
                            name="pyproject-fmt",
                            entry="uv run --frozen pyproject-fmt .",
                            language=Language("system"),
                        )
                    ],
                ),
                existing_repos=doc.model.repos,
                predecessor=None,
            )

        # Assert
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Adding hook 'pyproject-fmt' to '.pre-commit-config.yaml'.\n"
        assert isinstance(repos, list)
        assert len(repos) == 2
        assert [repo.repo for repo in repos] == ["local", "codespell"]

    def test_existing_repo_has_none_hooks(self):
        # Arrange
        from usethis._integrations.pre_commit.hooks import insert_repo
        from usethis._integrations.pre_commit.schema import (
            HookDefinition,
            Language,
            LocalRepo,
        )

        existing_repos = [LocalRepo(repo="local", hooks=None)]
        new_hook = HookDefinition(
            id="new-hook",
            name="New Hook",
            entry="echo 'New hook'",
            language=Language("system"),
        )
        repo_to_insert = LocalRepo(
            repo="local",
            hooks=[new_hook],
        )

        # Act
        results = insert_repo(
            repo_to_insert=repo_to_insert,
            existing_repos=existing_repos,
            predecessor=None,
        )

        # Assert
        assert isinstance(results, list)
        assert len(results) == 2
        assert results == [
            LocalRepo(repo="local", hooks=[new_hook]),
            LocalRepo(repo="local", hooks=None),
        ]

    def test_duplicate_predecessor(
        self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
    ):
        # What if the predecessor ID is repeated multiple times? Will we end up
        # inserting the new repo multiple times? No.
        # Arrange
        from usethis._integrations.pre_commit.hooks import insert_repo
        from usethis._integrations.pre_commit.io_ import edit_pre_commit_config_yaml
        from usethis._integrations.pre_commit.schema import (
            HookDefinition,
            Language,
            LocalRepo,
        )
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text("""\
repos:
  - repo: foo
    hooks:
    - id: bar
  - repo: foo
    hooks:
    - id: bar
""")

        # Act
        with change_cwd(tmp_path), edit_pre_commit_config_yaml() as doc:
            repos = insert_repo(
                repo_to_insert=LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="pyproject-fmt",
                            name="pyproject-fmt",
                            entry="uv run --frozen pyproject-fmt .",
                            language=Language("system"),
                        )
                    ],
                ),
                existing_repos=doc.model.repos,
                predecessor="bar",
            )

        # Assert
        assert isinstance(repos, list)
        assert len(repos) == 3
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Adding hook 'pyproject-fmt' to '.pre-commit-config.yaml'.\n"


class TestRemoveHook:
    def test_empty(self, tmp_path: Path):
        from usethis._integrations.pre_commit.hooks import remove_hook
        from usethis._test import change_cwd

        with change_cwd(tmp_path):
            remove_hook("foo")
        assert (
            (tmp_path / ".pre-commit-config.yaml").read_text()
            == """\
repos:
  - repo: local
    hooks:
      - id: placeholder
        name: Placeholder - add your own hooks!
        entry: uv run --isolated --frozen --offline python -c "print('hello world!')"
        language: system
"""
        )

    def test_single(self, tmp_path: Path):
        from usethis._integrations.pre_commit.hooks import remove_hook
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text(
            """\
repos:
  - repo: foo
    hooks:    
    - id: bar
"""
        )
        with change_cwd(tmp_path):
            remove_hook("bar")
        assert (
            (tmp_path / ".pre-commit-config.yaml").read_text()
            == """\
repos:
  - repo: local
    hooks:
      - id: placeholder
        name: Placeholder - add your own hooks!
        entry: uv run --isolated --frozen --offline python -c "print('hello world!')"
        language: system
"""
        )

    def test_multihooks(self, tmp_path: Path):
        from usethis._integrations.pre_commit.hooks import remove_hook
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text(
            """\
repos:
  - repo: local # comment
    hooks:    
      - id: bar
        name: bar
        entry: bar
        language: python
  - repo: local # other comment
    hooks:
      - id: baz
        name: baz
        entry: baz
        language: python
"""
        )
        with change_cwd(tmp_path):
            remove_hook("bar")
        assert (tmp_path / ".pre-commit-config.yaml").read_text() == (
            """\
repos:
  - repo: local # other comment
    hooks:
      - id: baz
        name: baz
        entry: baz
        language: python
"""
        )

    def test_dont_delete_no_hook_repo(self, tmp_path: Path):
        from usethis._integrations.pre_commit.hooks import remove_hook
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text(
            """\
repos:
  - repo: local
"""
        )

        with change_cwd(tmp_path):
            remove_hook("bar")

        assert (tmp_path / ".pre-commit-config.yaml").read_text() == (
            """\
repos:
  - repo: local
"""
        )


class TestGetHookNames:
    def test_empty(self, tmp_path: Path):
        from usethis._integrations.pre_commit.hooks import get_hook_ids
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n")

        with change_cwd(tmp_path):
            assert get_hook_ids() == []

    def test_single(self, tmp_path: Path):
        from usethis._integrations.pre_commit.hooks import get_hook_ids
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text(
            """
repos:
  - repo: foo
    hooks:
      - id: bar
"""
        )
        with change_cwd(tmp_path):
            assert get_hook_ids() == ["bar"]

    def test_multihooks(self, tmp_path: Path):
        from usethis._integrations.pre_commit.hooks import get_hook_ids
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text(
            """
repos:
  - repo: foo
    hooks:
      - id: bar
      - id: baz
"""
        )
        with change_cwd(tmp_path):
            assert get_hook_ids() == ["bar", "baz"]

    def test_multirepo(self, tmp_path: Path):
        from usethis._integrations.pre_commit.hooks import get_hook_ids
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text(
            """
repos:
  - repo: foo
    hooks:
    - id: bar
  - repo: baz
    hooks:
    - id: qux
"""
        )
        with change_cwd(tmp_path):
            assert get_hook_ids() == ["bar", "qux"]

    def test_duplicated_ok(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pre_commit.hooks import get_hook_ids
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text(
            """
repos:
  - repo: foo
    hooks:
    - id: bar
  - repo: baz
    hooks:
    - id: bar
"""
        )

        # Act
        with change_cwd(tmp_path):
            result = get_hook_ids()

        # Assert
        assert result == ["bar", "bar"]


class TestAddPlaceholderHook:
    def test_contents(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.pre_commit.hooks import add_placeholder_hook
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path):
            add_placeholder_hook()

        # Assert
        assert (tmp_path / ".pre-commit-config.yaml").exists()
        assert (
            (tmp_path / ".pre-commit-config.yaml").read_text()
            == """\
repos:
  - repo: local
    hooks:
      - id: placeholder
        name: Placeholder - add your own hooks!
        entry: uv run --isolated --frozen --offline python -c "print('hello world!')"
        language: system
"""
        )

        out, _ = capfd.readouterr()
        # Keep these messages in sync with the ones used for bitbucket
        assert out == (
            "✔ Writing '.pre-commit-config.yaml'.\n"
            "✔ Adding placeholder hook to '.pre-commit-config.yaml'.\n"
            "☐ Remove the placeholder hook in '.pre-commit-config.yaml'.\n"
            "☐ Replace it with your own hooks.\n"
            "☐ Alternatively, use 'usethis tool' to add other tools and their hooks.\n"
        )


class TestHooksAreEquivalent:
    def test_identical(self):
        # Arrange
        from usethis._integrations.pre_commit.hooks import _hooks_are_equivalent
        from usethis._integrations.pre_commit.schema import HookDefinition, Language

        hook = HookDefinition(
            id="foo",
            name="Foo",
            entry="echo 'Hello, world!'",
            language=Language("python"),
        )
        other = HookDefinition(
            id="foo",
            name="Foo",
            entry="echo 'Hello, world!'",
            language=Language("python"),
        )

        # Act
        result = _hooks_are_equivalent(hook, other)

        # Assert
        assert result is True

    def test_different_id(self):
        # Arrange
        from usethis._integrations.pre_commit.hooks import _hooks_are_equivalent
        from usethis._integrations.pre_commit.schema import HookDefinition, Language

        hook = HookDefinition(
            id="foo",
            name="Foo",
            entry="echo 'Hello, world!'",
            language=Language("python"),
        )
        other = HookDefinition(
            id="bar",
            name="Foo",
            entry="echo 'Hello, world!'",
            language=Language("python"),
        )

        # Act
        result = _hooks_are_equivalent(hook, other)

        # Assert
        assert result is False

    def test_different_name(self):
        # Arrange
        from usethis._integrations.pre_commit.hooks import _hooks_are_equivalent
        from usethis._integrations.pre_commit.schema import HookDefinition, Language

        hook = HookDefinition(
            id="foo",
            name="Foo",
            entry="echo 'Hello, world!'",
            language=Language("python"),
        )
        other = HookDefinition(
            id="foo",
            name="Bar",
            entry="echo 'Hello, world!'",
            language=Language("python"),
        )

        # Act
        result = _hooks_are_equivalent(hook, other)

        # Assert
        assert result is True

    def test_case_sensitive_id_difference(self):
        # Arrange
        from usethis._integrations.pre_commit.hooks import _hooks_are_equivalent
        from usethis._integrations.pre_commit.schema import HookDefinition

        hook = HookDefinition(
            id="foo",
            name="Foo",
            entry="echo 'Hello, world!'",
        )
        other = HookDefinition(
            id="FOO",
            name="Different",
            entry="echo 'Au revoir!'",
        )

        # Act
        result = _hooks_are_equivalent(hook, other)

        # Assert
        assert result is True

    def test_no_id(self):
        # Arrange
        from usethis._integrations.pre_commit.hooks import _hooks_are_equivalent
        from usethis._integrations.pre_commit.schema import HookDefinition, Language

        hook = HookDefinition(
            id=None,
            name="Foo",
            entry="echo 'Hello, world!'",
            language=Language("python"),
        )
        other = HookDefinition(
            id="foo",
            name="Foo",
            entry="echo 'Hello, world!'",
            language=Language("python"),
        )

        # Act
        result = _hooks_are_equivalent(hook, other)

        # Assert
        assert result is False
