//! Position and PnL tracking for arbitrage trades.

use anyhow::Result;
use chrono::{DateTime, Utc};
use log::{debug, error, info};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Position {
    pub condition_id: String,
    pub question: String,
    pub yes_token_id: String,
    pub no_token_id: String,
    pub position_size: f64,
    pub yes_cost: f64,
    pub no_cost: f64,
    pub total_cost: f64,
    pub expected_profit: f64,
    pub timestamp: DateTime<Utc>,
    pub yes_order_id: Option<String>,
    pub no_order_id: Option<String>,
    pub resolved: bool,
    pub actual_payout: Option<f64>,
    pub actual_profit: Option<f64>,
}

impl Position {
    /// Check if both sides of the position are filled
    pub fn is_complete(&self) -> bool {
        self.yes_order_id.is_some() && self.no_order_id.is_some()
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct PositionStorage {
    active: Vec<Position>,
    closed: Vec<Position>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PortfolioStats {
    pub total_positions: usize,
    pub active_positions: usize,
    pub closed_positions: usize,
    pub total_profit: f64,
    pub win_rate: f64,
    pub avg_profit_per_trade: f64,
    pub total_invested: f64,
}

pub struct PositionManager {
    storage_file: String,
    active_positions: HashMap<String, Position>,
    closed_positions: Vec<Position>,
}

impl PositionManager {
    /// Initialize the position manager
    pub fn new(storage_file: &str) -> Self {
        let mut manager = Self {
            storage_file: storage_file.to_string(),
            active_positions: HashMap::new(),
            closed_positions: Vec::new(),
        };
        manager.load_positions();
        manager
    }

    /// Add a new position
    pub fn add_position(&mut self, position: Position) {
        let question_preview = &position.question[..position.question.len().min(50)];
        info!("Added position: {}...", question_preview);
        self.active_positions
            .insert(position.condition_id.clone(), position);
        self.save_positions();
    }

    /// Update an existing position
    pub fn update_position(&mut self, condition_id: &str, update_fn: impl FnOnce(&mut Position)) {
        if let Some(position) = self.active_positions.get_mut(condition_id) {
            update_fn(position);
            self.save_positions();
            debug!("Updated position {}", condition_id);
        }
    }

    /// Close a position and calculate actual profit
    pub fn close_position(&mut self, condition_id: &str, actual_payout: f64) {
        if let Some(mut position) = self.active_positions.remove(condition_id) {
            position.resolved = true;
            position.actual_payout = Some(actual_payout);
            position.actual_profit = Some(actual_payout - position.total_cost);

            let question_preview = &position.question[..position.question.len().min(50)];
            info!(
                "Closed position: {}... | Profit: ${:.4}",
                question_preview,
                position.actual_profit.unwrap_or(0.0)
            );

            self.closed_positions.push(position);
            self.save_positions();
        }
    }

    /// Get portfolio statistics
    pub fn get_stats(&self) -> PortfolioStats {
        let total_positions = self.active_positions.len() + self.closed_positions.len();

        if self.closed_positions.is_empty() {
            let total_invested: f64 = self.active_positions.values().map(|p| p.total_cost).sum();

            return PortfolioStats {
                total_positions,
                active_positions: self.active_positions.len(),
                closed_positions: 0,
                total_profit: 0.0,
                win_rate: 0.0,
                avg_profit_per_trade: 0.0,
                total_invested,
            };
        }

        let total_profit: f64 = self
            .closed_positions
            .iter()
            .filter_map(|p| p.actual_profit)
            .sum();

        let wins = self
            .closed_positions
            .iter()
            .filter(|p| p.actual_profit.map_or(false, |profit| profit > 0.0))
            .count();

        let win_rate = if !self.closed_positions.is_empty() {
            (wins as f64 / self.closed_positions.len() as f64) * 100.0
        } else {
            0.0
        };

        let avg_profit = if !self.closed_positions.is_empty() {
            total_profit / self.closed_positions.len() as f64
        } else {
            0.0
        };

        let total_invested: f64 = self.active_positions.values().map(|p| p.total_cost).sum();

        PortfolioStats {
            total_positions,
            active_positions: self.active_positions.len(),
            closed_positions: self.closed_positions.len(),
            total_profit,
            win_rate,
            avg_profit_per_trade: avg_profit,
            total_invested,
        }
    }

    /// Print portfolio statistics to logger
    pub fn print_stats(&self) {
        let stats = self.get_stats();

        info!("============================================================");
        info!("PORTFOLIO STATISTICS");
        info!("============================================================");
        info!("Total Positions: {}", stats.total_positions);
        info!("Active Positions: {}", stats.active_positions);
        info!("Closed Positions: {}", stats.closed_positions);
        info!("Total Profit: ${:.2}", stats.total_profit);
        info!("Win Rate: {:.2}%", stats.win_rate);
        info!("Avg Profit/Trade: ${:.4}", stats.avg_profit_per_trade);
        info!("Total Invested: ${:.2}", stats.total_invested);
        info!("============================================================");
    }

    /// Save positions to file
    fn save_positions(&self) {
        let storage = PositionStorage {
            active: self.active_positions.values().cloned().collect(),
            closed: self.closed_positions.clone(),
        };

        match serde_json::to_string_pretty(&storage) {
            Ok(json) => {
                if let Err(e) = fs::write(&self.storage_file, json) {
                    error!("Error saving positions: {}", e);
                }
            }
            Err(e) => error!("Error serializing positions: {}", e),
        }
    }

    /// Load positions from file
    fn load_positions(&mut self) {
        match fs::read_to_string(&self.storage_file) {
            Ok(content) => match serde_json::from_str::<PositionStorage>(&content) {
                Ok(storage) => {
                    for position in storage.active {
                        self.active_positions
                            .insert(position.condition_id.clone(), position);
                    }
                    self.closed_positions = storage.closed;
                    info!("Loaded {} active positions", self.active_positions.len());
                }
                Err(e) => error!("Error deserializing positions: {}", e),
            },
            Err(e) => {
                if e.kind() == std::io::ErrorKind::NotFound {
                    info!("No existing positions file found");
                } else {
                    error!("Error loading positions: {}", e);
                }
            }
        }
    }
}
