#!/usr/bin/env python3
"""
Test script to demonstrate ultra-fast price refresh performance
"""

import sys
import os
import time

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from services.unified_price_service import (
    get_detailed_price_data_ultra_fast,
    get_multiple_prices,
    get_global_price_service,
)

def test_price_refresh_performance():
    # Test symbols (mix of Indian and US stocks)
    test_symbols = [
        'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
        'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'
    ]
    
    print("Ultra-Fast Price Refresh Performance Test")
    print("=" * 50)
    print(f"Testing with {len(test_symbols)} symbols:")
    for symbol in test_symbols:
        print(f"  - {symbol}")
    print()
    
    # Clear cache for fair comparison
    get_global_price_service().clear_cache()
    
    # Test 1: Ultra-fast fetcher (first run - no cache)
    print("1. Ultra-Fast Fetcher (Cold Cache):")
    start_time = time.time()
    ultra_results = get_detailed_price_data_ultra_fast(test_symbols)
    ultra_time_cold = time.time() - start_time
    
    print(f"   Time: {ultra_time_cold:.2f}s")
    print(f"   Success: {len(ultra_results)}/{len(test_symbols)}")
    print(f"   Cache Stats: {get_global_price_service().get_cache_stats()}")
    
    # Test 2: Ultra-fast fetcher (second run - with cache)
    print("\n2. Ultra-Fast Fetcher (Hot Cache):")
    start_time = time.time()
    ultra_results_cached = get_detailed_price_data_ultra_fast(test_symbols)
    ultra_time_hot = time.time() - start_time
    
    print(f"   Time: {ultra_time_hot:.2f}s")
    print(f"   Success: {len(ultra_results_cached)}/{len(test_symbols)}")
    print(f"   Cache Stats: {get_global_price_service().get_cache_stats()}")
    
    # Test 3: Original enhanced fetcher for comparison
    print("\n3. Original Enhanced Fetcher:")
    start_time = time.time()
    enhanced_results = get_multiple_prices(test_symbols)
    enhanced_time = time.time() - start_time
    
    print(f"   Time: {enhanced_time:.2f}s")
    print(f"   Success: {len(enhanced_results)}/{len(test_symbols)}")
    
    # Performance comparison
    print("\nPerformance Comparison:")
    print("=" * 50)
    speedup_cold = enhanced_time / ultra_time_cold if ultra_time_cold > 0 else 0
    speedup_hot = enhanced_time / ultra_time_hot if ultra_time_hot > 0 else 0
    
    print(f"Ultra-Fast (Cold): {ultra_time_cold:.2f}s - {speedup_cold:.1f}x faster")
    print(f"Ultra-Fast (Hot):  {ultra_time_hot:.2f}s - {speedup_hot:.1f}x faster")
    print(f"Enhanced Original: {enhanced_time:.2f}s - baseline")
    
    cache_speedup = ultra_time_cold / ultra_time_hot if ultra_time_hot > 0 else 0
    print(f"Cache Speedup: {cache_speedup:.1f}x faster with cache")
    
    # Show sample results
    print("\nSample Price Results:")
    print("-" * 30)
    for symbol in test_symbols[:3]:  # Show first 3
        if symbol in ultra_results:
            data = ultra_results[symbol]
            price = data.get('current_price', 'N/A')
            source = data.get('source', 'unknown')
            print(f"{symbol:12} ₹{price:8.2f} ({source})")
    
    print("\nOptimization Features Active:")
    print("  - Concurrent batch processing")
    print("  - Smart caching with TTL")
    print("  - Connection pooling")
    print("  - Optimized timeout handling")
    print("  - Fast API selection")

if __name__ == "__main__":
    test_price_refresh_performance()
