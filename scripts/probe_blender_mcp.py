"""Functional MCP stdio check. Run with the installed MCP virtualenv's Python."""
import argparse
import json
from pathlib import Path
import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def check(output):
    parameters = StdioServerParameters(command=str(ROOT / 'scripts/blender_mcp_server.sh'))
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            listing = await session.list_tools()
            response = await session.call_tool('get_scene_info', {'user_prompt': 'Validate cloud installation by inspecting scene only', 'limit': 3})
            texts = [item.text for item in response.content if item.type == 'text']
            text = '\n'.join(texts)
            # Upstream may return textual errors with isError=false; inspect actual content.
            if response.isError or text.startswith('Error') or not text.startswith('Scene '):
                raise RuntimeError(f'MCP get_scene_info failed: {text}')
            evidence = {'server': initialized.serverInfo.model_dump(),
                        'tools': [tool.name for tool in listing.tools],
                        'get_scene_info_passed': True, 'scene_result': text}
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(evidence, indent=2) + '\n')
            print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    anyio.run(check, args.out)
