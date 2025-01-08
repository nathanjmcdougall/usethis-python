# generated by datamodel-codegen:
#   filename:  schema.json
#   timestamp: 2024-12-13T02:08:42+00:00
# using the command:
#   datamodel-codegen --input tests\usethis\_integrations\bitbucket\schema.json --input-file-type jsonschema --output src\usethis\_integrations\bitbucket\schema.py --enum-field-as-literal all --field-constraints --use-double-quotes --use-union-operator --use-standard-collections --use-default-kwarg --output-model-type pydantic_v2.BaseModel --target-python-version 3.12
# ruff: noqa: ERA001
# pyright: reportGeneralTypeIssues=false
# plus manually add Definitions.scripts for type hinting
# plus manually add ScriptItemAnchor as a root type of Script, and import it
# plus manually forbid StepItem.step from being None

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel

from usethis._integrations.bitbucket.anchor import ScriptItemAnchor


class Depth(RootModel[int]):
    root: int = Field(
        ...,
        description='The depth argument of Git clone operation. It can be either number or "full" value',
        examples=["full"],
        ge=1,
        title="Git Clone Depth",
    )


class SparseCheckout(BaseModel):
    cone_mode: bool | None = Field(
        default=True,
        alias="cone-mode",
        description="Controls whether to use cone-mode or non-cone-mode.",
    )
    enabled: bool | None = Field(default=True, description="Enables sparse checkout.")
    patterns: list[str] | None = Field(
        default=None,
        description="List of patterns to include in sparse checkout. The patterns should be directories or gitignore-style patterns based on the cone-mode settings.",
    )


class Clone(BaseModel):
    depth: Depth | Literal["full"] | None = Field(
        default=50,
        description='The depth argument of Git clone operation. It can be either number or "full" value',
        examples=["full"],
        title="Git Clone Depth",
    )
    enabled: bool | None = Field(
        default=True, description="Enables cloning of the repository."
    )
    filter: str | None = Field(
        default=None,
        description='The partial clone filter argument of Git fetch operation. It can be either "blob:none" or "tree:<n>" value',
    )
    lfs: bool | None = Field(
        default=False,
        description="Enables the download of files from LFS storage when cloning.",
    )
    skip_ssl_verify: bool | None = Field(
        default=False,
        alias="skip-ssl-verify",
        description="Disables SSL verification during Git clone operation, allowing the use of self-signed certificates.",
    )
    sparse_checkout: SparseCheckout | None = Field(
        default=None,
        alias="sparse-checkout",
        description="When this is provided, the repository will be cloned using sparse checkout using the provided settings.",
        title="Sparse Checkout Settings",
    )
    strategy: Literal["clone", "fetch"] | None = Field(
        default="fetch",
        description='Set the Git clone strategy to use. "fetch" is the new default strategy, "clone" is the legacy strategy.',
    )
    tags: bool | None = Field(
        default=False, description="Enables fetching tags when cloning."
    )


class MaxTime(RootModel[int]):
    root: int = Field(
        ...,
        description="The maximum time a step can execute for in minutes.",
        examples=[60],
        gt=0,
    )


class Size(RootModel[Literal["1x", "2x", "4x", "8x", "16x", "32x"]]):
    root: Literal["1x", "2x", "4x", "8x", "16x", "32x"] = Field(
        ...,
        description="The size of the step, sets the amount of resources allocated.",
        title="Step Size",
    )


class Key(BaseModel):
    files: list[str] = Field(
        ...,
        description="Checksum of these file paths will be used to generate the cache key.",
        min_length=1,
    )


class CachePath(RootModel[str]):
    root: str = Field(
        ...,
        description="Path to the directory to be cached, can be absolute or relative to the clone directory.",
        title="Cache Path",
    )


class Cloud(BaseModel):
    atlassian_ip_ranges: bool | None = Field(
        default=False,
        alias="atlassian-ip-ranges",
        description="Whether it uses Atlassian ip ranges.",
    )
    version: str | None = Field(default=None, description="Cloud Runtime version.")


