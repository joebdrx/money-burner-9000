//! Arbitrage opportunity detection and validation.

use crate::market_scanner::MarketPrice;
use log::{debug, info};
use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArbitrageOpportunity {
    pub market_price: MarketPrice,
    pub expected_profit: f64,
    pub expected_profit_pct: f64,
    pub position_size: f64,
    pub yes_cost: f64,
    pub no_cost: f64,
    pub total_cost: f64,
}

impl fmt::Display for ArbitrageOpportunity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Arbitrage: {}... | Profit: ${:.4} ({:.2}%) | Cost: ${:.2}",
            &self.market_price.question[..self.market_price.question.len().min(40)],
            self.expected_profit,
            self.expected_profit_pct,
            self.total_cost
        )
    }
}

pub struct ArbitrageDetector {
    /// Maximum acceptable total price (YES + NO)
    threshold: f64,

    /// Minimum profit in dollars to execute
    min_profit: f64,

    /// Maximum position size in dollars
    max_position_size: f64,
}

impl ArbitrageDetector {
    /// Initialize the arbitrage detector
    pub fn new(threshold: f64, min_profit: f64, max_position_size: f64) -> Self {
        Self {
            threshold,
            min_profit,
            max_position_size,
        }
    }

    /// Validate if a market price represents a profitable arbitrage
    pub fn validate_opportunity(
        &self,
        market_price: &MarketPrice,
    ) -> Option<ArbitrageOpportunity> {
        // Check if total price is below threshold
        if market_price.total_price >= self.threshold {
            return None;
        }

        // Calculate expected profit per $1 position
        let _spread = market_price.arbitrage_spread();

        // Determine optimal position size (limited by max_position_size)
        let position_size = self.max_position_size.min(self.max_position_size);

        // Calculate costs for buying both sides
        let yes_cost = market_price.yes_price * position_size;
        let no_cost = market_price.no_price * position_size;
        let total_cost = yes_cost + no_cost;

        // Expected payout is $1.00 per share
        let expected_payout = position_size * 1.0;

        // Expected profit
        let expected_profit = expected_payout - total_cost;
        let expected_profit_pct = (expected_profit / total_cost) * 100.0;

        // Check if profit meets minimum threshold
        if expected_profit < self.min_profit {
            debug!(
                "Profit ${:.4} below minimum ${}",
                expected_profit, self.min_profit
            );
            return None;
        }

        let opportunity = ArbitrageOpportunity {
            market_price: market_price.clone(),
            expected_profit,
            expected_profit_pct,
            position_size,
            yes_cost,
            no_cost,
            total_cost,
        };

        info!("Valid opportunity: {}", opportunity);
        Some(opportunity)
    }

    /// Filter and validate a list of market prices for arbitrage
    pub fn filter_opportunities(
        &self,
        market_prices: Vec<MarketPrice>,
    ) -> Vec<ArbitrageOpportunity> {
        let mut opportunities: Vec<ArbitrageOpportunity> = market_prices
            .iter()
            .filter_map(|price| self.validate_opportunity(price))
            .collect();

        // Sort by expected profit (highest first)
        opportunities.sort_by(|a, b| {
            b.expected_profit
                .partial_cmp(&a.expected_profit)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        info!("Found {} valid arbitrage opportunities", opportunities.len());
        opportunities
    }
}
