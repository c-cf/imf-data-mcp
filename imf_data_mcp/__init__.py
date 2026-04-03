#!/usr/bin/env python3
"""
IMF Data MCP Server

A Model Context Protocol server wrapping the imfp library, which uses
the current IMF SDMX API at data.imf.org. Provides tools to list databases,
explore available parameters/codes, and fetch time series data.
"""

import asyncio
import json
from typing import Any, Optional

import imfp
import pandas as pd
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

# ── Server ────────────────────────────────────────────────────────────────────

mcp = FastMCP("imf_mcp")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to a list of plain dicts (JSON-serialisable)."""
    return df.where(pd.notna(df), None).to_dict(orient="records")


def _run_sync(fn, *args, **kwargs):
    """Run a synchronous imfp call in a thread so we don't block the event loop."""
    return asyncio.to_thread(fn, *args, **kwargs)


def _format_table(records: list[dict], max_rows: int = 500) -> str:
    """Return a compact JSON array, capped at max_rows."""
    if len(records) > max_rows:
        records = records[:max_rows]
        truncated = True
    else:
        truncated = False
    out = json.dumps(records, indent=2, ensure_ascii=False)
    if truncated:
        out += f"\n\n[Results truncated to {max_rows} rows. Refine your query to see more.]"
    return out


# ── Tool: list databases ───────────────────────────────────────────────────────

