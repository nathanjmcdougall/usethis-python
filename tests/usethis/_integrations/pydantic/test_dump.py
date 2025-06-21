from typing import Literal


class TestFancyModelDump:
    def test_base_model(self):
        # Arrange
        from pydantic import BaseModel

        from usethis._integrations.pydantic.dump import fancy_model_dump

        class MyBaseModel(BaseModel):
            x: int
            y: float

        mbm = MyBaseModel(x=1, y=2.0)

        # Act
        output = fancy_model_dump(mbm)

        # Assert
        assert output == {"x": 1, "y": 2.0}

    def test_list_remove_element(self):
        # Arrange
        from pydantic import RootModel

        from usethis._integrations.pydantic.dump import fancy_model_dump

        class MyRootModel(RootModel):
            root: list[int]

        mrm = MyRootModel([1, 3])

        # Act
        output = fancy_model_dump(mrm, reference=[1, 2, 3])

        # Assert
        assert output == [1, 3]

    def test_alias(self):
        # Arrange
        from pydantic import BaseModel, Field

        from usethis._integrations.pydantic.dump import fancy_model_dump

        class MyModel(BaseModel):
            x: int
            y: float = Field(alias="z")

        mm = MyModel(x=1, z=2.0)

        # Act
        output = fancy_model_dump(mm)

        # Assert
        assert output == {"x": 1, "z": 2.0}

    class TestRootModel:
        def test_singleton_list(self):
            # Arrange
            from pydantic import RootModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyRootModel(RootModel):
                root: list[int]

            mrm = MyRootModel([2])

            # Act
            output = fancy_model_dump(mrm)

            # Assert
            assert output == [2]

        def test_list_length_differs_ref_length(self):
            # Arrange
            from pydantic import BaseModel, RootModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MySubModel(BaseModel):
                x: Literal[0, 1] = 1
                y: Literal[0, 1] = 0

            class MyRootModel(RootModel):
                root: list[MySubModel]

            mrm = MyRootModel(
                [
                    MySubModel(x=0, y=0),
                    MySubModel(x=0, y=1),
                    MySubModel(x=1, y=0),
                    MySubModel(x=1, y=0),
                ]
            )

            # Act
            output = fancy_model_dump(mrm, reference=[2, 3, MySubModel(x=1, y=0)])

            # Assert
            assert output == [
                {"x": 0},
                {"x": 0, "y": 1},
                {"x": 1, "y": 0},
                {},
            ]

        def test_mismatch_list_ref(self):
            # Arrange
            from pydantic import RootModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyRootModel(RootModel):
                root: list[int]

            mrm = MyRootModel([2])

            # Act
            output = fancy_model_dump(mrm, reference=3)

            # Assert
            assert output == [2]

        def test_constant(self):
            # Arrange
            from pydantic import RootModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyRootModel(RootModel):
                root: str

            mrm = MyRootModel("yo")

            # Act
            output = fancy_model_dump(mrm)

            # Assert
            assert output == "yo"

        def test_basemodel(self):
            # Arrange
            from pydantic import BaseModel, RootModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MySubModel(BaseModel):
                x: int = -1
                y: int = 0
                z: int = 1
                w: int

            class MyRootModel(RootModel):
                root: MySubModel

            mrm = MyRootModel(MySubModel(x=-1, y=1, z=1, w=2))

            # Act
            output = fancy_model_dump(mrm, reference={"x": -1, "y": 0})

            # Assert
            assert output == {"x": -1, "y": 1, "w": 2}

    def test_bool_type(self):
        # Arrange
        from pydantic import RootModel

        from usethis._integrations.pydantic.dump import fancy_model_dump

        class MyRootModel(RootModel):
            root: list[bool]

        mrm = MyRootModel([False, True])

        # Act
        output = fancy_model_dump(mrm)

        # Assert
        assert output == [False, True]

    class TestNesting:
        def test_basemodel(self):
            # Arrange
            from pydantic import BaseModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyInnerModel(BaseModel):
                x: int

            class MyOuterModel(BaseModel):
                mim: MyInnerModel

            mom = MyOuterModel(mim=MyInnerModel(x=-1))

            # Act
            output = fancy_model_dump(mom)

            # Assert
            assert output == {"mim": {"x": -1}}

        def test_rootmodel(self):
            # Arrange
            from pydantic import RootModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyInnerModel(RootModel):
                root: list[str]

            class MyOuterModel(RootModel):
                root: list[MyInnerModel]

            mom = MyOuterModel([MyInnerModel(["hello"])])

            # Act
            output = fancy_model_dump(mom)

            # Assert
            assert output == [["hello"]]

    class TestCustomOrder:
        def test_unnested(self):
            # Arrange
            from pydantic import BaseModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyBaseModel(BaseModel):
                x: int
                y: float

            mbm = MyBaseModel(x=1, y=2.0)

            # Act
            output = fancy_model_dump(mbm, order_by_cls={MyBaseModel: ["y", "x"]})

            # Assert
            assert isinstance(output, dict)
            assert list(output.keys()) == ["y", "x"]

        def test_nested(self):
            # Arrange
            from pydantic import BaseModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyInnerModel(BaseModel):
                x: int
                y: float

            class MyOuterModel(BaseModel):
                mim: MyInnerModel

            mom = MyOuterModel(mim=MyInnerModel(x=1, y=2.0))

            # Act
            output = fancy_model_dump(mom, order_by_cls={MyInnerModel: ["y", "x"]})

            # Assert
            assert isinstance(output, dict)
            assert isinstance(output["mim"], dict)
            assert list(output["mim"].keys()) == ["y", "x"]

    class TestReference:
        def test_no_reference_drop_default(self):
            # Arrange
            from pydantic import BaseModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyModel(BaseModel):
                x: int
                y: float = 2.0

            mm = MyModel(x=1)

            # Act
            output = fancy_model_dump(mm)

            # Assert
            assert output == {"x": 1}

        def test_keep_default(self):
            # Arrange
            from pydantic import BaseModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyModel(BaseModel):
                x: int
                y: float = 2.0

            mm = MyModel(x=1)
            ref = {"x": 0, "y": 2.0}

            # Act
            output = fancy_model_dump(mm, reference=ref)

            # Assert
            assert output == {"x": 1, "y": 2.0}

        def test_nondefault(self):
            # Arrange
            from pydantic import BaseModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyModel(BaseModel):
                x: int
                y: float = 2.0

            mm = MyModel(x=1)
            ref = MyModel(x=0, y=3.0)

            # Act
            output = fancy_model_dump(mm, reference=ref)

            # Assert
            assert output == {"x": 1}

        def test_nested(self):
            # Arrange
            from pydantic import BaseModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyInnerModel(BaseModel):
                x: int
                y: float = 2.0

            class MyOuterModel(BaseModel):
                mim: MyInnerModel

            mom = MyOuterModel(mim=MyInnerModel(x=1))
            ref = MyOuterModel(mim=MyInnerModel(x=0, y=2.0))

            # Act
            output = fancy_model_dump(mom, reference=ref)

            # Assert
            assert output == {"mim": {"x": 1, "y": 2.0}}

        def test_drop_default_with_ref(self):
            # Arrange
            from pydantic import BaseModel

            from usethis._integrations.pydantic.dump import fancy_model_dump

            class MyModel(BaseModel):
                x: int = 1

            mm = MyModel(x=1)
            ref = {}

            # Act
            output = fancy_model_dump(mm, reference=ref)

            # Assert
            assert output == {}
