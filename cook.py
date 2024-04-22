# IMPORT STANDARD MODULES
import json
import os
import random
import re
import smtplib
import ssl
import sys
import time
from collections import defaultdict
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import NoReturn

# IMPORT THIRD-PARTY MODULES
import requests
from dotenv import load_dotenv
from recipe_scrapers import scrape_me
from tqdm import tqdm

# IMPORT LISTS
from lists import veggies as VEGGIES
from lists import websites as WEBSITES


# check for debug mode or default to full mode
def check_debug_mode() -> bool:
    if len(sys.argv) != 1 and sys.argv[1] == "-d" or sys.argv[1] == "--debug":
        print("debug mode detected")
        return True
    return False


# if in debug mode, tell the user what keys (website title) are in the dictonary along with their index
def debug_list_selection() -> dict:
    print("The websites list supports the following sites:")
    websites_keys = list(WEBSITES.keys())
    for website in websites_keys:
        # note we increment by 1 to make output more user-friendly
        print(f"{websites_keys).index(website)+1}\t{website}")
    while True:
        try:
            # prompt user to enter the index of the list they wish to debug
            number = int(input("Which website would you like to debug? (#) "))
            # only accept input that would fall within the indicies of
            # the dictionary. Recall the increment
            if 1 <= number <= len(websites_keys):
                # account for the increment when saving user selection
                selection = list(WEBSITES)[number - 1]
                break
            raise ValueError
        except ValueError:
            print("I'm sorry, that wasn't a valid number.")
    # show user what they've selected before proceeding
    print(f"You've selectected to debug {selection}.")
    print("The dictionary entry is:")
    print(json.dumps(WEBSITES[selection], indent=4))
    return WEBSITES[selection]


# OPENING RESOURCE FILES
def save_json(filename: str, data: dict) -> NoReturn:
    with open(filename, "w") as f:
        json.dump(data, f)


def load_json(filename: str) -> dict:
    try:
        with open(filename) as f:
            data = json.load(f)
        if len(data) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f"Did not find {filename}, returning empty dictionary")
        return {}
    return data


def is_file_old(filename: str, age: int) -> bool:
    if os.path.isfile(filename):  # check that the file exists
        age = os.stat(filename).st_mtime
        age = (time.time() - age) / 3600  # convert age from seconds to hours
    if age < 12:
        return False
    return True


def remove_duplicates(urls):
    seen = set()
    return [x for x in urls if not (x in seen or seen.add(x))]


def remove_already_scraped(urls, used_recipes):
    return [url for url in urls if url not in used_recipes.keys()]


def remove_known_failures(urls, failed_recipes):
    return [url for url in urls if url not in failed_recipes.keys()]


def scrape_urls(urls, scraper, unused_recipes):
    for url in tqdm(urls):
        recipe_elements = scraper(url)
        if recipe_elements is not None:
            unused_recipes[url] = recipe_elements


def get_fresh_data(websites: dict) -> tuple:
    unused_main_recipes = defaultdict(list)
    unused_side_recipes = defaultdict(list)
    used_recipes = {}
    failed_recipes = {}

    main_urls, side_urls = [], []

    # GET LATEST URLS FROM HTML, separating entrees and sides
    print("Getting HTML")
    for site_info in tqdm(websites.values()):
        fresh_main_urls, fresh_side_urls = get_recipe_urls(site_info)
        main_urls.extend(fresh_main_urls)
        side_urls.extend(fresh_side_urls)

    # REMOVE DUPLICATES
    print("Removing duplicate urls")
    main_urls = remove_duplicates(main_urls)
    side_urls = remove_duplicates(side_urls)

    # REMOVE URLS ALREADY SCRAPED
    print("Removing urls already scraped")
    main_urls = remove_already_scraped(main_urls, used_recipes)
    side_urls = remove_already_scraped(side_urls, used_recipes)

    # REMOVE URLS ALREADY SENT
    print("Removing urls already sent")
    main_urls = remove_already_scraped(main_urls, used_recipes)
    side_urls = remove_already_scraped(side_urls, used_recipes)

    # REMOVE URLS THAT FAIL
    print("Removing URLs known to fail")
    main_urls = remove_known_failures(main_urls, failed_recipes)
    side_urls = remove_known_failures(side_urls, failed_recipes)
    print(f"main {len(main_urls)} new\nside {len(side_urls)} new")

    # USE HHURSEV'S RECIPE SCRAPER
    if main_urls:
        print("Scraping main course urls")
        scrape_urls(main_urls, scraper, unused_main_recipes)
    if side_urls:
        print("Scraping side dish urls")
        scrape_urls(side_urls, scraper, unused_side_recipes)

    print(f"main {len(unused_main_recipes)}\nside {len(unused_side_recipes)}")
    return unused_main_recipes, unused_side_recipes


