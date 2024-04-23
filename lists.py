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

reciperunner.com
paleorunningmomma.com
skinnytaste.com
twopeasandtheirpod.com
wellplated.com
thespruceeats.com
nourishedbynutrition.com
eatingbirdfood.com
budgetbytes.com
leanandgreenrecipes.net
minimalistbaker.com
gimmesomeoven.com
pinchofyum.com
heatherchristo.com
fitslowcookerqueen.com
eatliverun.com
'''

# --------------------------------------------------------------------------- #

websites = {
        'Recipe Runner' : {
            'regex' : r'a href="(\S*)" class="wpp-post-title" target="_self"',
            'main course' : 'https://www.reciperunner.com/category/recipes/dinners/',
            'side dish' : 'https://reciperunner.com/category/recipes/side-dishes/'
        },
        'Paleo Running Momma' : {
            'regex' : r'a class="entry-title-link" rel="bookmark" href="(\S*)"',
            'main course' : 'https://www.paleorunningmomma.com/course/dinner/',
            'side dish' : 'https://www.paleorunningmomma.com/course/veggies-sides/'
        },
        'Skinny Taste 1 of 2' : {
            'regex' : r'h2 class="entry-title"><a href="(\S*)"',
            'main course' : 'https://www.skinnytaste.com/recipe-index/?_course=dinner-recipes',
            'side dish' : 'https://www.skinnytaste.com/recipe-index/?_course=side-dishes'
        },
        'Skinny Taste 2 of 2' : {
            'regex' : r'h3 class="entry-title(?: ast-blog-single-element)*"><a href="(\S*)"(?: rel="bookmark")*',
            'main course' : 'https://www.skinnytaste.com/recipes/dinner-recipes/',
            'side dish' : 'https://www.skinnytaste.com/recipes/side-dishes/',
        },
        'Two Peas and Their Pod' : {
            'regex' : r'<p class="entry-category">(?!Breakfast\/Brunch).*?<\/p><h2 class="post-summary__title"><a href="(\S*)"',
            'main course' : 'https://www.twopeasandtheirpod.com/category/recipes/main-dishes/',
            'side dish' : 'https://www.twopeasandtheirpod.com/category/recipes/side/',
        },
        'Well Plated' : {
            'regex' : r'h2 class="post-summary__title"><a href="(\S*)"',
            'main course' : 'https://www.wellplated.com/category/recipes-by-type/entreesmain-dishes/#recent',
            'side dish' : 'https://www.wellplated.com/category/recipes-by-type/side-dishes-recipe-type/#recent',
        },
        'The Spruce Eats' : {
            'regex' : r'a.*class="comp mntl-card-list-items mntl-document-card mntl-card card card--no-image".*href="(\S*)"',
            'main course' : 'https://www.thespruceeats.com/dinner-4162806',
            'side dish' : 'https://www.thespruceeats.com/side-dishes-4162722',
        },
        'Nourished By Nutrition' : {
            'regex' : r'a class="post" href="(\S*)"',
            'main course' : 'https://nourishedbynutrition.com/recipe-index/?_sft_category=entrees',
            'side dish' : 'https://nourishedbynutrition.com/category/recipes/sides/',
        },
        'Eating Bird Food' : {
            'regex' : r'h2 class="post-summary__title"><a href="(\S*)"',
            'main course' : 'https://www.eatingbirdfood.com/category/meal-type/dinnerlunch/',
            'side dish' : 'https://www.eatingbirdfood.com/category/meal-type/dinnerlunch/sides/',
        },
        'Budget Bytes' : {
            'regex' : r'article class="post-summary post-summary--\S*"><a href="(\S*)" aria-label=',
            'main course' : 'https://www.budgetbytes.com/category/recipes/?fwp_by_course=main-dish',
            'side dish' : 'https://www.budgetbytes.com/category/recipes/side-dish/',
        },
        'Lean and Green Recipes' : {
            'regex' : r'h2 class="recipe-card-title"><a href="(\S*)"',
            'main course' : 'https://www.leanandgreenrecipes.net/recipes/category/main-course/',
            'side dish' : 'https://www.leanandgreenrecipes.net/recipes/category/accompaniment/',
        },
        'Minimalist Baker' : {
            'regex' : r'h3 class="post-summary__title"><a href="(\S*)"',
            'main course' : 'https://www.minimalistbaker.com/recipe-index/?fwp_recipe-type=entree',
            'side dish' : 'https://www.minimalistbaker.com/recipe-index/?fwp_recipe-type=salad',
        },
        'Gimme Some Oven' : {
            'regex' : r'a href="(\S*)" rel="bookmark" title="',
            'main course' : 'https://www.gimmesomeoven.com/all-recipes/?fwp_course=main-course',
            'side dish' : 'https://www.gimmesomeoven.com/all-recipes/?fwp_course=side-dishes',
        },
        'Half Baked Harvest' : {
            'regex' : r'h2 class="post-summary__title"><a href="(\S*)"',
            'main course' : 'https://www.halfbakedharvest.com/category/recipes/type-of-meal/main-course/',
            'side dish' : 'https://www.halfbakedharvest.com/category/recipes/type-of-meal/side-dishesvegetables/',
        },
        'Pinch of Yum' : {
            'regex' : r'<a class="block md:hover:opacity-60 space-y-2 flex flex-col" href="(\S*)">',
            'main course' : 'https://pinchofyum.com/recipes/dinner',
            'side dish' : 'https://pinchofyum.com/recipes/salad',
        },
        'Heather Christo' : {
            'regex' : r'<div class="title-label post">Recipe<\/div>\s*<a href="(\S*)"',
            'main course' : 'https://heatherchristo.com/category/recipes/?cat=10533&orderby=date',
            'side dish' : 'https://heatherchristo.com/category/recipes/?cat=200&orderby=date',
        },
        'Fit Slow Cooker Queen' : {
            'regex' : r'a href="(\S*)" class="excerpt-link" title=".*"><figure class="post-thumbnail"',
            'main course' : 'https://fitslowcookerqueen.com/category/slowcooker/',
            'side dish' : 'https://fitslowcookerqueen.com/category/salads/',
        },
        'Eat Live Run' : {
            'regex' : r'div class="post-img">\s*<a href="(\S*)"',
            'main course' : 'https://www.eatliverun.com/category/recipes-2/main-course-2/',
            'side dish' : 'https://www.eatliverun.com/category/recipes-2/side-dishes/',
        }
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
