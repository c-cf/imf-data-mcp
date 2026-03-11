"""Integration tests for MCP tools using mocked HTTP requests."""
import json
import os
import pytest
from unittest.mock import patch, MagicMock
import imf_data_mcp as server


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Build a mock requests.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status.return_value = None
    return mock


def _imf_response(country: str, time: str, value: str) -> dict:
    """Minimal IMF CompactData response."""
    return {
        "CompactData": {
            "DataSet": {
                "Series": {
                    "@REF_AREA": country,
                    "Obs": {"@TIME_PERIOD": time, "@OBS_VALUE": value},
                }
            }
        }
    }


# --- fetch_ifs_data ---

def test_fetch_ifs_data_success():
    payload = _imf_response("US", "2020", "21427.7")
    with patch("requests.get", return_value=_mock_response(payload)):
        result = server.fetch_ifs_data("A", "US", "NGDP_XDC", 2020, 2020)
    assert "US" in result
    assert "2020" in result
    assert "21427.70" in result


def test_fetch_ifs_data_invalid_freq():
    result = server.fetch_ifs_data("X", "US", "NGDP_XDC", 2020, 2020)
    assert "Invalid frequency" in result or "Error" in result


def test_fetch_ifs_data_freq_normalized():
    """Lowercase freq should be accepted and normalized."""
    payload = _imf_response("JP", "2019", "5.00")
    with patch("requests.get", return_value=_mock_response(payload)) as mock_get:
        result = server.fetch_ifs_data("a", "JP", "NGDP_XDC", 2019, 2019)
    assert "JP" in result
    # Check that the URL used uppercase freq
    called_url = mock_get.call_args[0][0]
    assert "/A.JP.NGDP_XDC" in called_url


def test_fetch_ifs_data_rate_limit():
    mock = MagicMock()
    mock.status_code = 429
    with patch("requests.get", return_value=mock):
        result = server.fetch_ifs_data("A", "US", "NGDP_XDC", 2020, 2020)
    assert "429" in result or "Rate limit" in result


def test_fetch_ifs_data_bad_request():
    mock = MagicMock()
    mock.status_code = 400
    with patch("requests.get", return_value=mock):
        result = server.fetch_ifs_data("A", "BADCODE", "BADIND", 2020, 2020)
    assert "400" in result or "Bad request" in result


def test_fetch_ifs_data_uses_https():
    payload = _imf_response("US", "2020", "1.0")
    with patch("requests.get", return_value=_mock_response(payload)) as mock_get:
        server.fetch_ifs_data("A", "US", "NGDP_XDC", 2020, 2020)
    url = mock_get.call_args[0][0]
    assert url.startswith("https://"), f"Expected HTTPS, got: {url}"


# --- fetch_dot_data ---

def test_fetch_dot_data_success():
    payload = _imf_response("US", "2020", "1500.0")
    with patch("requests.get", return_value=_mock_response(payload)):
        result = server.fetch_dot_data("A", "US", "TXG_FOB_USD", "W00", 2020, 2020)
    assert "1500.00" in result


def test_fetch_dot_data_url_includes_counterpart():
    payload = _imf_response("US", "2020", "1.0")
    with patch("requests.get", return_value=_mock_response(payload)) as mock_get:
        server.fetch_dot_data("A", "US", "TXG_FOB_USD", "CN", 2020, 2020)
    url = mock_get.call_args[0][0]
    assert "A.US.TXG_FOB_USD.CN" in url


# --- fetch_gfsmab_data ---

def test_fetch_gfsmab_unit_xdc():
    payload = _imf_response("DE", "2020", "100.0")
    with patch("requests.get", return_value=_mock_response(payload)) as mock_get:
        server.fetch_gfsmab_data("A", "DE", "XDC", "GNLB__Z", 2020, 2020)
    url = mock_get.call_args[0][0]
    assert "S13.XDC" in url


def test_fetch_gfsmab_unit_pct_gdp():
    payload = _imf_response("FR", "2020", "3.5")
    with patch("requests.get", return_value=_mock_response(payload)) as mock_get:
        server.fetch_gfsmab_data("A", "FR", "XDC_R_B1GQ", "GNLB__Z", 2020, 2020)
    url = mock_get.call_args[0][0]
    assert "S13.XDC_R_B1GQ" in url


def test_fetch_gfsmab_invalid_unit():
    result = server.fetch_gfsmab_data("A", "US", "INVALID_UNIT", "GNLB__Z", 2020, 2020)
    assert "Invalid unit" in result


# --- fetch_cpis_data ---

def test_fetch_cpis_url_has_sector_totals():
    payload = _imf_response("US", "2020", "500.0")
    with patch("requests.get", return_value=_mock_response(payload)) as mock_get:
        server.fetch_cpis_data("A", "US", "I_A_T_T_BP6_USD", "W00", 2020, 2020)
    url = mock_get.call_args[0][0]
    assert ".T.T." in url


# --- list_indicators ---

def test_list_indicators_ifs():
    result = server.list_indicators("IFS")
    assert isinstance(result, list)
    assert len(result) > 0
    assert "code" in result[0]
    assert "description" in result[0]


def test_list_indicators_case_insensitive():
    result_lower = server.list_indicators("ifs")
    result_upper = server.list_indicators("IFS")
    assert result_lower == result_upper


def test_list_indicators_all_datasets():
    for dataset in ["IFS", "DOT", "BOP", "CDIS", "CPIS", "GFSMAB", "MFS", "FSI"]:
        result = server.list_indicators(dataset)
        assert isinstance(result, list), f"Expected list for {dataset}"
        assert len(result) > 0, f"Empty indicators for {dataset}"


def test_list_indicators_invalid_dataset():
    with pytest.raises(Exception):
        server.list_indicators("INVALID")


# --- list_countries ---

def test_list_countries_ifs():
    result = server.list_countries("IFS")
    assert isinstance(result, list)
    assert len(result) > 0
    assert "code" in result[0]


def test_list_countries_all_datasets():
    for dataset in ["IFS", "DOT", "BOP", "CDIS", "CPIS", "GFSMAB", "MFS", "FSI"]:
        result = server.list_countries(dataset)
        assert isinstance(result, list), f"Expected list for {dataset}"
        assert len(result) > 0, f"Empty countries for {dataset}"


def test_list_countries_invalid_dataset():
    with pytest.raises(Exception):
        server.list_countries("NOTEXIST")


# --- URL validation ---

def test_all_fetch_tools_use_https():
    """All fetch tools must use HTTPS."""
    payload = _imf_response("US", "2020", "1.0")
    tools_and_args = [
        (server.fetch_ifs_data, ("A", "US", "NGDP_XDC", 2020, 2020)),
        (server.fetch_dot_data, ("A", "US", "TXG_FOB_USD", "W00", 2020, 2020)),
        (server.fetch_bop_data, ("A", "US", "BCA_BP6_USD", 2020, 2020)),
        (server.fetch_mfs_data, ("A", "US", "FASMB_XDC", 2020, 2020)),
        (server.fetch_fsi_data, ("A", "US", "FSANL_PT", 2020, 2020)),
    ]
    for func, args in tools_and_args:
        with patch("requests.get", return_value=_mock_response(payload)) as mock_get:
            func(*args)
        url = mock_get.call_args[0][0]
        assert url.startswith("https://"), f"{func.__name__} used HTTP instead of HTTPS: {url}"
