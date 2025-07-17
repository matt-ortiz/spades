#!/usr/bin/env python3
"""Test script for combination bid functionality"""

from scoring import parse_bid, calculate_round_points, format_bid_display

# Mock game configuration
mock_game = {
    'nil_penalty': 100,
    'blind_nil_penalty': 200,
    'bag_penalty_threshold': 10,
    'bag_penalty_points': 100,
    'failed_nil_handling': 'takes_bags'
}

def test_combination_bids():
    """Test combination bid functionality"""
    print("Testing combination bid functionality:")
    
    # Test parsing
    print("\n1. Testing bid parsing:")
    test_cases = [
        ("0n", (0, 'nil')),       # Pure nil
        ("4n", (4, 'combination_nil')),  # Combination: nil + 4
        ("7n", (7, 'combination_nil')),  # Combination: nil + 7
        ("0bn", (0, 'blind_nil')),       # Blind nil
    ]
    
    for bid_string, expected in test_cases:
        result = parse_bid(bid_string)
        print(f"  {bid_string} -> {result} (expected: {expected})")
        assert result == expected, f"Failed for {bid_string}"
    
    print("  ✓ Bid parsing tests passed!")
    
    # Test point calculation
    print("\n2. Testing point calculation:")
    test_cases = [
        # Combination bids (treat as regular bids for team total)
        ("4n", 4, 40),      # Made exactly
        ("4n", 5, 41),      # Made with 1 overtrick
        ("4n", 3, -40),     # Failed by 1
        ("7n", 7, 70),      # Made exactly
        ("7n", 8, 71),      # Made with 1 overtrick
        ("7n", 6, -70),     # Failed by 1
    ]
    
    for bid_string, actual, expected in test_cases:
        result = calculate_round_points(bid_string, actual, mock_game)
        print(f"  Bid: {bid_string}, Actual: {actual} -> {result} points (expected: {expected})")
        assert result == expected, f"Failed for bid {bid_string} with {actual} actual"
    
    print("  ✓ Point calculation tests passed!")
    
    # Test display formatting
    print("\n3. Testing display formatting:")
    test_cases = [
        ("0n", "Nil"),
        ("4n", "Nil + 4"),
        ("7n", "Nil + 7"),
        ("0bn", "Blind Nil"),
    ]
    
    for bid_string, expected in test_cases:
        result = format_bid_display(bid_string)
        print(f"  {bid_string} -> '{result}' (expected: '{expected}')")
        assert result == expected, f"Failed for {bid_string}"
    
    print("  ✓ Display formatting tests passed!")
    
    print("\n🎉 All combination bid tests passed!")

if __name__ == '__main__':
    test_combination_bids()
