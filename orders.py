"""
Order placement logic.

This module turns validated, normalized order requests into the exact
parameters the Binance Futures API expects, submits them through the
client layer, and returns a normalized result. It also owns the
"print a clean summary" formatting so the CLI layer stays thin.
"""

import logging

from .client import BinanceClientError, BinanceFuturesClient

logger = logging.getLogger("trading_bot.orders")


class OrderManager:
    def __init__(self, client: BinanceFuturesClient):
        self._client = client

    # ---- Public API -----------------------------------------------------

    def place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        """
        Dispatch to the right order-building method based on order_type,
        submit it, and return the raw Binance response dict.

        Expects already-validated input (see bot.validators).
        """
        if order_type == "MARKET":
            params = self._build_market_params(symbol, side, quantity)
        elif order_type == "LIMIT":
            params = self._build_limit_params(symbol, side, quantity, price)
        elif order_type == "STOP_LIMIT":
            params = self._build_stop_limit_params(symbol, side, quantity, price, stop_price)
        else:
            # Should never happen if validators.py was used upstream.
            raise ValueError(f"Unsupported order type: {order_type}")

        self._print_request_summary(params)
        logger.info("Submitting order request: %s", params)

        try:
            response = self._client.create_order(**params)
        except BinanceClientError as exc:
            logger.error("Order submission failed: %s", exc)
            self._print_failure(exc)
            raise

        logger.info("Order submission succeeded: orderId=%s status=%s",
                     response.get("orderId"), response.get("status"))
        self._print_response_summary(response)
        return response

    # ---- Param builders ---------------------------------------------------

    @staticmethod
    def _build_market_params(symbol, side, quantity):
        return {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
        }

    @staticmethod
    def _build_limit_params(symbol, side, quantity, price):
        return {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": quantity,
            "price": price,
            "timeInForce": "GTC",
        }

    @staticmethod
    def _build_stop_limit_params(symbol, side, quantity, price, stop_price):
        # Bonus order type: STOP (stop-limit) futures order.
        return {
            "symbol": symbol,
            "side": side,
            "type": "STOP",
            "quantity": quantity,
            "price": price,
            "stopPrice": stop_price,
            "timeInForce": "GTC",
        }

    # ---- Output formatting -------------------------------------------------

    @staticmethod
    def _print_request_summary(params):
        print("\n--- Order Request ---")
        print(f"  Symbol     : {params.get('symbol')}")
        print(f"  Side       : {params.get('side')}")
        print(f"  Type       : {params.get('type')}")
        print(f"  Quantity   : {params.get('quantity')}")
        if "price" in params:
            print(f"  Price      : {params.get('price')}")
        if "stopPrice" in params:
            print(f"  Stop Price : {params.get('stopPrice')}")

    @staticmethod
    def _print_response_summary(response):
        print("\n--- Order Response ---")
        print(f"  Order ID     : {response.get('orderId')}")
        print(f"  Status       : {response.get('status')}")
        print(f"  Executed Qty : {response.get('executedQty')}")
        avg_price = response.get("avgPrice")
        if avg_price is not None:
            print(f"  Avg Price    : {avg_price}")
        print("\nSUCCESS: order submitted to Binance Futures Testnet.\n")

    @staticmethod
    def _print_failure(exc):
        print("\n--- Order Response ---")
        print(f"  Error: {exc}")
        print("\nFAILURE: order was not placed. See logs/trading_bot.log for details.\n")
