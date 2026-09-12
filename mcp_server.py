from fastmcp import FastMCP
from app.tools import check_order_status
mcp=FastMCP("ecommerce-order-tools")
@mcp.tool()
def lookup_order(record_id: str) -> dict:
    """Look up a fabricated E-commerce order and return status, value and escalation score."""
    return check_order_status(record_id)
if __name__=="__main__":
    mcp.run(transport="http",host="127.0.0.1",port=8001)
