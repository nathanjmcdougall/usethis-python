class TestAllTools:
    def test_sorted_alphabetically(self):
        from usethis._tool.all_ import ALL_TOOLS

        names = [tool.name.lower() for tool in ALL_TOOLS]
        assert names == sorted(names)
