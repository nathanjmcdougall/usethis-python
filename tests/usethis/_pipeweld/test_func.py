from usethis._pipeweld.containers import depgroup, parallel, series
from usethis._pipeweld.func import Partition, _parallel_merge_partitions, add
from usethis._pipeweld.ops import InsertParallel, InsertSuccessor
from usethis._pipeweld.result import WeldResult


class TestAdd:
    def test_empty_series_start(self):
        # Arrange
        step = "A"
        pipeline = series()

        # Act
        result = add(pipeline, step=step)

        # Assert
        assert isinstance(result, WeldResult)
        assert result.instructions == [
            # N.B. None means Place at the start of the pipeline
            InsertParallel(after=None, step="A")
        ]
        assert result.solution == series("A")

    def test_series_singleton_start(self):
        # Arrange
        step = "B"
        pipeline = series("A")

        # Act
        result = add(pipeline, step=step)

        # Assert
        assert isinstance(result, WeldResult)
        assert result.instructions == [
            # N.B. None means Place at the start of the pipeline
            InsertParallel(after=None, step="B")
        ]
        assert result.solution == series(parallel("A", "B"))

    def test_parallel_singleton_start(self):
        # Arrange
        step = "B"
        pipeline = series(parallel("A"))

        # Act
        result = add(pipeline, step=step)

        # Assert
        assert isinstance(result, WeldResult)
        assert result.instructions == [
            # N.B. None means Place at the start of the pipeline
            InsertParallel(after=None, step="B")
        ]
        assert result.solution == series(parallel("A", "B"))

    def test_two_element_start(self):
        # Arrange
        step = "C"
        pipeline = series("A", "B")

        # Act
        result = add(pipeline, step=step)

        # Assert
        assert isinstance(result, WeldResult)
        assert result.instructions == [
            # N.B. None means Place at the start of the pipeline
            InsertParallel(after=None, step="C")
        ]
        assert result.solution == series(parallel("A", "C"), "B")

    def test_prerequisite(self):
        # Arrange
        step = "C"
        pipeline = series("A", "B")
        prerequisites = {"A"}

        # Act
        result = add(pipeline, step=step, prerequisites=prerequisites)

        # Assert
        assert isinstance(result, WeldResult)
        assert result.instructions == [InsertParallel(after="A", step="C")]
        assert result.solution == series("A", parallel("B", "C"))

    def test_mixed_dependency_parallelism_of_steps(self):
        # Arrange
        step = "C"
        pipeline = series(parallel("A", "B"))
        prerequisites = {"A"}
        postrequisites = {"B"}

        # Act
        result = add(
            pipeline,
            step=step,
            prerequisites=prerequisites,
            postrequisites=postrequisites,
        )

        # Assert
        assert isinstance(result, WeldResult)
        assert result.solution == series("A", "C", "B")
        assert result.instructions == [
            InsertSuccessor(after=None, step="A"),
            InsertSuccessor(after="A", step="B"),
            InsertSuccessor(after="A", step="C"),
        ]

    def test_mixed_dependency_parallelism_of_series(self):
        # Arrange
        step = "F"
        pipeline = series("A", parallel(series("B", "D"), series("C", "E")))
        prerequisites = {"B"}
        postrequisites = {"E"}

        # Act
        result = add(
            pipeline,
            step=step,
            prerequisites=prerequisites,
            postrequisites=postrequisites,
        )

        # Assert
        assert isinstance(result, WeldResult)
        assert result.solution == series("A", "B", parallel("D", "C", "F"), "E")
        assert result.instructions == [
            InsertSuccessor(after="A", step="B"),
            InsertParallel(after="B", step="C"),
            InsertSuccessor(after="B", step="D"),
            InsertSuccessor(after="C", step="E"),
            InsertParallel(after="B", step="F"),
        ]

    def test_singleton_series(self):
        # Arrange
        step = "B"
        pipeline = series("A")

        # Act
        result = add(pipeline, step=step)

        # Assert
        assert isinstance(result, WeldResult)
        assert result.solution == series(parallel("A", "B"))

    def test_nested_series(self):
        # Arrange
        step = "B"
        pipeline = series(series("A"))

        # Act
        result = add(pipeline, step=step)

        # Assert
        assert isinstance(result, WeldResult)
        assert result.solution == series(series(parallel("A", "B")))

    class TestDoubleNesting:
        """A series of related tests building up to a complex case"""

        def test_no_nesting(self):
            # Arrange
            step = "H"
            pipeline = series("D", "E", "F")
            prerequisites = {"A"}
            postrequisites = {"B", "E"}

            # Act
            result = add(
                pipeline,
                step=step,
                prerequisites=prerequisites,
                postrequisites=postrequisites,
            )

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series(parallel("D", "H"), "E", "F")

        def test_single_nesting(self):
            # Arrange
            step = "H"
            pipeline = series(series("D", "E", "F"))

            # Act
            result = add(
                pipeline,
                step=step,
            )

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series(series(parallel("D", "H"), "E", "F"))

        def test_single_nesting_with_dep(self):
            # Arrange
            step = "H"
            pipeline = series(series("D", "E", "F"))
            prerequisites = {"A"}
            postrequisites = {"B", "E"}

            # Act
            result = add(
                pipeline,
                step=step,
                prerequisites=prerequisites,
                postrequisites=postrequisites,
            )

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series(parallel("D", "H"), series("E", "F"))

        def test_multiple_nesting(self):
            # Arrange
            step = "H"
            pipeline = series(series(parallel(series("D", "E", "F"))))
            prerequisites = {"A"}
            postrequisites = {"B", "E"}

            # Act
            result = add(
                pipeline,
                step=step,
                prerequisites=prerequisites,
                postrequisites=postrequisites,
            )

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series(
                series(parallel(series(parallel("D", "H"), "E", "F")))
            )

        def test_full_complex_case(self):
            # Arrange
            step = "H"
            pipeline = series(
                parallel("A", "B"), "C", series(parallel(series("D", "E", "F"), "G"))
            )
            prerequisites = {"A"}
            postrequisites = {"B", "E"}

            # Act
            result = add(
                pipeline,
                step=step,
                prerequisites=prerequisites,
                postrequisites=postrequisites,
            )

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series(
                "A", "H", "B", "C", parallel(series("D", "E", "F"), "G")
            )

    def test_multi_level_heirarchy(self):
        # Arrange
        step = "E"
        pipeline = series("A", parallel("B", series("C", "D")))
        prerequisites = {"C"}

        # Act
        result = add(
            pipeline,
            step=step,
            prerequisites=prerequisites,
        )

        # Assert
        assert isinstance(result, WeldResult)
        assert result.solution == series(
            "A", parallel("B", series("C", parallel("D", "E")))
        )
        assert result.instructions == [InsertParallel(after="C", step="E")]

    def test_mixed_dependency_parallelism_of_series_pure_parallel(self):
        # Arrange
        step = "E"
        pipeline = series(parallel(series("A", "B"), series("C", "D")))
        prerequisites = {"A"}
        postrequisites = {"D"}

        # Act
        result = add(
            pipeline,
            step=step,
            prerequisites=prerequisites,
            postrequisites=postrequisites,
        )

        # Assert
        assert isinstance(result, WeldResult)
        assert result.solution == series("A", parallel("C", "E", "B"), "D")

    def test_dependency_groups(self):
        # Arrange
        step = "A"
        pipeline = series(depgroup("B", "C", category="x"))
        prerequisites = {"B"}
        postrequisites = {"C"}

        # Act
        result = add(
            pipeline,
            step=step,
            prerequisites=prerequisites,
            postrequisites=postrequisites,
        )

        # Assert
        assert isinstance(result, WeldResult)
        assert result.solution == series(
            depgroup("B", category="x"), "A", depgroup("C", category="x")
        )

    def test_dependency_groups_in_series(self):
        # Arrange
        step = "E"
        pipeline = series("A", depgroup("B", "C", category="x"))
        prerequisites = {"B"}
        compatible_config_groups = {"x"}

        # Act
        result = add(
            pipeline,
            step=step,
            prerequisites=prerequisites,
            compatible_config_groups=compatible_config_groups,
        )

        # Assert
        assert isinstance(result, WeldResult)
        assert result.solution == series(
            "A", depgroup("B", category="x"), parallel(depgroup("C", category="x"), "E")
        )

    # TODO need to decide how to determine when a step should be removed via
    # instructions. We don't need to remove steps which are being added for the first
    # time. It could just be assumed that names are unique and then it's a "remove if
    # present" approach.


class TestParallelMergePartitions:
    def test_basic(self):
        # Arrange
        partition1 = Partition(
            prerequisite_component=None,
            nondependent_component="C",
            postrequisite_component=None,
            top_ranked_endpoint="C",
        )
        partition2 = Partition(
            prerequisite_component="A",
            nondependent_component=None,
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )

        # Act
        result, instructions = _parallel_merge_partitions(
            partition1, partition2, predecessor=None
        )

        # Assert
        assert result == Partition(
            prerequisite_component="A",
            nondependent_component="C",
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )
        assert instructions == [
            InsertSuccessor(after=None, step="A"),
            InsertSuccessor(after="A", step="C"),
            InsertSuccessor(after="C", step="B"),
        ]
