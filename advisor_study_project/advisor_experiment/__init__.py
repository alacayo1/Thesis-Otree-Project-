# Player fields to show in the clean spreadsheet (excludes accuracy_1a... onwards)
PLAYER_DISPLAY_FIELDS = [
    'consent_accepted', 'computer_number',
    'block_type', 'block_end_round', 'advisor_high_name', 'advisor_low_name', 'true_color',
    'accuracy_high_this_block', 'accuracy_low_this_block', 'selected_advisor_firm',
    'advice_shown', 'initial_confidence', 'final_confidence',
    'round_payoff', 'round_had_payoff', 'total_time_seconds', 'current_block_time_seconds',
    'final_total_pay',
]


def custom_export(players):
    """Export only the display columns (no accuracy_1a... or block-end survey columns)."""
    rows = []
    for p in players:
        row = {
            'session_code': p.session.code,
            'participant_code': p.participant.code,
            'round_number': p.round_number,
        }
        for fname in PLAYER_DISPLAY_FIELDS:
            row[fname] = getattr(p, fname, None)
        rows.append(row)
    return rows
