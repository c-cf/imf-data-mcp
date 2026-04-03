"""Integration tests for the imfp-based MCP tools."""
import json
import pytest
from unittest.mock import patch
import pandas as pd

import imf_data_mcp as server
from imf_data_mcp import (
    SearchDatabasesInput,
    DatabaseIdInput,
    GetCodesInput,
    FetchDataInput,
)

DATABASES_DF = pd.DataFrame([
    {"database_id": "CPI",     "description": "Consumer Price Index (CPI)"},
    {"database_id": "PCPS",    "description": "Primary Commodity Price System"},
    {"database_id": "BOP_AGG", "description": "Balance of Payments (BOP)"},
])
PARAM_DEFS_DF = pd.DataFrame([
    {"parameter": "country",   "description": "Country"},
    {"parameter": "frequency", "description": "Frequency"},
])
PARAM_CODES = {
    "country":   pd.DataFrame([{"input_code": "AUT", "description": "Austria"},
                                {"input_code": "DEU", "description": "Germany"}]),
    "frequency": pd.DataFrame([{"input_code": "A", "description": "Annual"},
                                {"input_code": "M", "description": "Monthly"}]),
}
DATA_DF = pd.DataFrame([
    {"country": "AUT", "frequency": "A", "time_period": "2022", "obs_value": 5.8},
    {"country": "AUT", "frequency": "A", "time_period": "2023", "obs_value": 7.7},
])

@pytest.mark.asyncio
async def test_list_databases_returns_json_array():
    with patch("imfp.imf_databases", return_value=DATABASES_DF):
        result = await server.imf_list_databases()
    data = json.loads(result)
    assert isinstance(data, list) and len(data) == 3

@pytest.mark.asyncio
async def test_search_databases_finds_match():
    with patch("imfp.imf_databases", return_value=DATABASES_DF):
        result = await server.imf_search_databases(SearchDatabasesInput(keyword="price"))
    assert len(json.loads(result)) == 2

@pytest.mark.asyncio
async def test_search_databases_case_insensitive():
    with patch("imfp.imf_databases", return_value=DATABASES_DF):
        r1 = await server.imf_search_databases(SearchDatabasesInput(keyword="balance of payments"))
        r2 = await server.imf_search_databases(SearchDatabasesInput(keyword="Balance of Payments"))
    assert json.loads(r1) == json.loads(r2)

@pytest.mark.asyncio
async def test_search_databases_no_match():
    with patch("imfp.imf_databases", return_value=DATABASES_DF):
        result = await server.imf_search_databases(SearchDatabasesInput(keyword="zzznomatch"))
    assert "message" in json.loads(result)

@pytest.mark.asyncio
async def test_get_parameter_defs_returns_list():
    with patch("imfp.imf_parameter_defs", return_value=PARAM_DEFS_DF):
        result = await server.imf_get_parameter_defs(DatabaseIdInput(database_id="CPI"))
    assert json.loads(result)[0]["parameter"] == "country"

@pytest.mark.asyncio
async def test_get_parameter_defs_invalid_db():
    with patch("imfp.imf_parameter_defs", side_effect=ValueError("not found")):
        result = await server.imf_get_parameter_defs(DatabaseIdInput(database_id="NOTEXIST"))
    data = json.loads(result)
    assert "error" in data and "hint" in data

@pytest.mark.asyncio
async def test_get_parameter_codes_all_params():
    with patch("imfp.imf_parameters", return_value=PARAM_CODES):
        result = await server.imf_get_parameter_codes(GetCodesInput(database_id="CPI"))
    data = json.loads(result)
    assert "country" in data and "frequency" in data

@pytest.mark.asyncio
async def test_get_parameter_codes_single_param():
    with patch("imfp.imf_parameters", return_value=PARAM_CODES):
        result = await server.imf_get_parameter_codes(
            GetCodesInput(database_id="CPI", parameter="country"))
    assert list(json.loads(result).keys()) == ["country"]

@pytest.mark.asyncio
async def test_get_parameter_codes_search_filter():
    with patch("imfp.imf_parameters", return_value=PARAM_CODES):
        result = await server.imf_get_parameter_codes(
            GetCodesInput(database_id="CPI", parameter="country", search="austria"))
    data = json.loads(result)
    assert len(data["country"]) == 1 and data["country"][0]["input_code"] == "AUT"

@pytest.mark.asyncio
async def test_get_parameter_codes_invalid_param():
    with patch("imfp.imf_parameters", return_value=PARAM_CODES):
        result = await server.imf_get_parameter_codes(
            GetCodesInput(database_id="CPI", parameter="notexist"))
    data = json.loads(result)
    assert "error" in data and "available_parameters" in data

@pytest.mark.asyncio
async def test_get_parameter_codes_invalid_db():
    with patch("imfp.imf_parameters", side_effect=ValueError("not found")):
        result = await server.imf_get_parameter_codes(GetCodesInput(database_id="NOTEXIST"))
    data = json.loads(result)
    assert "error" in data and "hint" in data

@pytest.mark.asyncio
async def test_fetch_data_returns_rows():
    with patch("imfp.imf_dataset", return_value=DATA_DF):
        result = await server.imf_fetch_data(FetchDataInput(
            database_id="CPI", start_year=2022, end_year=2023,
            filters={"country": ["AUT"], "frequency": ["A"]}))
    data = json.loads(result)
    assert data["row_count"] == 2 and data["rows"][0]["country"] == "AUT"

@pytest.mark.asyncio
async def test_fetch_data_respects_max_rows():
    big_df = pd.DataFrame([{"country": "AUT", "time_period": str(y), "obs_value": 1.0}
                            for y in range(2000)])
    with patch("imfp.imf_dataset", return_value=big_df):
        result = await server.imf_fetch_data(FetchDataInput(database_id="CPI", max_rows=10))
    data = json.loads(result)
    assert data["row_count"] == 10 and data["truncated"] is True

@pytest.mark.asyncio
async def test_fetch_data_empty_result():
    with patch("imfp.imf_dataset", return_value=pd.DataFrame()):
        result = await server.imf_fetch_data(
            FetchDataInput(database_id="CPI", filters={"country": ["ZZZ"]}))
    assert json.loads(result)["row_count"] == 0

@pytest.mark.asyncio
async def test_fetch_data_invalid_db():
    with patch("imfp.imf_dataset", side_effect=ValueError("not found")):
        result = await server.imf_fetch_data(FetchDataInput(database_id="NOTEXIST"))
    data = json.loads(result)
    assert "error" in data and "hint" in data

@pytest.mark.asyncio
async def test_fetch_data_passes_filters_as_kwargs():
    with patch("imfp.imf_dataset", return_value=DATA_DF) as mock_ds:
        await server.imf_fetch_data(FetchDataInput(
            database_id="CPI", start_year=2022, end_year=2023,
            filters={"country": ["AUT"], "frequency": ["A"]}))
    _, kwargs = mock_ds.call_args
    assert kwargs.get("country") == ["AUT"]
    assert kwargs.get("start_year") == 2022
