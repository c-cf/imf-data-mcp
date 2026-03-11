#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP protocol test script for the IMF Data MCP server.

Connects to the server via stdio transport (same as Claude Desktop does)
and exercises every tool and resource. No mocking — uses the real MCP
handshake so this validates the full integration.

Usage:
    uv run python test_mcp.py

Requirements:
    The package must be installed (uv sync) so that `python -m imf_data_mcp` works.
"""
import asyncio
import sys
import textwrap

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
SKIP = "\033[33m~\033[0m"

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        print(f"  {PASS} {name}")
        passed += 1
    else:
        msg = f": {detail}" if detail else ""
        print(f"  {FAIL} {name}{msg}")
        failed += 1


async def run_tests() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "imf_data_mcp"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("\n=== IMF Data MCP Server Tests ===\n")

            # ------------------------------------------------------------------
            # 1. Tools list
            # ------------------------------------------------------------------
            print("[ Tools ]")
            tools_result = await session.list_tools()
            tool_names = {t.name for t in tools_result.tools}
            expected_tools = {
                "fetch_ifs_data", "fetch_dot_data", "fetch_bop_data",
                "fetch_cdis_data", "fetch_cpis_data", "fetch_gfsmab_data",
                "fetch_mfs_data", "fetch_fsi_data",
                "list_indicators", "list_countries",
            }
            check("10 tools registered", tool_names == expected_tools,
                  f"missing={expected_tools - tool_names}, extra={tool_names - expected_tools}")

            for t in sorted(tools_result.tools, key=lambda x: x.name):
                check(f"  {t.name} has description", bool(t.description))

            # ------------------------------------------------------------------
            # 2. Resources
            # ------------------------------------------------------------------
            print("\n[ Resources ]")
            resources_result = await session.list_resources()
            resource_uris = {r.uri for r in resources_result.resources}
            check("imf://datasets resource present", "imf://datasets" in resource_uris,
                  f"found: {resource_uris}")

            datasets_content = await session.read_resource("imf://datasets")
            check("imf://datasets returns content",
                  len(datasets_content.contents) > 0)

            # ------------------------------------------------------------------
            # 3. Prompts
            # ------------------------------------------------------------------
            print("\n[ Prompts ]")
            prompts_result = await session.list_prompts()
            prompt_names = {p.name for p in prompts_result.prompts}
            check("imf_query_prompt registered", "imf_query_prompt" in prompt_names,
                  f"found: {prompt_names}")

            prompt_result = await session.get_prompt("imf_query_prompt", {})
            check("imf_query_prompt returns messages", len(prompt_result.messages) > 0)

            # ------------------------------------------------------------------
            # 4. list_indicators
            # ------------------------------------------------------------------
            print("\n[ list_indicators ]")
            for dataset in ["IFS", "DOT", "BOP", "MFS", "FSI"]:
                result = await session.call_tool("list_indicators", {"dataset_id": dataset})
                check(
                    f"list_indicators({dataset}) returns data",
                    not result.isError and len(result.content) > 0,
                    str(result.content)[:100] if result.isError else "",
                )

            # Invalid dataset should return an error
            result = await session.call_tool("list_indicators", {"dataset_id": "INVALID"})
            check("list_indicators(INVALID) returns error", result.isError)

            # ------------------------------------------------------------------
            # 5. list_countries
            # ------------------------------------------------------------------
            print("\n[ list_countries ]")
            for dataset in ["IFS", "DOT", "GFSMAB"]:
                result = await session.call_tool("list_countries", {"dataset_id": dataset})
                check(
                    f"list_countries({dataset}) returns data",
                    not result.isError and len(result.content) > 0,
                )

            result = await session.call_tool("list_countries", {"dataset_id": "NOTEXIST"})
            check("list_countries(NOTEXIST) returns error", result.isError)

            # ------------------------------------------------------------------
            # 6. fetch_ifs_data — real API call (US GDP 2020)
            # ------------------------------------------------------------------
            print("\n[ fetch_ifs_data (live API) ]")
            result = await session.call_tool("fetch_ifs_data", {
                "freq": "A",
                "country": "US",
                "indicator": "NGDP_XDC",
                "start": 2020,
                "end": 2022,
            })
            content_text = result.content[0].text if result.content else ""
            check(
                "fetch_ifs_data(US, NGDP_XDC, 2020-2022) returns data",
                not result.isError and ("US" in content_text or "Warning" in content_text),
                content_text[:120],
            )

            # ------------------------------------------------------------------
            # 7. fetch_ifs_data — invalid frequency
            # ------------------------------------------------------------------
            print("\n[ Input validation ]")
            result = await session.call_tool("fetch_ifs_data", {
                "freq": "Z",
                "country": "US",
                "indicator": "NGDP_XDC",
                "start": 2020,
                "end": 2020,
            })
            content_text = result.content[0].text if result.content else ""
            check(
                "Invalid freq 'Z' returns error message",
                result.isError or "Invalid" in content_text or "Error" in content_text,
                content_text[:120],
            )

            # ------------------------------------------------------------------
            # 8. fetch_gfsmab_data — unit validation
            # ------------------------------------------------------------------
            result = await session.call_tool("fetch_gfsmab_data", {
                "freq": "A",
                "country": "US",
                "unit": "BADUNIT",
                "indicator": "GNLB__Z",
                "start": 2020,
                "end": 2020,
            })
            content_text = result.content[0].text if result.content else ""
            check(
                "Invalid GFSMAB unit returns error message",
                result.isError or "Invalid unit" in content_text,
                content_text[:120],
            )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    total = passed + failed
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed", end="")
    if failed:
        print(f"  ({failed} failed)")
    else:
        print()
    print("="*40)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_tests())
