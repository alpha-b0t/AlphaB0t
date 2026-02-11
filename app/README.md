# APP

# RiskManager Design

RiskManager should enforce:

Max risk per trade (% of balance)

Max position size

Max daily loss

Max total drawdown

Optional: leverage limits

# Professional Risk Model

Typical rules:

Risk per trade: 1–2%

Max portfolio exposure: 20–30%

Max drawdown: 10–20%

Max leverage: configurable

# Advanced Improvements (Professional Grade)

If you're building something serious:

Add:

Trailing stop logic

Kelly criterion sizing (optional)

Daily loss limit

Per-symbol exposure cap

Volatility-adjusted sizing (ATR-based)

Slippage modeling

Commission modeling

# Important Architecture Advice

Do NOT:

Put risk logic in Strategy

Put position tracking in Exchange

Let Strategy control size directly

Keep:

Strategy → direction only

RiskManager → sizing + approval

PositionManager → state + PnL

Exchange → execution only

That separation prevents catastrophic bugs.

# How Everything Connects

Here’s the correct execution flow in your Bot:

Strategy → generates signal
↓
RiskManager → calculates position size
↓
RiskManager → validates order
↓
Exchange → executes order
↓
PositionManager → tracks position
↓
PositionManager → monitors stop/TP

# Advanced Improvements (Professional Grade)

If you're building something serious:

Add:

Trailing stop logic

Kelly criterion sizing (optional)

Daily loss limit

Per-symbol exposure cap

Volatility-adjusted sizing (ATR-based)

Slippage modeling

Commission modeling