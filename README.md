# IMF Data MCP

A Model Context Protocol server for IMF economic data, built on
[imfp](https://github.com/Promptly-Technologies-LLC/imfp) and the
[IMF SDMX API](https://data.imf.org) at `data.imf.org`.

> **v0.2.0 — Breaking change:** The old server called `dataservices.imf.org`,
> which the IMF decommissioned in 2025. All requests timed out as a result.
> This version migrates to `imfp`, which targets the current `data.imf.org`
> SDMX 3.0 API and is actively maintained.

---

## Installation

### Using `uv` (recommended)

```bash
uvx --from git+https://github.com/c-cf/imf-data-mcp imf-data-mcp
```

### Using pip

```bash
pip install git+https://github.com/c-cf/imf-data-mcp.git
```

---

## Claude Desktop configuration

```json
{
  "mcpServers": {
    "imf": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/c-cf/imf-data-mcp", "imf-data-mcp"]
    }
  }
}
```

Or, if installed via pip:

```json
{
  "mcpServers": {
    "imf": {
      "command": "imf-data-mcp"
    }
  }
}
```

---

## Available tools

| Tool | Description |
|---|---|
| `imf_list_databases` | List all ~155 IMF databases with their IDs |
| `imf_search_databases` | Filter databases by keyword (e.g. `"inflation"`, `"trade"`) |
| `imf_get_parameter_defs` | List query dimensions for a database |
| `imf_get_parameter_codes` | List valid codes for a dimension, with optional search |
| `imf_fetch_data` | Fetch time series data with year range and dimension filters |

---

## Typical workflow

```
1. imf_search_databases(keyword="consumer price")
   → CPI, CPI_WCA, ...

2. imf_get_parameter_defs(database_id="CPI")
   → country, index_type, coicop_1999, frequency, ...

3. imf_get_parameter_codes(database_id="CPI", parameter="country", search="austria")
   → AUT

4. imf_fetch_data(
       database_id="CPI",
       start_year=2015, end_year=2023,
       filters={"country": ["AUT"], "frequency": ["M"]}
   )
```

---

## Common database IDs

| Topic | ID |
|---|---|
| Consumer Prices | `CPI` |
| Producer Prices | `PPI` |
| National Accounts (Annual) | `ANEA` |
| National Accounts (Quarterly) | `QNEA` |
| Balance of Payments | `BOP_AGG` |
| Exchange Rates | `ER_2026_JAN_VINTAGE` |
| Commodity Prices | `PCPS` |
| Fiscal Monitor | `FM` |
| Gov. Finance Statistics | `GFS_COFOG` |
| Monetary Statistics | `MFS_CBS`, `MFS_MA`, `MFS_IR` |
| Financial Soundness | `FSIC` |
| Trade in Services | `ITS` |
| SDG Data | `SDG` |

---

## Rate limits

The IMF API allows roughly 10 requests / 5 seconds. `imfp` handles
rate limiting and retries automatically.

---

## Debugging

```bash
npx @modelcontextprotocol/inspector imf-data-mcp
```

---

## License

Apache 2.0
