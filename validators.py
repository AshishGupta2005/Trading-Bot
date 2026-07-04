"""
Input validation helpers for the trading bot CLI.

All functions raise ValueError with a clear, user-facing message on
invalid input. Keeping validation separate from the CLI and the API
layer makes it easy to unit test and reuse.
"""

import re

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}

# Reasonable symbol pattern for Binance USDT-M perpetual futures, e.g. BTCUSDT
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


def validate_symbol(symbol: str) -> str:
    if not symbol:
        raise ValueError("Symbol is required (e.g. BTCUSDT).")
    symbol = symbol.strip().upper()
    if not _SYMBOL_PATTERN.match(symbol):
        raise ValueError(
            f"Invalid symbol '{symbol}'. Expected an uppercase alphanumeric "
            f"symbol like 'BTCUSDT'."
        )
    return symbol


def validate_side(side: str) -> str:
    if not side:
        raise ValueError("Side is required (BUY or SELL).")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type: str) -> str:
    if not order_type:
        raise ValueError("Order type is required (MARKET, LIMIT, or STOP_LIMIT).")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity) -> float:
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity must be a number, got '{quantity}'.")
    if quantity <= 0:
        raise ValueError(f"Quantity must be greater than 0, got {quantity}.")
    return quantity


def validate_price(price, field_name: str = "price") -> float:
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number, got '{price}'.")
    if price <= 0:
        raise ValueError(f"{field_name} must be greater than 0, got {price}.")
    return price


def validate_order_request(symbol, side, order_type, quantity, price=None, stop_price=None):
    """
    Validate a full order request and return normalized values as a dict.
    Raises ValueError on the first invalid field found.
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)

    result = {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": None,
        "stop_price": None,
    }

    if order_type == "LIMIT":
        if price is None:
            raise ValueError("Price is required for LIMIT orders.")
        result["price"] = validate_price(price, "price")

    elif order_type == "STOP_LIMIT":
        if price is None:
            raise ValueError("Price is required for STOP_LIMIT orders.")
        if stop_price is None:
            raise ValueError("Stop price is required for STOP_LIMIT orders.")
        result["price"] = validate_price(price, "price")
        result["stop_price"] = validate_price(stop_price, "stop_price")

    return result
