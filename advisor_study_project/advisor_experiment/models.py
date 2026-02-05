from otree.api import (  # type: ignore[import-untyped]
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    cu,
    models,
    widgets,
)
import random

doc = """
Advisor Study: Active vs Passive Sampling.
3 Blocks: Blocks 1 & 2 (Active/Passive counterbalanced), Block 3 always Active.
TEMPORARY TESTING: 2 rounds per block (6 total). For real experiment use 20 per block, 60 total.
Switching costs and advisor reliability.
"""

ROUNDS_PER_BLOCK = 2

class Constants(BaseConstants):
    name_in_url = 'advisor_experiment'
    players_per_group = None
    num_rounds = ROUNDS_PER_BLOCK * 3
    rounds_per_block = ROUNDS_PER_BLOCK  # for pages (block boundaries, survey rounds)

    # Payoffs
    endowment = cu(6.00)
    bonus_per_correct = cu(0.20)
    switching_cost = cu(0.05)
    
    # Grid Settings for pixel image
    grid_width = 20
    grid_height = 10
    total_pixels = 200
    majority_threshold = 0.55 # 55% majority

class Subsession(BaseSubsession):
    def creating_session(self):
        # 1. Block Counterbalancing (Blocks 1 & 2: Active/Passive; Block 3 is always Active)
        # Advisor accuracy: A, C, E use dominant probs (30,30,20,20); B, D, F use inverse (20,20,30,30)
        ACCURACY_LEVELS = [0.80, 0.60, 0.40, 0.20]
        PROBS_DOMINANT = [0.30, 0.30, 0.20, 0.20]   # A, C, E: 80/60/40/20 with 30%, 30%, 20%, 20%
        PROBS_INVERSE = [0.20, 0.20, 0.30, 0.30]    # B, D, F: 80/60/40/20 with 20%, 20%, 30%, 30%

        if self.round_number == 1:
            # Male European-sounding names; A,C,E = Dots & Co., B,D,F = PixelHouse
            NAMES_DOTS = ['Josh', 'Thomas', 'Lukas', 'Henrik', 'Stefan', 'Marc']
            NAMES_PIXEL = ['Marcus', 'Niklas', 'Felix', 'Erik', 'Jonas', 'Paul']
            for p in self.get_players():
                # Even IDs: Active first in block 1; Odd: Passive first. Block 3 is always Active.
                if p.id_in_group % 2 == 0:
                    participant_vars = {'block_order': ['Active', 'Passive', 'Active']}
                else:
                    participant_vars = {'block_order': ['Passive', 'Active', 'Active']}
                # Draw all six advisors independently (B, D, F use inverse odds)
                participant_vars['accuracy_A'] = random.choices(ACCURACY_LEVELS, weights=PROBS_DOMINANT, k=1)[0]
                participant_vars['accuracy_B'] = random.choices(ACCURACY_LEVELS, weights=PROBS_INVERSE, k=1)[0]
                participant_vars['accuracy_C'] = random.choices(ACCURACY_LEVELS, weights=PROBS_DOMINANT, k=1)[0]
                participant_vars['accuracy_D'] = random.choices(ACCURACY_LEVELS, weights=PROBS_INVERSE, k=1)[0]
                participant_vars['accuracy_E'] = random.choices(ACCURACY_LEVELS, weights=PROBS_DOMINANT, k=1)[0]
                participant_vars['accuracy_F'] = random.choices(ACCURACY_LEVELS, weights=PROBS_INVERSE, k=1)[0]
                # Display names: "Name (Dots & Co.)" or "Name (PixelHouse)" — 3 distinct names per company so the same name never appears in two blocks
                dots = random.sample(NAMES_DOTS, 3)
                pixel = random.sample(NAMES_PIXEL, 3)
                participant_vars['advisor_name_A'] = f"{dots[0]} (Dots & Co.)"
                participant_vars['advisor_name_B'] = f"{pixel[0]} (PixelHouse)"
                participant_vars['advisor_name_C'] = f"{dots[1]} (Dots & Co.)"
                participant_vars['advisor_name_D'] = f"{pixel[1]} (PixelHouse)"
                participant_vars['advisor_name_E'] = f"{dots[2]} (Dots & Co.)"
                participant_vars['advisor_name_F'] = f"{pixel[2]} (PixelHouse)"
                # Half of participants have 5¢ switching cost when changing advisor in Active block
                participant_vars['has_switching_cost'] = random.choice([True, False])
                p.participant.vars.update(participant_vars)

        for p in self.get_players():
            # Store true advisor accuracies on player for admin/data export (same every round)
            p.accuracy_A = p.participant.vars['accuracy_A']
            p.accuracy_B = p.participant.vars['accuracy_B']
            p.accuracy_C = p.participant.vars['accuracy_C']
            p.accuracy_D = p.participant.vars['accuracy_D']
            p.accuracy_E = p.participant.vars['accuracy_E']
            p.accuracy_F = p.participant.vars['accuracy_F']
            # 2. Determine Current Block (1-2, 3-4, 5-6 for testing; use 20/40/60 for real)
            if self.round_number <= ROUNDS_PER_BLOCK:
                current_block_idx = 0
            elif self.round_number <= ROUNDS_PER_BLOCK * 2:
                current_block_idx = 1
            else:
                current_block_idx = 2
            p.block_type = p.participant.vars['block_order'][current_block_idx]
            
            # 3. Determine Truth (Red vs Blue)
            p.true_color = random.choice(['Red', 'Blue'])
            
            # 4. Generate Advisor Advice (Block 1: A/B, Block 2: C/D, Block 3: E/F)
            acc_A = p.participant.vars['accuracy_A']
            acc_B = p.participant.vars['accuracy_B']
            acc_C = p.participant.vars['accuracy_C']
            acc_D = p.participant.vars['accuracy_D']
            acc_E = p.participant.vars['accuracy_E']
            acc_F = p.participant.vars['accuracy_F']

            if self.round_number <= ROUNDS_PER_BLOCK:
                p.advisor_high_name = p.participant.vars['advisor_name_A']
                p.advisor_low_name = p.participant.vars['advisor_name_B']
                if random.random() < acc_A:
                    p.advice_high = p.true_color
                else:
                    p.advice_high = 'Blue' if p.true_color == 'Red' else 'Red'
                if random.random() < acc_B:
                    p.advice_low = p.true_color
                else:
                    p.advice_low = 'Blue' if p.true_color == 'Red' else 'Red'
            elif self.round_number <= ROUNDS_PER_BLOCK * 2:
                p.advisor_high_name = p.participant.vars['advisor_name_C']
                p.advisor_low_name = p.participant.vars['advisor_name_D']
                if random.random() < acc_C:
                    p.advice_high = p.true_color
                else:
                    p.advice_high = 'Blue' if p.true_color == 'Red' else 'Red'
                if random.random() < acc_D:
                    p.advice_low = p.true_color
                else:
                    p.advice_low = 'Blue' if p.true_color == 'Red' else 'Red'
            else:
                p.advisor_high_name = p.participant.vars['advisor_name_E']
                p.advisor_low_name = p.participant.vars['advisor_name_F']
                if random.random() < acc_E:
                    p.advice_high = p.true_color
                else:
                    p.advice_high = 'Blue' if p.true_color == 'Red' else 'Red'
                if random.random() < acc_F:
                    p.advice_low = p.true_color
                else:
                    p.advice_low = 'Blue' if p.true_color == 'Red' else 'Red'

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    # Experimental State
    block_type = models.StringField()
    true_color = models.StringField()
    
    # Advisor Variables (true accuracies; also stored in participant.vars, here for admin/data export)
    advisor_high_name = models.StringField()
    advisor_low_name = models.StringField()
    advice_high = models.StringField()
    advice_low = models.StringField()
    accuracy_A = models.FloatField(blank=True, null=True)
    accuracy_B = models.FloatField(blank=True, null=True)
    accuracy_C = models.FloatField(blank=True, null=True)
    accuracy_D = models.FloatField(blank=True, null=True)
    accuracy_E = models.FloatField(blank=True, null=True)
    accuracy_F = models.FloatField(blank=True, null=True)
    
    # User Inputs
    initial_prediction = models.StringField(choices=['Red', 'Blue'], widget=widgets.RadioSelectHorizontal)
    initial_confidence = models.IntegerField(min=50, max=100, label="How confident are you? (50-100%)")
    
    # Active Sampling Choice (Who do they want to see?)
    # We store "High" or "Low" to track the reliable vs unreliable advisor
    selected_advisor_type = models.StringField(choices=['High', 'Low'], blank=True)
    
    # Final Inputs
    final_prediction = models.StringField(choices=['Red', 'Blue'], widget=widgets.RadioSelectHorizontal)
    final_confidence = models.IntegerField(min=50, max=100, label="Updated confidence (50-100%)")
    
    # Outcomes
    is_correct = models.BooleanField()
    round_payoff = models.CurrencyField()
    switch_cost_incurred = models.CurrencyField(initial=0)

    # Block-end surveys: perceived accuracy (80/60/40/20%) and WTP
    ACCURACY_CHOICES = [[80, "80%"], [60, "60%"], [40, "40%"], [20, "20%"]]
    confidence_A = models.IntegerField(choices=ACCURACY_CHOICES, blank=True, null=True, label="How accurate was advisor A?")
    confidence_B = models.IntegerField(choices=ACCURACY_CHOICES, blank=True, null=True, label="How accurate was advisor B?")
    pay_A = models.IntegerField(min=0, max=20, blank=True, null=True, label="Would pay for Team A advice (cents, 0-20)")
    pay_B = models.IntegerField(min=0, max=20, blank=True, null=True, label="Would pay for Team B advice (cents, 0-20)")
    confidence_C = models.IntegerField(choices=ACCURACY_CHOICES, blank=True, null=True, label="How accurate was advisor C?")
    confidence_D = models.IntegerField(choices=ACCURACY_CHOICES, blank=True, null=True, label="How accurate was advisor D?")
    pay_C = models.IntegerField(min=0, max=20, blank=True, null=True, label="Would pay for Team C advice (cents, 0-20)")
    pay_D = models.IntegerField(min=0, max=20, blank=True, null=True, label="Would pay for Team D advice (cents, 0-20)")
    confidence_E = models.IntegerField(choices=ACCURACY_CHOICES, blank=True, null=True, label="How accurate was advisor E?")
    confidence_F = models.IntegerField(choices=ACCURACY_CHOICES, blank=True, null=True, label="How accurate was advisor F?")
    pay_E = models.IntegerField(min=0, max=20, blank=True, null=True, label="Would pay for Team E advice (cents, 0-20)")
    pay_F = models.IntegerField(min=0, max=20, blank=True, null=True, label="Would pay for Team F advice (cents, 0-20)")

    def calculate_payoff(self):
        # 1. Determine Correctness
        self.is_correct = (self.final_prediction == self.true_color)
        
        # 2. Calculate Bonus
        if self.is_correct:
            self.round_payoff = Constants.bonus_per_correct
        else:
            self.round_payoff = cu(0)
            
        # 3. Handle Switching Costs (Active blocks only, and only for half of participants)
        if self.block_type == 'Active' and self.participant.vars.get('has_switching_cost', False):
            if (self.round_number - 1) % ROUNDS_PER_BLOCK != 0:  # not first trial of this block
                prev_player = self.in_round(self.round_number - 1)
                if prev_player.selected_advisor_type != self.selected_advisor_type:
                    self.switch_cost_incurred = Constants.switching_cost
        
        # 4. Final Payoff Update
        self.payoff = self.round_payoff - self.switch_cost_incurred