# IMF Data MCP

This MCP server integrates with the free IMF data API to provide a set of tools and resources for retrieving and processing economic data. It enables users to query datasets, fetch time series data, and list available indicators and countries, making it easier to work with IMF data in a structured and programmatic way.

## Features
- **List Datasets**: Retrieve a list of all available IMF datasets using the Dataflow API.
- **Get Dataset Structure**: Fetch the structure of a specified dataset via the DataStructure API.
- **Fetch Time Series Data**: Retrieve time series data for various datasets (e.g., CDIS, CPIS, MFS, IFS, etc.) using the CompactData API.
- **List Indicators**: List all available indicators for a specific dataset using the DataMapper API.
- **List Countries**: Retrieve a list of available countries for a specific dataset.
- **Query Prompt Template**: Provide a query prompt template to guide users on how to query data with indicators and intentions.

## Installation and Usage Guide

### Using `uv` (Recommended)
You can run the server directly using `uvx` without additional installation:
```bash
uvx imf-data-mcp
```
### Using PIP
Alternatively, you can install the server using pip:

```bash
pip install imf-data-mcp
```

After installation, run the server with:
```bash
python -m imf_data_mcp
```
## Configuration
You can configure the server to suit different use cases. For example, to integrate with a specific application, you might add the following configuration:

```json
{
  "mcpServers": {
    "imf": {
      "command": "uvx",
      "args": ["imf-data-mcp"]
    }
  }
}
```

## Debugging
To debug the server, you can use the MCP Inspector. For installations using uvx, run:

```bash
npx @modelcontextprotocol/inspector uvx imf-data-mcp
```

## Contribution Guide
We welcome contributions to the imf-data-mcp project. Whether it's adding new tools, enhancing existing features, or improving documentation, your input is highly valuable. Please feel free to submit pull requests or open issues.

## License
This project is licensed under the Apache 2.0 License. See the LICENSE file for details.


``
