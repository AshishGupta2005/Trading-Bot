#!/usr/bin/env python3
"""
CLI entry point for the Simplified Trading Bot (Binance Futures Testnet).

Examples
--------
Market order:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

Limit order:
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000

Stop-limit order (bonus):
    python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.01 \\
        --price 59000 --stop-price 59500

Dry run (validate + print request, do not call the API -- useful without
real credentials, e.g. for demoing or testing):
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --dry-run
"""

import argparse
import os
import sys

from bot.logging_config import setup_logging
from bot.validators import validate_order_request

logger = setup_logging()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET/LIMIT/STOP_LIMIT orders on Binance Futures Testnet (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"])
    parser.add_argument(
        "--type", dest="order_type", required=True,
        choices=["MARKET", "LIMIT", "STOP_LIMIT", "market", "limit", "stop_limit"],
    )
    parser.add_argument("--quantity", required=True, help="Order quantity, e.g. 0.01")
    parser.add_argument("--price", help="Required for LIMIT and STOP_LIMIT orders")
    parser.add_argument("--stop-price", dest="stop_price", help="Required for STOP_LIMIT orders")

    parser.add_argument(
        "--api-key", dest="api_key", default=os.environ.get("BINANCE_API_KEY"),
        help="Defaults to BINANCE_API_KEY env var",
    )
    parser.add_argument(
        "--api-secret", dest="api_secret", default=os.environ.get("BINANCE_API_SECRET"),
        help="Defaults to BINANCE_API_SECRET env var",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate and print the order request without calling the Binance API",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log verbosity (file log always captures DEBUG)",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # 1. Validate input first -- fail fast, before touching the network.
    try:
        order = validate_order_request(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValueError as exc:
        logger.error("Input validation failed: %s", exc)
        print(f"\nERROR: {exc}\n")
        return 1

    logger.info("Validated order request: %s", order)

    if args.dry_run:
        print("\n[DRY RUN] No request will be sent to Binance.")
        print("--- Order Request (validated) ---")
        for key, value in order.items():
            print(f"  {key}: {value}")
        return 0

    # 2. Build the client (this is where missing credentials get caught).
    try:
        from bot.client import BinanceClientError, BinanceFuturesClient
        from bot.orders import OrderManager

        client = BinanceFuturesClient(args.api_key, args.api_secret)
        order_manager = OrderManager(client)
    except BinanceClientError as exc:
        logger.error("Client initialization failed: %s", exc)
        print(f"\nERROR: {exc}\n")
        return 1
    except Exception as exc:  # e.g. python-binance import issue
        logger.exception("Unexpected error initializing client")
        print(f"\nERROR: unexpected error initializing client: {exc}\n")
        return 1

    # 3. Submit the order.
    try:
        order_manager.place_order(
            symbol=order["symbol"],
            side=order["side"],
            order_type=order["order_type"],
            quantity=order["quantity"],
            price=order["price"],
            stop_price=order["stop_price"],
        )
        return 0
    except BinanceClientError:
        # Already logged and printed inside OrderManager/client.
        return 1
    except Exception:
        logger.exception("Unexpected error placing order")
        print("\nERROR: unexpected error placing order. See logs/trading_bot.log for details.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
