def parse_bid(bid_string):
    """Parse bid string format: '7', '4b', '0n', '0bn', '4n' (combination)"""
    if bid_string.endswith('bn'):
        bid_value = int(bid_string[:-2])
        if bid_value == 0:
            return 0, 'blind_nil'
        else:
            return bid_value, 'combination_blind_nil'
    elif bid_string.endswith('b'):
        return int(bid_string[:-1]), 'blind'  
    elif bid_string.endswith('n'):
        bid_value = int(bid_string[:-1])
        if bid_value == 0:
            return 0, 'nil'
        else:
            return bid_value, 'combination_nil'
    else:
        return int(bid_string), 'regular'

def calculate_round_points_with_flags(bid_string, actual_tricks, game, nil_success=False, blind_nil_success=False, blind_success=False):
    """Calculate points for a round with explicit success/failure flags for special bids"""
    bid_value, bid_type = parse_bid(bid_string)
    
    if bid_type == 'nil':
        # Pure nil bid
        return game['nil_penalty'] if actual_tricks == 0 else -game['nil_penalty']
    
    elif bid_type == 'combination_nil':
        # Combination nil bid (e.g., "4n" = one player nil, other bids 4)
        base_points = 0
        if actual_tricks >= bid_value:
            base_points = (bid_value * 10) + (actual_tricks - bid_value)
        else:
            base_points = -(bid_value * 10)
        
        # Add nil bonus/penalty based on success flag
        nil_bonus = game['nil_penalty'] if nil_success else -game['nil_penalty']
        return base_points + nil_bonus
    
    elif bid_type == 'combination_blind_nil':
        # Combination blind nil bid (e.g., "4bn" = one player blind nil, other bids 4)
        base_points = 0
        if actual_tricks >= bid_value:
            base_points = (bid_value * 10) + (actual_tricks - bid_value)
        else:
            base_points = -(bid_value * 10)
        
        # Add blind nil bonus/penalty based on success flag
        blind_nil_bonus = game['blind_nil_penalty'] if blind_nil_success else -game['blind_nil_penalty']
        return base_points + blind_nil_bonus
    
    elif bid_type == 'blind_nil':
        # Pure blind nil bid
        return game['blind_nil_penalty'] if actual_tricks == 0 else -game['blind_nil_penalty']
    
    elif bid_type == 'blind':
        # Blind bid (doubled points/penalties)
        if blind_success:
            # Successful blind bid: doubled points + overtricks
            return (bid_value * 10 * 2) + (actual_tricks - bid_value)
        else:
            # Failed blind bid: doubled penalty
            return -(bid_value * 10 * 2)
    
    else:  # 'regular'
        # Standard bid
        if actual_tricks >= bid_value:
            return (bid_value * 10) + (actual_tricks - bid_value)
        else:
            return -(bid_value * 10)

def calculate_round_points(bid_string, actual_tricks, game):
    """Calculate points for a round based on bid and actual tricks"""
    bid_value, bid_type = parse_bid(bid_string)
    
    if bid_type == 'nil':
        # Nil bid
        if actual_tricks == 0:
            return game['nil_penalty']  # Successful nil
        else:
            # Failed nil - handle based on game configuration
            base_penalty = -game['nil_penalty']
            
            if game['failed_nil_handling'] == 'takes_bags':
                # Failed nil tricks count as bags (handled in main logic)
                return base_penalty
            elif game['failed_nil_handling'] == 'helps_team':
                # Failed nil tricks help partner (handled in main logic)
                return base_penalty
            else:  # 'no_effect'
                # Failed nil tricks ignored
                return base_penalty
    
    elif bid_type == 'combination_nil':
        # Combination bid (e.g., "4n" = one player bids nil, other bids 4)
        # Score as regular bid + nil bonus if successful
        base_points = 0
        if actual_tricks >= bid_value:
            base_points = (bid_value * 10) + (actual_tricks - bid_value)
        else:
            base_points = -(bid_value * 10)
        
        # Add nil bonus (assuming nil player took 0 tricks)
        # This is simplified - in reality you'd need to track individual player performance
        nil_bonus = game['nil_penalty']
        return base_points + nil_bonus
    
    elif bid_type == 'combination_blind_nil':
        # Combination blind nil bid (e.g., "4bn" = one player bids blind nil, other bids 4)
        # Score as regular bid + blind nil bonus if successful
        base_points = 0
        if actual_tricks >= bid_value:
            base_points = (bid_value * 10) + (actual_tricks - bid_value)
        else:
            base_points = -(bid_value * 10)
        
        # Add blind nil bonus (assuming blind nil player took 0 tricks)
        # This is simplified - in reality you'd need to track individual player performance
        blind_nil_bonus = game['blind_nil_penalty']
        return base_points + blind_nil_bonus
    
    elif bid_type == 'blind_nil':
        # Blind nil bid
        if actual_tricks == 0:
            return game['blind_nil_penalty']  # Successful blind nil
        else:
            # Failed blind nil - same handling as regular nil
            base_penalty = -game['blind_nil_penalty']
            
            if game['failed_nil_handling'] == 'takes_bags':
                return base_penalty
            elif game['failed_nil_handling'] == 'helps_team':
                return base_penalty
            else:  # 'no_effect'
                return base_penalty
    
    elif bid_type == 'blind':
        # Blind bid (not nil) - doubled points/penalties
        if actual_tricks >= bid_value:
            return (bid_value * 10 * 2) + (actual_tricks - bid_value)
        else:
            return -(bid_value * 10 * 2)
    
    else:  # 'regular'
        # Standard bid
        if actual_tricks >= bid_value:
            return (bid_value * 10) + (actual_tricks - bid_value)
        else:
            return -(bid_value * 10)

