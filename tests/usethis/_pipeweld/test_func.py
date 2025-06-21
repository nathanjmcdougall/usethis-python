import pytest


class TestAdder:
    class TestAdd:
        def test_empty_series_start(self):
            # Arrange
            from usethis._pipeweld.containers import series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.ops import InsertParallel
            from usethis._pipeweld.result import WeldResult

            step = "A"
            pipeline = series()

            # Act
            result = Adder(pipeline=pipeline, step=step).add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.instructions == [
                # N.B. None means Place at the start of the pipeline
                InsertParallel(after=None, step="A")
            ]
            assert result.solution == series("A")

        def test_series_singleton_start(self):
            # Arrange
            from usethis._pipeweld.containers import parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.ops import InsertParallel
            from usethis._pipeweld.result import WeldResult

            adder = Adder(step="B", pipeline=series("A"))

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.instructions == [
                # N.B. None means Place at the start of the pipeline
                InsertParallel(after=None, step="B")
            ]
            assert result.solution == series(parallel("A", "B"))

        def test_parallel_singleton_start(self):
            # Arrange
            from usethis._pipeweld.containers import parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.ops import InsertParallel
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="B",
                pipeline=series(parallel("A")),
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.instructions == [
                # N.B. None means Place at the start of the pipeline
                InsertParallel(after=None, step="B")
            ]
            assert result.solution == series(parallel("A", "B"))

        def test_two_element_start(self):
            # Arrange
            from usethis._pipeweld.containers import parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.ops import InsertParallel
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="C",
                pipeline=series("A", "B"),
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.instructions == [
                # N.B. None means Place at the start of the pipeline
                InsertParallel(after=None, step="C")
            ]
            assert result.solution == series(parallel("A", "C"), "B")

        def test_prerequisite(self):
            # Arrange
            from usethis._pipeweld.containers import parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.ops import InsertParallel
            from usethis._pipeweld.result import WeldResult

            prerequisites = {"A"}
            adder = Adder(
                step="C",
                pipeline=series("A", "B"),
                prerequisites=prerequisites,
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.instructions == [InsertParallel(after="A", step="C")]
            assert result.solution == series("A", parallel("B", "C"))

        def test_mixed_dependency_parallelism_of_steps(self):
            # Arrange
            from usethis._pipeweld.containers import parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.ops import InsertSuccessor
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="C",
                pipeline=series(parallel("A", "B")),
                prerequisites={"A"},
                postrequisites={"B"},
            )

            # Act
            result = adder.add()

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
            from usethis._pipeweld.containers import parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.ops import InsertParallel, InsertSuccessor
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="F",
                pipeline=series("A", parallel(series("B", "D"), series("C", "E"))),
                prerequisites={"B"},
                postrequisites={"E"},
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series("A", "B", parallel("D", "C", "F"), "E")
            assert result.instructions == [
                InsertSuccessor(after="A", step="B"),
                InsertSuccessor(after="B", step="C"),
                InsertParallel(after="B", step="D"),
                InsertSuccessor(after="C", step="E"),
                InsertParallel(after="B", step="F"),
            ]

        def test_singleton_series(self):
            # Arrange
            from usethis._pipeweld.containers import parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="B",
                pipeline=series("A"),
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series(parallel("A", "B"))

        def test_nested_series(self):
            # Arrange
            from usethis._pipeweld.containers import parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="B",
                pipeline=series(series("A")),
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series(series(parallel("A", "B")))

        class TestDoubleNesting:
            """A series of related tests building up to a complex case"""

            def test_no_nesting(self):
                # Arrange
                from usethis._pipeweld.containers import parallel, series
                from usethis._pipeweld.func import Adder
                from usethis._pipeweld.result import WeldResult

                adder = Adder(
                    step="H",
                    pipeline=series("D", "E", "F"),
                    prerequisites={"A"},
                    postrequisites={"B", "E"},
                )

                # Act
                result = adder.add()

                # Assert
                assert isinstance(result, WeldResult)
                assert result.solution == series(parallel("D", "H"), "E", "F")

            def test_single_nesting(self):
                # Arrange
                from usethis._pipeweld.containers import parallel, series
                from usethis._pipeweld.func import Adder
                from usethis._pipeweld.result import WeldResult

                adder = Adder(
                    step="H",
                    pipeline=series(series("D", "E", "F")),
                )

                # Act
                result = adder.add()

                # Assert
                assert isinstance(result, WeldResult)
                assert result.solution == series(series(parallel("D", "H"), "E", "F"))

            def test_single_nesting_with_dep(self):
                # Arrange
                from usethis._pipeweld.containers import parallel, series
                from usethis._pipeweld.func import Adder
                from usethis._pipeweld.result import WeldResult

                adder = Adder(
                    step="H",
                    pipeline=series(series("D", "E", "F")),
                    prerequisites={"A"},
                    postrequisites={"B", "E"},
                )

                # Act
                result = adder.add()

                # Assert
                assert isinstance(result, WeldResult)
                assert result.solution == series(parallel("D", "H"), series("E", "F"))

            def test_multiple_nesting(self):
                # Arrange
                from usethis._pipeweld.containers import parallel, series
                from usethis._pipeweld.func import Adder
                from usethis._pipeweld.result import WeldResult

                adder = Adder(
                    step="H",
                    pipeline=series(series(parallel(series("D", "E", "F")))),
                    prerequisites={"A"},
                    postrequisites={"B", "E"},
                )

                # Act
                result = adder.add()

                # Assert
                assert isinstance(result, WeldResult)
                assert result.solution == series(
                    series(parallel(series(parallel("D", "H"), "E", "F")))
                )

            def test_full_complex_case(self):
                # Arrange
                from usethis._pipeweld.containers import parallel, series
                from usethis._pipeweld.func import Adder
                from usethis._pipeweld.result import WeldResult

                adder = Adder(
                    step="H",
                    pipeline=series(
                        parallel("A", "B"),
                        "C",
                        series(parallel(series("D", "E", "F"), "G")),
                    ),
                    prerequisites={"A"},
                    postrequisites={"B", "E"},
                )

                # Act
                result = adder.add()

                # Assert
                assert isinstance(result, WeldResult)
                assert result.solution == series(
                    "A", "H", "B", "C", parallel(series("D", "E", "F"), "G")
                )

        def test_multi_level_heirarchy(self):
            # Arrange
            from usethis._pipeweld.containers import parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.ops import InsertParallel
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="E",
                pipeline=series("A", parallel("B", series("C", "D"))),
                prerequisites={"C"},
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series(
                "A", parallel("B", series("C", parallel("D", "E")))
            )
            assert result.instructions == [InsertParallel(after="C", step="E")]

        def test_mixed_dependency_parallelism_of_series_pure_parallel(self):
            # Arrange
            from usethis._pipeweld.containers import parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="E",
                pipeline=series(parallel(series("A", "B"), series("C", "D"))),
                prerequisites={"A"},
                postrequisites={"D"},
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series("A", parallel("C", "E", "B"), "D")

        def test_config_groups(self):
            # Arrange
            from usethis._pipeweld.containers import depgroup, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="A",
                pipeline=series(depgroup("B", "C", config_group="x")),
                prerequisites={"B"},
                postrequisites={"C"},
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series(
                depgroup("B", config_group="x"), "A", depgroup("C", config_group="x")
            )

        def test_config_groups_in_series(self):
            # Arrange
            from usethis._pipeweld.containers import depgroup, parallel, series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="E",
                pipeline=series("A", depgroup("B", "C", config_group="x")),
                prerequisites={"B"},
                compatible_config_groups={"x"},
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series(
                "A",
                depgroup("B", config_group="x"),
                parallel(depgroup("C", config_group="x"), "E"),
            )

        def test_insert_at_end(self):
            # Arrange
            from usethis._pipeweld.containers import series
            from usethis._pipeweld.func import Adder
            from usethis._pipeweld.result import WeldResult

            adder = Adder(
                step="C",
                pipeline=series("A", "B"),
                prerequisites={"B"},
            )

            # Act
            result = adder.add()

            # Assert
            assert isinstance(result, WeldResult)
            assert result.solution == series("A", "B", "C")


