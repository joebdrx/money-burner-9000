# Polymarket Arbitrage Bot

A Python-based arbitrage bot that exploits price inefficiencies in Polymarket's binary prediction markets.

## Strategy

The bot identifies and exploits a simple mathematical inefficiency:

- In Polymarket binary markets, exactly one of YES or NO pays $1.00
- Therefore, `YES price + NO price` should always equal $1.00
- When markets move quickly, this can slip (e.g., YES=$0.48, NO=$0.49)
- The bot buys both sides and locks in risk-free profit regardless of outcome

**Example Trade:**
```
Buy YES @ $0.48
Buy NO @ $0.49
Total cost: $0.97

When market resolves:
One side pays: $1.00
Profit: $0.03 (3.1% return)
```

## Features

- ✅ Real-time market scanning
- ✅ Automatic arbitrage detection
- ✅ Simultaneous YES/NO order execution
- ✅ Position tracking and PnL calculation
- ✅ Dry-run mode for testing
- ✅ Configurable thresholds and limits
- ✅ Comprehensive logging

## Installation

### Prerequisites

- Python 3.9 or higher
- Polygon (MATIC) wallet with private key
- USDC on Polygon network for trading

### Setup

1. Clone the repository:
```bash
cd /home/pete/Documents/software_projects/prediction-bots
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your PRIVATE_KEY
```

## Configuration

Edit `.env` to configure the bot:

```bash
# Wallet Configuration
PRIVATE_KEY=your_private_key_here
CHAIN_ID=137  # Polygon mainnet

# Bot Parameters
ARBITRAGE_THRESHOLD=0.99    # Execute when YES+NO < this value
MIN_PROFIT=0.02             # Minimum profit in $ to execute
SCAN_INTERVAL=2             # Seconds between scans
MAX_POSITION_SIZE=100       # Maximum $ per position

# Safety
DRY_RUN=true               # Set to false for live trading
LOG_LEVEL=INFO
```

## Usage

### Dry Run (Recommended First)

Test without risking real funds:

```bash
python main.py
```

The bot will scan markets and log opportunities without executing trades.

### Live Trading

**⚠️ WARNING: Live trading uses real money. Start small!**

1. Set `DRY_RUN=false` in `.env`
2. Ensure you have USDC on Polygon
3. Set appropriate `MAX_POSITION_SIZE`
4. Run the bot:

```bash
python main.py
```

## How It Works

### 1. Market Scanner
- Continuously monitors Polymarket binary markets
- Fetches real-time prices for YES and NO tokens
- Focuses on high-volume markets for better liquidity

### 2. Arbitrage Detector
- Calculates `YES + NO` for each market
- Identifies when total < threshold (default 0.99)
- Validates profit potential after fees
- Filters for minimum profit requirements

### 3. Order Executor
- Places simultaneous market orders for both sides
- Uses Fill-or-Kill (FOK) orders for atomicity
- Handles partial fills and errors
- Implements retry logic

### 4. Position Manager
- Tracks all open positions
- Monitors market resolutions
- Calculates realized PnL
- Generates performance statistics

## Performance Metrics

The bot tracks:
- Total profit/loss
- Win rate (successful executions)
- Average profit per trade
- Total capital deployed
- Number of positions (active/closed)

View stats with `CTRL+C` or check `positions.json`.

## Risk Considerations

### Execution Risk
- Both orders must fill simultaneously
- Partial fills can result in directional exposure
- Network latency affects speed

### Market Risk
- Market cancellations (rare)
- API downtime
- Insufficient liquidity for large sizes

### Fee Considerations
- Polymarket charges trading fees
- Must be factored into MIN_PROFIT
- Gas fees on Polygon (usually negligible)

### Competition
- Other bots compete for same opportunities
- Speed is critical (milliseconds matter)
- Spreads disappear quickly

## Monitoring

The bot logs:
- ✅ Detected opportunities
- 📊 Execution results
- 💰 Position updates
- 📈 Performance statistics

Check `positions.json` for detailed position history.

## Troubleshooting

### "PRIVATE_KEY environment variable is required"
- Ensure `.env` file exists
- Check `PRIVATE_KEY` is set correctly

### "Insufficient funds"
- Ensure USDC balance on Polygon
- Check wallet has enough for position size

### "No opportunities found"
- Markets may be efficient currently
- Try lowering `ARBITRAGE_THRESHOLD`
- Increase `SCAN_INTERVAL` to reduce API calls

### Rate Limiting
- Reduce scan frequency
- Implement exponential backoff
- Contact Polymarket for rate limit increase

## Development

### Project Structure
```
.
├── main.py                 # Entry point
├── bot.py                  # Main orchestration
├── config.py               # Configuration management
├── market_scanner.py       # Market data fetching
├── arbitrage_detector.py   # Opportunity detection
├── order_executor.py       # Trade execution
├── position_manager.py     # Position tracking
├── requirements.txt        # Dependencies
├── .env.example           # Config template
└── claude.md              # Strategy documentation
```

### Adding Features

1. **WebSocket Support**: Implement real-time price feeds
2. **Advanced Filters**: Add liquidity/volume requirements
3. **Multi-Market**: Support more than binary markets
4. **Auto-Compound**: Reinvest profits automatically
5. **Telegram Alerts**: Get notified of executions

## API Reference

- [Polymarket Documentation](https://docs.polymarket.com)
- [py-clob-client](https://github.com/Polymarket/py-clob-client)

## Disclaimer

**This bot is for educational purposes.**

- Use at your own risk
- Start with small position sizes
- Understand the risks before trading
- No guarantee of profitability
- Markets can change rapidly

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Polymarket documentation
3. Check py-clob-client issues on GitHub

---

**Remember:** Past performance does not guarantee future results. Always test thoroughly in dry-run mode first.
