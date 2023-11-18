import lea
import pytest
import pandas as pd


@pytest.fixture
def client():
    from lea.clients import duckdb

    return duckdb.DuckDB(":memory:", username=None)


class MockRichConsole:
    def log(self, msg):
        pass


@pytest.mark.parametrize(
    "test_data,query,ok",
    [
        pytest.param(*case, id=f"test_assertion{tag}#{i}")
        for tag, cases in {
            "@UNIQUE": [
                (
                    pd.DataFrame({"test_column": [1, 2, 3, 4, 5]}),
                    """
                    SELECT
                        -- @UNIQUE
                        test_column
                    FROM test_data
                    """,
                    True,
                ),
                (
                    pd.DataFrame(
                        {
                            "test_column": [1, 1, 2, 2, 3],
                        }
                    ),
                    """
                    SELECT
                        -- @UNIQUE
                        test_column
                    FROM test_data
                    """,
                    False,
                ),
                (
                    pd.DataFrame({"test_column": [1, 2, 3, 4, None]}),
                    """
                    SELECT
                        -- @UNIQUE
                        test_column
                    FROM test_data
                    """,
                    True,
                ),
                (
                    pd.DataFrame(
                        {
                            "test_column": [1, 2, 3, None, None],
                        }
                    ),
                    """
                    SELECT
                        -- @UNIQUE
                        test_column
                    FROM test_data
                    """,
                    False,
                ),
            ],
            "@UNIQUE_BY": [
                (
                    pd.DataFrame(
                        {
                            "by": ["a", "a", "b", "b", "c"],
                            "col": [1, 1, 2, 2, 3],
                        }
                    ),
                    """
                    SELECT
                        by,
                        -- @UNIQUE_BY(by)
                        col
                    FROM test_data
                    """,
                    False,
                ),
                (
                    pd.DataFrame(
                        {
                            "by": ["a", "a", "b", "b", "c"],
                            "col": [1, 2, 1, 2, 3],
                        }
                    ),
                    """
                    SELECT
                        by,
                        -- @UNIQUE_BY(by)
                        col
                    FROM test_data
                    """,
                    True,
                ),
                (
                    pd.DataFrame(
                        {
                            "by": ["a", "a", "a", "b", "c"],
                            "col": [1, None, None, 2, 3],
                        }
                    ),
                    """
                    SELECT
                        by,
                        -- @UNIQUE_BY(by)
                        col
                    FROM test_data
                    """,
                    False,
                ),
            ],
            "@NOT_NULL": [
                (
                    pd.DataFrame(
                        {
                            "test_column": [1, 2, 3, 4, 5],
                        }
                    ),
                    """
                    SELECT
                        -- @NOT_NULL
                        test_column
                    FROM test_data
                    """,
                    True,
                ),
                (
                    pd.DataFrame(
                        {
                            "test_column": [1, 2, 3, 4, None],
                        }
                    ),
                    """
                    SELECT
                        -- @NOT_NULL
                        test_column
                    FROM test_data
                    """,
                    False,
                ),
            ],
        }.items()
        for i, case in enumerate(cases, start=1)
    ],
)
def test_duckdb_assertions(test_data, query, ok, client):
    view = lea.views.GenericSQLView(
        schema="tests",
        name=f"test_assertion",
        query=query,
        sqlglot_dialect=client.sqlglot_dialect,
    )
    dummy_console = MockRichConsole()
    client.prepare([view], console=dummy_console)
    client.create(view)

    for test in client.yield_unit_tests(view, test_data.columns):
        conflicts = client.load(test)
        assert conflicts.empty == ok
