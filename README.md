# Simplified Trading Bot — Binance Futures Testnet (USDT-M)

> Submission for the **Primetrade.ai AI Agent Development Internship** —
> "Build a Simplified Trading Bot" application task.

A small, structured Python CLI app for placing MARKET, LIMIT, and STOP_LIMIT
orders on Binance Futures Testnet (USDT-M), with input validation, logging,
and error handling.

## Project Structure

```
trading_bot/
  bot/
    __init__.py
    client.py          # Binance Futures client wrapper (API layer)
    orders.py          # Order-building + submission logic
    validators.py       # Input validation
    logging_config.py   # Logging setup
  cli.py                 # CLI entry point (command layer)
  requirements.txt
  .env.example
  sample_logs/           # Illustrative example logs (see "About the sample logs" below)
  logs/                  # Real logs land here when you run the app (auto-created)
  README.md
```

The **client layer** (`bot/client.py`) only knows how to talk to Binance.
The **order layer** (`bot/orders.py`) knows how to build order payloads and
format output. The **CLI layer** (`cli.py`) only handles argument parsing
and wiring things together. `bot/validators.py` is fully independent and
easy to unit test on its own.

## Setup

### 1. Create a Binance Futures Testnet account & API key

1. Go to https://testnet.binancefuture.com and log in with a GitHub account
   (this is a separate account system from binance.com).
2. Once logged in, go to the **API Key** section of the testnet site and
   generate an API key + secret.
3. You'll be given test USDT funds automatically — no real funds are ever
   involved on the testnet.

### 2. Clone and install dependencies

```bash
git clone <this-repo-url>
cd trading_bot
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure credentials

Copy `.env.example` to `.env` and fill in your testnet key/secret, **or**
just export them in your shell:

```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

(This app reads them via `os.environ`; if you prefer `.env` files, load them
with `python-dotenv` or `source .env` before running.)

You can also pass credentials directly via `--api-key` / `--api-secret`
flags instead of environment variables.

## Running the bot

### Market order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Limit order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 62000
```

### Stop-limit order (bonus order type)

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.01 \
    --price 59000 --stop-price 59500
```

### Dry run (no network call)

Useful for checking validation logic or demoing the CLI without valid
credentials:

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --dry-run
```

### Full CLI reference

```
--symbol       Trading pair, e.g. BTCUSDT               (required)
--side         BUY or SELL                              (required)
--type         MARKET, LIMIT, or STOP_LIMIT              (required)
--quantity     Order quantity, e.g. 0.01                 (required)
--price        Required for LIMIT and STOP_LIMIT
--stop-price   Required for STOP_LIMIT
--api-key      Overrides BINANCE_API_KEY env var
--api-secret   Overrides BINANCE_API_SECRET env var
--dry-run      Validate and print the request without calling the API
--log-level    Console verbosity: DEBUG/INFO/WARNING/ERROR (default INFO)
```

## What gets printed

Every run prints:
1. **Order Request** — the exact parameters about to be sent.
2. **Order Response** — `orderId`, `status`, `executedQty`, and `avgPrice`
   (when available) from Binance, or a clear error message on failure.
3. A final **SUCCESS** / **FAILURE** line.

## Logging

All requests, responses, and errors are logged to `logs/trading_bot.log`
(rotating file, DEBUG level — full detail) and to the console (INFO level
by default — clean, minimal). Nothing sensitive (API secret) is ever
logged.

## Error handling

- **Invalid input** (bad symbol, missing price for LIMIT, non-numeric
  quantity, etc.) is caught by `bot/validators.py` before any network call
  is made, and reported with a specific message.
- **API errors** (e.g. insufficient testnet balance, invalid symbol,
  rate limits) raise `binance.exceptions.BinanceAPIException`, which is
  caught and normalized into a `BinanceClientError` with the Binance error
  code/message.
- **Network/timeout errors** (connection refused, DNS failure, timeout)
  are caught and reported distinctly from API errors.
- All of the above are logged with full detail before a short, clear
  message is printed to the console.

## About the sample logs

This project was built and verified in a sandboxed development
environment whose outbound network access does not include
`testnet.binancefuture.com`. In that environment, running the bot end
to end correctly progresses through validation → client initialization
→ request building → the API call, and then fails at the network layer
with a clear, well-formatted connectivity error — which is exactly the
behavior the "network failures" requirement asks the app to handle
correctly. That failure log is proof the error-handling path works, but
it is not a successful order.

Because of that, `sample_logs/sample_market_order.log` and
`sample_logs/sample_limit_order.log` are **illustrative examples**
(clearly labeled as such) showing the exact log format you will get for
a real, successful MARKET and LIMIT order — populated with a realistic
Binance response shape. When you run this app yourself with real
testnet credentials from a machine with normal internet access, genuine
versions of these logs will be written to `logs/trading_bot.log`.

## Assumptions

- USDT-M perpetual futures only (not COIN-M).
- Quantity/price precision (`stepSize`/`tickSize`/`minNotional` per
  symbol) is validated by Binance itself at request time, not
  re-implemented client-side; API rejections are surfaced as clear error
  messages rather than silently retried or auto-corrected.
- `timeInForce` for LIMIT/STOP_LIMIT orders defaults to `GTC`.
- The bonus order type implemented is **STOP_LIMIT**, mapped to Binance
  Futures' `STOP` order type (stop price + limit price).
- Credentials are read from environment variables by default so they're
  never hard-coded or committed to source control.

## Bonus implemented

- **Third order type**: STOP_LIMIT (`--type STOP_LIMIT --price ... --stop-price ...`)
- **Enhanced CLI UX**: `--dry-run` mode, clear per-field validation error
  messages, and a `--log-level` flag for adjustable verbosity.
