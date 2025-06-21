from pathlib import Path
from uuid import UUID

import pytest


class TestApplyPipeweldInstruction:
    def test_add_to_brand_new_pipeline(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.pipeweld import (
            apply_pipeweld_instruction,
        )
        from usethis._integrations.ci.bitbucket.schema import Script, Step
        from usethis._pipeweld.ops import InsertSuccessor
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path):
            apply_pipeweld_instruction(
                InsertSuccessor(step="foo", after=None),
                new_step=Step(name="foo", script=Script(["echo foo"])),
            )

        # Assert
        content = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            content
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: foo
            script:
              - echo foo
"""
        )

    def test_import_pipeline_fails(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.errors import (
            UnexpectedImportPipelineError,
        )
        from usethis._integrations.ci.bitbucket.pipeweld import (
            apply_pipeweld_instruction,
        )
        from usethis._integrations.ci.bitbucket.schema import Script, Step
        from usethis._pipeweld.ops import InsertSuccessor
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
        import: shared-pipeline:master:share-pipeline-1
"""
        )

        # Act, Assert
        with change_cwd(tmp_path), pytest.raises(UnexpectedImportPipelineError):
            apply_pipeweld_instruction(
                InsertSuccessor(step="foo", after=None),
                new_step=Step(name="foo", script=Script(["echo foo"])),
            )

    def test_existing_pipeline(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.pipeweld import (
            apply_pipeweld_instruction,
        )
        from usethis._integrations.ci.bitbucket.schema import Script, Step
        from usethis._pipeweld.ops import InsertSuccessor
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: bar
            script:
              - echo bar
"""
        )

        # Act
        with change_cwd(tmp_path):
            apply_pipeweld_instruction(
                InsertSuccessor(step="foo", after=None),
                new_step=Step(name="foo", script=Script(["echo foo"])),
            )

        # Assert
        content = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            content
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: foo
            script:
              - echo foo
      - step:
            name: bar
            script:
              - echo bar
"""
        )

    class TestInsertAfter:
        def test_step_item(self, tmp_path: Path):
            # Arrange
            from usethis._integrations.ci.bitbucket.pipeweld import (
                apply_pipeweld_instruction,
            )
            from usethis._integrations.ci.bitbucket.schema import Script, Step
            from usethis._pipeweld.ops import InsertSuccessor
            from usethis._test import change_cwd

            (tmp_path / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: bar
            script:
              - echo bar
"""
            )

            # Act
            with change_cwd(tmp_path):
                apply_pipeweld_instruction(
                    InsertSuccessor(step="foo", after="bar"),
                    new_step=Step(name="foo", script=Script(["echo foo"])),
                )

            # Assert
            content = (tmp_path / "bitbucket-pipelines.yml").read_text()
            assert (
                content
                == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: bar
            script:
              - echo bar
      - step:
            name: foo
            script:
              - echo foo
"""
            )

        def test_parallel_item(self, tmp_path: Path):
            # Arrange
            from usethis._integrations.ci.bitbucket.pipeweld import (
                apply_pipeweld_instruction,
            )
            from usethis._integrations.ci.bitbucket.schema import Script, Step
            from usethis._pipeweld.ops import InsertSuccessor
            from usethis._test import change_cwd

            (tmp_path / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
          - step:
              name: baz
              script:
                - echo baz
          - step:
              name: qux
              script:
                - echo qux
"""
            )

            # Act
            with change_cwd(tmp_path):
                apply_pipeweld_instruction(
                    InsertSuccessor(step="foo", after="qux"),
                    new_step=Step(name="foo", script=Script(["echo foo"])),
                )

            # Assert
            content = (tmp_path / "bitbucket-pipelines.yml").read_text()
            assert (
                content
                == """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
          - step:
                name: baz
                script:
                  - echo baz
          - step:
                name: qux
                script:
                  - echo qux
      - step:
            name: foo
            script:
              - echo foo
"""
            )

        def test_parallel_expanded(self, tmp_path: Path):
            # Arrange
            from usethis._integrations.ci.bitbucket.pipeweld import (
                apply_pipeweld_instruction,
            )
            from usethis._integrations.ci.bitbucket.schema import Script, Step
            from usethis._pipeweld.ops import InsertSuccessor
            from usethis._test import change_cwd

            (tmp_path / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
          steps:
            - step:
                name: baz
                script:
                  - echo baz
            - step:
                name: qux
                script:
                  - echo qux
"""
            )

            # Act
            with change_cwd(tmp_path):
                apply_pipeweld_instruction(
                    InsertSuccessor(step="foo", after="qux"),
                    new_step=Step(name="foo", script=Script(["echo foo"])),
                )

            # Assert
            content = (tmp_path / "bitbucket-pipelines.yml").read_text()
            assert (
                content
                == """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
            steps:
              - step:
                    name: baz
                    script:
                      - echo baz
              - step:
                    name: qux
                    script:
                      - echo qux
      - step:
            name: foo
            script:
              - echo foo
"""
            )

        def test_stage_item(self, tmp_path: Path):
            # Arrange
            from usethis._integrations.ci.bitbucket.pipeweld import (
                apply_pipeweld_instruction,
            )
            from usethis._integrations.ci.bitbucket.schema import Script, Step
            from usethis._pipeweld.ops import InsertSuccessor
            from usethis._test import change_cwd

            (tmp_path / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
pipelines:
    default:
      - stage:
            steps:
              - step:
                    name: baz
                    script:
                      - echo baz
"""
            )

            # Act
            with change_cwd(tmp_path):
                apply_pipeweld_instruction(
                    InsertSuccessor(step="foo", after="baz"),
                    new_step=Step(name="foo", script=Script(["echo foo"])),
                )

            # Assert
            content = (tmp_path / "bitbucket-pipelines.yml").read_text()
            assert (
                content
                == """\
image: atlassian/default-image:3
pipelines:
    default:
      - stage:
            steps:
              - step:
                    name: baz
                    script:
                      - echo baz
      - step:
            name: foo
            script:
              - echo foo
"""
            )


class TestGetInstructionsForInsertion:
    class TestStr:
        def test_after_str(self):
            # Arrange
            from usethis._pipeweld.func import _get_instructions_for_insertion
            from usethis._pipeweld.ops import InsertSuccessor

            component = "foo"
            after = "bar"

            # Act
            instructions, endpoint = _get_instructions_for_insertion(
                component, after=after
            )

            # Assert
            assert instructions == [InsertSuccessor(step="foo", after="bar")]
            assert endpoint == "foo"

        def test_after_none(self):
            # Arrange
            from usethis._pipeweld.func import _get_instructions_for_insertion
            from usethis._pipeweld.ops import InsertSuccessor

            component = "foo"
            after = None

            # Act
            instructions, endpoint = _get_instructions_for_insertion(
                component, after=after
            )

            # Assert
            assert instructions == [InsertSuccessor(step="foo", after=None)]
            assert endpoint == "foo"

    class TestSeries:
        def test_empty(self):
            # Arrange
            from usethis._pipeweld.containers import series
            from usethis._pipeweld.func import _get_instructions_for_insertion

            component = series()
            after = None

            # Act
            instructions, endpoint = _get_instructions_for_insertion(
                component, after=after
            )

            # Assert
            assert instructions == []
            assert endpoint is None

        def test_single(self):
            # Arrange
            from usethis._pipeweld.containers import series
            from usethis._pipeweld.func import _get_instructions_for_insertion
            from usethis._pipeweld.ops import InsertSuccessor

            component = series("A")
            after = "0"

            # Act
            instructions, endpoint = _get_instructions_for_insertion(
                component, after=after
            )

            # Assert
            assert instructions == [InsertSuccessor(step="A", after="0")]
            assert endpoint == "A"

        def test_multiple(self):
            # Arrange
            from usethis._pipeweld.containers import series
            from usethis._pipeweld.func import _get_instructions_for_insertion
            from usethis._pipeweld.ops import InsertSuccessor

            component = series("A", "B", "C")
            after = "0"

            # Act
            instructions, endpoint = _get_instructions_for_insertion(
                component, after=after
            )

            # Assert
            assert instructions == [
                InsertSuccessor(step="A", after="0"),
                InsertSuccessor(step="B", after="A"),
                InsertSuccessor(step="C", after="B"),
            ]
            assert endpoint == "C"

    class TestParallel:
        def test_empty(self):
            # Arrange
            from usethis._pipeweld.containers import parallel
            from usethis._pipeweld.func import _get_instructions_for_insertion

            component = parallel()
            after = None

            # Act
            instructions, endpoint = _get_instructions_for_insertion(
                component, after=after
            )

            # Assert
            assert instructions == []
            assert endpoint is None

        def test_single(self):
            # Arrange
            from usethis._pipeweld.containers import parallel
            from usethis._pipeweld.func import _get_instructions_for_insertion
            from usethis._pipeweld.ops import InsertSuccessor

            component = parallel("A")
            after = "0"

            # Act
            instructions, endpoint = _get_instructions_for_insertion(
                component, after=after
            )

            # Assert
            assert instructions == [InsertSuccessor(step="A", after="0")]
            assert endpoint == "A"

        def test_multiple(self):
            # Arrange
            from usethis._pipeweld.containers import parallel
            from usethis._pipeweld.func import _get_instructions_for_insertion
            from usethis._pipeweld.ops import InsertParallel, InsertSuccessor

            component = parallel("A", "B", "C")
            after = "0"

            # Act
            instructions, endpoint = _get_instructions_for_insertion(
                component, after=after
            )

            # Assert
            assert instructions == [
                InsertSuccessor(step="A", after="0"),
                InsertParallel(step="B", after="0"),
                InsertParallel(step="C", after="0"),
            ]
            assert endpoint == "A"  # Alphabetical order wins tiebreaks

    class TestDepGroup:
        def test_basic(self):
            # Arrange
            from usethis._pipeweld.containers import depgroup, series
            from usethis._pipeweld.func import _get_instructions_for_insertion
            from usethis._pipeweld.ops import InsertSuccessor

            component = depgroup("A", series("B", "C"), config_group="x")
            after = "0"

            # Act
            instructions, endpoint = _get_instructions_for_insertion(
                component, after=after
            )

            # Assert
            assert instructions == [
                InsertSuccessor(step="A", after="0"),
                InsertSuccessor(step="B", after="A"),
                InsertSuccessor(step="C", after="B"),
            ]

            assert endpoint == "C"


class TestGetPipeweldPipelineFromDefault:
    def test_image_only(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.pipeweld import (
            get_pipeweld_pipeline_from_default,
        )
        from usethis._integrations.ci.bitbucket.schema import (
            Image,
            ImageName,
            PipelinesConfiguration,
        )
        from usethis._pipeweld.containers import series

        model = PipelinesConfiguration(
            image=Image(ImageName("atlassian/default-image:3"))
        )

        # Act
        result = get_pipeweld_pipeline_from_default(model)

        # Assert
        assert result == series()

    def test_import_pipeline_raises(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.errors import (
            UnexpectedImportPipelineError,
        )
        from usethis._integrations.ci.bitbucket.pipeweld import (
            get_pipeweld_pipeline_from_default,
        )
        from usethis._integrations.ci.bitbucket.schema import (
            ImportPipeline,
            Pipeline,
            Pipelines,
            PipelinesConfiguration,
        )

        model = PipelinesConfiguration(
            pipelines=Pipelines(
                default=Pipeline(
                    ImportPipeline(
                        # import is a keyword so we need to use a dict
                        **{"import": "shared-pipeline:master:share-pipeline-1"}
                    )
                ),
            ),
        )

        # Act, Assert
        with pytest.raises(UnexpectedImportPipelineError):
            get_pipeweld_pipeline_from_default(model)

    def test_series(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.pipeweld import (
            get_pipeweld_pipeline_from_default,
        )
        from usethis._integrations.ci.bitbucket.schema import (
            Items,
            Pipeline,
            Pipelines,
            PipelinesConfiguration,
            Script,
            Step,
            StepItem,
        )
        from usethis._pipeweld.containers import series

        model = PipelinesConfiguration(
            pipelines=Pipelines(
                default=Pipeline(
                    Items(
                        [
                            StepItem(
                                step=Step(
                                    name="foo",
                                    script=Script(["echo foo"]),
                                )
                            )
                        ]
                    )
                ),
            ),
        )

        # Act
        result = get_pipeweld_pipeline_from_default(model)

        # Assert
        assert result == series("foo")

    def test_parallel(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.pipeweld import (
            get_pipeweld_pipeline_from_default,
        )
        from usethis._integrations.ci.bitbucket.schema import (
            Items,
            Parallel,
            ParallelItem,
            ParallelSteps,
            Pipeline,
            Pipelines,
            PipelinesConfiguration,
            Script,
            Step,
            StepItem,
        )
        from usethis._pipeweld.containers import parallel, series

        model = PipelinesConfiguration(
            pipelines=Pipelines(
                default=Pipeline(
                    Items(
                        [
                            ParallelItem(
                                parallel=Parallel(
                                    ParallelSteps(
                                        [
                                            StepItem(
                                                step=Step(
                                                    name="foo",
                                                    script=Script(["echo foo"]),
                                                )
                                            ),
                                            StepItem(
                                                step=Step(
                                                    name="bar",
                                                    script=Script(["echo bar"]),
                                                )
                                            ),
                                        ]
                                    )
                                )
                            )
                        ]
                    )
                ),
            ),
        )

        # Act
        result = get_pipeweld_pipeline_from_default(model)

        # Assert
        assert result == series(
            parallel("foo", "bar"),
        )

    def test_parallel_expanded(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.pipeweld import (
            get_pipeweld_pipeline_from_default,
        )
        from usethis._integrations.ci.bitbucket.schema import (
            Items,
            Parallel,
            ParallelExpanded,
            ParallelItem,
            ParallelSteps,
            Pipeline,
            Pipelines,
            PipelinesConfiguration,
            Script,
            Step,
            StepItem,
        )
        from usethis._pipeweld.containers import parallel, series

        model = PipelinesConfiguration(
            pipelines=Pipelines(
                default=Pipeline(
                    Items(
                        [
                            ParallelItem(
                                parallel=Parallel(
                                    ParallelExpanded(
                                        steps=ParallelSteps(
                                            [
                                                StepItem(
                                                    step=Step(
                                                        name="foo",
                                                        script=Script(["echo foo"]),
                                                    )
                                                ),
                                                StepItem(
                                                    step=Step(
                                                        name="bar",
                                                        script=Script(["echo bar"]),
                                                    )
                                                ),
                                            ]
                                        )
                                    )
                                )
                            )
                        ]
                    )
                ),
            ),
        )

        # Act
        result = get_pipeweld_pipeline_from_default(model)

        # Assert
        assert result == series(
            parallel("foo", "bar"),
        )

    def test_named_stage_item(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.pipeweld import (
            get_pipeweld_pipeline_from_default,
        )
        from usethis._integrations.ci.bitbucket.schema import (
            Items,
            Pipeline,
            Pipelines,
            PipelinesConfiguration,
            Script,
            Stage,
            StageItem,
            Step1,
            Step2,
        )
        from usethis._pipeweld.containers import depgroup, series

        model = PipelinesConfiguration(
            pipelines=Pipelines(
                default=Pipeline(
                    Items(
                        [
                            StageItem(
                                stage=Stage(
                                    name="mystage",
                                    steps=[
                                        Step1(
                                            step=Step2(
                                                name="foo",
                                                script=Script(["echo foo"]),
                                            )
                                        )
                                    ],
                                )
                            )
                        ]
                    )
                ),
            ),
        )

        # Act
        result = get_pipeweld_pipeline_from_default(model)

        # Assert
        assert result == series(
            depgroup(
                "foo",
                config_group="mystage",
            )
        )

    def test_unnamed_stage_item(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.pipeweld import (
            get_pipeweld_pipeline_from_default,
        )
        from usethis._integrations.ci.bitbucket.schema import (
            Items,
            Pipeline,
            Pipelines,
            PipelinesConfiguration,
            Script,
            Stage,
            StageItem,
            Step1,
            Step2,
        )
        from usethis._pipeweld.containers import DepGroup, depgroup, series

        model = PipelinesConfiguration(
            pipelines=Pipelines(
                default=Pipeline(
                    Items(
                        [
                            StageItem(
                                stage=Stage(
                                    steps=[
                                        Step1(
                                            step=Step2(
                                                name="foo",
                                                script=Script(["echo foo"]),
                                            )
                                        )
                                    ],
                                )
                            )
                        ]
                    )
                ),
            ),
        )

        # Act
        result = get_pipeweld_pipeline_from_default(model)

        # Assert
        dg = result[0]
        assert isinstance(dg, DepGroup)
        assert result == series(
            depgroup(
                "foo",
                config_group=dg.config_group,
            )
        )
        assert dg.config_group.startswith("Unnamed Stage ")
        uuid = dg.config_group.removeprefix("Unnamed Stage ")
        UUID(uuid)  # Raises no error


class TestGetPipeweldStep:
    def test_no_name(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.pipeweld import get_pipeweld_step
        from usethis._integrations.ci.bitbucket.schema import Script, Step

        step = Step(
            name=None,
            script=Script(["echo foo"]),
        )

        # Act
        result = get_pipeweld_step(step)

        # Assert
        assert result == """{"script":["echo foo"]}"""

    def test_with_name(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.pipeweld import get_pipeweld_step
        from usethis._integrations.ci.bitbucket.schema import Script, Step

        step = Step(
            name="foo",
            script=Script(["echo foo"]),
        )

        # Act
        result = get_pipeweld_step(step)

        # Assert
        assert result == "foo"
