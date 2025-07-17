#!/usr/bin/env python3
"""Test script for Spades scoring logic"""

from scoring import parse_bid, calculate_round_points, format_bid_display

# Mock game configuration
mock_game = {
    'nil_penalty': 100,
    'blind_nil_penalty': 200,
    'bag_penalty_threshold': 10,
    'bag_penalty_points': 100,
    'failed_nil_handling': 'takes_bags'
}

def test_parse_bid():
    """Test bid parsing function"""
    print("Testing bid parsing:")
    
    test_cases = [
        ("7", (7, 'regular')),
        ("4b", (4, 'blind')),
        ("0n", (0, 'nil')),
        ("0bn", (0, 'blind_nil')),
        ("13", (13, 'regular')),
        ("1b", (1, 'blind'))
    ]
    
    for bid_string, expected in test_cases:
        result = parse_bid(bid_string)
        print(f"  {bid_string} -> {result} (expected: {expected})")
        assert result == expected, f"Failed for {bid_string}"
    
    print("  ✓ All bid parsing tests passed!\n")

def test_calculate_points():
    """Test point calculation function"""
    print("Testing point calculation:")
    
    test_cases = [
        # Regular bids
        ("7", 7, 70 + 0),  # Made exactly
        ("7", 8, 70 + 1),  # Made with 1 overtrick
        ("7", 6, -70),     # Failed by 1
        ("7", 4, -70),     # Failed by 3
        
        # Nil bids
        ("0n", 0, 100),    # Successful nil
        ("0n", 1, -100),   # Failed nil
        ("0n", 3, -100),   # Failed nil with 3 tricks
        
        # Blind nil bids
        ("0bn", 0, 200),   # Successful blind nil
        ("0bn", 1, -200),  # Failed blind nil
        
        # Blind bids
        ("4b", 4, 40),     # Made exactly
        ("4b", 5, 41),     # Made with 1 overtrick
        ("4b", 3, -40),    # Failed by 1
    ]
    
    for bid_string, actual, expected in test_cases:
        result = calculate_round_points(bid_string, actual, mock_game)
        print(f"  Bid: {bid_string}, Actual: {actual} -> {result} points (expected: {expected})")
        assert result == expected, f"Failed for bid {bid_string} with {actual} actual"
    
    print("  ✓ All point calculation tests passed!\n")

def test_format_display():
    """Test bid display formatting"""
    print("Testing bid display formatting:")
    
    test_cases = [
        ("7", "7"),
        ("4b", "4 (Blind)"),
        ("0n", "Nil"),
        ("0bn", "Blind Nil"),
        ("13", "13"),
    ]
    
    for bid_string, expected in test_cases:
        result = format_bid_display(bid_string)
        print(f"  {bid_string} -> '{result}' (expected: '{expected}')")
        assert result == expected, f"Failed for {bid_string}"
    
    print("  ✓ All display formatting tests passed!\n")

def test_scoring_scenarios():
    """Test various real-world scoring scenarios"""
    print("Testing real-world scenarios:")
    
    scenarios = [
        {
            'name': 'Standard round',
            'team1_bid': '6', 'team1_actual': 7,
            'team2_bid': '7', 'team2_actual': 6,
            'expected_team1': 61, 'expected_team2': -70
        },
        {
            'name': 'Successful nil',
            'team1_bid': '0n', 'team1_actual': 0,
            'team2_bid': '13', 'team2_actual': 13,
            'expected_team1': 100, 'expected_team2': 130
        },
        {
            'name': 'Failed nil with blind bid',
            'team1_bid': '0n', 'team1_actual': 2,
            'team2_bid': '5b', 'team2_actual': 11,
            'expected_team1': -100, 'expected_team2': 56
        },
        {
            'name': 'Both teams make exactly',
            'team1_bid': '7', 'team1_actual': 7,
            'team2_bid': '6', 'team2_actual': 6,
            'expected_team1': 70, 'expected_team2': 60
        }
    ]
    
    for scenario in scenarios:
        team1_points = calculate_round_points(scenario['team1_bid'], scenario['team1_actual'], mock_game)
        team2_points = calculate_round_points(scenario['team2_bid'], scenario['team2_actual'], mock_game)
        
        print(f"  {scenario['name']}:")
        print(f"    Team 1: {scenario['team1_bid']} bid, {scenario['team1_actual']} actual -> {team1_points} points")
        print(f"    Team 2: {scenario['team2_bid']} bid, {scenario['team2_actual']} actual -> {team2_points} points")
        
        assert team1_points == scenario['expected_team1'], f"Team 1 failed: {team1_points} != {scenario['expected_team1']}"
        assert team2_points == scenario['expected_team2'], f"Team 2 failed: {team2_points} != {scenario['expected_team2']}"
    
    print("  ✓ All scenario tests passed!\n")

if __name__ == '__main__':
    print("🃏 Testing Spades Scoring Logic\n")
    
    test_parse_bid()
    test_calculate_points()
    test_format_display()
    test_scoring_scenarios()
    
    print("🎉 All tests passed! The scoring system is working correctly.")