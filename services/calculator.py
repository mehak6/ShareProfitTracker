from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.models import Stock, PortfolioSummary

class PortfolioCalculator:
    @staticmethod
    def calculate_portfolio_summary(stocks: List[Stock]) -> PortfolioSummary:
        if not stocks:
            return PortfolioSummary(
                total_investment=0,
                current_value=0,
                total_profit_loss=0,
                total_profit_loss_percentage=0,
                total_stocks=0
            )
        
        total_investment = sum(stock.total_investment for stock in stocks)
        current_value = sum(stock.current_value for stock in stocks if stock.current_price is not None)
        total_profit_loss = current_value - total_investment
        
        total_profit_loss_percentage = 0
        if total_investment > 0:
            total_profit_loss_percentage = (total_profit_loss / total_investment) * 100
        
        # Find best and worst performers
        valid_stocks = [stock for stock in stocks if stock.current_price is not None]
        best_performer = None
        worst_performer = None
        
        if valid_stocks:
            best_performer = max(valid_stocks, key=lambda s: s.profit_loss_percentage)
            worst_performer = min(valid_stocks, key=lambda s: s.profit_loss_percentage)
        
        return PortfolioSummary(
            total_investment=total_investment,
            current_value=current_value,
            total_profit_loss=total_profit_loss,
            total_profit_loss_percentage=total_profit_loss_percentage,
            best_performer=best_performer,
            worst_performer=worst_performer,
            total_stocks=len(stocks)
        )
    
    @staticmethod
    def format_currency(amount: float) -> str:
        return f"₹{amount:,.2f}"
    
    @staticmethod
    def format_percentage(percentage: float) -> str:
        return f"{percentage:+.2f}%"
    
    @staticmethod
    def get_profit_loss_color(amount: float) -> str:
        if amount > 0:
            return "green"
        elif amount < 0:
            return "red"
        else:
            return "black"