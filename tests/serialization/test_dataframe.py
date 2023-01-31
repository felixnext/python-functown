"""Tests for DataFrame Serialization

Copyright (c) 2023, Felix Geilert
"""

from azure.functions import HttpRequest, HttpResponse
import pandas
import pytest

from functown.args import ContentTypes
from functown.serialization import DataFrameResponse, DataFrameRequest


@pytest.fixture
def df_data():
    """Fixture for DataFrame data."""
    return pandas.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@pytest.mark.parametrize(
    "ctype, allow_empty, is_empty, error",
    [
        (ContentTypes.CSV, True, False, None),
        (ContentTypes.CSV, True, True, None),
        (ContentTypes.CSV, False, False, None),
        (ContentTypes.CSV, False, True, ValueError),
        (ContentTypes.JSON, True, False, None),
        (ContentTypes.JSON, True, True, None),
        (ContentTypes.JSON, False, False, None),
        (ContentTypes.JSON, False, True, ValueError),
        (ContentTypes.PARQUET, True, False, None),
        (ContentTypes.PARQUET, True, True, None),
        (ContentTypes.PARQUET, False, False, None),
        (ContentTypes.PARQUET, False, True, ValueError),
    ],
)
def test_dataframe_response(
    df_data, ctype: ContentTypes, allow_empty: bool, is_empty: bool, error: Exception
):
    # test the response for different
    @DataFrameResponse(format=ctype, allow_empty=allow_empty)
    def main(req: HttpRequest) -> pandas.DataFrame:
        return df_data if not is_empty else pandas.DataFrame()

    req = HttpRequest("GET", "http://localhost", body=None)
    if error is not None:
        with pytest.raises(error):
            main(req=req)
        return

    # test response
    res = main(req=req)
    assert isinstance(res, HttpResponse)
    assert res.mimetype == ctype.value

    # check empty
    if is_empty:
        assert res.get_body() == b""
        return

    # decode dataframe based on content type
    if ctype == ContentTypes.CSV:
        df = pandas.read_csv(res.get_body().decode("utf-8"))
    elif ctype == ContentTypes.JSON:
        df = pandas.read_json(res.get_body().decode("utf-8"))
    elif ctype == ContentTypes.PARQUET:
        df = pandas.read_parquet(res.get_body())
    assert df is not None
    assert df.equals(df_data)