# getting individual recipes
# get html for both pages of each site in the dictionary (main course href and side dish href)
def get_recipe_urls(selection: dict) -> tuple:
    main_html = get_html(selection["main course"])
    side_html = get_html(selection["side dish"])
    # using regex, match all instances of href's to individual recipes from the main course html
    main_urls = re.findall(selection["regex"], main_html)
    side_urls = re.findall(selection["regex"], side_html)
    cleanup_recipe_urls(main_urls)
    cleanup_recipe_urls(side_urls)
    return main_urls, side_urls


def get_html(website: str) -> str:
    h = {
        "user-agent":
        "mozilla/5.0 (macintosh; intel mac os x \
                10_11_5) applewebkit/537.36 (khtml, like gecko) \
                chrome/50.0.2661.102 safari/537.36"
    }
    try:
        response = requests.get(website, headers=h, timeout=5)
    except requests.exceptions.Timeout:
        print(f"{website} timed out. skipping.")
    return response.text


def cleanup_recipe_urls(urls: list) -> None:
    # Fix bad entries
    for url in urls[:]:
        if url.lower().startswith("/recipes/"):
            index = urls.index(url)
            urls[index] = f"https://www.leanandgreenrecipes.net{url}"

    # Remove bad entries
    bad_keywords = [
        "plan", "eggplant", "dishes", "best", "black friday", "how", "use",
        "ideas", "30-whole30-meals-in-30-minutes", "guide"
    ]
    urls[:] = [
        url for url in urls
        if not any(keyword in url.lower() for keyword in bad_keywords)
    ]


def scraper(url: str) -> dict:
    # scrapes URL and returns hhursev recipe_scraper elements
    try:
        scrape = scrape_me(url)
        recipe_elements = scrape.to_json()
        # replace returned canonical_url with the URL used as input for
        # the scraper if the two differ
        if recipe_elements["canonical_url"] != url:
            recipe_elements["canonical_url"] = url
        # Verify recipe_elements are valid before returning
        if "title" not in recipe_elements:
            raise AssertionError
        if "site_name" not in recipe_elements:
            raise AssertionError
        if "host" not in recipe_elements:
            raise AssertionError
        if "ingredients" not in recipe_elements:
            raise AssertionError
        if "instructions" not in recipe_elements:
            raise AssertionError
        if "image" not in recipe_elements:
            raise AssertionError
        if recipe_elements["ingredients"] == []:
            raise AssertionError
        if recipe_elements["instructions"] == "":
            raise AssertionError
        if recipe_elements["image"] is None:
            raise AssertionError
    except AssertionError:
        failed_recipes[url] = "FAILS"
        return None
    except Exception:
        failed_recipes[url] = "FAILS"
        return None
    # Everything passes, return the elements
    return recipe_elements


