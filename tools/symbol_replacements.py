"""Trading symbol replacements when tickers change."""

import csv
from functools import lru_cache
from pathlib import Path

REPLACEMENTS_FILE = Path(__file__).resolve().parent / 'symbol-replacements.csv'
DO_NOT_INCLUDE_FILE = Path(__file__).resolve().parent / 'do-not-include.csv'


RESERVED_PORTFOLIO_KEYS = frozenset({'Title'})


def _looks_like_trading_symbol(key):
    """
    Return True when key should be treated as a ticker for replacements.

    Asset class and subclass names (for example ``US Stocks:Financials``)
    contain spaces or colons and must not be uppercased like tickers.
    """
    key = str(key).strip()
    if not key or key in RESERVED_PORTFOLIO_KEYS:
        return False
    if any(ch in key for ch in (' ', ':')):
        return False
    return True


@lru_cache(maxsize=1)
def load_replacements():
    """Return a dict of old_symbol -> new_symbol from symbol-replacements.csv."""
    mapping = {}
    if not REPLACEMENTS_FILE.is_file():
        return mapping

    with REPLACEMENTS_FILE.open(newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            old = row.get('old_symbol', '').strip().upper()
            new = row.get('new_symbol', '').strip().upper()
            if old and new:
                mapping[old] = new
    return mapping


def resolve_symbol(symbol):
    """Return the current trading symbol, applying replacements when configured."""
    if symbol is None:
        return symbol
    symbol = str(symbol).strip().upper()
    return load_replacements().get(symbol, symbol)


def resolve_symbols(symbols):
    """Return {original: resolved} for a list of symbols."""
    return {symbol: resolve_symbol(symbol) for symbol in symbols}


@lru_cache(maxsize=1)
def load_do_not_include():
    """Return symbols to exclude from strategy portfolio_option dicts."""
    blocked = set()
    if not DO_NOT_INCLUDE_FILE.is_file():
        return frozenset(blocked)

    with DO_NOT_INCLUDE_FILE.open(newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row.get('symbol', '').strip().upper()
            if symbol:
                blocked.add(resolve_symbol(symbol))
    return frozenset(blocked)


def remove_do_not_include(portfolio_option, verbose=True):
    """
    Remove do-not-include symbols from a portfolio_option dict in place.

    Skips reserved keys (for example ``Title``) and non-ticker keys such as
    asset subclass names.
    """
    if not portfolio_option:
        return portfolio_option

    blocked = load_do_not_include()
    if not blocked:
        return portfolio_option

    for key in list(portfolio_option.keys()):
        if key in RESERVED_PORTFOLIO_KEYS or not _looks_like_trading_symbol(key):
            continue
        canonical = resolve_symbol(key)
        if canonical in blocked:
            if verbose:
                print(f'Do-not-include: removing {key} from portfolio_option')
            del portfolio_option[key]

    return portfolio_option


def log_replacement(old_symbol, new_symbol):
    if old_symbol != new_symbol:
        print(f'Symbol replacement: {old_symbol} -> {new_symbol}')


def normalize_portfolio(portfolio):
    """
    Rename portfolio keys using symbol replacements and merge duplicate keys.
    """
    if not portfolio:
        return {}

    result = {}
    for symbol, quantity in portfolio.items():
        canonical = resolve_symbol(symbol)
        if canonical != str(symbol).strip().upper():
            log_replacement(str(symbol).strip().upper(), canonical)
        result[canonical] = result.get(canonical, 0) + int(quantity)
    return dict(sorted(result.items()))


def normalize_portfolio_option(portfolio_option):
    """
    Rename portfolio option keys using symbol replacements and merge weights.
   """
    if not portfolio_option:
        return portfolio_option

    merged = {}
    for key, weight in portfolio_option.items():
        if key in RESERVED_PORTFOLIO_KEYS:
            merged[key] = weight
            continue
        if not _looks_like_trading_symbol(key):
            merged[key] = weight
            continue
        canonical = resolve_symbol(key)
        if canonical != str(key).strip().upper():
            log_replacement(str(key).strip().upper(), canonical)
        merged[canonical] = merged.get(canonical, 0) + weight

    portfolio_option.clear()
    portfolio_option.update(merged)
    return portfolio_option


def lookup_quote_price(symbol, quote_per_investment):
    """Find a quote price using current or replaced symbol keys."""
    if not quote_per_investment:
        return None

    resolved = resolve_symbol(symbol)
    for key in (resolved, str(symbol).strip().upper()):
        price = quote_per_investment.get(key)
        if price not in (None, 'N/A', 'None', '', 0):
            return float(price)

    for old, new in load_replacements().items():
        if new == resolved:
            price = quote_per_investment.get(old)
            if price not in (None, 'N/A', 'None', '', 0):
                return float(price)
    return None
