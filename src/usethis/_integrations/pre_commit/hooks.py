from collections import Counter
from pathlib import Path

import ruamel.yaml
from ruamel.yaml.comments import CommentedMap

from usethis._integrations.pre_commit.config import PreCommitRepoConfig
from usethis._integrations.yaml.io import edit_yaml

_HOOK_ORDER = [
    "validate-pyproject",
    "pyproject-fmt",
    "ruff-format",
    "ruff-check",
    "deptry",
]


class DuplicatedHookNameError(ValueError):
    """Raised when a hook name is duplicated in a pre-commit configuration file."""


def add_hook(config: PreCommitRepoConfig) -> None:
    path = Path.cwd() / ".pre-commit-config.yaml"

    with edit_yaml(path) as yaml_document:
        content = yaml_document.content
        if not isinstance(content, CommentedMap):
            msg = f"Unrecognized pre-commit configuration file format of type {type(content)}"
            raise NotImplementedError(msg)

        (hook_config,) = config.hooks
        hook_name = hook_config.id

        # Get an ordered list of the hooks already in the file
        existing_hooks = get_hook_names()

        if not existing_hooks:
            raise NotImplementedError

        # Get the precendents, i.e. hooks occuring before the new hook
        try:
            hook_idx = _HOOK_ORDER.index(hook_name)
        except ValueError:
            msg = f"Hook '{hook_name}' not recognized"
            raise NotImplementedError(msg)
        precedents = _HOOK_ORDER[:hook_idx]

        # Find the last of the precedents in the existing hooks
        existings_precedents = [hook for hook in existing_hooks if hook in precedents]
        if existings_precedents:
            last_precedent = existings_precedents[-1]
        else:
            # Use the last existing hook
            last_precedent = existing_hooks[-1]

        # Insert the new hook after the last precedent repo
        # Do this by iterating over the repos and hooks, and inserting the new hook after
        # the last precedent
        new_repos = []
        for repo in content["repos"]:
            new_repos.append(repo)
            for hook in repo["hooks"]:
                if hook["id"] == last_precedent:
                    # TODO check this shouldn't be a fancy model dump that chooses
                    # sensible key order automatically
                    new_repos.append(config.model_dump(exclude_none=True))
        content["repos"] = new_repos


def remove_hook(name: str) -> None:
    path = Path.cwd() / ".pre-commit-config.yaml"

    with edit_yaml(path) as yaml_document:
        content = yaml_document.content
        if not isinstance(content, CommentedMap):
            msg = f"Unrecognized pre-commit configuration file format of type {type(content)}"
            raise NotImplementedError(msg)

        # search across the repos for any hooks with ID equal to name
        for repo in content["repos"]:
            for hook in repo["hooks"]:
                if hook["id"] == name:
                    repo["hooks"].remove(hook)

            # if repo has no hooks, remove it
            if not repo["hooks"]:
                content["repos"].remove(repo)

    # TODO but what if there's no hooks left at all? Should we delete the file?


def get_hook_names() -> list[str]:
    yaml = ruamel.yaml.YAML()
    with (Path.cwd() / ".pre-commit-config.yaml").open(mode="r") as f:
        content = yaml.load(f)

    hook_names = []
    for repo in content["repos"]:
        for hook in repo["hooks"]:
            hook_names.append(hook["id"])

    # Need to validate there are no duplciates
    for name, count in Counter(hook_names).items():
        if count > 1:
            msg = f"Hook name '{name}' is duplicated"
            raise DuplicatedHookNameError(msg)

    return hook_names
