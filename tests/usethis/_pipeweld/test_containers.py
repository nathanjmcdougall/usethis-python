class TestSeries:
    def test_func(self):
        from usethis._pipeweld.containers import Series, series

        assert series("a", "b") == Series(["a", "b"])

    def test_hash_same(self):
        from usethis._pipeweld.containers import Series

        assert hash(Series(["a", "b"])) == hash(Series(["a", "b"]))

    def test_hash_different(self):
        from usethis._pipeweld.containers import Series

        assert hash(Series(["a", "b"])) != hash(Series(["b", "a"]))

    def test_getitem(self):
        from usethis._pipeweld.containers import Series

        assert Series(["a", "b"])[0] == "a"

    def test_setitem(self):
        from usethis._pipeweld.containers import Series

        srs = Series(["a", "b"])
        srs[0] = "c"
        assert srs == Series(["c", "b"])

    def test_eq_same(self):
        from usethis._pipeweld.containers import (
            Series,
        )

        assert Series(["a", "b"]) == Series(["a", "b"])

    def test_eq_different(self):
        from usethis._pipeweld.containers import (
            Series,
        )

        assert Series(["a", "b"]) != Series(["b", "a"])

    def test_eq_wrong_type(self):
        from usethis._pipeweld.containers import (
            Series,
        )

        assert Series(["a", "b"]) != ["a", "b"]

    def test_len(self):
        from usethis._pipeweld.containers import (
            Series,
        )

        assert len(Series(["a", "b"])) == 2


class TestParallel:
    def test_func(self):
        from usethis._pipeweld.containers import Parallel, parallel

        assert parallel("a", "b") == Parallel(frozenset({"a", "b"}))

    def test_hash_same(self):
        from usethis._pipeweld.containers import Parallel

        assert hash(Parallel(frozenset({"a", "b"}))) == hash(
            Parallel(frozenset({"a", "b"}))
        )

    def test_hash_different(self):
        from usethis._pipeweld.containers import Parallel

        assert hash(Parallel(frozenset({"a", "b"}))) != hash(Parallel(frozenset({"a"})))

    def test_or(self):
        from usethis._pipeweld.containers import Parallel

        assert Parallel(frozenset({"a"})) | Parallel(frozenset({"b"})) == Parallel(
            frozenset({"a", "b"})
        )

    def test_eq_same(self):
        from usethis._pipeweld.containers import Parallel

        assert Parallel(frozenset({"a", "b"})) == Parallel(frozenset({"a", "b"}))

    def test_eq_subset(self):
        from usethis._pipeweld.containers import Parallel

        assert Parallel(frozenset({"a", "b"})) != Parallel(frozenset({"a"}))

    def test_eq_superset(self):
        from usethis._pipeweld.containers import Parallel

        assert Parallel(frozenset({"a"})) != Parallel(frozenset({"a", "b"}))

    def test_eq_wrong_type(self):
        from usethis._pipeweld.containers import Parallel

        assert Parallel(frozenset({"a", "b"})) != {"a", "b"}
        assert Parallel(frozenset({"a", "b"})) != frozenset({"a", "b"})

    def test_len(self):
        from usethis._pipeweld.containers import Parallel

        assert len(Parallel(frozenset({"a", "b"}))) == 2


class TestDepGroup:
    def test_func(self):
        from usethis._pipeweld.containers import DepGroup, depgroup, series

        assert depgroup("a", "b", config_group="group") == DepGroup(
            series=series("a", "b"), config_group="group"
        )

    def test_hash_same(self):
        from usethis._pipeweld.containers import DepGroup, series

        assert hash(DepGroup(series=series("a", "b"), config_group="group")) == hash(
            DepGroup(series=series("a", "b"), config_group="group")
        )

    def test_hash_different(self):
        from usethis._pipeweld.containers import DepGroup, series

        assert hash(DepGroup(series=series("a", "b"), config_group="group")) != hash(
            DepGroup(series=series("b", "a"), config_group="group")
        )
