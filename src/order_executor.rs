//! Order execution for arbitrage trades.

use crate::arbitrage_detector::ArbitrageOpportunity;
use anyhow::Result;
use log::{error, info};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionResult {
    pub success: bool,
    pub yes_order_id: Option<String>,
    pub no_order_id: Option<String>,
    pub yes_filled: bool,
    pub no_filled: bool,
    pub error: Option<String>,
}

impl ExecutionResult {
    /// Check if both YES and NO orders were filled
    pub fn both_filled(&self) -> bool {
        self.yes_filled && self.no_filled
    }
}

pub struct OrderExecutor {
    client: reqwest::Client,
    base_url: String,
    dry_run: bool,
}

impl OrderExecutor {
    /// Initialize the order executor
    pub fn new(base_url: &str, dry_run: bool) -> Self {
        Self {
            client: reqwest::Client::new(),
            base_url: base_url.to_string(),
            dry_run,
        }
    }

    /// Execute an arbitrage trade by buying both YES and NO
    pub async fn execute_arbitrage(
        &self,
        opportunity: &ArbitrageOpportunity,
    ) -> Result<ExecutionResult> {
        if self.dry_run {
            info!("[DRY RUN] Would execute: {}", opportunity);
            return Ok(ExecutionResult {
                success: true,
                yes_order_id: Some("dry_run_yes".to_string()),
                no_order_id: Some("dry_run_no".to_string()),
                yes_filled: true,
                no_filled: true,
                error: None,
            });
        }

        // Execute both orders simultaneously
        let yes_result = self
            .place_market_order(
                &opportunity.market_price.yes_token_id,
                opportunity.position_size,
                "YES",
            )
            .await;

        let no_result = self
            .place_market_order(
                &opportunity.market_price.no_token_id,
                opportunity.position_size,
                "NO",
            )
            .await;

        // Check if both orders succeeded
        let success = yes_result.0 && no_result.0;

        if !success {
            let mut error_msgs = Vec::new();
            if !yes_result.0 {
                error_msgs.push(format!("YES order failed: {}", yes_result.2));
            }
            if !no_result.0 {
                error_msgs.push(format!("NO order failed: {}", no_result.2));
            }

            let error_msg = error_msgs.join(" | ");
            error!("Execution failed: {}", error_msg);

            // TODO: Implement rollback logic if only one side filled

            return Ok(ExecutionResult {
                success: false,
                yes_order_id: yes_result.1,
                no_order_id: no_result.1,
                yes_filled: yes_result.0,
                no_filled: no_result.0,
                error: Some(error_msg),
            });
        }

        info!(
            "Arbitrage executed successfully! YES order: {:?}, NO order: {:?}",
            yes_result.1, no_result.1
        );

        Ok(ExecutionResult {
            success: true,
            yes_order_id: yes_result.1,
            no_order_id: no_result.1,
            yes_filled: true,
            no_filled: true,
            error: None,
        })
    }

    /// Place a market order for a token
    async fn place_market_order(
        &self,
        token_id: &str,
        amount: f64,
        side: &str,
    ) -> (bool, Option<String>, String) {
        // In a real implementation, this would interact with the Polymarket API
        // For now, we'll return a mock response
        info!("{} order placed for token {} (amount: {})", side, token_id, amount);
        (
            true,
            Some(format!("order_{}_{}", side.to_lowercase(), token_id)),
            String::new(),
        )
    }
}