@mcp.tool(
    name="imf_list_databases",
    annotations={
        "title": "List IMF Databases",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def imf_list_databases() -> str:
    """List all IMF databases available via the current data.imf.org API.

    Returns a JSON array where each element has:
        - database_id (str): Pass this to other tools.
        - description (str): Human-readable name of the database.

    Use imf_search_databases to filter by keyword instead of scanning this
    full list. There are ~155 databases.

    Returns:
        str: JSON array of {database_id, description} objects.
    """
    try:
        df = await _run_sync(imfp.imf_databases)
        records = _df_to_records(df)
        return _format_table(records, max_rows=200)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Tool: search databases ────────────────────────────────────────────────────

class SearchDatabasesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    keyword: str = Field(
        ...,
        description=(
            "Case-insensitive keyword to search in database descriptions. "
            "Examples: 'inflation', 'trade', 'fiscal', 'commodity', 'gender'."
        ),
        min_length=2,
        max_length=100,
    )


@mcp.tool(
    name="imf_search_databases",
    annotations={
        "title": "Search IMF Databases by Keyword",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def imf_search_databases(params: SearchDatabasesInput) -> str:
    """Search IMF databases by keyword in their description.

    Filters the full list of ~155 databases to those whose description
    contains the keyword (case-insensitive). Use this to discover the
    correct database_id before calling imf_get_parameters or imf_fetch_data.

    Args:
        params (SearchDatabasesInput):
            - keyword (str): Search term, e.g. 'consumer price', 'trade', 'fiscal'.

    Returns:
        str: JSON array of {database_id, description} objects matching the keyword,
             or an empty array if nothing matches.
    """
    try:
        df = await _run_sync(imfp.imf_databases)
        mask = df["description"].str.contains(params.keyword, case=False, na=False)
        matches = df[mask]
        if matches.empty:
            return json.dumps(
                {"message": f"No databases found matching '{params.keyword}'."}
            )
        return _format_table(_df_to_records(matches))
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Tool: get parameter definitions ──────────────────────────────────────────

class DatabaseIdInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    database_id: str = Field(
        ...,
        description=(
            "IMF database ID, e.g. 'CPI', 'PCPS', 'BOP_AGG', 'ANEA'. "
            "Obtain valid IDs from imf_search_databases or imf_list_databases."
        ),
        min_length=1,
        max_length=60,
    )


@mcp.tool(
    name="imf_get_parameter_defs",
    annotations={
        "title": "Get Parameter Definitions for an IMF Database",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def imf_get_parameter_defs(params: DatabaseIdInput) -> str:
    """Return the list of query dimensions (parameters) for an IMF database.

    Each parameter corresponds to a keyword argument you can pass to
    imf_fetch_data. Call imf_get_parameter_codes to see the valid codes
    for each parameter.

    Args:
        params (DatabaseIdInput):
            - database_id (str): e.g. 'CPI', 'PCPS', 'BOP_AGG'.

    Returns:
        str: JSON array of {parameter, description} objects, where 'parameter'
             is the kwarg name to use in imf_fetch_data.

    Example response:
        [
          {"parameter": "ref_area", "description": "Reference Area"},
          {"parameter": "indicator", "description": "CPI Indicator"},
          {"parameter": "freq",      "description": "Frequency"}
        ]
    """
    try:
        df = await _run_sync(imfp.imf_parameter_defs, params.database_id)
        return _format_table(_df_to_records(df))
    except ValueError as e:
        return json.dumps(
            {
                "error": str(e),
                "hint": "Use imf_search_databases to find a valid database_id.",
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Tool: get parameter codes ─────────────────────────────────────────────────

class GetCodesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    database_id: str = Field(
        ...,
        description="IMF database ID, e.g. 'CPI', 'PCPS', 'BOP_AGG'.",
        min_length=1,
        max_length=60,
    )
    parameter: Optional[str] = Field(
        default=None,
        description=(
            "Specific parameter name to return codes for, e.g. 'ref_area', 'freq'. "
            "If omitted, all parameters and their codes are returned. "
            "Get valid parameter names from imf_get_parameter_defs."
        ),
        min_length=1,
        max_length=60,
    )
    search: Optional[str] = Field(
        default=None,
        description=(
            "Optional keyword to filter codes or descriptions, e.g. 'Austria', 'annual'. "
            "Case-insensitive."
        ),
        max_length=100,
    )


@mcp.tool(
    name="imf_get_parameter_codes",
    annotations={
        "title": "List Valid Codes for IMF Database Parameters",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def imf_get_parameter_codes(params: GetCodesInput) -> str:
    """List valid input codes for one or all parameters of an IMF database.

    Use this to find the exact codes to pass as filter values in imf_fetch_data.
    For example, to find Austria's country code for 'ref_area', or the code for
    'annual' frequency.

    Args:
        params (GetCodesInput):
            - database_id (str): IMF database ID.
            - parameter (str, optional): Specific parameter to inspect (e.g. 'ref_area').
              If omitted, returns codes for all parameters.
            - search (str, optional): Keyword to filter the code list.

    Returns:
        str: JSON object keyed by parameter name, each value being an array of
             {input_code, description} objects.

    Example return structure:
        {
          "ref_area": [
            {"input_code": "AT", "description": "Austria"},
            {"input_code": "DE", "description": "Germany"}
          ]
        }
    """
    try:
        all_params = await _run_sync(imfp.imf_parameters, params.database_id)
    except ValueError as e:
        return json.dumps(
            {
                "error": str(e),
                "hint": "Use imf_search_databases to find a valid database_id.",
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e)})

    # Filter to requested parameter
    if params.parameter:
        if params.parameter not in all_params:
            available = list(all_params.keys())
            return json.dumps(
                {
                    "error": f"Parameter '{params.parameter}' not found.",
                    "available_parameters": available,
                }
            )
        subset = {params.parameter: all_params[params.parameter]}
    else:
        subset = all_params

    # Apply optional search filter
    result: dict[str, list[dict]] = {}
    for name, df in subset.items():
        records = _df_to_records(df)
        if params.search:
            kw = params.search.lower()
            records = [
                r
                for r in records
                if kw in str(r.get("input_code", "")).lower()
                or kw in str(r.get("description", "")).lower()
            ]
        result[name] = records[:300]  # cap per parameter

    return json.dumps(result, indent=2, ensure_ascii=False)


# ── Tool: fetch data ──────────────────────────────────────────────────────────

class FetchDataInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    database_id: str = Field(
        ...,
        description="IMF database ID, e.g. 'CPI', 'PCPS', 'BOP_AGG', 'ANEA'.",
        min_length=1,
        max_length=60,
    )
    start_year: Optional[int] = Field(
        default=None,
        description="Earliest year to retrieve (4-digit integer), e.g. 2010.",
        ge=1900,
        le=2100,
    )
    end_year: Optional[int] = Field(
        default=None,
        description="Latest year to retrieve (4-digit integer), e.g. 2023.",
        ge=1900,
        le=2100,
    )
    filters: Optional[dict[str, list[str]]] = Field(
        default=None,
        description=(
            "Dictionary of parameter filters. Keys are parameter names from "
            "imf_get_parameter_defs, values are lists of input_code strings from "
            "imf_get_parameter_codes. "
            "Example: {\"ref_area\": [\"AT\", \"DE\"], \"freq\": [\"A\"]}. "
            "Omitting a parameter means 'all values' (may return a very large result)."
        ),
    )
    max_rows: Optional[int] = Field(
        default=500,
        description="Maximum number of rows to return (default 500, max 5000).",
        ge=1,
        le=5000,
    )


@mcp.tool(
    name="imf_fetch_data",
    annotations={
        "title": "Fetch IMF Time Series Data",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def imf_fetch_data(params: FetchDataInput) -> str:
    """Fetch time series data from any IMF database using the current data.imf.org API.

    Workflow:
        1. Use imf_search_databases to find the right database_id.
        2. Use imf_get_parameter_defs to see what dimensions are available.
        3. Use imf_get_parameter_codes to find exact filter codes.
        4. Call this tool with those codes in the 'filters' dict.

    Args:
        params (FetchDataInput):
            - database_id (str): IMF database ID, e.g. 'CPI'.
            - start_year (int, optional): Earliest year, e.g. 2010.
            - end_year (int, optional): Latest year, e.g. 2023.
            - filters (dict, optional): {parameter_name: [code1, code2, ...]}.
              Example: {"ref_area": ["US", "DE"], "freq": ["A"]}.
            - max_rows (int, optional): Row cap, default 500.

    Returns:
        str: JSON with keys:
            - columns (list[str]): Column names in the returned data.
            - rows (list[dict]): The data records.
            - row_count (int): Number of rows returned.
            - truncated (bool): Whether the result was capped at max_rows.

    Example filters for common databases:
        CPI:     {"ref_area": ["US"], "freq": ["A"]}
        PCPS:    {"commodity": ["PZINC"], "frequency": ["A"]}
        BOP_AGG: {"ref_area": ["AT"], "freq": ["A"]}
        ANEA:    {"ref_area": ["DE", "FR"], "freq": ["A"]}
    """
    try:
        kwargs: dict[str, Any] = {}
        if params.filters:
            kwargs.update(params.filters)

        df = await _run_sync(
            imfp.imf_dataset,
            params.database_id,
            start_year=params.start_year,
            end_year=params.end_year,
            **kwargs,
        )

        if df is None or df.empty:
            return json.dumps(
                {
                    "message": "No data returned. Check your filters and database_id.",
                    "row_count": 0,
                    "rows": [],
                }
            )

        total = len(df)
        cap = min(params.max_rows or 500, 5000)
        truncated = total > cap
        df = df.head(cap)

        records = _df_to_records(df)
        return json.dumps(
            {
                "database_id": params.database_id,
                "columns": list(df.columns),
                "row_count": len(records),
                "total_rows_before_cap": total,
                "truncated": truncated,
                "rows": records,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    except ValueError as e:
        return json.dumps(
            {
                "error": str(e),
                "hint": (
                    "Check that database_id is valid (use imf_search_databases) "
                    "and that filter codes match imf_get_parameter_codes output."
                ),
            }
        )
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {str(e)}"})


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
