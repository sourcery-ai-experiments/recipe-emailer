# CONSTANTS
# Info about how to process scraping recipe links each site
# source_list format is as follows (by index):
# 0 - html attribute to locate recipies on site
# 1 - html text to match for attribute 0
# 2 - address for main course
# 3 - address for side dishes
# 4 - address for spider (not yet implemented)

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
