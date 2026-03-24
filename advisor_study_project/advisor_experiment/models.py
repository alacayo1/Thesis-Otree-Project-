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
8 Blocks: 4 Active and 4 Passive per participant (counterbalanced). No switching costs.
"""

ROUNDS_PER_BLOCK = 20  # 18 participant rounds + 2 block-end rounds (one per advisor)

# Accuracy levels: 90%, 75%, 60%, 50% (display and sampling)
ACCURACY_LEVELS = [0.90, 0.75, 0.60, 0.50]
# Read-only list of perceived accuracy options for block-end surveys
ACCURACY_CHOICES = [
    (90, "90%"),
    (75, "75%"),
    (60, "60%"),
    (50, "50%"),
]

class Constants(BaseConstants):
    name_in_url = 'advisor_experiment'
    players_per_group = None
    num_blocks = 8
    num_rounds = ROUNDS_PER_BLOCK * num_blocks
    rounds_per_block = ROUNDS_PER_BLOCK

    # Payoffs: binarized scoring rule. Per block, one round drawn for prior and one for posterior; each draw pays or not. Max $8.
    endowment = cu(5.00)
    bonus_total = cu(8.00)
    # 2 draws per block × 8 blocks = 16 draws total; each win pays 8/16 = 0.50
    lottery_pay_per_win = cu(8.00 / 16)

    # Grid Settings for pixel image (400 pixels = 40×10, doubled from 200)
    grid_width = 40
    grid_height = 10
    total_pixels = 400
    majority_threshold = 0.51

class Subsession(BaseSubsession):
    def creating_session(self):
        PROBS_DOMINANT = [0.30, 0.30, 0.20, 0.20]   # 1a..8a (Dots & Co.)
        PROBS_INVERSE = [0.20, 0.20, 0.30, 0.30]    # 1b..8b (PixelHouse)
        HIGH_IDS = ['1a', '2a', '3a', '4a', '5a', '6a', '7a', '8a']
        LOW_IDS = ['1b', '2b', '3b', '4b', '5b', '6b', '7b', '8b']

        if self.round_number == 1:
            NAMES_DOTS = ['Josh', 'Thomas', 'Lukas', 'Henrik', 'Stefan', 'Marc', 'Leo', 'Finn']
            NAMES_PIXEL = ['Marcus', 'Niklas', 'Felix', 'Erik', 'Jonas', 'Paul', 'Noah', 'Liam']
            for p in self.get_players():
                if p.id_in_group % 2 == 0:
                    participant_vars = {'block_order': ['Active', 'Passive', 'Active', 'Passive', 'Active', 'Passive', 'Active', 'Passive']}
                else:
                    participant_vars = {'block_order': ['Passive', 'Active', 'Passive', 'Active', 'Passive', 'Active', 'Passive', 'Active']}
                for i in range(8):
                    participant_vars[f'accuracy_{HIGH_IDS[i]}'] = random.choices(ACCURACY_LEVELS, weights=PROBS_DOMINANT, k=1)[0]
                    participant_vars[f'accuracy_{LOW_IDS[i]}'] = random.choices(ACCURACY_LEVELS, weights=PROBS_INVERSE, k=1)[0]
                dots = random.sample(NAMES_DOTS, 8)
                pixel = random.sample(NAMES_PIXEL, 8)
                for i in range(8):
                    participant_vars[f'advisor_name_{HIGH_IDS[i]}'] = f"{dots[i]} (Dots & Co.)"
                    participant_vars[f'advisor_name_{LOW_IDS[i]}'] = f"{pixel[i]} (PixelHouse)"
                p.participant.vars.update(participant_vars)

        rpb = ROUNDS_PER_BLOCK
        HIGH_IDS = ['1a', '2a', '3a', '4a', '5a', '6a', '7a', '8a']
        LOW_IDS = ['1b', '2b', '3b', '4b', '5b', '6b', '7b', '8b']
        for p in self.get_players():
            rn = self.round_number
            current_block_idx = min((rn - 1) // rpb, Constants.num_blocks - 1)
            block_num = current_block_idx + 1
            p.block_type = p.participant.vars['block_order'][current_block_idx]
            # Passive blocks: pre-assign 9 High + 9 Low for rounds 1–18 so exposure is symmetrical
            if (rn - 1) % rpb == 0 and p.block_type == 'Passive':
                p.participant.vars[f'block_{block_num}_advisor_sequence'] = random.sample(
                    ['High'] * 9 + ['Low'] * 9, 18
                )
            p.true_color = random.choice(['Red', 'Blue'])
            high_id = HIGH_IDS[current_block_idx]
            low_id = LOW_IDS[current_block_idx]
            p.advisor_high_name = p.participant.vars[f'advisor_name_{high_id}']
            p.advisor_low_name = p.participant.vars[f'advisor_name_{low_id}']
            acc_high = p.participant.vars[f'accuracy_{high_id}']
            acc_low = p.participant.vars[f'accuracy_{low_id}']
            a_high = p.true_color if random.random() < acc_high else ('Blue' if p.true_color == 'Red' else 'Red')
            a_low = p.true_color if random.random() < acc_low else ('Blue' if p.true_color == 'Red' else 'Red')
            p.participant.vars[f'advice_high_r{rn}'] = a_high
            p.participant.vars[f'advice_low_r{rn}'] = a_low
            p.accuracy_high_this_block = acc_high
            p.accuracy_low_this_block = acc_low
            # Block-end rounds 19 and 20 (within-block index 18 and 19): always passive, one advisor each
            within_block = (rn - 1) % rpb
            p.block_end_round = (1 if within_block == 18 else (2 if within_block == 19 else 0))

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    # Consent (round 1 only; stored on first round's player)
    consent_accepted = models.BooleanField(initial=False, blank=True)
    computer_number = models.StringField(blank=False, label="Computer number (top right of your desk)")
    # Admin datasheet: key round columns only
    block_type = models.StringField()
    advisor_high_name = models.StringField()
    advisor_low_name = models.StringField()
    true_color = models.StringField()
    accuracy_high_this_block = models.FloatField(blank=True, null=True)
    accuracy_low_this_block = models.FloatField(blank=True, null=True)
    selected_advisor_firm = models.StringField(blank=True)  # "Dots & Co." or "PixelHouse"
    advice_shown = models.StringField(blank=True)  # color shown (Red/Blue) this round
    initial_confidence = models.IntegerField(min=0, max=100, label="Probability (0-100%) that Red is majority")
    final_confidence = models.IntegerField(min=0, max=100, label="Updated probability (0-100%) that Red is majority")
    round_payoff = models.CurrencyField(initial=0)
    round_had_payoff = models.BooleanField(blank=True, null=True)
    total_time_seconds = models.FloatField(blank=True, null=True)
    current_block_time_seconds = models.FloatField(blank=True, null=True)
    final_total_pay = models.CurrencyField(blank=True, null=True)  # participation + lottery (set on last round)

    # 0 = normal round, 1 = block end round 1 (see High advisor), 2 = block end round 2 (see Low advisor)
    block_end_round = models.IntegerField(initial=0)
    # Internal (for logic only); labels from selected_advisor_type_choices below
    selected_advisor_type = models.StringField(
        choices=['High', 'Low'], widget=widgets.RadioSelect
    )

    @staticmethod
    def selected_advisor_type_choices(player):
        """Display advisor names and firms (not "High"/"Low")."""
        high = player.advisor_high_name
        low = player.advisor_low_name
        return [
            ['High', high + ' (Company historically more accurate)'],
            ['Low', low + ' (Company historically less accurate)'],
        ]
    # Comprehension and block surveys (required for forms)
    odds_dots_90 = models.StringField(
        choices=[(str(i), str(i)) for i in range(10, 101, 10)],
        label="Dots & Co.: how many out of 100 advisors are 90% accurate",
    )
    odds_pixel_90 = models.StringField(
        choices=[(str(i), str(i)) for i in range(10, 101, 10)],
        label="PixelHouse: how many out of 100 advisors are 90% accurate",
    )
    # Block end surveys: must select an option (required), but any choice is accepted
    confidence_1a = models.IntegerField(choices=ACCURACY_CHOICES)
    confidence_1b = models.IntegerField(choices=ACCURACY_CHOICES)
    pay_1a = models.IntegerField(min=0, max=20)
    pay_1b = models.IntegerField(min=0, max=20)
    confidence_2a = models.IntegerField(choices=ACCURACY_CHOICES)
    confidence_2b = models.IntegerField(choices=ACCURACY_CHOICES)
    pay_2a = models.IntegerField(min=0, max=20)
    pay_2b = models.IntegerField(min=0, max=20)
    confidence_3a = models.IntegerField(choices=ACCURACY_CHOICES)
    confidence_3b = models.IntegerField(choices=ACCURACY_CHOICES)
    pay_3a = models.IntegerField(min=0, max=20)
    pay_3b = models.IntegerField(min=0, max=20)
    confidence_4a = models.IntegerField(choices=ACCURACY_CHOICES)
    confidence_4b = models.IntegerField(choices=ACCURACY_CHOICES)
    pay_4a = models.IntegerField(min=0, max=20)
    pay_4b = models.IntegerField(min=0, max=20)
    confidence_5a = models.IntegerField(choices=ACCURACY_CHOICES)
    confidence_5b = models.IntegerField(choices=ACCURACY_CHOICES)
    pay_5a = models.IntegerField(min=0, max=20)
    pay_5b = models.IntegerField(min=0, max=20)
    confidence_6a = models.IntegerField(choices=ACCURACY_CHOICES)
    confidence_6b = models.IntegerField(choices=ACCURACY_CHOICES)
    pay_6a = models.IntegerField(min=0, max=20)
    pay_6b = models.IntegerField(min=0, max=20)
    confidence_7a = models.IntegerField(choices=ACCURACY_CHOICES)
    confidence_7b = models.IntegerField(choices=ACCURACY_CHOICES)
    pay_7a = models.IntegerField(min=0, max=20)
    pay_7b = models.IntegerField(min=0, max=20)
    confidence_8a = models.IntegerField(choices=ACCURACY_CHOICES)
    confidence_8b = models.IntegerField(choices=ACCURACY_CHOICES)
    pay_8a = models.IntegerField(min=0, max=20)
    pay_8b = models.IntegerField(min=0, max=20)

    @staticmethod
    def _win_prob(p, true_color_red):
        """Probability of winning one lottery: if Red then 1-(1-p)^2, if Blue then 1-p^2."""
        p = p / 100.0
        if true_color_red:
            return 1.0 - (1.0 - p) ** 2
        return 1.0 - p ** 2

    @staticmethod
    def run_block_payoff(player, block_num):
        """
        For this block: pick one round for the prior draw and one for the posterior draw (from the block).
        Each draw: win prob from formula, then pay lottery_pay_per_win or 0. Add to participant.payoff.
        Set round_payoff and round_had_payoff on the affected player(s).
        """
        rpb = Constants.rounds_per_block
        pay_per_win = round(float(Constants.lottery_pay_per_win), 2)
        first_round = (block_num - 1) * rpb + 1
        last_round = block_num * rpb
        prior_round = random.randint(first_round, last_round)
        posterior_round = random.randint(first_round, last_round)
        prior_player = player.in_round(prior_round)
        posterior_player = player.in_round(posterior_round)
        # Prior draw
        prob_prior = Player._win_prob(prior_player.initial_confidence, prior_player.true_color == 'Red')
        win_prior = random.random() < prob_prior
        pay_prior = pay_per_win if win_prior else 0.0
        # Posterior draw
        prob_post = Player._win_prob(posterior_player.final_confidence, posterior_player.true_color == 'Red')
        win_post = random.random() < prob_post
        pay_post = pay_per_win if win_post else 0.0
        # Assign round_payoff to the round(s) that were drawn
        prior_player.round_payoff = cu(pay_prior)
        prior_player.round_had_payoff = pay_prior > 0
        if posterior_round == prior_round:
            prior_player.round_payoff = cu(pay_prior + pay_post)
            prior_player.round_had_payoff = (pay_prior + pay_post) > 0
        else:
            posterior_player.round_payoff = cu(pay_post)
            posterior_player.round_had_payoff = pay_post > 0
        block_total = round(pay_prior + pay_post, 2)
        participant = player.participant
        participant.payoff = (participant.payoff or cu(0)) + cu(block_total)
