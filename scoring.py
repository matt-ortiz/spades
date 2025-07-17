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

def get_score_breakdown_detailed(bid_string, actual_tricks, points, game, nil_success=None, blind_nil_success=None, blind_success=None):
    """Get detailed score breakdown in structured format for display"""
    bid_value, bid_type = parse_bid(bid_string)
    breakdown = []
    
    if bid_type == 'combination_nil':
        # Base score calculation
        if actual_tricks >= bid_value:
            base_score = bid_value * 10
            breakdown.append({
                'label': f'Base ({bid_value} tricks)',
                'value': f'+{base_score}',
                'color': 'text-green-600'
            })
            if actual_tricks > bid_value:
                bags = actual_tricks - bid_value
                breakdown.append({
                    'label': 'Bags',
                    'value': f'+{bags}',
                    'color': 'text-yellow-600'
                })
        else:
            base_score = -(bid_value * 10)
            breakdown.append({
                'label': f'Base (failed {bid_value})',
                'value': f'{base_score}',
                'color': 'text-red-600'
            })
        
        # Nil bonus/penalty
        if nil_success:
            breakdown.append({
                'label': 'Nil bonus',
                'value': f'+{game["nil_penalty"]}',
                'color': 'text-green-600'
            })
        else:
            breakdown.append({
                'label': 'Nil penalty',
                'value': f'-{game["nil_penalty"]}',
                'color': 'text-red-600'
            })
            
    elif bid_type == 'combination_blind_nil':
        # Base score calculation
        if actual_tricks >= bid_value:
            base_score = bid_value * 10
            breakdown.append({
                'label': f'Base ({bid_value} tricks)',
                'value': f'+{base_score}',
                'color': 'text-green-600'
            })
            if actual_tricks > bid_value:
                bags = actual_tricks - bid_value
                breakdown.append({
                    'label': 'Bags',
                    'value': f'+{bags}',
                    'color': 'text-yellow-600'
                })
        else:
            base_score = -(bid_value * 10)
            breakdown.append({
                'label': f'Base (failed {bid_value})',
                'value': f'{base_score}',
                'color': 'text-red-600'
            })
        
        # Blind nil bonus/penalty
        if blind_nil_success:
            breakdown.append({
                'label': 'Blind nil bonus',
                'value': f'+{game["blind_nil_penalty"]}',
                'color': 'text-green-600'
            })
        else:
            breakdown.append({
                'label': 'Blind nil penalty',
                'value': f'-{game["blind_nil_penalty"]}',
                'color': 'text-red-600'
            })
            
    elif bid_type == 'blind':
        if blind_success:
            doubled_score = bid_value * 10 * 2
            breakdown.append({
                'label': f'Blind success ({bid_value} × 2)',
                'value': f'+{doubled_score}',
                'color': 'text-green-600'
            })
            if actual_tricks > bid_value:
                bags = actual_tricks - bid_value
                breakdown.append({
                    'label': 'Bags',
                    'value': f'+{bags}',
                    'color': 'text-yellow-600'
                })
        else:
            doubled_penalty = -(bid_value * 10 * 2)
            breakdown.append({
                'label': f'Blind failed ({bid_value} × 2)',
                'value': f'{doubled_penalty}',
                'color': 'text-red-600'
            })
            
    elif bid_type in ['nil', 'blind_nil']:
        penalty_amount = game['blind_nil_penalty'] if bid_type == 'blind_nil' else game['nil_penalty']
        if actual_tricks == 0:
            label = 'Blind nil bonus' if bid_type == 'blind_nil' else 'Nil bonus'
            breakdown.append({
                'label': label,
                'value': f'+{penalty_amount}',
                'color': 'text-green-600'
            })
        else:
            label = 'Blind nil penalty' if bid_type == 'blind_nil' else 'Nil penalty'
            breakdown.append({
                'label': label,
                'value': f'-{penalty_amount}',
                'color': 'text-red-600'
            })
            
    else:
        # Regular bid
        if actual_tricks >= bid_value:
            base_score = bid_value * 10
            breakdown.append({
                'label': f'Base ({bid_value} tricks)',
                'value': f'+{base_score}',
                'color': 'text-green-600'
            })
            if actual_tricks > bid_value:
                bags = actual_tricks - bid_value
                breakdown.append({
                    'label': 'Bags',
                    'value': f'+{bags}',
                    'color': 'text-yellow-600'
                })
        else:
            base_score = -(bid_value * 10)
            breakdown.append({
                'label': f'Base (failed {bid_value})',
                'value': f'{base_score}',
                'color': 'text-red-600'
            })
    
    # Add bag penalty if applicable (this would need to be passed in)
    # For now, this is a placeholder
    # if bag_penalty_applied:
    #     breakdown.append({
    #         'label': 'Bag penalty',
    #         'value': f'-{game["bag_penalty_points"]}',
    #         'color': 'text-red-600'
    #     })
    
    return breakdown