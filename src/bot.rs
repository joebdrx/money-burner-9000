//! Main arbitrage bot orchestration.

use crate::arbitrage_detector::{ArbitrageDetector, ArbitrageOpportunity};
use crate::config::BotConfig;
use crate::market_scanner::MarketScanner;
use crate::order_executor::OrderExecutor;
use crate::position_manager::{Position, PositionManager};
use anyhow::Result;
use chrono::Utc;
use log::{error, info, warn};
use tokio::time::{sleep, Duration};

pub struct PolymarketArbitrageBot {
    config: BotConfig,
    scanner: MarketScanner,
    detector: ArbitrageDetector,
    executor: OrderExecutor,
    position_manager: PositionManager,
    running: bool,
}

impl PolymarketArbitrageBot {
    /// Initialize the arbitrage bot
    pub fn new(config: BotConfig) -> Self {
        info!("Initializing Polymarket client...");

        let base_url = "https://clob.polymarket.com";

        // Initialize components
        let scanner = MarketScanner::new(base_url);
        let detector = ArbitrageDetector::new(
            config.arbitrage_threshold,
            config.min_profit,
            config.max_position_size,
        );
        let executor = OrderExecutor::new(base_url, config.dry_run);
        let position_manager = PositionManager::new("positions.json");

        info!("Bot initialized (DRY RUN: {})", config.dry_run);

        Self {
            config,
            scanner,
            detector,
            executor,
            position_manager,
            running: false,
        }
    }

    /// Perform a single scan for arbitrage opportunities
    pub async fn scan_once(&mut self) -> Result<Vec<ArbitrageOpportunity>> {
        info!("Scanning markets for arbitrage opportunities...");

        // Scan markets for price gaps
        let market_prices = self
            .scanner
            .scan_for_arbitrage(self.config.arbitrage_threshold)
            .await?;

        // Validate and filter opportunities
        let opportunities = self.detector.filter_opportunities(market_prices);

        info!("Found {} valid opportunities", opportunities.len());
        Ok(opportunities)
    }

    /// Execute a single arbitrage opportunity
    pub async fn execute_opportunity(&mut self, opportunity: &ArbitrageOpportunity) -> bool {
        info!("Executing: {}", opportunity);

        // Execute the trade
        let result = match self.executor.execute_arbitrage(opportunity).await {
            Ok(r) => r,
            Err(e) => {
                error!("Error executing arbitrage: {}", e);
                return false;
            }
        };

        if result.success && result.both_filled() {
            // Create position
            let position = Position {
                condition_id: opportunity.market_price.condition_id.clone(),
                question: opportunity.market_price.question.clone(),
                yes_token_id: opportunity.market_price.yes_token_id.clone(),
                no_token_id: opportunity.market_price.no_token_id.clone(),
                position_size: opportunity.position_size,
                yes_cost: opportunity.yes_cost,
                no_cost: opportunity.no_cost,
                total_cost: opportunity.total_cost,
                expected_profit: opportunity.expected_profit,
                timestamp: Utc::now(),
                yes_order_id: result.yes_order_id,
                no_order_id: result.no_order_id,
                resolved: false,
                actual_payout: None,
                actual_profit: None,
            };

            // Track position
            self.position_manager.add_position(position);

            info!("Position created successfully");
            true
        } else {
            warn!(
                "Execution failed: {}",
                result.error.unwrap_or_else(|| "Unknown error".to_string())
            );
            false
        }
    }

    /// Run the bot in continuous mode
    pub async fn run(&mut self) -> Result<()> {
        self.running = true;
        info!("Starting arbitrage bot...");

        let mut scan_count = 0;

        while self.running {
            scan_count += 1;
            info!("Scan #{}", scan_count);

            // Find opportunities
            let opportunities = match self.scan_once().await {
                Ok(opps) => opps,
                Err(e) => {
                    error!("Error scanning markets: {}", e);
                    Vec::new()
                }
            };

            // Execute opportunities
            for opportunity in opportunities {
                if let Err(e) = self.try_execute_opportunity(&opportunity).await {
                    error!("Error executing opportunity: {}", e);
                }

                // Small delay between executions
                sleep(Duration::from_secs(1)).await;
            }

            // Print stats periodically
            if scan_count % 10 == 0 {
                self.position_manager.print_stats();
            }

            // Wait before next scan
            info!(
                "Waiting {}s until next scan...",
                self.config.scan_interval
            );
            sleep(Duration::from_secs(self.config.scan_interval)).await;
        }

        Ok(())
    }

    /// Try to execute an opportunity, catching errors
    async fn try_execute_opportunity(&mut self, opportunity: &ArbitrageOpportunity) -> Result<()> {
        self.execute_opportunity(opportunity).await;
        Ok(())
    }

    /// Stop the bot
    pub fn stop(&mut self) {
        self.running = false;
        self.position_manager.print_stats();
        info!("Bot stopped");
    }
}