def calculate_bags_earned(bid_string, actual_tricks, game):
    """Calculate bags earned this round"""
    bid_value, bid_type = parse_bid(bid_string)
    
    if bid_type in ['nil', 'blind_nil']:
        if actual_tricks == 0:
            return 0  # Successful nil/blind nil
        else:
            # Failed nil/blind nil
            if game['failed_nil_handling'] == 'takes_bags':
                return actual_tricks
            elif game['failed_nil_handling'] == 'helps_team':
                return 0  # Tricks help partner, don't count as bags
            else:  # 'no_effect'
                return 0  # Tricks ignored
    
    elif bid_type == 'combination_nil':
        # Combination bid - bags are calculated like regular bids
        return max(0, actual_tricks - bid_value)
    
    elif bid_type == 'combination_blind_nil':
        # Combination blind nil bid - bags are calculated like regular bids
        return max(0, actual_tricks - bid_value)
    
    else:
        # Regular or blind bid
        return max(0, actual_tricks - bid_value)

def format_bid_display(bid_string):
    """Format bid string for display"""
    bid_value, bid_type = parse_bid(bid_string)
    
    if bid_type == 'nil':
        return "Nil"
    elif bid_type == 'combination_nil':
        return f"{bid_value} nil"
    elif bid_type == 'combination_blind_nil':
        return f"{bid_value} blind nil"
    elif bid_type == 'blind_nil':
        return "Blind Nil"
    elif bid_type == 'blind':
        return f"Blind {bid_value}"
    else:
        return str(bid_value)

def format_made_display(bid_string, actual_tricks, nil_success=None, blind_nil_success=None, blind_success=None):
    """Format the 'made' display for round history"""
    bid_value, bid_type = parse_bid(bid_string)
    
    if bid_type == 'nil':
        return f"{actual_tricks} {'✓' if actual_tricks == 0 else '✗'}"
    elif bid_type == 'combination_nil':
        # Show like "6 nil+2" for 4 nil bid with 6 actual (nil success + 2 partner tricks)
        if nil_success is not None:
            if nil_success:
                partner_tricks = actual_tricks
                return f"{actual_tricks} nil ✓+{partner_tricks}"
            else:
                return f"{actual_tricks} nil ✗"
        else:
            # Fallback if success info not available
            return f"{actual_tricks}"
    elif bid_type == 'combination_blind_nil':
        if blind_nil_success is not None:
            if blind_nil_success:
                partner_tricks = actual_tricks
                return f"{actual_tricks} blind nil ✓+{partner_tricks}"
            else:
                return f"{actual_tricks} blind nil ✗"
        else:
            return f"{actual_tricks}"
    elif bid_type == 'blind_nil':
        return f"{actual_tricks} {'✓' if actual_tricks == 0 else '✗'}"
    elif bid_type == 'blind':
        if blind_success is not None:
            return f"{actual_tricks} {'✓' if blind_success else '✗'}"
        else:
            return f"{actual_tricks}"
    else:
        return str(actual_tricks)