def get_random_proteins(recipes: dict) -> list:
    seafood = []
    landfood = []

    # Categorize recipes
    for recipe in recipes.values():
        try:
            categorize_recipe(recipe)
        except TypeError:
            print(f"Invalid recipe: {recipe}")

    # Shuffle the lists
    random.shuffle(landfood)
    random.shuffle(seafood)

    # Select three main courses at random
    if len(landfood) >= 2 and len(seafood) >= 1:
        landfood = random.sample(landfood, 2)
        seafood = random.sample(seafood, 1)
    elif len(landfood) >= 3 and len(seafood) == 0:
        landfood = random.sample(landfood, 3)
    else:
        print("Cannot select main courses. Exiting.")
        sys.exit()

    return landfood + seafood


def veggie_checker(meals: list, sides: dict, veggies: list = None) -> dict:
    # check that each main course recipe has sufficient veggies, if not, pull a recipe at random from the side dish list
    checked_meals = []
    for meal in meals:
        has_veggies = False
        key = next(iter(meal))
        for ingredient in meal[key]["ingredients"]:
            if any(veggie in ingredient.lower() for veggie in veggies):
                has_veggies = True
                break
        if not has_veggies:
            side = random.choice(list(sides.items()))
            side = {side[0]: side[1]}
            checked_meals.append({"type": "combo_main", "obj": meal})
            checked_meals.append({"type": "combo_side", "obj": side})
        else:
            checked_meals.append({"type": "single_main", "obj": meal})
    return checked_meals


def prettify(meals: dict, start: float) -> str:
    """Function converts meal object info into HTML for email
    receives a recipe object or dict of recipe objects"""
    print("Making HTML content from recipe objects.")

    # Import CSS stylesheet
    with open("style.css", "r") as f:
        css = f.read()

    html = f"{css}\t<body>\n"

    for info in meals:
        # get elements of hhursev recipe-scraper object dict
        elements = info["obj"][next(iter(info["obj"]))]

        title = elements["title"]
        if info["type"] == "combo_main":
            title = f"Main: {title}"
        elif info["type"] == "combo_side":
            title = f"Side: {title}"
        title = '\t\t<div class="card">\n' f"\t\t\t<h1>{title}</h1>\n"

        try:
            servings = f'\t\t\t<i>{elements["yields"]}'
        except Exception:
            servings = "\t\t\t<i>servings unknown"

        host = f' | {elements["site_name"]}</i>'

        title_servings = title + servings + host

        image = (
            '<div class="polaroid">\n'
            f'\t\t\t\t<img src={elements["image"]} alt="{elements["title"]} from {elements["host"]}" />\n'
            "\t\t\t</div>")

        ingredients = [
            "\t\t\t\t<li>" + i + "</li>" for i in elements["ingredients"]
        ]
        ingredients = "\n".join(ingredients)
        ingredients = ("\t\t\t<h2>Ingredients</h2>\n"
                       f"\t\t\t<ul>\n{ingredients}\n\t\t\t</ul>")

        instructions = (
            "\t\t\t<h2>Instructions</h2>\n"
            f'\t\t\t<p>{elements["instructions"]}</p>\n\t\t</div>\n')

        container = "\n".join(
            [title_servings, image, ingredients, instructions])
        html = html + container

    # some logic to handle calculating and displaying elapsed time
    elapsed_time = time.time() - start
    if elapsed_time > 1:
        elapsed_time = f"{elapsed_time:.2f} seconds"  # as time in seconds
    else:
        elapsed_time = (
            # convert from seconds to milliseconds
            f"{elapsed_time * 1000:.0f}ms")

    pretty = (
        f"{html}"
        f'\t\t<p style="color: #888;text-align: center;">Wowza! We found '
        f"{len(unused_main_recipes) + len(unused_side_recipes)} recipes! These {len(meals)} were "
        f"selected at random for your convenience and your family's delight. "
        f"It took {elapsed_time} to do this using v14."
        f"</p>\n</body>\n</html>")
    return pretty


