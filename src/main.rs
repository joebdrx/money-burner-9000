//! Entry point for Polymarket arbitrage bot.

mod arbitrage_detector;
mod bot;
mod config;
mod market_scanner;
mod order_executor;
mod position_manager;

use bot::PolymarketArbitrageBot;
use colored::*;
use config::BotConfig;
use log::info;
use std::io::{self, Write};

fn setup_logging(log_level: &str) {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or(log_level))
        .format(|buf, record| {
            use std::io::Write;
            writeln!(
                buf,
                "{} [{}] {}: {}",
                chrono::Local::now().format("%Y-%m-%d %H:%M:%S"),
                record.level(),
                record.target(),
                record.args()
            )
        })
        .init();
}

#[tokio::main]
async fn main() {
    println!(
        "{}",
        r#"
    ╔══════════════════════════════════════════════════════════╗
    ║         Polymarket Arbitrage Bot                         ║
    ║         Binary Market Price Gap Exploiter                ║
    ╚══════════════════════════════════════════════════════════╝
    "#
    );

    // Load configuration
    println!("Loading configuration...");
    let config = match BotConfig::from_env() {
        Ok(c) => c,
        Err(e) => {
            eprintln!("{} Configuration error: {}", "❌".red(), e);
            eprintln!("\nPlease ensure:");
            eprintln!("1. You have created a .env file (copy from .env.example)");
            eprintln!("2. PRIVATE_KEY is set in .env");
            eprintln!("3. All configuration values are valid");
            std::process::exit(1);
        }
    };

    if let Err(e) = config.validate() {
        eprintln!("{} Configuration validation error: {}", "❌".red(), e);
        std::process::exit(1);
    }

    // Setup logging
    setup_logging(&config.log_level);
    let logger = log::logger();

    // Display configuration
    info!("============================================================");
    info!("BOT CONFIGURATION");
    info!("============================================================");
    info!("Arbitrage Threshold: {}", config.arbitrage_threshold);
    info!("Minimum Profit: ${}", config.min_profit);
    info!("Scan Interval: {}s", config.scan_interval);
    info!("Max Position Size: ${}", config.max_position_size);
    info!("Dry Run Mode: {}", config.dry_run);
    info!("============================================================");

    if config.dry_run {
        println!(
            "{} {}",
            "⚠️".yellow(),
            "DRY RUN MODE ENABLED - No real trades will be executed".yellow()
        );
    } else {
        println!(
            "{} {}",
            "🔴".red(),
            "LIVE TRADING MODE - Real money will be used!".red()
        );
        print!("Are you sure you want to continue? (yes/no): ");
        io::stdout().flush().unwrap();

        let mut response = String::new();
        io::stdin().read_line(&mut response).unwrap();

        if response.trim().to_lowercase() != "yes" {
            println!("Exiting...");
            return;
        }
    }

    // Initialize and run bot
    let mut bot = PolymarketArbitrageBot::new(config);

    match bot.run().await {
        Ok(_) => {
            println!("\n{} Bot finished successfully", "✓".green());
        }
        Err(e) => {
            eprintln!("{} Fatal error: {}", "❌".red(), e);
            std::process::exit(1);
        }
    }
}
