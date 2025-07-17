def parse_bid(bid_string):
    """Parse bid string format: '7', '4b', '0n', '0bn'"""
    if bid_string.endswith('bn'):
        return int(bid_string[:-2]), 'blind_nil'
    elif bid_string.endswith('b'):
        return int(bid_string[:-1]), 'blind'  
    elif bid_string.endswith('n'):
        return int(bid_string[:-1]), 'nil'
    else:
        return int(bid_string), 'regular'

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
        # Blind bid (not nil)
        if actual_tricks >= bid_value:
            return (bid_value * 10) + (actual_tricks - bid_value)
        else:
            return -(bid_value * 10)
    
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
    
    else:
        # Regular or blind bid
        return max(0, actual_tricks - bid_value)

def format_bid_display(bid_string):
    """Format bid string for display"""
    bid_value, bid_type = parse_bid(bid_string)
    
    if bid_type == 'nil':
        return "Nil"
    elif bid_type == 'blind_nil':
        return "Blind Nil"
    elif bid_type == 'blind':
        return f"{bid_value} (Blind)"
    else:
        return str(bid_value)