def mailer(content: str, debug_mode: bool) -> NoReturn:
    """Function emails pretty formatted meals to recipents, can do BCC
    https://www.justintodata.com/send-email-using-python-tutorial/
    https://docs.python.org/3/library/email.examples.html"""
    # take environment variables from .env
    load_dotenv()

    msg = MIMEMultipart()
    msg["Subject"] = "Weekly Meals"
    # Set msg['Bcc'] to SENDER if in debug mode
    msg["Bcc"] = os.getenv("EMAIL_BCC")
    if debug_mode:
        msg["Bcc"] = os.getenv("EMAIL_SENDER")

    msg["From"] = os.getenv("EMAIL_SENDER")
    msg.attach(MIMEText(content, "html"))

    c = ssl.create_default_context()
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=c)
    server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
    server.send_message(msg)
    server.quit()


# START TIMER
START_TIME = time.time()

# FILENAME CONSTANTS
unused_mains_filename = "unused_mains_recipes.json"
unused_sides_filename = "unused_sides_recipes.json"
failed_filename = "failed_recipes.json"
used_filename = "used_recipes.json"

DEBUG_MODE = check_debug_mode()
if DEBUG_MODE:
    SELECTION = debug_list_selection()
    # redifine websites list for debug session
    WEBSITES = {"debugging": SELECTION}
    unused_main_recipes, unused_side_recipes, scraped_mains, scraped_sides = (
        {},
        {},
        {},
        {},
    )
    unused_main_recipes = load_json(unused_mains_filename)

else:
    # LOAD PREVIOUSLY COLLECTED DATA
    print("Loading previously collected data")
    unused_main_recipes = load_json(unused_mains_filename)
    unused_side_recipes = load_json(unused_sides_filename)
    failed_recipes = load_json(failed_filename)
    used_recipes = load_json(used_filename)

    # CHECK RECENCY OF PREVIOUSLY COLLECTED DATA
    if is_file_old(unused_mains_filename, 12):
        print(f'"{unused_mains_filename}" is old, getting fresh data')
        # SCRAPE FRESH DATA IF EXISTING DATA IS OLD
        unused_main_recipes, unused_side_recipes = get_fresh_data(WEBSITES)
        save_json(unused_mains_filename, unused_main_recipes)
        save_json(unused_sides_filename, unused_side_recipes)

    # SORT BY PROTEIN AND RETURN LIST OF THREE RANDOM MEALS
    print("Getting meals with select proteins at random")
    randomized_meals = get_random_proteins(unused_main_recipes)

    # ENSURE MEALS HAVE ADEQUATE VEGGIES OR ADD A SIDE
    print("Checking for veggies")
    MEALS = veggie_checker(randomized_meals, unused_side_recipes, VEGGIES)

    # PRETTYIFY THE MEALS INTO EMAILABLE HTML BODY
    print("Prettifying meals into HTML")
    PRETTY = prettify(MEALS, START_TIME)

    # SEND EMAIL
    print("Emailing recipients")
    mailer(PRETTY, DEBUG_MODE)

    # UPDATE THE RESOURCE FILES BEFORE SAVING OUT
    date = datetime.today().strftime("%Y-%m-%d")
    for MEAL in MEALS:
        try:
            URL = next(iter(MEAL["obj"]))
            used_recipes[URL] = date
            if URL in unused_main_recipes:
                del unused_main_recipes[URL]
            elif URL in unused_side_recipes:
                del unused_side_recipes[URL]
            else:
                raise KeyError
        except KeyError:
            print(f"{URL} was not in the main or side lists, so not removing")
    print(
        f"main {len(unused_main_recipes)} final\nside {len(unused_side_recipes)} final"
    )

    # SAVE OUT DICTIONARIES AS FILES FOR REUSE
    print("Saving out files")
    save_json(unused_mains_filename, unused_main_recipes)
    save_json(unused_sides_filename, unused_side_recipes)
    save_json(failed_filename, failed_recipes)
    save_json(used_filename, used_recipes)
