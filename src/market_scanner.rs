//! Market scanner for monitoring Polymarket prices.

use anyhow::Result;
use log::{debug, error, info, warn};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketPrice {
    pub token_id: String,
    pub yes_price: f64,
    pub no_price: f64,
    pub yes_token_id: String,
    pub no_token_id: String,
    pub condition_id: String,
    pub question: String,
    pub total_price: f64,
}

impl MarketPrice {
    /// Calculate the arbitrage spread (1.0 - total_price)
    pub fn arbitrage_spread(&self) -> f64 {
        1.0 - self.total_price
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Token {
    token_id: String,
    outcome: String,
    price: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Market {
    condition_id: String,
    tokens: Vec<Token>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SimplifiedMarketsResponse {
    data: Vec<Market>,
}

pub struct MarketScanner {
    client: reqwest::Client,
    base_url: String,
    market_cache: HashMap<String, Market>,
}

impl MarketScanner {
    /// Initialize the market scanner
    pub fn new(base_url: &str) -> Self {
        Self {
            client: reqwest::Client::new(),
            base_url: base_url.to_string(),
            market_cache: HashMap::new(),
        }
    }

    /// Fetch active binary markets
    pub async fn get_active_markets(&mut self, limit: usize) -> Result<Vec<Market>> {
        let url = format!("{}/simplified-markets", self.base_url);

        let response = self
            .client
            .get(&url)
            .send()
            .await?
            .json::<SimplifiedMarketsResponse>()
            .await?;

        let mut binary_markets = Vec::new();

        for market in response.data {
            // Check if market has exactly 2 outcomes (YES/NO)
            if market.tokens.len() != 2 {
                continue;
            }

            let p0 = market.tokens[0].price;
            let p1 = market.tokens[1].price;

            // Skip fully resolved markets (prices are exactly 0 or 1)
            if (p0 == 0.0 || p0 == 1.0) && (p1 == 0.0 || p1 == 1.0) {
                continue;
            }

            // Skip markets with invalid prices
            if p0 <= 0.0 || p1 <= 0.0 {
                continue;
            }

            // Cache market metadata
            self.market_cache
                .insert(market.condition_id.clone(), market.clone());

            binary_markets.push(market);

            if binary_markets.len() >= limit {
                break;
            }
        }

        info!("Found {} active binary markets", binary_markets.len());
        Ok(binary_markets)
    }

    /// Get current prices for a binary market
    pub fn get_market_prices(&self, condition_id: &str) -> Option<MarketPrice> {
        let market = self.market_cache.get(condition_id)?;

        if market.tokens.len() != 2 {
            return None;
        }

        let token_0 = &market.tokens[0];
        let token_1 = &market.tokens[1];

        let price_0 = token_0.price;
        let price_1 = token_1.price;

        // Skip if prices are invalid
        if price_0 <= 0.0 || price_1 <= 0.0 {
            debug!(
                "Invalid prices for {}: {}, {}",
                condition_id, price_0, price_1
            );
            return None;
        }

        // Create descriptive question from outcomes
        let question = format!("{} vs {}", token_0.outcome, token_1.outcome);

        Some(MarketPrice {
            token_id: condition_id.to_string(),
            yes_price: price_0,
            no_price: price_1,
            yes_token_id: token_0.token_id.clone(),
            no_token_id: token_1.token_id.clone(),
            condition_id: condition_id.to_string(),
            question,
            total_price: price_0 + price_1,
        })
    }

    /// Scan all markets for arbitrage opportunities
    pub async fn scan_for_arbitrage(&mut self, threshold: f64) -> Result<Vec<MarketPrice>> {
        let mut opportunities = Vec::new();

        // Get active markets
        let markets = self.get_active_markets(100).await?;

        for market in markets {
            let condition_id = &market.condition_id;
            if let Some(prices) = self.get_market_prices(condition_id) {
                if prices.total_price < threshold {
                    info!(
                        "Arbitrage opportunity: {}... YES={:.4} NO={:.4} Total={:.4} Spread={:.4}",
                        &prices.question[..prices.question.len().min(50)],
                        prices.yes_price,
                        prices.no_price,
                        prices.total_price,
                        prices.arbitrage_spread()
                    );
                    opportunities.push(prices);
                }
            }
        }

        Ok(opportunities)
    }
}
