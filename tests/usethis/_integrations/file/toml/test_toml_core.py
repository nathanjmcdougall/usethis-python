# TODO these tests need to be migrated out of here into the test_io_.py file


# class TestGetTOMLValue:
#     def test_no_keys_raises(self):
#         # Arrange
#         toml_document = TOMLDocument()

#         # Act
#         with pytest.raises(ValueError, match="At least one ID key must be provided."):
#             set_toml_value(toml_document=toml_document, id_keys=[], value="d")


# class TestSetTOMLValue:
#     def test_no_inplace_modifications(self):
#         # Arrange
#         toml_document = TOMLDocument()
#         toml_document["a"] = "b"
#         original = toml_document.copy()

#         # Act
#         new_toml_document = set_toml_value(
#             toml_document=toml_document, id_keys=["c"], value="d"
#         )

#         # Assert
#         assert not (new_toml_document == original)
#         assert toml_document == original

#     def test_no_keys_raises(self):
#         # Arrange
#         toml_document = TOMLDocument()

#         # Act
#         with pytest.raises(ValueError, match="At least one ID key must be provided."):
#             set_toml_value(toml_document=toml_document, id_keys=[], value="d")


# class TestRemoveTOMLValue:
#     def test_no_inplace_modifications(self):
#         # Arrange
#         toml_document = TOMLDocument()
#         toml_document["a"] = "b"
#         original = toml_document.copy()

#         # Act
#         new_toml_document = remove_toml_value(
#             toml_document=toml_document, id_keys=["a"]
#         )

#         # Assert
#         assert not (new_toml_document == original)
#         assert toml_document == original

#     def test_no_keys_raises(self):
#         # Arrange
#         toml_document = TOMLDocument()

#         # Act
#         with pytest.raises(ValueError, match="At least one ID key must be provided."):
#             remove_toml_value(toml_document=toml_document, id_keys=[])


# class TestExtendTOMLList:
#     def test_no_inplace_modifications(self):
#         # Arrange
#         toml_document = TOMLDocument()
#         toml_document["a"] = ["b"]
#         original = toml_document.copy()

#         # Act
#         new_toml_document = extend_toml_list(
#             toml_document=toml_document, id_keys=["a"], values=["c", "d"]
#         )

#         # Assert
#         assert not (new_toml_document == original)
#         assert toml_document == original

#     def test_no_keys_raises(self):
#         # Arrange
#         toml_document = TOMLDocument()

#         # Act
#         with pytest.raises(ValueError, match="At least one ID key must be provided."):
#             extend_toml_list(toml_document=toml_document, id_keys=[], values=["c", "d"])


# class TestRemoveFromTOMLList:
#     def test_no_inplace_modifications(self):
#         # Arrange
#         toml_document = TOMLDocument()
#         toml_document["a"] = ["b", "c", "d"]
#         original = toml_document.copy()

#         # Act
#         new_toml_document = remove_from_toml_list(
#             toml_document=toml_document, id_keys=["a"], values=["c"]
#         )

#         # Assert
#         assert not (new_toml_document == original)
#         assert toml_document == original

#     def test_no_keys_raises(self):
#         # Arrange
#         toml_document = TOMLDocument()

#         # Act
#         with pytest.raises(ValueError, match="At least one ID key must be provided."):
#             remove_from_toml_list(toml_document=toml_document, id_keys=[], values=["c"])

#     def test_already_not_present(self):
#         # Arrange
#         toml_document = TOMLDocument()
#         toml_document["a"] = ["b", "d"]
#         original = toml_document.copy()

#         # Act
#         new_toml_document = remove_from_toml_list(
#             toml_document=toml_document, id_keys=["c"], values=["e"]
#         )

#         # Assert
#         assert new_toml_document == original
