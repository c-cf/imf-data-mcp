#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMF MCP Server Example

This server integrates the free IMF data API and provides the following features:
  1. Returns all IMF datasets as resources (Dataflow API)
  2. Returns the structure of a specified dataset as a resource (DataStructure API)
  3. Retrieves time series data based on requirements as a tool (CompactData API)
  4. Lists available indicators in the DataMapper API as a resource
  5. Lists available countries as a resource (according to the IMF DataMapper API, the URL may need to be adjusted based on official documentation)
  6. Provides a prompt template to guide users on how to query data with indicators and intentions

Note:
  - The IMF API limits each user to a maximum of 10 requests every 5 seconds, and the overall application to a maximum of 50 requests per second.
  - The default return format is XML (some APIs return JSON).

Please further parse or convert the returned data format as needed.
"""
from .utils import process_imf_data
from mcp.server.fastmcp import FastMCP
import requests
import os
import json

# Create an instance of the MCP server
mcp = FastMCP("IMF Data Server")

# 1. Resource: List all IMF datasets (Dataflow API)
@mcp.resource("imf://datasets")
def list_datasets() -> dict:
    """
    Returns IMF Dataflow information (list of datasets).

    Returns:
        dict: A dictionary containing dataset IDs and their descriptions.
    """
    return {
        "IFS": "International Financial Statistics",
        "DOT": "Direction of Trade Statistics",
        "BOP": "Balance of Payments Statistics",
        "CDIS": "Coordinated Direct Investment Survey",
        "CPIS": "Coordinated Portfolio Investment Survey",
        "GFSMAB": "Government Finance Statistics, Main Aggregates and Balances",
        "MFS": "Monetary and Financial Statistics",
        "FSI": "Financial Soundness Indicators"
    }

# 2. Resource: Get the structure of a specified dataset (DataStructure API)
@mcp.resource("imf://structure/{dataset_id}")
def get_structure(dataset_id: str):
    """
    Returns the structure description of the specified dataset.

    Args:
        dataset_id (str): The ID of the dataset.

    Returns:
        str: The structure description in XML format.
    """
    url = f"http://dataservices.imf.org/REST/SDMX_XML.svc/DataStructure/{dataset_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text  # XML format data
    except Exception as e:
        return f"Error fetching structure for {dataset_id}: {str(e)}"

@mcp.tool()
def fetch_ifs_data(freq: str, country: str, indicator: str, start: str | int, end: str | int) -> str:
    """
    Retrieves compact format time series data from the IFS database based on the input parameters.

    Args:
        freq (str): Frequency (e.g., "A" for annual).
        country (str): Country code, multiple country codes can be connected with "+".
        indicator (str): Indicator code.
        start (str | int): Start year.
        end (str | int): End year.

    Returns:
        str: Description of the queried data. Do not perform further analysis or retry if the query fails.
    """
    dimensions = f"{freq}.{country}.{indicator}"
    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/IFS/{dimensions}?startPeriod={start}&endPeriod={end}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return process_imf_data(data)
    except Exception as e:
        return f"Error fetching IFS data: {str(e)}"

@mcp.tool()
def fetch_dot_data(freq: str, country: str, indicator: str, counterpart: str, start: str | int, end: str | int) -> str:
    """
    Retrieves compact format time series data from the DOT database based on the input parameters.

    Args:
        freq (str): Frequency (e.g., "A" for annual).
        country (str): Country code, multiple country codes can be connected with "+".
        indicator (str): Indicator code.
        counterpart (str): Counterpart country code.
        start (str | int): Start year.
        end (str | int): End year.

    Returns:
        str: Description of the queried data. Do not perform further analysis or retry if the query fails.
    """
    dimensions = f"{freq}.{country}.{indicator}.{counterpart}"
    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/DOT/{dimensions}?startPeriod={start}&endPeriod={end}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return process_imf_data(data)
    except Exception as e:
        return f"Error fetching DOT data: {str(e)}"

@mcp.tool()
def fetch_bop_data(freq: str, country: str, indicator: str, start: str | int, end: str | int) -> str:
    """
    Retrieves compact format time series data from the BOP database based on the input parameters.

    Args:
        freq (str): Frequency (e.g., "A" for annual, "Q" for quarterly, "M" for monthly).
        country (str): Country code, multiple country codes can be connected with "+".
        indicator (str): Indicator code.
        start (str | int): Start year.
        end (str | int): End year.

    Returns:
        str: Description of the queried data. Do not perform further analysis or retry if the query fails.
    """
    dimensions = f"{freq}.{country}.{indicator}"
    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/BOP/{dimensions}?startPeriod={start}&endPeriod={end}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return process_imf_data(data)
    except Exception as e:
        return f"Error fetching BOP data: {str(e)}"

@mcp.tool()
def fetch_cdis_data(freq: str, country: str, indicator: str, counterpart: str, start: str | int, end: str | int) -> str:
    """
    Retrieves compact format time series data from the CDIS database based on the input parameters.

    Args:
        freq (str): Frequency (e.g., "A" for annual).
        country (str): Country code, multiple country codes can be connected with "+".
        indicator (str): Indicator code.
        counterpart (str): Counterpart country code.
        start (str | int): Start year.
        end (str | int): End year.

    Returns:
        str: Description of the queried data. Do not perform further analysis or retry if the query fails.
    """
    dimensions = f"{freq}.{country}.{indicator}.{counterpart}"
    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/CDIS/{dimensions}?startPeriod={start}&endPeriod={end}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return process_imf_data(data)
    except Exception as e:
        return f"Error fetching CDIS data: {str(e)}"

@mcp.tool()
def fetch_cpis_data(freq: str, country: str, indicator: str, counter_country: str, start: str | int, end: str | int) -> str:
    """
    Retrieves compact format time series data from the CPIS database based on the input parameters.

    Args:
        freq (str): Frequency (e.g., "A" for annual).
        country (str): Country code, multiple country codes can be connected with "+".
        indicator (str): Indicator code.
        counter_country (str): Counterpart country code.
        start (str | int): Start year.
        end (str | int): End year.

    Returns:
        str: Description of the queried data. Do not perform further analysis or retry if the query fails.
    """
    dimensions = f"{freq}.{country}.{indicator}.T.T.{counter_country}"
    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/CPIS/{dimensions}?startPeriod={start}&endPeriod={end}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return process_imf_data(data)
    except Exception as e:
        return f"Error fetching CPIS data: {str(e)}"

@mcp.tool()
def fetch_gfsmab_data(freq: str, country: str, unit: str, indicator: str, start: str | int, end: str | int) -> str:
    """
    Retrieves compact format time series data from the GFSMAB database based on the input parameters.

    Args:
        freq (str): Frequency (e.g., "A" for annual).
        country (str): Country code, multiple country codes can be connected with "+".
        unit (str): Unit code XDC or XDC_R_B1GQ (Percent of GDP).
        indicator (str): Indicator code.
        start (str | int): Start year.
        end (str | int): End year.

    Returns:
        str: Description of the queried data. Do not perform further analysis or retry if the query fails.
    """
    if "xdc" == unit.lower():
        unit = "XDC"
    else:
        unit = "XDC_R_B1GQ"
    
    dimensions = f"{freq}.{country}.S13.{unit}.{indicator}"
    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/GFSMAB/{dimensions}?startPeriod={start}&endPeriod={end}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return process_imf_data(data)

    except Exception as e:
        return f"Error fetching GFSMAB data: {str(e)}"

@mcp.tool()
def fetch_mfs_data(freq: str, country: str, indicator: str, start: str | int, end: str | int) -> str:
    """
    Retrieves compact format time series data from the MFS database based on the input parameters.

    Args:
        freq (str): Frequency (e.g., "A" for annual).
        country (str): Country code, multiple country codes can be connected with "+".
        indicator (str): Indicator code.
        start (str | int): Start year.
        end (str | int): End year.

    Returns:
        str: Description of the queried data. Do not perform further analysis or retry if the query fails.
    """
    dimensions = f"{freq}.{country}.{indicator}"
    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/MFS/{dimensions}?startPeriod={start}&endPeriod={end}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return process_imf_data(data)
    except Exception as e:
        return f"Error fetching MFS data: {str(e)}"

@mcp.tool()
def fetch_fsi_data(freq: str, country: str, indicator: str, start: str | int, end: str | int) -> str:
    """
    Retrieves compact format time series data from the FSI database based on the input parameters.

    Args:
        freq (str): Frequency (e.g., "A" for annual).
        country (str): Country code, multiple country codes can be connected with "+".
        indicator (str): Indicator code.
        start (str | int): Start year.
        end (str | int): End year.

    Returns:
        str: Description of the queried data. Do not perform further analysis or retry if the query fails.
    """
    dimensions = f"{freq}.{country}.{indicator}"
    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/FSI/{dimensions}?startPeriod={start}&endPeriod={end}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return process_imf_data(data)
    except Exception as e:
        return f"Error fetching FSI data: {str(e)}"

# 4. Resource: List indicators in the DataMapper API (returns list format)
@mcp.tool()
def list_indicators(dataset_id: str) -> list:
    """
    Returns a list of indicators for the specified dataset, read from the corresponding .json file in the local indicators directory.

    Args:
        dataset_id (str): Dataset ID, such as "IFS", "DOT", "BOP", etc.

    Returns:
        list: List of indicators.
    """
    file_path = os.path.join(os.path.dirname(__file__), "resources", "indicators", f"{dataset_id.lower()}.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except json.JSONDecodeError:
        return {"error": f"Error decoding JSON from file: {file_path}"}
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}

# 5. Resource: List available countries (according to the IMF DataMapper API)
@mcp.tool()
def list_countries(dataset_id: str) -> list:
    """
    Returns a list of available countries for the specified dataset, read from the corresponding .json file in the local areas directory.

    Args:
        dataset_id (str): Dataset ID, such as "IFS", "DOT", "BOP", etc.

    Returns:
        list: List of countries.
    """
    file_path = os.path.join(os.path.dirname(__file__), "resources", "areas", f"{dataset_id.lower()}.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except json.JSONDecodeError:
        return {"error": f"Error decoding JSON from file: {file_path}"}
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}

# 6. Prompt: Provide a query prompt template to guide users on how to query data with indicators and intentions
@mcp.prompt()
def imf_query_prompt() -> str:
    """
    Returns a prompt template explaining how to query IMF data with indicators and user intentions.

    Returns:
        str: A prompt template for guiding users on querying IMF data.
    """
    prompt_text = """
        You are a professional IMF data analysis assistant. Please follow these steps to help users obtain and analyze IMF data:

        1. First, use the imf://datasets resource to get a list of available datasets and show the user the 5-10 most commonly used datasets with a brief description.

        2. When the user selects a dataset, use the following two tools to get detailed information about the dataset:
            - list_countries: List available country or region codes
            - list_indicators: List available indicator codes and names
        3. Assist the user in determining their interests:
        - Country or region (provide codes, and multiple country codes can be connected with "+")
        - Indicator (provide codes and names)
        - Time range (start year and end year)
        - Data frequency (if applicable: annual A, quarterly Q, monthly M, etc.)

        4. Based on the user's selection, construct appropriate query parameters and use the fetch_compact_data tool to get the data

        ** Note: When you get warnings like "Warning: No indicator value" or "Warning: No indicator value for {country} in that Year," it means there is a lack of data for that period. Do not perform further analysis or retry. **

    """
    return prompt_text

def main():
    """Main entry point for the MCP server."""
    mcp.run()

# Start the MCP server
if __name__ == "__main__":
    main()
