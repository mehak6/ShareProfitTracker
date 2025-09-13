"""
Stock symbol database with popular Indian and international stocks
"""

# Indian Stock Symbols (NSE format with .NS suffix for yfinance)
INDIAN_STOCKS = {
    "RELIANCE.NS": "Reliance Industries Limited",
    "TCS.NS": "Tata Consultancy Services Limited",
    "HDFCBANK.NS": "HDFC Bank Limited",
    "INFY.NS": "Infosys Limited",
    "HINDUNILVR.NS": "Hindustan Unilever Limited",
    "ICICIBANK.NS": "ICICI Bank Limited",
    "HDFC.NS": "Housing Development Finance Corporation Limited",
    "SBIN.NS": "State Bank of India",
    "BHARTIARTL.NS": "Bharti Airtel Limited",
    "ITC.NS": "ITC Limited",
    "ASIANPAINT.NS": "Asian Paints Limited",
    "KOTAKBANK.NS": "Kotak Mahindra Bank Limited",
    "LT.NS": "Larsen & Toubro Limited",
    "AXISBANK.NS": "Axis Bank Limited",
    "MARUTI.NS": "Maruti Suzuki India Limited",
    "HCLTECH.NS": "HCL Technologies Limited",
    "WIPRO.NS": "Wipro Limited",
    "ULTRACEMCO.NS": "UltraTech Cement Limited",
    "TITAN.NS": "Titan Company Limited",
    "SUNPHARMA.NS": "Sun Pharmaceutical Industries Limited",
    "POWERGRID.NS": "Power Grid Corporation of India Limited",
    "NESTLEIND.NS": "Nestle India Limited",
    "ADANIPORTS.NS": "Adani Ports and Special Economic Zone Limited",
    "NTPC.NS": "NTPC Limited",
    "TECHM.NS": "Tech Mahindra Limited",
    "ONGC.NS": "Oil and Natural Gas Corporation Limited",
    "JSWSTEEL.NS": "JSW Steel Limited",
    "TATAMOTORS.NS": "Tata Motors Limited",
    "COALINDIA.NS": "Coal India Limited",
    "DIVISLAB.NS": "Divi's Laboratories Limited",
    "BAJFINANCE.NS": "Bajaj Finance Limited",
    "DRREDDY.NS": "Dr. Reddy's Laboratories Limited",
    "GRASIM.NS": "Grasim Industries Limited",
    "TATASTEEL.NS": "Tata Steel Limited",
    "EICHERMOT.NS": "Eicher Motors Limited",
    "HEROMOTOCO.NS": "Hero MotoCorp Limited",
    "CIPLA.NS": "Cipla Limited",
    "BRITANNIA.NS": "Britannia Industries Limited",
    "HINDALCO.NS": "Hindalco Industries Limited",
    "BPCL.NS": "Bharat Petroleum Corporation Limited",
    "SHREECEM.NS": "Shree Cement Limited",
    "BAJAJ-AUTO.NS": "Bajaj Auto Limited",
    "IOC.NS": "Indian Oil Corporation Limited",
    "INDUSINDBK.NS": "IndusInd Bank Limited",
    "ADANIENT.NS": "Adani Enterprises Limited",
    "TATACONSUM.NS": "Tata Consumer Products Limited",
    "GODREJCP.NS": "Godrej Consumer Products Limited",
    "SBILIFE.NS": "SBI Life Insurance Company Limited",
}

# Popular US Stocks (for international investors)
US_STOCKS = {
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc. (Google)",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "NVDA": "NVIDIA Corporation",
    "META": "Meta Platforms Inc. (Facebook)",
    "NFLX": "Netflix Inc.",
    "ORCL": "Oracle Corporation",
    "CRM": "Salesforce Inc.",
    "ADBE": "Adobe Inc.",
    "PYPL": "PayPal Holdings Inc.",
    "INTC": "Intel Corporation",
    "CSCO": "Cisco Systems Inc.",
    "PEP": "PepsiCo Inc.",
    "KO": "The Coca-Cola Company",
    "DIS": "The Walt Disney Company",
    "BA": "The Boeing Company",
    "JNJ": "Johnson & Johnson",
    "V": "Visa Inc.",
}

# Combined database for easy searching
ALL_STOCKS = {**INDIAN_STOCKS, **US_STOCKS}

def search_stocks(query: str, limit: int = 10):
    """
    Search for stocks by symbol or company name
    Returns list of (symbol, company_name) tuples
    """
    query = query.upper()
    matches = []
    
    # First, exact symbol matches
    for symbol, company in ALL_STOCKS.items():
        if symbol.upper().startswith(query):
            matches.append((symbol, company))
    
    # Then, company name matches
    for symbol, company in ALL_STOCKS.items():
        if query in company.upper() and (symbol, company) not in matches:
            matches.append((symbol, company))
    
    return matches[:limit]

def get_popular_indian_stocks(limit: int = 20):
    """Get list of popular Indian stocks for suggestions"""
    popular = list(INDIAN_STOCKS.items())[:limit]
    return popular

def get_company_name(symbol: str) -> str:
    """Get company name for a given symbol"""
    return ALL_STOCKS.get(symbol.upper(), symbol)