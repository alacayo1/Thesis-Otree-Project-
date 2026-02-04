from otree.api import Currency as cu, currency_range  # type: ignore[import-untyped]
from ._builtin import Page, WaitPage  # type: ignore[import-untyped]
from .models import Constants
import random

class Welcome(Page):
    def is_displayed(self):
        return self.round_number == 1


class AdvisorOddsIntro(Page):
    """Second welcome page: 'Don't worry...' text and two ACCURACY / ODDS tables side by side."""
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        # Favorable (e.g. Dots & Co.): 30%, 30%, 20%, 20% for 80, 60, 40, 20
        # Other (e.g. PixelHouse): 20%, 20%, 30%, 30%
        acc_pct = [80, 60, 40, 20]
        favorable_odds = [30, 30, 20, 20]
        inverse_odds = [20, 20, 30, 30]
        table_favorable = [
            {'accuracy': f'{a}% accurate', 'odds': f'{o}% of the time'}
            for a, o in zip(acc_pct, favorable_odds)
        ]
        table_inverse = [
            {'accuracy': f'{a}% accurate', 'odds': f'{o}% of the time'}
            for a, o in zip(acc_pct, inverse_odds)
        ]
        return {
            'table_favorable': table_favorable,
            'table_inverse': table_inverse,
        }


class BlockIntro(Page):
    def is_displayed(self):
        # Show at start of each block (rounds 1, 1+RPB, 1+2*RPB)
        rpb = Constants.rounds_per_block
        return self.round_number in (1, 1 + rpb, 1 + 2 * rpb)

    def vars_for_template(self):
        rpb = Constants.rounds_per_block
        if self.round_number <= rpb:
            block_num = 1
            block_high_name = self.participant.vars.get('advisor_name_A', 'Team A')
            block_low_name = self.participant.vars.get('advisor_name_B', 'Team B')
        elif self.round_number <= 2 * rpb:
            block_num = 2
            block_high_name = self.participant.vars.get('advisor_name_C', 'Team C')
            block_low_name = self.participant.vars.get('advisor_name_D', 'Team D')
        else:
            block_num = 3
            block_high_name = self.participant.vars.get('advisor_name_E', 'Team E')
            block_low_name = self.participant.vars.get('advisor_name_F', 'Team F')
        # Same ACCURACY / ODDS table data as AdvisorOddsIntro (favorable vs inverse)
        acc_pct = [80, 60, 40, 20]
        table_favorable = [
            {'accuracy': f'{a}% accurate', 'odds': f'{o}% of the time'}
            for a, o in zip(acc_pct, [30, 30, 20, 20])
        ]
        table_inverse = [
            {'accuracy': f'{a}% accurate', 'odds': f'{o}% of the time'}
            for a, o in zip(acc_pct, [20, 20, 30, 30])
        ]
        return {
            'block_num': block_num,
            'block_high_name': block_high_name,
            'block_low_name': block_low_name,
            'table_favorable': table_favorable,
            'table_inverse': table_inverse,
            'is_active': self.player.block_type == 'Active',
            'has_switching_cost': self.participant.vars.get('has_switching_cost', False)
        }

class ViewImage(Page):
    timeout_seconds = 5 
    
    def vars_for_template(self):
        # Pass data to JS to generate the grid
        return {
            'true_color': self.player.true_color,
            'majority_threshold': Constants.majority_threshold
        }

class InitialPrediction(Page):
    form_model = 'player'
    form_fields = ['initial_prediction', 'initial_confidence']
    preserve_unsubmitted_inputs = True  # keep slider values if validation fails

class AdvisorSelection(Page):
    form_model = 'player'
    form_fields = ['selected_advisor_type']

    def is_displayed(self):
        return self.player.block_type == 'Active'

    def vars_for_template(self):
        has_cost = self.participant.vars.get('has_switching_cost', False)
        if not has_cost:
            cost_text = "No switching cost."
        elif (self.round_number - 1) % Constants.rounds_per_block == 0:
            cost_text = "No switching cost (First trial of this block)."
        else:
            cost_text = f"Switching advisors costs {Constants.switching_cost}"
        return {
            'high_name': self.player.advisor_high_name,
            'low_name': self.player.advisor_low_name,
            'cost_text': cost_text
        }

class AdvisorDisplay(Page):
    # This page just shows the advice (passive or active result)
    def is_displayed(self):
        return True
        
    def vars_for_template(self):
        # If Passive, system randomly selects
        if self.player.block_type == 'Passive':
            # Randomly pick High or Low for display
            self.player.selected_advisor_type = random.choice(['High', 'Low'])
            
        # Retrieve the specific advice based on selection
        if self.player.selected_advisor_type == 'High':
            advisor_name = self.player.advisor_high_name
            advice = self.player.advice_high
        else:
            advisor_name = self.player.advisor_low_name
            advice = self.player.advice_low
            
        return {
            'advisor_name': advisor_name,
            'advice': advice,
            'is_passive': self.player.block_type == 'Passive'
        }

class FinalPrediction(Page):
    form_model = 'player'
    form_fields = ['final_prediction', 'final_confidence']
    preserve_unsubmitted_inputs = True  # keep slider values if validation fails

    def vars_for_template(self):
        if self.player.selected_advisor_type == 'High':
            advisor_name = self.player.advisor_high_name
            advisor_advice = self.player.advice_high
        else:
            advisor_name = self.player.advisor_low_name
            advisor_advice = self.player.advice_low
        return {
            'initial_prediction': self.player.initial_prediction,
            'initial_confidence': self.player.initial_confidence,
            'advisor_name': advisor_name,
            'advisor_advice': advisor_advice,
        }
    
    def before_next_page(self):
        self.player.calculate_payoff()

class Feedback(Page):
    def vars_for_template(self):
        if self.player.selected_advisor_type == 'High':
            advisor_name = self.player.advisor_high_name
            advice_picked = self.player.advice_high
        else:
            advisor_name = self.player.advisor_low_name
            advice_picked = self.player.advice_low
        total_payoff = self.participant.payoff_plus_participation_fee()
        return {
            'correct_answer': self.player.true_color,
            'advisor_name': advisor_name,
            'advice_picked': advice_picked,
            'total_payoff': total_payoff
        }


class Block1EndSurvey(Page):
    form_model = 'player'
    form_fields = ['confidence_A', 'confidence_B', 'pay_A', 'pay_B']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == Constants.rounds_per_block  # end of block 1

    def vars_for_template(self):
        last = self.player.in_round(Constants.rounds_per_block)
        return {'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name}


class Block2EndSurvey(Page):
    form_model = 'player'
    form_fields = ['confidence_C', 'confidence_D', 'pay_C', 'pay_D']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == Constants.rounds_per_block * 2  # end of block 2

    def vars_for_template(self):
        last = self.player.in_round(Constants.rounds_per_block * 2)
        return {'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name}


class Block3EndSurvey(Page):
    form_model = 'player'
    form_fields = ['confidence_E', 'confidence_F', 'pay_E', 'pay_F']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == Constants.num_rounds  # end of block 3

    def vars_for_template(self):
        last = self.player.in_round(Constants.num_rounds)
        return {'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name}


page_sequence = [
    Welcome,
    AdvisorOddsIntro,
    BlockIntro,
    ViewImage,
    InitialPrediction,
    AdvisorSelection,
    AdvisorDisplay,
    FinalPrediction,
    Feedback,
    Block1EndSurvey,
    Block2EndSurvey,
    Block3EndSurvey
]