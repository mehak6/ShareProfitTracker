from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Stock:
    symbol: str
    company_name: str
    quantity: float
    purchase_price: float
    purchase_date: str
    broker: str = ""
    cash_invested: float = 0
    id: Optional[int] = None
    current_price: Optional[float] = None
    last_updated: Optional[str] = None
    created_at: Optional[str] = None
    
    def __post_init__(self):
        # If cash_invested is 0 or not provided, calculate it from quantity * price
        if self.cash_invested == 0:
            self.cash_invested = self.quantity * self.purchase_price
    
    @property
    def total_investment(self) -> float:
        return self.quantity * self.purchase_price
    
    @property
    def actual_cash_invested(self) -> float:
        """Returns the actual cash invested (different from calculated investment)"""
        return self.cash_invested
    
    @property
    def current_value(self) -> float:
        if self.current_price is None:
            return 0
        return self.quantity * self.current_price
    
    @property
    def profit_loss_amount(self) -> float:
        return self.current_value - self.total_investment
    
    @property
    def profit_loss_percentage(self) -> float:
        if self.total_investment == 0:
            return 0
        return (self.profit_loss_amount / self.total_investment) * 100
    
    @property
    def days_held(self) -> int:
        try:
            purchase_dt = datetime.strptime(self.purchase_date, "%Y-%m-%d")
            return (datetime.now() - purchase_dt).days
        except:
            return 0
    
    @property
    def annualized_return(self) -> float:
        days = self.days_held
        if days == 0:
            return 0
        return (self.profit_loss_percentage / days) * 365

@dataclass
class PortfolioSummary:
    total_investment: float
    current_value: float
    total_profit_loss: float
    total_profit_loss_percentage: float
    best_performer: Optional[Stock] = None
    worst_performer: Optional[Stock] = None
    total_stocks: int = 0