class Aws(BaseModel):
    access_key: str = Field(
        ...,
        alias="access-key",
        description="The access key for Amazon Elastic Container Registry (AWS ECR).",
        title="AWS Access Key",
    )
    secret_key: str = Field(
        ...,
        alias="secret-key",
        description="The secret key for Amazon Elastic Container Registry (AWS ECR).",
        title="AWS Secret Key",
    )


class Aws1(BaseModel):
    oidc_role: str = Field(
        ...,
        alias="oidc-role",
        description="OIDC role with access to private Docker images hosted in Amazon Elastic Container Registry (AWS ECR).",
        title="OpenID Connect Role",
    )


class ImageName(RootModel[str]):
    root: str = Field(
        ...,
        description="The name of the Docker image which may or may not include registry URL, tag, and digest value.",
        title="Docker Image Name",
    )


class ImportPipeline(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    import_: str = Field(
        ...,
        alias="import",
        description="The import needs to match the following format: {repo-slug|repo-uuid}:{tag-name|branch-name}:{pipeline-name}.",
        pattern="^[^:]+:[^:]+:[^:]+$",
        title="Identifier of the pipeline configuration to import",
    )


class ImageBase(BaseModel):
    name: ImageName
    run_as_user: int | None = Field(
        default=0,
        alias="run-as-user",
        description="The UID of a user in the docker image to run as. Overrides image's default user, specified user UID must be an existing user in the image with a valid home directory.",
        title="User ID",
    )


class Variable(BaseModel):
    allowed_values: list[str] | None = Field(
        default=None,
        alias="allowed-values",
        description="A list of values that are allowed for the variable.",
        min_length=1,
        title="Allowed Variable Values",
    )
    default: str | None = Field(default=None, title="Default Variable Value")
    description: str | None = Field(default=None, title="Variable Description")
    name: str = Field(..., title="Variable Name")


class VariablesItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    variables: list[Variable] | None = Field(
        default=None,
        description="List of variables for the custom pipeline.",
        min_length=1,
        title="Custom Pipeline Variables",
    )


class Changesets(BaseModel):
    includePaths: list[str] = Field(
        ...,
        description="Condition which holds only if any of the modified files match any of the specified patterns.",
        min_length=1,
        title="Include Paths",
    )


class Condition(BaseModel):
    changesets: Changesets = Field(
        ...,
        description="Condition on the changesets involved in the pipeline.",
        title="Changeset Condition",
    )


class Trigger(RootModel[Literal["automatic", "manual"]]):
    root: Literal["automatic", "manual"]


class FailFast(RootModel[bool]):
    root: bool = Field(..., title="Fail Fast")


class ArtifactsPaths(RootModel[list[str]]):
    root: list[str] = Field(..., min_length=1)


class Pipe(BaseModel):
    pipe: str = Field(
        ..., description="The full pipe identifier.", title="Pipe Identifier"
    )
    variables: dict[str, str | list[str]] | None = Field(
        default=None,
        description="Environment variables passed to the pipe container.",
        title="Pipe Variables",
    )


class RunsOnItem(RootModel[str]):
    root: str = Field(
        ..., description="Label of a runner.", max_length=50, title="Step Runner Label"
    )


class Runtime(BaseModel):
    cloud: Cloud | None = None


class CacheExpanded(BaseModel):
    key: Key | None = Field(default=None, title="Cache Key")
    path: CachePath


class ImageAwsAuth(ImageBase):
    aws: Aws | Aws1


class ImageBasicAuth(ImageBase):
    password: str = Field(
        ...,
        description="The password to use when fetching the Docker image.",
        title="Docker Registry Password",
    )
    username: str = Field(
        ...,
        description="The username to use when fetching the Docker image.",
        title="Docker Registry Username",
    )


class ImageNoAuth(ImageBase):
    aws: Any | None = None
    password: Any | None = None
    username: Any | None = None


class Script(RootModel[list[str | Pipe | ScriptItemAnchor]]):
    root: list[str | Pipe | ScriptItemAnchor] = Field(..., min_length=1)


class ArtifactsExpanded(BaseModel):
    download: bool | None = Field(
        default=True,
        description="Enables downloading of all available artifacts at the start of a step.",
    )
    paths: ArtifactsPaths | None = None


class RunsOnExpanded(RootModel[list[RunsOnItem]]):
    root: list[RunsOnItem] = Field(
        ...,
        description="Required labels of a runner to run the step.",
        examples=[["self.hosted", "linux"]],
        max_length=10,
        min_length=1,
        title="Step Runner Labels",
    )


class Options(BaseModel):
    docker: bool | None = Field(
        default=False, description="Enables Docker service for every step."
    )
    max_time: MaxTime | None = Field(default=None, alias="max-time")
    runtime: Runtime | None = None
    size: Size | None = None


class Cache(RootModel[CachePath | CacheExpanded]):
    root: CachePath | CacheExpanded


class Image(RootModel[ImageNoAuth | ImageBasicAuth | ImageAwsAuth | ImageName]):
    root: ImageNoAuth | ImageBasicAuth | ImageAwsAuth | ImageName


class Service(BaseModel):
    image: Image | None = None
    memory: int | None = Field(
        default=1024,
        description="Memory limit for the service container, in megabytes.",
        ge=128,
        title="Service Memory",
    )
    type: Literal["docker"] | None = Field(
        default=None,
        description="Specifies Docker service container (to run Docker-in-Docker).",
    )
    variables: dict[str, str] | None = Field(
        default=None,
        description="Environment variables passed to the service container.",
        title="Service Variables",
    )


class Artifacts(RootModel[ArtifactsPaths | ArtifactsExpanded]):
    root: ArtifactsPaths | ArtifactsExpanded


class RunsOn(RootModel[RunsOnItem | RunsOnExpanded]):
    root: RunsOnItem | RunsOnExpanded


class StepBase(BaseModel):
    after_script: Script | None = Field(
        default=None,
        alias="after-script",
        description="List of commands to execute after the step succeeds or fails.",
        title="Step Post Script",
    )
    artifacts: Artifacts | None = None
    caches: list[str] | None = Field(
        default=None,
        description="Caches enabled for the step.",
        min_length=1,
        title="Step Caches",
    )
    clone: Clone | None = None
    deployment: str | None = Field(
        default=None,
        description="The deployment environment for the step.",
        title="Step Deployment Environment",
    )
    fail_fast: FailFast | None = Field(
        default=None,
        alias="fail-fast",
        description="Stop the parent parallel group in case this step fails.",
    )
    image: Image | None = None
    max_time: MaxTime | None = Field(
        default=None, alias="max-time", title="Step Maximum Time"
    )
    name: str | None = Field(
        default=None,
        description="The name of the step.",
        examples=["Build and test"],
        title="Step Name",
    )
    oidc: bool | None = Field(
        default=None,
        description="Enables the use of OpenID Connect to connect a pipeline step to a resource server.",
    )
    runs_on: RunsOn | None = Field(default=None, alias="runs-on")
    runtime: Runtime | None = None
    script: Script = Field(
        ...,
        description="List of commands that are executed in sequence.",
        title="Step Script",
    )
    services: list[str] | None = Field(
        default=None,
        description="Services enabled for the step.",
        max_length=5,
        min_length=1,
        title="Step Services",
    )
    size: Size | None = None
    trigger: Trigger | None = Field(
        default=None,
        description="The trigger used for the pipeline step.",
        title="Step Trigger",
    )


class Step2(StepBase):
    condition: Any | None = None


class Step1(BaseModel):
    step: Step2 | None = None


class Stage(BaseModel):
    condition: Condition | None = Field(
        default=None,
        description="The condition to execute the stage.",
        title="Stage Condition",
    )
    deployment: str | None = Field(
        default=None,
        description="The deployment environment for the stage.",
        title="Stage Deployment Environment",
    )
    name: str | None = Field(
        default=None, description="The name of the stage.", title="Stage Name"
    )
    steps: list[Step1] = Field(
        ...,
        description="List of steps in the stage.",
        min_length=1,
        title="Stage Steps",
    )
    trigger: Trigger | None = Field(
        default=None,
        description="The trigger used for the pipeline stage.",
        title="Stage Trigger",
    )


class Step(StepBase):
    condition: Condition | None = Field(
        default=None,
        description="The condition to execute the step.",
        title="Step Condition",
    )


class StageItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    stage: Stage | None = None


class StepItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    step: Step


class ParallelSteps(RootModel[list[StepItem]]):
    root: list[StepItem] = Field(
        ...,
        description="List of steps in the parallel group to run concurrently.",
        min_length=1,
        title="Parallel Group Steps",
    )


class ParallelExpanded(BaseModel):
    fail_fast: FailFast | None = Field(
        default=None,
        alias="fail-fast",
        description="Stop the whole parallel group in case one of its steps fails.",
    )
    steps: ParallelSteps


class Parallel(RootModel[ParallelSteps | ParallelExpanded]):
    root: ParallelSteps | ParallelExpanded


class ParallelItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    parallel: Parallel | None = None


class Items(RootModel[list[StepItem | ParallelItem | StageItem]]):
    root: list[StepItem | ParallelItem | StageItem] = Field(
        ...,
        description="List of steps, stages and parallel groups of the pipeline.",
        min_length=1,
        title="Pipeline Items",
    )


class ItemsWithVariables(
    RootModel[list[VariablesItem | StepItem | ParallelItem | StageItem]]
):
    root: list[VariablesItem | StepItem | ParallelItem | StageItem] = Field(
        ...,
        description="List of variables, steps, stages and parallel groups of the custom pipeline.",
        min_length=1,
        title="Custom Pipeline Items",
    )


class CustomPipeline(RootModel[ItemsWithVariables | ImportPipeline]):
    root: ItemsWithVariables | ImportPipeline


class Pipeline(RootModel[Items | ImportPipeline]):
    root: Items | ImportPipeline


class PullRequestsPipeline1(BaseModel):
    destinations: dict[str, Pipeline] | None = None


class PullRequestsPipeline(RootModel[Items | PullRequestsPipeline1]):
    root: Items | PullRequestsPipeline1


class Definitions(BaseModel):
    caches: dict[str, Cache] | None = Field(
        default=None, title="Custom cache definitions"
    )
    pipelines: dict[str, CustomPipeline] | None = Field(
        default=None,
        description="Definitions of the pipelines which can be used in other repositories of the same Bitbucket workspace.",
        title="Shared pipeline definitions",
    )
    services: dict[str, Service] | None = Field(
        default=None, title="Service definitions"
    )
    script_items: list[str | Pipe] | None = Field(
        default=None, title="Script Item definitions"
    )


class Pipelines(BaseModel):
    branches: dict[str, Pipeline] | None = Field(
        default=None,
        description="Branch-specific build pipelines.",
        title="Branch Pipelines",
    )
    custom: dict[str, CustomPipeline] | None = Field(
        default=None,
        description="Pipelines that can only be triggered manually or be scheduled.",
        title="Custom Pipelines",
    )
    default: Pipeline | None = Field(
        default=None,
        description="Default pipeline runs on every push except for tags unless a branch-specific pipeline is defined.",
        title="Default Pipeline",
    )
    pull_requests: dict[str, PullRequestsPipeline] | None = Field(
        default=None,
        alias="pull-requests",
        description="Pull-request-specific build pipelines.",
        title="Pull Request Pipelines",
    )
    tags: dict[str, Pipeline] | None = Field(
        default=None, description="Tag-specific build pipelines.", title="Tag Pipelines"
    )


class PipelinesConfiguration(BaseModel):
    clone: Clone | None = None
    definitions: Definitions | None = Field(
        default=None,
        description="The definitions of caches and services used in the declared pipelines.",
        title="Global Definitions",
    )
    export: bool | None = Field(
        default=False,
        description="Allows other Bitbucket repositories to import pipeline definitions from this file. A shared pipeline definition can't contain another `import` property.",
        title="Enables shared pipelines definitions.",
    )
    image: Image | None = None
    labels: dict[str, Any] | None = Field(
        default=None,
        description="Additional key value data supplied in the configuration YAML.",
        examples=[{"buildTool": "maven", "jvm": "jdk17"}],
        title="Pipeline Labels",
    )
    options: Options | None = Field(
        default=None,
        description="Global options allow to override the default values applied to all steps in all declared pipelines.",
        title="Global Options",
    )
    pipelines: Pipelines | None = Field(default=None, title="Pipelines")


class Model(RootModel[PipelinesConfiguration]):
    root: PipelinesConfiguration
