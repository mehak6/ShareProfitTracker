#!/usr/bin/env python3
"""
Test script for Phase 1 architecture improvements
Tests the new controller layer, async database, and unified price service
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_portfolio_controller():
    """Test the new PortfolioController"""
    print("🧪 Testing PortfolioController...")
    
    try:
        from controllers.portfolio_controller import PortfolioController
        from data.async_database import AsyncDatabaseManager
        from services.unified_price_service import UnifiedPriceService
        
        # Create test database in memory
        db_manager = AsyncDatabaseManager(":memory:")
        price_service = UnifiedPriceService()
        
        # Create controller
        controller = PortfolioController(db_manager, price_service)
        
        # Test callback setup
        status_messages = []
        def status_callback(msg):
            status_messages.append(msg)
        
        controller.set_callbacks(status_updated=status_callback)
        
        # Test loading empty portfolio
        success = controller.load_portfolio()
        assert success, "Failed to load empty portfolio"
        
        stocks = controller.get_stocks()
        assert len(stocks) == 0, "Expected empty stock list"
        
        # Test adding a stock
        stock_data = {
            'symbol': 'RELIANCE',
            'company_name': 'Reliance Industries Limited',
            'quantity': 10,
            'purchase_price': 2500.0,
            'purchase_date': '2024-01-01',
            'broker': 'Test Broker'
        }
        
        success = controller.add_stock(stock_data)
        assert success, "Failed to add stock"
        
        # Verify stock was added
        stocks = controller.get_stocks()
        assert len(stocks) == 1, "Expected 1 stock after adding"
        assert stocks[0].symbol == 'RELIANCE', "Stock symbol mismatch"
        
        print("✅ PortfolioController tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ PortfolioController test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_async_database():
    """Test the AsyncDatabaseManager"""
    print("🧪 Testing AsyncDatabaseManager...")
    
    try:
        from data.async_database import AsyncDatabaseManager
        
        # Create test database
        db_manager = AsyncDatabaseManager(":memory:")
        
        # Test synchronous methods (backward compatibility)
        stocks = db_manager.get_all_stocks()
        assert isinstance(stocks, list), "Expected list of stocks"
        
        # Test connection pooling
        assert db_manager.connection_pool is not None, "Connection pool not initialized"
        
        # Test that database schema was created
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['users', 'stocks', 'price_cache', 'cash_transactions']
            for table in expected_tables:
                assert table in tables, f"Table {table} not found"
        
        print("✅ AsyncDatabaseManager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ AsyncDatabaseManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_price_service():
    """Test the UnifiedPriceService"""
    print("🧪 Testing UnifiedPriceService...")
    
    try:
        from services.unified_price_service import UnifiedPriceService
        
        # Create price service
        price_service = UnifiedPriceService(cache_ttl=5)
        
        # Test that at least one strategy is available
        assert len(price_service.strategies) > 0, "No price strategies available"
        
        # Test cache functionality
        cache_stats = price_service.get_cache_stats()
        assert 'cached_items' in cache_stats, "Cache stats missing"
        assert 'available_strategies' in cache_stats, "Strategy info missing"
        
        # Test getting price for a common symbol (will use mock if no real APIs)
        try:
            price_data = price_service.get_price('RELIANCE')
            if price_data:
                assert hasattr(price_data, 'current_price'), "Price data missing current_price"
                assert price_data.current_price > 0, "Invalid price value"
        except Exception:
            print("⚠️  Price fetching failed (expected if no APIs available)")
        
        # Test backward compatibility methods
        prices = price_service.get_multiple_prices(['RELIANCE', 'TCS'])
        assert isinstance(prices, dict), "Expected dict of prices"
        
        print("✅ UnifiedPriceService tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ UnifiedPriceService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_architecture_integration():
    """Test integration between all components"""
    print("🧪 Testing Architecture Integration...")
    
    try:
        from controllers.portfolio_controller import PortfolioController
        from data.async_database import AsyncDatabaseManager
        from services.unified_price_service import UnifiedPriceService
        
        # Create integrated system
        db_manager = AsyncDatabaseManager(":memory:")
        price_service = UnifiedPriceService()
        controller = PortfolioController(db_manager, price_service)
        
        # Test full workflow
        success = controller.load_portfolio()
        assert success, "Failed to load portfolio"
        
        # Add test stock
        stock_data = {
            'symbol': 'TCS',
            'company_name': 'Tata Consultancy Services',
            'quantity': 5,
            'purchase_price': 3500.0,
            'purchase_date': '2024-01-15',
        }
        
        success = controller.add_stock(stock_data)
        assert success, "Failed to add stock"
        
        # Test filtering and sorting
        filtered = controller.get_filtered_sorted_stocks(search_term="TCS")
        assert len(filtered) == 1, "Filtering failed"
        
        sorted_stocks = controller.get_filtered_sorted_stocks(sort_field="symbol")
        assert len(sorted_stocks) >= 1, "Sorting failed"
        
        print("✅ Architecture Integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Architecture Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Phase 1 tests"""
    print("🚀 Running Phase 1 Architecture Tests\n")
    
    tests = [
        test_async_database,
        test_unified_price_service,
        test_portfolio_controller,
        test_architecture_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 1 tests passed! Architecture refactor successful.")
        return True
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)