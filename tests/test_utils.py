"""Unit tests for imf_data_mcp.utils.process_imf_data."""
import pytest
from imf_data_mcp.utils import process_imf_data


def _wrap(series):
    """Wrap series in the standard IMF CompactData envelope."""
    return {"CompactData": {"DataSet": {"Series": series}}}


# --- Happy path ---

def test_single_series_single_obs():
    data = _wrap({
        "@REF_AREA": "US",
        "Obs": {"@TIME_PERIOD": "2020", "@OBS_VALUE": "21427.7"},
    })
    result = process_imf_data(data)
    assert result == "In 2020, US had an indicator value of 21427.70."


def test_single_series_multiple_obs():
    data = _wrap({
        "@REF_AREA": "JP",
        "Obs": [
            {"@TIME_PERIOD": "2019", "@OBS_VALUE": "5.00"},
            {"@TIME_PERIOD": "2020", "@OBS_VALUE": "6.50"},
        ],
    })
    result = process_imf_data(data)
    lines = result.splitlines()
    assert len(lines) == 2
    assert "2019" in lines[0] and "5.00" in lines[0]
    assert "2020" in lines[1] and "6.50" in lines[1]


def test_multiple_series():
    data = _wrap([
        {"@REF_AREA": "US", "Obs": {"@TIME_PERIOD": "2020", "@OBS_VALUE": "1.0"}},
        {"@REF_AREA": "GB", "Obs": {"@TIME_PERIOD": "2020", "@OBS_VALUE": "2.0"}},
    ])
    result = process_imf_data(data)
    assert "US" in result
    assert "GB" in result


def test_float_formatting():
    data = _wrap({
        "@REF_AREA": "DE",
        "Obs": {"@TIME_PERIOD": "2021", "@OBS_VALUE": "3.14159"},
    })
    result = process_imf_data(data)
    assert "3.14" in result


# --- Warning cases ---

def test_series_is_none():
    data = _wrap(None)
    result = process_imf_data(data)
    assert "Warning" in result


def test_obs_is_none():
    data = _wrap({"@REF_AREA": "FR", "Obs": None})
    result = process_imf_data(data)
    assert "Warning" in result and "FR" in result


def test_obs_value_missing():
    data = _wrap({
        "@REF_AREA": "IT",
        "Obs": {"@TIME_PERIOD": "2020"},  # no @OBS_VALUE
    })
    result = process_imf_data(data)
    assert "Warning" in result and "IT" in result and "2020" in result


def test_obs_entry_is_none_in_list():
    data = _wrap({
        "@REF_AREA": "CA",
        "Obs": [None, {"@TIME_PERIOD": "2021", "@OBS_VALUE": "1.5"}],
    })
    result = process_imf_data(data)
    assert "Warning" in result
    assert "2021" in result and "1.50" in result


# --- Error cases ---

def test_missing_compact_data_key():
    result = process_imf_data({})
    assert result.startswith("Error processing IMF data")


def test_missing_dataset_key():
    result = process_imf_data({"CompactData": {}})
    assert result.startswith("Error processing IMF data")


def test_unexpected_series_type():
    data = _wrap("not-a-series")
    result = process_imf_data(data)
    assert "Error" in result


def test_empty_observations_list():
    data = _wrap({"@REF_AREA": "AU", "Obs": []})
    result = process_imf_data(data)
    assert result == "No data returned."
