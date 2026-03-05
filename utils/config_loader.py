import json
import os

_config = None
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


def load_config(path: str = _CONFIG_PATH) -> dict:
    """Load and cache config.json. Call this once at startup."""
    global _config
    with open(path, "r") as f:
        _config = json.load(f)
    return _config


def get(key_path: str, default=None):
    """
    Fetch a value from config using dot-notation.
    Example: get("risk.risk_per_trade_pct") → 0.25
    """
    if _config is None:
        load_config()

    keys = key_path.split(".")
    val = _config
    try:
        for k in keys:
            val = val[k]
        return val
    except (KeyError, TypeError):
        return default


def get_risk_amount_inr() -> float:
    """Returns actual ₹ amount to risk per trade based on current balance."""
    balance = get("account.balance")
    risk_pct = get("risk.risk_per_trade_pct")
    return round(balance * risk_pct / 100, 2)


def get_max_loss_day_inr() -> float:
    """Returns max allowed loss per day in ₹."""
    balance = get("account.balance")
    pct = get("risk.max_loss_day_pct")
    return round(balance * pct / 100, 2)


def get_max_loss_week_inr() -> float:
    """Returns max allowed loss per week in ₹."""
    balance = get("account.balance")
    pct = get("risk.max_loss_week_pct")
    return round(balance * pct / 100, 2)


def get_profit_target_inr(rr: float = None) -> float:
    """Returns profit target in ₹ based on R:R ratio."""
    risk = get_risk_amount_inr()
    rr = rr or get("targets.rr_ratio_min")
    return round(risk * rr, 2)


def update_balance(new_balance: float):
    """
    Update account balance in config.json.
    Called automatically when scaling trigger is hit.
    """
    global _config
    if _config is None:
        load_config()

    _config["account"]["balance"] = new_balance
    with open(_CONFIG_PATH, "w") as f:
        json.dump(_config, f, indent=2)

def get_api_key() -> str:
    """Return API key from config or environment."""
    key = get("account.api_key")
    if key:
        return key
    exch = get("account.exchange", "").upper()
    return os.environ.get(f"{exch}_API_KEY", "")


def get_api_secret() -> str:
    """Return API secret from config or environment."""
    secret = get("account.api_secret")
    if secret:
        return secret
    exch = get("account.exchange", "").upper()
    return os.environ.get(f"{exch}_API_SECRET", "")




# API CREDENTIALS UTILITIES

def get_api_key() -> str:
    """Return API key from config or environment. """
    key = get("account.api_key")
    if key:
        return key
    exch = get("account.exchange", "").upper()
    import os
    return os.environ.get(f"{exch}_API_KEY", "")


def get_api_secret() -> str:
    """Return API secret from config or environment. """
    secret = get("account.api_secret")
    if secret:
        return secret
    exch = get("account.exchange", "").upper()
    import os
    return os.environ.get(f"{exch}_API_SECRET", "")
