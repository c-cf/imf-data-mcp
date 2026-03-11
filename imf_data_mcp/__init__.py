#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMF MCP Server

Integrates the IMF free public data API via the Model Context Protocol.
Exposes 8 IMF datasets (IFS, DOT, BOP, CDIS, CPIS, GFSMAB, MFS, FSI)
as MCP tools and resources.

Rate limits: 10 requests/5 seconds per user, 50 requests/second global.
"""
from .utils import process_imf_data
from mcp.server.fastmcp import FastMCP
import requests
import os
import json

BASE_URL = "https://dataservices.imf.org/REST/SDMX_JSON.svc"
STRUCTURE_BASE_URL = "https://dataservices.imf.org/REST/SDMX_XML.svc"

VALID_DATASETS = {"IFS", "DOT", "BOP", "CDIS", "CPIS", "GFSMAB", "MFS", "FSI"}
VALID_FREQS = {"A", "Q", "M", "D", "W", "B"}

mcp = FastMCP("IMF Data Server")


def _validate_freq(freq: str) -> str:
    """Normalize and validate frequency code."""
    freq = freq.upper()
    if freq not in VALID_FREQS:
        valid = ", ".join(sorted(VALID_FREQS))
        raise ValueError(f"Invalid frequency '{freq}'. Valid values: {valid}")
    return freq


def _fetch_compact_data(dataset: str, dimensions: str, start: str | int, end: str | int) -> str:
    """Fetch and process CompactData from IMF API."""
    url = f"{BASE_URL}/CompactData/{dataset}/{dimensions}?startPeriod={start}&endPeriod={end}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 400:
            return (
                f"Bad request for {dataset} (HTTP 400). "
                "Check that frequency, country, and indicator codes are valid."
            )
        if response.status_code == 404:
            return f"No data found for {dataset} with dimensions: {dimensions}"
        if response.status_code == 429:
            return (
                "Rate limit exceeded (HTTP 429). "
                "IMF allows 10 requests per 5 seconds. Please wait before retrying."
            )
        response.raise_for_status()
        return process_imf_data(response.json())
    except requests.exceptions.Timeout:
        return f"Request timed out fetching {dataset} data."
    except requests.exceptions.ConnectionError:
        return f"Connection error fetching {dataset} data. Check your internet connection."
    except Exception as e:
        return f"Error fetching {dataset} data: {str(e)}"


def _fetch(dataset: str, freq: str, dimensions_suffix: str, start: str | int, end: str | int) -> str:
    """Validate freq, then fetch data. Returns an error string on invalid freq."""
    try:
        freq = _validate_freq(freq)
    except ValueError as e:
        return str(e)
    return _fetch_compact_data(dataset, f"{freq}.{dimensions_suffix}", start, end)


def _load_resource(subdir: str, dataset_id: str) -> list:
    """Load a JSON resource file from the resources directory."""
    dataset_id = dataset_id.upper()
    if dataset_id not in VALID_DATASETS:
        valid = ", ".join(sorted(VALID_DATASETS))
        raise ValueError(f"Unknown dataset '{dataset_id}'. Valid datasets: {valid}")
    file_path = os.path.join(
        os.path.dirname(__file__), "resources", subdir, f"{dataset_id.lower()}.json"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Resources ---

@mcp.resource("imf://datasets")
def list_datasets() -> dict:
    """
    Returns all available IMF datasets with their descriptions.

    Returns:
        dict: Dataset IDs mapped to their full names.
    """
    return {
        "IFS": "International Financial Statistics",
        "DOT": "Direction of Trade Statistics",
        "BOP": "Balance of Payments Statistics",
        "CDIS": "Coordinated Direct Investment Survey",
        "CPIS": "Coordinated Portfolio Investment Survey",
        "GFSMAB": "Government Finance Statistics, Main Aggregates and Balances",
        "MFS": "Monetary and Financial Statistics",
        "FSI": "Financial Soundness Indicators",
    }


@mcp.resource("imf://structure/{dataset_id}")
def get_structure(dataset_id: str) -> str:
    """
    Returns the SDMX structure definition (XML) for the specified dataset.

    Args:
        dataset_id: One of IFS, DOT, BOP, CDIS, CPIS, GFSMAB, MFS, FSI.

    Returns:
        str: XML structure definition or an error message.
    """
    dataset_id = dataset_id.upper()
    url = f"{STRUCTURE_BASE_URL}/DataStructure/{dataset_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        return f"Request timed out fetching structure for {dataset_id}."
    except Exception as e:
        return f"Error fetching structure for {dataset_id}: {str(e)}"


# --- Tools: fetch data ---

@mcp.tool()
def fetch_ifs_data(
    freq: str, country: str, indicator: str, start: str | int, end: str | int
) -> str:
    """
    Fetch time series data from IFS (International Financial Statistics).

    Args:
        freq: Frequency — A (annual), Q (quarterly), M (monthly).
        country: Country code. Join multiple codes with "+", e.g. "US+GB".
        indicator: Indicator code, e.g. "NGDP_XDC" for nominal GDP.
        start: Start year (e.g. 2000).
        end: End year (e.g. 2023).

    Returns:
        str: Formatted data observations or an error/warning message.
    """
    return _fetch("IFS", freq, f"{country}.{indicator}", start, end)


@mcp.tool()
def fetch_dot_data(
    freq: str, country: str, indicator: str, counterpart: str, start: str | int, end: str | int
) -> str:
    """
    Fetch time series data from DOT (Direction of Trade Statistics).

    Args:
        freq: Frequency — A (annual), Q (quarterly), M (monthly).
        country: Reporting country code.
        indicator: Indicator code, e.g. "TXG_FOB_USD" for exports.
        counterpart: Counterpart country code, or "W00" for world total.
        start: Start year.
        end: End year.

    Returns:
        str: Formatted data observations or an error/warning message.
    """
    return _fetch("DOT", freq, f"{country}.{indicator}.{counterpart}", start, end)


@mcp.tool()
def fetch_bop_data(
    freq: str, country: str, indicator: str, start: str | int, end: str | int
) -> str:
    """
    Fetch time series data from BOP (Balance of Payments Statistics).

    Args:
        freq: Frequency — A (annual), Q (quarterly), M (monthly).
        country: Country code.
        indicator: Indicator code.
        start: Start year.
        end: End year.

    Returns:
        str: Formatted data observations or an error/warning message.
    """
    return _fetch("BOP", freq, f"{country}.{indicator}", start, end)


@mcp.tool()
def fetch_cdis_data(
    freq: str, country: str, indicator: str, counterpart: str, start: str | int, end: str | int
) -> str:
    """
    Fetch time series data from CDIS (Coordinated Direct Investment Survey).

    Args:
        freq: Frequency — A (annual).
        country: Reporting country code.
        indicator: Indicator code.
        counterpart: Counterpart country code.
        start: Start year.
        end: End year.

    Returns:
        str: Formatted data observations or an error/warning message.
    """
    return _fetch("CDIS", freq, f"{country}.{indicator}.{counterpart}", start, end)


@mcp.tool()
def fetch_cpis_data(
    freq: str, country: str, indicator: str, counter_country: str, start: str | int, end: str | int
) -> str:
    """
    Fetch time series data from CPIS (Coordinated Portfolio Investment Survey).

    Uses total holdings (sector=T, instrument=T) aggregated across all sectors.

    Args:
        freq: Frequency — A (annual).
        country: Reporting country code.
        indicator: Indicator code.
        counter_country: Counterpart country code.
        start: Start year.
        end: End year.

    Returns:
        str: Formatted data observations or an error/warning message.
    """
    # T.T = Total sector, Total instrument type
    return _fetch("CPIS", freq, f"{country}.{indicator}.T.T.{counter_country}", start, end)


@mcp.tool()
def fetch_gfsmab_data(
    freq: str, country: str, unit: str, indicator: str, start: str | int, end: str | int
) -> str:
    """
    Fetch time series data from GFSMAB (Government Finance Statistics, Main Aggregates and Balances).

    Queries general government (sector S13) data.

    Args:
        freq: Frequency — A (annual).
        country: Country code.
        unit: "XDC" for domestic currency, or "XDC_R_B1GQ" for percent of GDP.
        indicator: Indicator code, e.g. "GNLB__Z" for net lending/borrowing.
        start: Start year.
        end: End year.

    Returns:
        str: Formatted data observations or an error/warning message.
    """
    unit_upper = unit.upper()
    if unit_upper not in ("XDC", "XDC_R_B1GQ"):
        return f"Invalid unit '{unit}'. Use 'XDC' (domestic currency) or 'XDC_R_B1GQ' (% of GDP)."
    # S13 = General government sector
    return _fetch("GFSMAB", freq, f"{country}.S13.{unit_upper}.{indicator}", start, end)


@mcp.tool()
def fetch_mfs_data(
    freq: str, country: str, indicator: str, start: str | int, end: str | int
) -> str:
    """
    Fetch time series data from MFS (Monetary and Financial Statistics).

    Args:
        freq: Frequency — A (annual), Q (quarterly), M (monthly).
        country: Country code.
        indicator: Indicator code.
        start: Start year.
        end: End year.

    Returns:
        str: Formatted data observations or an error/warning message.
    """
    return _fetch("MFS", freq, f"{country}.{indicator}", start, end)


@mcp.tool()
def fetch_fsi_data(
    freq: str, country: str, indicator: str, start: str | int, end: str | int
) -> str:
    """
    Fetch time series data from FSI (Financial Soundness Indicators).

    Args:
        freq: Frequency — A (annual), Q (quarterly), M (monthly).
        country: Country code.
        indicator: Indicator code.
        start: Start year.
        end: End year.

    Returns:
        str: Formatted data observations or an error/warning message.
    """
    return _fetch("FSI", freq, f"{country}.{indicator}", start, end)


# --- Tools: lookup ---

@mcp.tool()
def list_indicators(dataset_id: str) -> list:
    """
    List available indicators for a dataset (reads from cached local JSON).

    Args:
        dataset_id: One of IFS, DOT, BOP, CDIS, CPIS, GFSMAB, MFS, FSI.

    Returns:
        list: Each item has "code" and "description" fields.
    """
    return _load_resource("indicators", dataset_id)


@mcp.tool()
def list_countries(dataset_id: str) -> list:
    """
    List available countries/areas for a dataset (reads from cached local JSON).

    Args:
        dataset_id: One of IFS, DOT, BOP, CDIS, CPIS, GFSMAB, MFS, FSI.

    Returns:
        list: Each item has "code" and "description" fields.
    """
    return _load_resource("areas", dataset_id)


# --- Prompt ---

@mcp.prompt()
def imf_query_prompt() -> str:
    """
    Returns a step-by-step guide for querying IMF data.
    """
    return """
You are a professional IMF data analysis assistant. Follow these steps:

1. Use the `imf://datasets` resource to show the user available datasets
   (IFS, DOT, BOP, CDIS, CPIS, GFSMAB, MFS, FSI) with brief descriptions.

2. Once a dataset is selected, call:
   - `list_countries(dataset_id)` — get valid country codes
   - `list_indicators(dataset_id)` — get valid indicator codes

3. Clarify with the user:
   - Country/region (code from step 2; join multiple with "+", e.g. "US+GB")
   - Indicator (code from step 2)
   - Time range (start year, end year)
   - Frequency: A=annual, Q=quarterly, M=monthly

4. Call the appropriate `fetch_*_data` tool with the confirmed parameters.

**Important:** If the result contains "Warning: No indicator value", the data
simply does not exist for that period. Do not retry or attempt alternative queries.
""".strip()


def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