class TestParallelMergePartitions:
    def test_basic(self):
        # Arrange
        from usethis._pipeweld.func import Partition, _parallel_merge_partitions
        from usethis._pipeweld.ops import InsertSuccessor

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


class TestFlattenPartition:
    def test_basic(self):
        # Arrange
        from usethis._pipeweld.containers import series
        from usethis._pipeweld.func import Partition, _flatten_partition

        partition = Partition(
            prerequisite_component="A",
            nondependent_component="B",
            postrequisite_component="C",
            top_ranked_endpoint="C",
        )

        # Act
        result = _flatten_partition(partition)

        # Assert
        assert result == series("A", "B", "C")

    def test_no_components(self):
        # Arrange
        from usethis._pipeweld.func import Partition, _flatten_partition

        partition = Partition(
            prerequisite_component=None,
            nondependent_component=None,
            postrequisite_component=None,
            top_ranked_endpoint="fake",
        )

        # Act, Assert
        with pytest.raises(ValueError, match="Flatten failed: no components"):
            _flatten_partition(partition)


class TestOpSeriesMergePartitions:
    def test_rhs_prerequisite_lhs_no_prerequisite(self):
        # Arrange
        from usethis._pipeweld.containers import series
        from usethis._pipeweld.func import Partition, _op_series_merge_partitions

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
        partition = _op_series_merge_partitions(partition1, partition2)

        # Assert
        assert partition == Partition(
            prerequisite_component=series("C", "A"),
            nondependent_component=None,
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )

    def test_both_prerequisite(self):
        # Arrange
        from usethis._pipeweld.containers import series
        from usethis._pipeweld.func import Partition, _op_series_merge_partitions

        partition1 = Partition(
            prerequisite_component="A",
            nondependent_component=None,
            postrequisite_component=None,
            top_ranked_endpoint="A",
        )
        partition2 = Partition(
            prerequisite_component="B",
            nondependent_component=None,
            postrequisite_component=None,
            top_ranked_endpoint="B",
        )

        # Act
        partition = _op_series_merge_partitions(partition1, partition2)

        # Assert
        assert partition == Partition(
            prerequisite_component=series("A", "B"),
            nondependent_component=None,
            postrequisite_component=None,
            top_ranked_endpoint="B",
        )

    def test_no_rhs_prerequsite_rhs_non_dependent_and_lhs_postrequsite(self):
        # Arrange
        from usethis._pipeweld.containers import series
        from usethis._pipeweld.func import Partition, _op_series_merge_partitions

        partition1 = Partition(
            prerequisite_component="A",
            nondependent_component=None,
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )
        partition2 = Partition(
            prerequisite_component=None,
            nondependent_component="C",
            postrequisite_component=None,
            top_ranked_endpoint="C",
        )

        # Act
        partition = _op_series_merge_partitions(partition1, partition2)

        # Assert
        assert partition == Partition(
            prerequisite_component="A",
            nondependent_component=None,
            postrequisite_component=series("B", "C"),
            top_ranked_endpoint="C",
        )

    def test_both_prerequisite_rhs_non_dependent_and_lhs_postrequsite(self):
        # Arrange
        from usethis._pipeweld.containers import series
        from usethis._pipeweld.func import Partition, _op_series_merge_partitions

        partition1 = Partition(
            prerequisite_component="A",
            nondependent_component=None,
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )
        partition2 = Partition(
            prerequisite_component="D",
            nondependent_component="C",
            postrequisite_component=None,
            top_ranked_endpoint="C",
        )

        # Act
        partition = _op_series_merge_partitions(partition1, partition2)

        # Assert
        assert partition == Partition(
            prerequisite_component=series("A", "B", "D"),
            nondependent_component="C",
            postrequisite_component=None,
            top_ranked_endpoint="C",
        )

    def test_no_prerequsites_rhs_non_dependent_and_lhs_postrequsite(self):
        # Arrange
        from usethis._pipeweld.containers import series
        from usethis._pipeweld.func import Partition, _op_series_merge_partitions

        partition1 = Partition(
            prerequisite_component=None,
            nondependent_component=None,
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )
        partition2 = Partition(
            prerequisite_component=None,
            nondependent_component="A",
            postrequisite_component=None,
            top_ranked_endpoint="A",
        )

        # Act
        partition = _op_series_merge_partitions(partition1, partition2)

        # Assert
        assert partition == Partition(
            prerequisite_component=None,
            nondependent_component=None,
            postrequisite_component=series("B", "A"),
            top_ranked_endpoint="A",
        )

    def test_no_prequisites_and_no_nondependents_both_postrequisites(self):
        # Arrange
        from usethis._pipeweld.containers import series
        from usethis._pipeweld.func import Partition, _op_series_merge_partitions

        partition1 = Partition(
            prerequisite_component=None,
            nondependent_component=None,
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )
        partition2 = Partition(
            prerequisite_component=None,
            nondependent_component=None,
            postrequisite_component="A",
            top_ranked_endpoint="A",
        )

        # Act
        partition = _op_series_merge_partitions(partition1, partition2)

        # Assert
        assert partition == Partition(
            prerequisite_component=None,
            nondependent_component=None,
            postrequisite_component=series("B", "A"),
            top_ranked_endpoint="A",
        )

    def test_no_rhs_prequisite_and_lhs_prerequisite_and_no_nondependents(self):
        # Arrange
        from usethis._pipeweld.func import Partition, _op_series_merge_partitions

        partition1 = Partition(
            prerequisite_component="A",
            nondependent_component=None,
            postrequisite_component=None,
            top_ranked_endpoint="A",
        )
        partition2 = Partition(
            prerequisite_component=None,
            nondependent_component=None,
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )

        # Act
        partition = _op_series_merge_partitions(partition1, partition2)

        # Assert
        assert partition == Partition(
            prerequisite_component="A",
            nondependent_component=None,
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )

    def test_rhs_nondependents_and_no_prequisites_and_lhs_prerequisite_and_nondependents(
        self,
    ):
        # Arrange
        from usethis._pipeweld.containers import series
        from usethis._pipeweld.func import Partition, _op_series_merge_partitions

        partition1 = Partition(
            prerequisite_component="A",
            nondependent_component="C",
            postrequisite_component=None,
            top_ranked_endpoint="A",
        )
        partition2 = Partition(
            prerequisite_component=None,
            nondependent_component="B",
            postrequisite_component=None,
            top_ranked_endpoint="B",
        )

        # Act
        partition = _op_series_merge_partitions(partition1, partition2)

        # Assert
        assert partition == Partition(
            prerequisite_component="A",
            nondependent_component=series("C", "B"),
            postrequisite_component=None,
            top_ranked_endpoint="B",
        )

    def test_rhs_no_nondependents_and_no_prequisites_and_lhs_prerequisite_and_nondependents(
        self,
    ):
        # Arrange
        from usethis._pipeweld.func import Partition, _op_series_merge_partitions

        partition1 = Partition(
            prerequisite_component="A",
            nondependent_component="C",
            postrequisite_component=None,
            top_ranked_endpoint="A",
        )
        partition2 = Partition(
            prerequisite_component=None,
            nondependent_component=None,
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )

        # Act
        partition = _op_series_merge_partitions(partition1, partition2)

        # Assert
        assert partition == Partition(
            prerequisite_component="A",
            nondependent_component="C",
            postrequisite_component="B",
            top_ranked_endpoint="B",
        )
