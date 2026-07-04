"""
Thin wrapper around python-binance's Client, pinned to the Binance
Futures Testnet (USDT-M) REST endpoint.

Keeping this as its own layer means the rest of the app (orders.py,
cli.py) never has to know whether we're using python-binance, raw
requests, or something else -- it just calls methods on
BinanceFuturesClient.
"""

import logging

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger("trading_bot.client")

# Binance Futures Testnet (USDT-M) endpoints
FUTURES_TESTNET_REST_URL = "https://testnet.binancefuture.com/fapi"


class BinanceClientError(Exception):
    """Raised for any client-side or API-side failure talking to Binance."""


class BinanceFuturesClient:
    """
    Wraps python-binance's Client and forces it to talk to the USDT-M
    Futures Testnet, regardless of library defaults.
    """

    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise BinanceClientError(
                "API key and secret are required. Set BINANCE_API_KEY and "
                "BINANCE_API_SECRET (env vars) or pass --api-key/--api-secret."
            )

        try:
            # ping=False: skip python-binance's automatic constructor-time
            # ping, which targets the SPOT endpoint and is irrelevant (and
            # sometimes unreachable) for a futures-only bot.
            self._client = Client(api_key, api_secret, testnet=True, ping=False)
            # Some python-binance versions only redirect the SPOT testnet URL
            # via testnet=True. Force the FUTURES URL explicitly to be safe.
            self._client.FUTURES_URL = FUTURES_TESTNET_REST_URL
        except Exception as exc:
            self._handle_exception("client_init", exc)

        logger.debug("Initialized Binance Futures client against %s", FUTURES_TESTNET_REST_URL)

    def ping(self):
        """Simple connectivity/auth check."""
        logger.debug("REQUEST -> futures_ping()")
        try:
            result = self._client.futures_ping()
            logger.debug("RESPONSE <- futures_ping(): %s", result)
            return result
        except Exception as exc:
            self._handle_exception("ping", exc)

    def get_account_balance(self):
        logger.debug("REQUEST -> futures_account_balance()")
        try:
            result = self._client.futures_account_balance()
            logger.debug("RESPONSE <- futures_account_balance(): %s", result)
            return result
        except Exception as exc:
            self._handle_exception("get_account_balance", exc)

    def create_order(self, **params):
        """
        Place a futures order. `params` should already be a fully-formed
        dict suitable for python-binance's futures_create_order, e.g.:
            {symbol, side, type, quantity, price, timeInForce, ...}
        """
        logger.debug("REQUEST -> futures_create_order(%s)", params)
        try:
            result = self._client.futures_create_order(**params)
            logger.debug("RESPONSE <- futures_create_order(): %s", result)
            return result
        except Exception as exc:
            self._handle_exception("create_order", exc, params)

    def get_order(self, symbol: str, order_id: int):
        logger.debug("REQUEST -> futures_get_order(symbol=%s, orderId=%s)", symbol, order_id)
        try:
            result = self._client.futures_get_order(symbol=symbol, orderId=order_id)
            logger.debug("RESPONSE <- futures_get_order(): %s", result)
            return result
        except Exception as exc:
            self._handle_exception("get_order", exc)

    @staticmethod
    def _handle_exception(operation: str, exc: Exception, context=None):
        """
        Normalize every failure mode (bad API response, malformed request,
        network/timeout issues) into a single BinanceClientError with a
        clear message, after logging the full detail.
        """
        if isinstance(exc, BinanceAPIException):
            logger.error(
                "Binance API error during %s | status=%s code=%s message=%s | context=%s",
                operation, exc.status_code, exc.code, exc.message, context,
            )
            raise BinanceClientError(
                f"Binance API rejected the request ({exc.code}): {exc.message}"
            ) from exc

        if isinstance(exc, BinanceRequestException):
            logger.error("Binance request error during %s: %s | context=%s", operation, exc, context)
            raise BinanceClientError(f"Malformed request/response during {operation}: {exc}") from exc

        if isinstance(exc, (Timeout,)):
            logger.error("Timeout during %s | context=%s", operation, context)
            raise BinanceClientError(
                f"Request to Binance timed out during {operation}. Check your network and retry."
            ) from exc

        if isinstance(exc, (RequestsConnectionError,)):
            logger.error("Connection error during %s | context=%s", operation, context)
            raise BinanceClientError(
                f"Could not connect to Binance Futures Testnet during {operation}. "
                f"Check your internet connection / firewall."
            ) from exc

        if isinstance(exc, RequestException):
            logger.error("Network error during %s: %s | context=%s", operation, exc, context)
            raise BinanceClientError(f"Network error during {operation}: {exc}") from exc

        logger.exception("Unexpected error during %s | context=%s", operation, context)
        raise BinanceClientError(f"Unexpected error during {operation}: {exc}") from exc
