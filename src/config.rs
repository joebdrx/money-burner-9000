//! Configuration management for Polymarket arbitrage bot.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BotConfig {
    /// Private key for authentication
    pub private_key: String,

    /// Chain ID (137 for Polygon mainnet)
    pub chain_id: u64,

    /// Combined YES+NO price threshold
    pub arbitrage_threshold: f64,

    /// Minimum profit to execute trade
    pub min_profit: f64,

    /// Seconds between scans
    pub scan_interval: u64,

    /// Maximum $ per position
    pub max_position_size: f64,

    /// Set to false for live trading
    pub dry_run: bool,

    /// Logging level
    pub log_level: String,

    /// List of token IDs to monitor
    pub target_markets: Option<Vec<String>>,
}

impl Default for BotConfig {
    fn default() -> Self {
        Self {
            private_key: String::new(),
            chain_id: 137,
            arbitrage_threshold: 0.99,
            min_profit: 0.02,
            scan_interval: 2,
            max_position_size: 100.0,
            dry_run: true,
            log_level: "INFO".to_string(),
            target_markets: None,
        }
    }
}

impl BotConfig {
    /// Load configuration from environment variables
    pub fn from_env() -> Result<Self> {
        dotenv::dotenv().ok();

        let private_key = env::var("PRIVATE_KEY")
            .context("PRIVATE_KEY environment variable is required")?;

        let target_markets_str = env::var("TARGET_MARKETS").unwrap_or_default();
        let target_markets = if target_markets_str.is_empty() {
            None
        } else {
            Some(
                target_markets_str
                    .split(',')
                    .map(|s| s.trim().to_string())
                    .filter(|s| !s.is_empty())
                    .collect(),
            )
        };

        Ok(Self {
            private_key,
            chain_id: env::var("CHAIN_ID")
                .unwrap_or_else(|_| "137".to_string())
                .parse()
                .context("Invalid CHAIN_ID")?,
            arbitrage_threshold: env::var("ARBITRAGE_THRESHOLD")
                .unwrap_or_else(|_| "0.99".to_string())
                .parse()
                .context("Invalid ARBITRAGE_THRESHOLD")?,
            min_profit: env::var("MIN_PROFIT")
                .unwrap_or_else(|_| "0.02".to_string())
                .parse()
                .context("Invalid MIN_PROFIT")?,
            scan_interval: env::var("SCAN_INTERVAL")
                .unwrap_or_else(|_| "2".to_string())
                .parse()
                .context("Invalid SCAN_INTERVAL")?,
            max_position_size: env::var("MAX_POSITION_SIZE")
                .unwrap_or_else(|_| "100".to_string())
                .parse()
                .context("Invalid MAX_POSITION_SIZE")?,
            dry_run: env::var("DRY_RUN")
                .unwrap_or_else(|_| "true".to_string())
                .to_lowercase()
                == "true",
            log_level: env::var("LOG_LEVEL").unwrap_or_else(|_| "INFO".to_string()),
            target_markets,
        })
    }

    /// Validate configuration settings
    pub fn validate(&self) -> Result<()> {
        if self.arbitrage_threshold >= 1.0 {
            anyhow::bail!("arbitrage_threshold must be < 1.0");
        }
        if self.min_profit <= 0.0 {
            anyhow::bail!("min_profit must be > 0");
        }
        if self.scan_interval == 0 {
            anyhow::bail!("scan_interval must be > 0");
        }
        if self.max_position_size <= 0.0 {
            anyhow::bail!("max_position_size must be > 0");
        }
        Ok(())
    }
}
