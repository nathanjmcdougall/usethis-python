from collections import Counter
from pathlib import Path

from usethis._console import box_print, tick_print
from usethis._integrations.pre_commit.dump import pre_commit_fancy_dump
from usethis._integrations.pre_commit.io_ import edit_pre_commit_config_yaml
from usethis._integrations.pre_commit.schema import (
    HookDefinition,
    JsonSchemaForPreCommitConfigYaml,
    Language,
    LocalRepo,
    MetaRepo,
    UriRepo,
)
from usethis._integrations.yaml.update import update_ruamel_yaml_map

_HOOK_ORDER = [
    "validate-pyproject",
    "uv-export",
    "pyproject-fmt",
    "ruff",  # ruff followed by ruff-format seems to be the recommended way by Astral
    "ruff-format",
    "deptry",
    "codespell",
]

_PLACEHOLDER_ID = "placeholder"


class DuplicatedHookNameError(ValueError):
    """Raised when a hook name is duplicated in a pre-commit configuration file."""


def add_repo(repo: LocalRepo | UriRepo) -> None:
    """Add a pre-commit repo configuration to the pre-commit configuration file.

    This assumes the hook doesn't already exist in the configuration file.
    """
    with edit_pre_commit_config_yaml() as doc:
        if repo.hooks is None or len(repo.hooks) != 1:
            msg = "Currently, only repos with exactly one hook are supported."
            raise NotImplementedError(msg)  # Should allow multiple or 0 hooks per repo

        (hook_config,) = repo.hooks
        hook_name = hook_config.id

        if hook_name is None:
            msg = "Hook ID must be specified"
            raise ValueError(msg)

        # Ordered list of the hooks already in the file
        existing_hooks = extract_hook_names(doc.model)

        if not existing_hooks:
            if hook_name == _PLACEHOLDER_ID:
                tick_print("Adding placeholder hook to '.pre-commit-config.yaml'.")
            else:
                tick_print(f"Adding hook '{hook_name}' to '.pre-commit-config.yaml'.")

            doc.model.repos.append(repo)
        else:
            # Get the precendents, i.e. hooks occurring before the new hook
            try:
                hook_idx = _HOOK_ORDER.index(hook_name)
            except ValueError:
                msg = f"Hook '{hook_name}' not recognized"
                raise NotImplementedError(msg) from None
            precedents = _HOOK_ORDER[:hook_idx]

            # Find the last of the precedents in the existing hooks
            existings_precedents = [
                hook for hook in existing_hooks if hook in precedents
            ]
            if existings_precedents:
                last_precedent = existings_precedents[-1]
            else:
                # Use the last existing hook
                last_precedent = existing_hooks[-1]

            doc.model.repos = insert_repo(
                repo_to_insert=repo,
                existing_repos=doc.model.repos,
                predecessor=last_precedent,
            )

        update_ruamel_yaml_map(
            doc.content,
            pre_commit_fancy_dump(doc.model, reference=doc.content),
            preserve_comments=True,
        )


def insert_repo(
    *,
    repo_to_insert: LocalRepo | UriRepo | MetaRepo,
    existing_repos: list[LocalRepo | UriRepo | MetaRepo],
    predecessor: str,
) -> list[LocalRepo | UriRepo | MetaRepo]:
    # Insert the new hook after the last precedent repo
    # Do this by iterating over the repos and hooks, and inserting the new hook
    # after the last precedent

    repos = []
    for repo in existing_repos:
        hooks = repo.hooks
        if hooks is None:
            hooks = []

        # Don't include the placeholder from now on, since we're adding a repo
        # which can be there instead.
        if [hook.id for hook in hooks] != [_PLACEHOLDER_ID]:
            repos.append(repo)

        for hook in hooks:
            if hook.id == predecessor:
                if repo_to_insert.hooks is not None:
                    for inserted_hook in repo_to_insert.hooks:
                        tick_print(
                            f"Adding hook '{inserted_hook.id}' to '.pre-commit-config.yaml'."
                        )
                repos.append(repo_to_insert)

    return repos


def add_placeholder_hook() -> None:
    add_repo(_get_placeholder_repo_config())
    box_print("Remove the placeholder hook in '.pre-commit-config.yaml'.")
    box_print("Replace it with your own hooks.")
    box_print("Alternatively, use 'usethis tool' to add other tools and their hooks.")


def _get_placeholder_repo_config() -> LocalRepo:
    return LocalRepo(
        repo="local",
        hooks=[
            HookDefinition(
                id=_PLACEHOLDER_ID,
                name="Placeholder - add your own hooks!",
                entry="""uv run --isolated --frozen python -c "print('hello world!')\"""",
                language=Language("system"),
            )
        ],
    )


def remove_hook(name: str) -> None:
    """Remove pre-commit hook configuration.

    If the hook doesn't exist, this function will have no effect. Meta hooks are
    ignored.
    """
    with edit_pre_commit_config_yaml() as doc:
        # search across the repos for any hooks with ID equal to name
        for repo in doc.model.repos:
            if isinstance(repo, MetaRepo) or repo.hooks is None:
                continue

            for hook in repo.hooks:
                if hook.id == name:
                    tick_print(
                        f"Removing hook '{hook.id}' from '.pre-commit-config.yaml'."
                    )
                    repo.hooks.remove(hook)

            # if repo has no hooks, remove it
            if not repo.hooks:
                doc.model.repos.remove(repo)

        # If there are no more hooks, we should add a placeholder.
        if not doc.model.repos:
            doc.model.repos.append(_get_placeholder_repo_config())

        dump = pre_commit_fancy_dump(doc.model, reference=doc.content)
        update_ruamel_yaml_map(doc.content, dump, preserve_comments=True)


def get_hook_names() -> list[str]:
    path = Path.cwd() / ".pre-commit-config.yaml"

    if not path.exists():
        return []

    with edit_pre_commit_config_yaml() as doc:
        return extract_hook_names(doc.model)


def extract_hook_names(model: JsonSchemaForPreCommitConfigYaml) -> list[str]:
    hook_names = []
    for repo in model.repos:
        if repo.hooks is None:
            continue

        for hook in repo.hooks:
            hook_names.append(hook.id)

    # Need to validate there are no duplicates
    for name, count in Counter(hook_names).items():
        if count > 1:
            msg = f"Hook name '{name}' is duplicated"
            raise DuplicatedHookNameError(msg)

    return hook_names
