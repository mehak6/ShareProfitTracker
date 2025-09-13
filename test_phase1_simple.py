#!/usr/bin/env python3
"""
Simple test script for Phase 1 architecture improvements
Tests basic functionality without Unicode characters
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all new modules can be imported"""
    print("Testing imports...")
    
    try:
        from controllers.portfolio_controller import PortfolioController
        print("- PortfolioController imported successfully")
        
        from data.async_database import AsyncDatabaseManager
        print("- AsyncDatabaseManager imported successfully")
        
        from services.unified_price_service import UnifiedPriceService
        print("- UnifiedPriceService imported successfully")
        
        from gui.main_window_refactored import MainWindowRefactored
        print("- MainWindowRefactored imported successfully")
        
        return True
        
    except Exception as e:
        print(f"Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        # Test database creation
        from data.async_database import AsyncDatabaseManager
        db_manager = AsyncDatabaseManager(":memory:")
        print("- Database manager created successfully")
        
        # Test price service creation
        from services.unified_price_service import UnifiedPriceService
        price_service = UnifiedPriceService()
        print(f"- Price service created with {len(price_service.strategies)} strategies")
        
        # Test controller creation
        from controllers.portfolio_controller import PortfolioController
        controller = PortfolioController(db_manager, price_service)
        print("- Portfolio controller created successfully")
        
        # Test loading empty portfolio
        success = controller.load_portfolio()
        if success:
            print("- Empty portfolio loaded successfully")
        
        stocks = controller.get_stocks()
        print(f"- Found {len(stocks)} stocks in portfolio")
        
        return True
        
    except Exception as e:
        print(f"Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run simple tests"""
    print("Running Phase 1 Architecture Tests")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_basic_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
            print("PASSED")
        else:
            print("FAILED")
        print("-" * 40)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All Phase 1 tests passed! Architecture refactor successful.")
        return True
    else:
        print("Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)