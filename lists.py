# CONSTANTS
# Info about how to process scraping recipe links each site
# source_list format is as follows (by index):
# 0 - html regex to match for grabbing link to recipe
# 1 - address for main course meals

# --------------------------------------------------------------------------- #

'''
Currently runs the following websites:

Whole30
Bonappetit
'''

# --------------------------------------------------------------------------- #
websites = {
    'Whole30': {
        'regex': r'<a class="post-card" href="(\S*)">',
        'main course': 'https://whole30.com/recipes/category/entree/'
    },
    'Bonappetit': {
        'regex': r'<a class="external-link" data-event-click=".*" href="(\S*)"',
        'main course': 'https://www.bonappetit.com/gallery/whole30-recipes-that-taste-good'
    },
}

# a list of key veggies that we want in a meal
veggies = [
    'acorn aquash',
    'artichoke',
    'arugula',
    'asparagus',
    'bell pepper',
    'broccoli',
    'broccolini',
    'brussel sprouts',
    'butternut squash',
    'cabbage',
    'carrot',
    'cannellini',
    'cauliflower',
    'celery',
    'cucumber',
    'eggplant',
    'garbanzo',
    'green bean',
    'kale',
    'kohlrabi',
    'lettuce',
    'mushroom',
    'nori',
    'ogonori',
    'okra',
    'peas',
    'potato',
    'radish',
    'snap pea',
    'soybean',
    'spinach',
    'squash',
    'yam',
    'zucchini',
]
