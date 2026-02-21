from os import environ

SESSION_CONFIGS = [
    dict(
        name='advisor_study',
        display_name="Pixel Study",
        app_sequence=['advisor_experiment'],
        num_demo_participants=2,  # only for "Demo" session in admin; real sessions use created participant count
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=6.00, doc=""
)

# Include time tracking (advisor_experiment) in data monitoring / exports
PARTICIPANT_FIELDS = [
    'total_time_seconds',
    'block_1_time_seconds', 'block_2_time_seconds', 'block_3_time_seconds',
    'block_4_time_seconds', 'block_5_time_seconds', 'block_6_time_seconds',
]
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '3303269905762'
