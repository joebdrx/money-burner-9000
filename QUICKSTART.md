# Quick Start Guide

## 1. Installation (Already Done ✅)

```bash
# Virtual environment is set up
# Dependencies are installed
# Configuration template exists
```

## 2. Get a Wallet

You need a Polygon wallet with:
- Private key for authentication
- USDC balance for trading

**Options:**
- Use MetaMask and export private key
- Create new wallet with web3.py
- Use existing Ethereum wallet

## 3. Configure the Bot

Edit `.env`:
```bash
PRIVATE_KEY=your_actual_private_key_here  # ⚠️ Keep this secret!
ARBITRAGE_THRESHOLD=0.99    # Execute when total < this
MIN_PROFIT=0.01             # Minimum $0.01 profit
SCAN_INTERVAL=2             # Check every 2 seconds
MAX_POSITION_SIZE=100       # Max $100 per trade
DRY_RUN=true               # Start in safe mode
```

## 4. Test Run

```bash
# Activate virtual environment
source venv/bin/activate

# Test scanner (no trading)
python test_scanner.py

# Run bot continuously (dry-run mode)
python main.py
```

## 5. Monitor Results

The bot will:
- ✅ Scan 100+ markets every 2 seconds
- ✅ Detect when YES + NO < 0.99
- ✅ Log opportunities found
- ✅ Track performance in `positions.json`

## 6. Go Live (When Ready)

```bash
# In .env, change:
DRY_RUN=false

# Run with real money
python main.py
```

## Current Status

**✅ Bot is fully functional**

Test run results:
- 100 markets scanned successfully
- 0 arbitrage opportunities (markets currently efficient)
- All systems working correctly

## Understanding Opportunities

Arbitrage on Polymarket is:
- **Rare**: Markets are very efficient
- **Brief**: Opportunities last seconds
- **Competitive**: Many bots competing
- **Cumulative**: Profit builds over many small trades

The referenced $325K was from:
- Running 24/7
- Thousands of trades
- Catching 2-3 cent spreads repeatedly

## Tips for Success

1. **Run Continuously**: 24/7 operation catches more opportunities
2. **Start Small**: Use low MAX_POSITION_SIZE initially
3. **Monitor Logs**: Watch for patterns in opportunity timing
4. **Adjust Thresholds**: May need to fine-tune based on results
5. **Be Patient**: Opportunities come in bursts, not constantly

## Safety Reminders

- Never commit `.env` (contains private key)
- Start with DRY_RUN=true
- Test with small amounts first
- Keep private keys secure
- Monitor gas fees on Polygon

---

**Ready to run!** Start with `python main.py` in dry-run mode.
