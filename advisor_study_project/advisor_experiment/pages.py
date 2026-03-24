from otree.api import Currency as cu, currency_range  # type: ignore[import-untyped]
from ._builtin import Page, WaitPage  # type: ignore[import-untyped]
from .models import Constants, Player
import random
import time
import math


def _advice_for_round(participant, round_number):
    return (
        participant.vars.get(f'advice_high_r{round_number}'),
        participant.vars.get(f'advice_low_r{round_number}'),
    )


class TimeTrackingMixin:
    """Records time in total_time_seconds and current_block_time_seconds."""
    def vars_for_template(self):
        self.participant.vars['_page_start_time'] = time.time()
        return {}

    def before_next_page(self):
        start = self.participant.vars.get('_page_start_time', time.time())
        elapsed = max(0, time.time() - start)
        total = round(self.participant.vars.get('total_time_seconds', 0) + elapsed, 2)
        self.participant.vars['total_time_seconds'] = total
        rpb = Constants.rounds_per_block
        block_num = min((self.round_number - 1) // rpb + 1, Constants.num_blocks)
        block_key = f'block_{block_num}_time_seconds'
        self.participant.vars[block_key] = round(self.participant.vars.get(block_key, 0) + elapsed, 2)
        self.player.total_time_seconds = round(self.participant.vars.get('total_time_seconds'), 2)
        self.player.current_block_time_seconds = round(self.participant.vars.get(block_key, 0), 2)
        super().before_next_page()


class Consent(Page):
    """First page: consent form with required checkbox and computer number."""
    form_model = 'player'
    form_fields = ['consent_accepted', 'computer_number']

    def is_displayed(self):
        return self.round_number == 1

    def error_message(self, values):
        if not values.get('consent_accepted'):
            return 'You must check the box to confirm that you have read the consent form and agree to participate.'
        if not (values.get('computer_number') or '').strip():
            return 'Please enter your assigned computer number (top right of your desk) before continuing.'


class Welcome(TimeTrackingMixin, Page):
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        d = super().vars_for_template()
        return d


class AdvisorOddsIntro(TimeTrackingMixin, Page):
    """Second welcome page: 'Don't worry...' text and two ACCURACY / ODDS tables side by side."""
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        d = super().vars_for_template()
        acc_pct = [90, 75, 60, 50]
        favorable_counts = [30, 30, 20, 20]   # Dots & Co. total 100
        inverse_counts = [20, 20, 30, 30]     # PixelHouse total 100
        table_favorable = [
            {'accuracy': f'{a}% accurate', 'count': c}
            for a, c in zip(acc_pct, favorable_counts)
        ]
        table_inverse = [
            {'accuracy': f'{a}% accurate', 'count': c}
            for a, c in zip(acc_pct, inverse_counts)
        ]
        d.update({
            'table_favorable': table_favorable,
            'table_inverse': table_inverse,
        })
        return d


class OddsComprehensionCheck(TimeTrackingMixin, Page):
    """After AdvisorOddsIntro: force correct answers for 90% odds (Dots 30%, Pixel 20%)."""
    form_model = 'player'
    form_fields = ['odds_dots_90', 'odds_pixel_90']

    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        d = super().vars_for_template()
        acc_pct = [90, 75, 60, 50]
        table_favorable = [
            {'accuracy': f'{a}% accurate', 'count': c}
            for a, c in zip(acc_pct, [30, 30, 20, 20])
        ]
        table_inverse = [
            {'accuracy': f'{a}% accurate', 'count': c}
            for a, c in zip(acc_pct, [20, 20, 30, 30])
        ]
        d.update({
            'table_favorable': table_favorable,
            'table_inverse': table_inverse,
        })
        return d

    def error_message(self, values):
        if values.get('odds_dots_90') != '30' or values.get('odds_pixel_90') != '20':
            return (
                'One or both answers are incorrect. Use the table above: '
                'Dots & Co. has 30 out of 100 advisors who are 90% accurate (select 30). '
                'PixelHouse has 20 out of 100 advisors who are 90% accurate (select 20).'
            )


class BonusPayment(TimeTrackingMixin, Page):
    """Bonus payment explanation page after advisor intro and comprehension check."""
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        d = super().vars_for_template()
        return d


class BlockIntro(TimeTrackingMixin, Page):
    def is_displayed(self):
        rpb = Constants.rounds_per_block
        return self.round_number in (1, 1 + rpb, 1 + 2*rpb, 1 + 3*rpb, 1 + 4*rpb, 1 + 5*rpb, 1 + 6*rpb, 1 + 7*rpb)

    def vars_for_template(self):
        d = super().vars_for_template()
        rpb = Constants.rounds_per_block
        rn = self.round_number
        block_num = min((rn - 1) // rpb + 1, Constants.num_blocks)
        high_id = ['1a', '2a', '3a', '4a', '5a', '6a', '7a', '8a'][block_num - 1]
        low_id = ['1b', '2b', '3b', '4b', '5b', '6b', '7b', '8b'][block_num - 1]
        block_high_name = str(self.participant.vars.get(f'advisor_name_{high_id}', f'Team {high_id}'))
        block_low_name = str(self.participant.vars.get(f'advisor_name_{low_id}', f'Team {low_id}'))
        acc_pct = [90, 75, 60, 50]
        table_favorable = [
            {'accuracy': f'{a}% accurate', 'count': c}
            for a, c in zip(acc_pct, [30, 30, 20, 20])
        ]
        table_inverse = [
            {'accuracy': f'{a}% accurate', 'count': c}
            for a, c in zip(acc_pct, [20, 20, 30, 30])
        ]
        block_type = (getattr(self.player, 'block_type', None) or '').strip()
        d.update({
            'block_num': block_num,
            'block_high_name': block_high_name,
            'block_low_name': block_low_name,
            'table_favorable': table_favorable,
            'table_inverse': table_inverse,
            'is_active': block_type == 'Active',
        })
        return d

class ViewImage(TimeTrackingMixin, Page):
    timeout_seconds = 2

    def vars_for_template(self):
        d = super().vars_for_template()
        d.update({
            'true_color': self.player.true_color,
            'majority_threshold': Constants.majority_threshold,
            'grid_width': Constants.grid_width,
            'grid_height': Constants.grid_height,
            'total_pixels': Constants.total_pixels,
        })
        return d

class InitialPrediction(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['initial_confidence']
    preserve_unsubmitted_inputs = True

class AdvisorSelection(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['selected_advisor_type']

    def is_displayed(self):
        # Block-end rounds 19 and 20 are always passive (no advisor choice)
        if getattr(self.player, 'block_end_round', 0) != 0:
            return False
        return self.player.block_type == 'Active'

    def vars_for_template(self):
        d = super().vars_for_template()
        acc_pct = [90, 75, 60, 50]
        table_favorable = [
            {'accuracy': f'{a}% accurate', 'count': c}
            for a, c in zip(acc_pct, [30, 30, 20, 20])
        ]
        table_inverse = [
            {'accuracy': f'{a}% accurate', 'count': c}
            for a, c in zip(acc_pct, [20, 20, 30, 30])
        ]
        high_name = self.player.advisor_high_name
        low_name = self.player.advisor_low_name
        high_firm = 'Dots & Co.' if ' (Dots & Co.)' in high_name else 'PixelHouse'
        high_person = high_name.replace(' (Dots & Co.)', '').replace(' (PixelHouse)', '')
        low_firm = 'Dots & Co.' if ' (Dots & Co.)' in low_name else 'PixelHouse'
        low_person = low_name.replace(' (Dots & Co.)', '').replace(' (PixelHouse)', '')
        d.update({
            'high_name': high_name,
            'low_name': low_name,
            'high_firm': high_firm,
            'high_person': high_person,
            'low_firm': low_firm,
            'low_person': low_person,
            'table_favorable': table_favorable,
            'table_inverse': table_inverse,
        })
        return d

class AdvisorDisplay(TimeTrackingMixin, Page):
    def is_displayed(self):
        return True

    def vars_for_template(self):
        d = super().vars_for_template()
        advice_high, advice_low = _advice_for_round(self.participant, self.round_number)
        # Block-end rounds 19 and 20: always one round per advisor (High then Low), regardless of block type
        if getattr(self.player, 'block_end_round', 0) == 1:
            self.player.selected_advisor_type = 'High'
        elif getattr(self.player, 'block_end_round', 0) == 2:
            self.player.selected_advisor_type = 'Low'
        elif self.player.block_type == 'Passive':
            # Use pre-assigned sequence so each advisor appears exactly 9 times in rounds 1–18 (10 total with end rounds)
            rpb = Constants.rounds_per_block
            block_num = (self.round_number - 1) // rpb + 1
            within_block = (self.round_number - 1) % rpb
            seq = self.participant.vars.get(f'block_{block_num}_advisor_sequence', [])
            if within_block < len(seq):
                self.player.selected_advisor_type = seq[within_block]
            else:
                self.player.selected_advisor_type = random.choice(['High', 'Low'])
        if self.player.selected_advisor_type == 'High':
            advisor_name = self.player.advisor_high_name
            advice = advice_high
        else:
            advisor_name = self.player.advisor_low_name
            advice = advice_low
        if ' (Dots & Co.)' in advisor_name:
            advisor_firm = 'Dots & Co.'
            advisor_person = advisor_name.replace(' (Dots & Co.)', '')
        else:
            advisor_firm = 'PixelHouse'
            advisor_person = advisor_name.replace(' (PixelHouse)', '')
        d.update({
            'advisor_name': advisor_name,
            'advisor_firm': advisor_firm,
            'advisor_person': advisor_person,
            'advice': advice,
            'is_passive': self.player.block_type == 'Passive' or getattr(self.player, 'block_end_round', 0) != 0
        })
        return d

    def before_next_page(self):
        super().before_next_page()
        advice_high, advice_low = _advice_for_round(self.participant, self.round_number)
        self.player.advice_shown = advice_high if self.player.selected_advisor_type == 'High' else advice_low
        self.player.selected_advisor_firm = 'Dots & Co.' if self.player.selected_advisor_type == 'High' else 'PixelHouse'

class FinalPrediction(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['final_confidence']
    preserve_unsubmitted_inputs = True

    def vars_for_template(self):
        d = super().vars_for_template()
        advice_high, advice_low = _advice_for_round(self.participant, self.round_number)
        if self.player.selected_advisor_type == 'High':
            advisor_name = self.player.advisor_high_name
            advisor_advice = advice_high
        else:
            advisor_name = self.player.advisor_low_name
            advisor_advice = advice_low
        d.update({
            'initial_confidence': self.player.initial_confidence,
            'advisor_name': advisor_name,
            'advisor_advice': advisor_advice,
        })
        return d

    def before_next_page(self):
        super().before_next_page()

class Feedback(TimeTrackingMixin, Page):
    def vars_for_template(self):
        d = super().vars_for_template()
        advice_high, advice_low = _advice_for_round(self.participant, self.round_number)
        if self.player.selected_advisor_type == 'High':
            advisor_name = self.player.advisor_high_name
            advice_picked = advice_high
        else:
            advisor_name = self.player.advisor_low_name
            advice_picked = advice_low
        d.update({
            'true_color': self.player.true_color,
            'advisor_name': advisor_name,
            'advice_picked': advice_picked,
        })
        return d

    def before_next_page(self):
        super().before_next_page()
        # Run block payoff at end of each block (after round 20, 40, ..., 160)
        rpb = Constants.rounds_per_block
        if self.round_number % rpb == 0:
            block_num = self.round_number // rpb
            Player.run_block_payoff(self.player, block_num)


def _block_end_survey_rounds():
    """Round numbers where each block's end survey is shown (after round 18 of that block)."""
    rpb = Constants.rounds_per_block
    return [18 + k * rpb for k in range(Constants.num_blocks)]


class BlockEndRoundsIntro(TimeTrackingMixin, Page):
    """Shown after block end survey: you will play one more round with each advisor."""
    def is_displayed(self):
        return self.round_number in _block_end_survey_rounds()

    def vars_for_template(self):
        d = super().vars_for_template()
        rpb = Constants.rounds_per_block
        block_num = (self.round_number - 1) // rpb + 1
        d['block_num'] = block_num
        return d


class Block1EndSurvey(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['confidence_1a', 'confidence_1b']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == 18

    def vars_for_template(self):
        d = super().vars_for_template()
        last = self.player.in_round(self.round_number)
        d.update({'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name})
        return d


class Block2EndSurvey(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['confidence_2a', 'confidence_2b']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == Constants.rounds_per_block * 1 + 18  # 38

    def vars_for_template(self):
        d = super().vars_for_template()
        last = self.player.in_round(self.round_number)
        d.update({'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name})
        return d


class Block3EndSurvey(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['confidence_3a', 'confidence_3b']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == Constants.rounds_per_block * 2 + 18  # 58

    def vars_for_template(self):
        d = super().vars_for_template()
        last = self.player.in_round(self.round_number)
        d.update({'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name})
        return d


class Block4EndSurvey(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['confidence_4a', 'confidence_4b']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == Constants.rounds_per_block * 3 + 18  # 78

    def vars_for_template(self):
        d = super().vars_for_template()
        last = self.player.in_round(self.round_number)
        d.update({'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name})
        return d


class Block5EndSurvey(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['confidence_5a', 'confidence_5b']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == Constants.rounds_per_block * 4 + 18  # 98

    def vars_for_template(self):
        d = super().vars_for_template()
        last = self.player.in_round(self.round_number)
        d.update({'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name})
        return d


class Block6EndSurvey(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['confidence_6a', 'confidence_6b']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == Constants.rounds_per_block * 5 + 18  # 118

    def vars_for_template(self):
        d = super().vars_for_template()
        last = self.player.in_round(self.round_number)
        d.update({'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name})
        return d


class Block7EndSurvey(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['confidence_7a', 'confidence_7b']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == Constants.rounds_per_block * 6 + 18  # 138

    def vars_for_template(self):
        d = super().vars_for_template()
        last = self.player.in_round(self.round_number)
        d.update({'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name})
        return d


class Block8EndSurvey(TimeTrackingMixin, Page):
    form_model = 'player'
    form_fields = ['confidence_8a', 'confidence_8b']
    preserve_unsubmitted_inputs = True

    def is_displayed(self):
        return self.round_number == Constants.rounds_per_block * 7 + 18  # 158

    def vars_for_template(self):
        d = super().vars_for_template()
        last = self.player.in_round(self.round_number)
        d.update({'high_name': last.advisor_high_name, 'low_name': last.advisor_low_name})
        return d


class Earnings(TimeTrackingMixin, Page):
    """Final page: show-up fee + lottery earnings (each winning draw pays lottery_pay_per_win, e.g. $0.50 × wins)."""
    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        d = super().vars_for_template()
        participation = cu(self.session.config.get('participation_fee', 6))
        lottery_earned = cu(round(float(self.participant.payoff or 0), 2))
        total = participation + lottery_earned
        self.player.final_total_pay = total
        computer_number = getattr(self.player.in_round(1), 'computer_number', '') or ''
        d.update({
            'computer_number': computer_number,
            'lottery_earned': lottery_earned,
            'participation_fee': participation,
            'total_earnings': total,
        })
        return d

page_sequence = [
    Consent,
    Welcome,
    AdvisorOddsIntro,
    OddsComprehensionCheck,
    BonusPayment,
    BlockIntro,
    ViewImage,
    InitialPrediction,
    AdvisorSelection,
    AdvisorDisplay,
    FinalPrediction,
    Feedback,
    Block1EndSurvey,
    Block2EndSurvey,
    Block3EndSurvey,
    Block4EndSurvey,
    Block5EndSurvey,
    Block6EndSurvey,
    Block7EndSurvey,
    Block8EndSurvey,
    BlockEndRoundsIntro,  # after each block's survey so intro always follows the survey
    Earnings
]