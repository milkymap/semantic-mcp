import click

from .mcp_server import mcp


@click.group()
def cli():
    """MCP Runtime - Execution and lifecycle management for MCP servers"""
    pass


@cli.command()
@click.option("--transport", default="stdio", type=click.Choice(["stdio", "sse", "streamable-http"]))
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8001, type=int)
def serve(transport: str, host: str, port: int):
    """Start the MCP runtime server"""
    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=transport, host=host, port=port)


def main():
    cli()


if __name__ == "__main__":
    main()