def get_score_breakdown_detailed(round_data):
    """Get detailed score breakdown from stored database values"""
    breakdown = []
    
    # Always show base bid (even if 0)
    bid_points = round_data.get('bid_points', 0)
    breakdown.append({
        'label': 'Base bid',
        'value': f'{bid_points:+d}' if bid_points != 0 else '0',
        'color': 'text-green-600' if bid_points > 0 else 'text-red-600' if bid_points < 0 else 'text-gray-600'
    })
    
    # Add nil bonus if non-zero
    if round_data.get('nil_bonus', 0) != 0:
        nil_bonus = round_data['nil_bonus']
        breakdown.append({
            'label': 'Nil bonus' if nil_bonus > 0 else 'Nil penalty',
            'value': f'{nil_bonus:+d}',
            'color': 'text-green-600' if nil_bonus > 0 else 'text-red-600'
        })
    
    # Add blind nil bonus if non-zero
    if round_data.get('blind_nil_bonus', 0) != 0:
        blind_nil_bonus = round_data['blind_nil_bonus']
        breakdown.append({
            'label': 'Blind nil bonus' if blind_nil_bonus > 0 else 'Blind nil penalty',
            'value': f'{blind_nil_bonus:+d}',
            'color': 'text-green-600' if blind_nil_bonus > 0 else 'text-red-600'
        })
    
    # Add blind bonus with 2x notation
    if round_data.get('blind_bonus', 0) != 0:
        blind_bonus = round_data['blind_bonus']
        base_amount = abs(blind_bonus) // 2
        breakdown.append({
            'label': 'Blind bonus (2x)',
            'value': f'{blind_bonus:+d}',
            'color': 'text-green-600' if blind_bonus > 0 else 'text-red-600'
        })
    
    # Add bag points if non-zero
    if round_data.get('bag_points', 0) != 0:
        bag_points = round_data['bag_points']
        breakdown.append({
            'label': 'Bags',
            'value': f'{bag_points:+d}',
            'color': 'text-yellow-600'
        })
    
    # Add bag penalty if non-zero
    if round_data.get('bag_penalty', 0) != 0:
        bag_penalty = round_data['bag_penalty']
        breakdown.append({
            'label': 'Bag penalty',
            'value': f'-{bag_penalty}',
            'color': 'text-red-600'
        })
    
    return breakdown

def calculate_detailed_round_scoring(bid_string, actual_tricks, game, nil_success=False, blind_nil_success=False, blind_success=False):
    """Calculate detailed scoring components for database storage"""
    bid_value, bid_type = parse_bid(bid_string)
    
    # Initialize all components
    components = {
        'bid_points': 0,
        'nil_bonus': 0,
        'blind_nil_bonus': 0,
        'blind_bonus': 0,
        'bag_points': 0,
        'total_points': 0
    }
    
    if bid_type == 'nil':
        # Pure nil bid
        components['nil_bonus'] = game['nil_penalty'] if actual_tricks == 0 else -game['nil_penalty']
        components['total_points'] = components['nil_bonus']
        
    elif bid_type == 'combination_nil':
        # Combination nil bid (e.g., "4n")
        # Base bid scoring
        if actual_tricks >= bid_value:
            components['bid_points'] = bid_value * 10
            components['bag_points'] = actual_tricks - bid_value
        else:
            components['bid_points'] = -(bid_value * 10)

        # Nil bonus/penalty
        components['nil_bonus'] = game['nil_penalty'] if nil_success else -game['nil_penalty']
        # IMPORTANT: total_points should NOT include bag_points (tracked separately)
        components['total_points'] = components['bid_points'] + components['nil_bonus']
        
    elif bid_type == 'combination_blind_nil':
        # Combination blind nil bid (e.g., "4bn")
        # Base bid scoring
        if actual_tricks >= bid_value:
            components['bid_points'] = bid_value * 10
            components['bag_points'] = actual_tricks - bid_value
        else:
            components['bid_points'] = -(bid_value * 10)

        # Blind nil bonus/penalty
        components['blind_nil_bonus'] = game['blind_nil_penalty'] if blind_nil_success else -game['blind_nil_penalty']
        # IMPORTANT: total_points should NOT include bag_points (tracked separately)
        components['total_points'] = components['bid_points'] + components['blind_nil_bonus']
        
    elif bid_type == 'blind_nil':
        # Pure blind nil bid
        components['blind_nil_bonus'] = game['blind_nil_penalty'] if actual_tricks == 0 else -game['blind_nil_penalty']
        components['total_points'] = components['blind_nil_bonus']
        
    elif bid_type == 'blind':
        # Blind bid (doubled points/penalties)
        if blind_success:
            # Split into base bid and blind bonus for clearer display
            components['bid_points'] = bid_value * 10
            components['blind_bonus'] = bid_value * 10  # Additional doubling bonus
            components['bag_points'] = actual_tricks - bid_value
        else:
            # Failed blind bid: show as blind penalty only
            components['bid_points'] = 0
            components['blind_bonus'] = -(bid_value * 10 * 2)
        # IMPORTANT: total_points should NOT include bag_points (tracked separately)
        components['total_points'] = components['bid_points'] + components['blind_bonus']
        
    else:  # 'regular'
        # Standard bid
        if actual_tricks >= bid_value:
            components['bid_points'] = bid_value * 10
            components['bag_points'] = actual_tricks - bid_value
        else:
            components['bid_points'] = -(bid_value * 10)
        # IMPORTANT: total_points should NOT include bag_points
        # Bags are tracked separately and displayed in the ones digit
        components['total_points'] = components['bid_points']
    
    return components