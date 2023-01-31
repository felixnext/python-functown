"""Tests for DataFrame Serialization

Copyright (c) 2023, Felix Geilert
"""

from azure.functions import HttpRequest, HttpResponse
import pandas
import pytest
from io import StringIO, BytesIO

from functown.args import ContentTypes
from functown.serialization import DataFrameResponse, DataFrameRequest, DataFrameFormat


DF_MAP = {
    DataFrameFormat.CSV: ContentTypes.CSV,
    DataFrameFormat.JSON: ContentTypes.JSON,
    DataFrameFormat.PARQUET: ContentTypes.BINARY,
}


@pytest.fixture
def df_data():
    """Fixture for DataFrame data."""
    return pandas.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@pytest.mark.parametrize(
    "ctype, allow_empty, is_empty, error",
    [
        (DataFrameFormat.CSV, False, False, None),
        (DataFrameFormat.CSV, True, True, None),
        (DataFrameFormat.CSV, False, True, ValueError),
        (DataFrameFormat.JSON, False, False, None),
        (DataFrameFormat.JSON, True, True, None),
        (DataFrameFormat.JSON, False, True, ValueError),
        (DataFrameFormat.PARQUET, False, False, None),
        (DataFrameFormat.PARQUET, True, True, None),
        (DataFrameFormat.PARQUET, False, True, ValueError),
    ],
)
def test_dataframe_response(
    df_data, ctype: DataFrameFormat, allow_empty: bool, is_empty: bool, error: Exception
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
    assert res.mimetype == DF_MAP[ctype.value]

    # check empty
    if is_empty:
        assert res.get_body() == b""
        return

    # decode dataframe based on content type
    if ctype == DataFrameFormat.CSV:
        df = pandas.read_csv(StringIO(res.get_body().decode("utf-8")))
    elif ctype == DataFrameFormat.JSON:
        df = pandas.read_json(StringIO(res.get_body().decode("utf-8")))
    elif ctype == DataFrameFormat.PARQUET:
        df = pandas.read_parquet(BytesIO(res.get_body()))
    assert df is not None
    assert df.equals(df_data)
