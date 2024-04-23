#!/usr/bin/env python3

# IMPORT STANDARD MODULES
import argparse
import json
import random
import re
import smtplib
import ssl
import sys
import os
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# IMPORT THIRD-PARTY MODULES
import requests
from dotenv import load_dotenv
from recipe_scrapers import scrape_me
from tqdm import tqdm

# IMPORT LISTS
from lists import websites, veggies


# check for debug mode or default to full mode
def check_debug_mode() -> bool:
    parser = argparse.ArgumentParser(description="Check for debug mode")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        print("Debug mode detected")
        return True
    return False


# if in debug mode, tell the user what keys (website title) are in the dictonary along with their index
def debug_list_selection() -> dict:
    print("The websites list supports the following sites:")
    for n, website in enumerate(websites):
        # note we increment by 1 to make output more user-friendly
        print(f"{n + 1}\t{website}")
    while True:
        try:
            # prompt user to enter the index of the list they wish to debug
            number = int(input("Which website would you like to debug? (#) "))
            # only accept input that would fall within the indicies of
            # the dictionary. Recall the increment from above
            if 0 < number < len(websites) + 1:
                # account for the increment when saving user selection
                selection = list(websites)[number - 1]
                break
            raise ValueError
        except ValueError:
            print("I'm sorry, that wasn't a valid number.")
    # show user what they've selected before proceeding
    print(f"You've selectected to debug {selection}.")
    print("The dictionary entry is:")
    print(json.dumps(websites[selection], indent=4))
    return websites[selection]

# OPENING RESOURCE FILES
def save_json(filename: str, data: dict) -> None:
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


def get_fresh_data(websites: dict) -> tuple:
    # GET LATEST URLS FROM HTML, separating entrees and sides
    main_urls = []
    print("Getting HTML")
    for site_info in tqdm(websites.values()):
        fresh_main_urls = get_recipe_urls(site_info)
        main_urls.extend(fresh_main_urls)

    # REMOVE DUPLICATES
    print("Removing duplicate urls")
    main_urls = list(set(main_urls))

    # REMOVE URLS ALREADY SCRAPED
    print("Removing urls already scraped")
    main_urls = [url for url in main_urls if url not in unused_main_recipes.keys()]

    # REMOVE URLS ALREADY SENT
    print("Removing urls already sent")
    main_urls = [url for url in main_urls if url not in used_recipes.keys()]

    # REMOVE URLS THAT FAIL
    print("Removing URLs known to fail")
    main_urls = [url for url in main_urls if url not in failed_recipes.keys()]
    print(f"main {len(main_urls)} new")

    # USE HHURSEV'S RECIPE SCRAPER
    if len(main_urls) > 0:
        print(main_urls)
        print("Scraping main course urls")
        for url in tqdm(main_urls):
            recipe_elements = scraper(url)
            if recipe_elements is not None:
                unused_main_recipes[url] = recipe_elements
    del main_urls
    print(f"main {len(unused_main_recipes)}")
    return unused_main_recipes


# getting individual recipes
# get html for both pages of each site in the dictionary (main course href and side dish href)
def get_recipe_urls(selection: dict) -> tuple:
    main_html = get_html(selection["main course"])
    # using regex, match all instances of href's to individual recipes from the main course html
    main_urls = re.findall(selection["regex"], main_html)
    cleanup_recipe_urls(main_urls)
    return main_urls


def get_html(website: str) -> str:
    h = {
        "user-agent": "mozilla/5.0 (macintosh; intel mac os x \
                10_11_5) applewebkit/537.36 (khtml, like gecko) \
                chrome/50.0.2661.102 safari/537.36"
    }
    try:
        with requests.get(website, headers=h, timeout=5) as response:
            return response.text
    except requests.exceptions.Timeout:
         # Handle timeout gracefully
        print(f"{website} timed out. skipping.")


def cleanup_recipe_urls(urls: list[str]) -> None:
    # Create a list to store indices of bad entries
    bad_indicies = []

    for n, url in enumerate(urls):
        # Fix bad entries
        if url.lower()[:9] == "/recipes/":
            urls[n] = f"https://www.leanandgreenrecipes.net{url}"
        # Identify bad entries
        if (
            ("plan" in url.lower() or "eggplant" in url.lower())
            or (
                "dishes" in url.lower()
                and ("/recipes/" in url.lower() or "best" in url.lower())
            )
            or ("black" in url.lower() and "friday" in url.lower())
            or ("how" in url.lower() and "use" in url.lower())
            or ("dishes" in url.lower() or "ideas" in url.lower())
            or "guide" in url.lower()
        ):
            # Add the index of bad entry to the list
            bad_indicies.append(n)

    # Remove bad entries in reverse order to avoid index shifting
    for i in reversed(bad_indicies):
        del urls[i]

def scraper(url: str) -> dict | None:
    # scrapes URL and returns hhursev recipe_scraper elements
    try:
        scrape = scrape_me(url, wild_mode=True)
        recipe_elements = scrape.to_json()
        # Replace returned canonical_url with the input URL if they differ
        if recipe_elements["canonical_url"] != url:
            recipe_elements["canonical_url"] = url
        # Verify recipe_elements are valid before returning
        required_keys = ["title", "site_name", "host", "ingredients", "instructions", "image"]
        for key in required_keys:
            assert key in recipe_elements
            if key == "ingredients":
                assert recipe_elements[key] != []
            elif key == "instructions":
                assert recipe_elements[key] != ""
            elif key == "image":
                assert recipe_elements[key] is not None
    except (AssertionError, Exception):
        failed_recipes[url] = "FAILS"
        return None
    # Everything passes, return the elements
    return recipe_elements


def get_random_proteins(recipes: dict) -> list:
    # randomizing recipe selection
    seafood, landfood = [], []
    for recipe in recipes.items():
        try:
            for i in recipe[1]["ingredients"]:
                i = i.lower()
                if "scallops" in i or "salmon" in i or "shrimp" in i or "tuna" in i:
                    seafood.append({recipe[0]: recipe[1]})
                elif (
                    "chickpea" in i
                    or "chicken" in i
                    or "turkey" in i
                    or "pork" in i
                    or "tofu" in i
                ):
                    landfood.append({recipe[0]: recipe[1]})
                else:
                    pass
        except TypeError:
            print(f"needs removed: {recipe}, not valid recipe")
    # shuffle the lists
    random.shuffle(landfood)
    random.shuffle(seafood)
    # select three main courses at random
    if len(landfood) > 1 and len(seafood) > 0:
        landfood = random.sample(landfood, 2)
        seafood = random.sample(seafood, 1)
    elif len(landfood) > 2 and len(seafood) == 0:
        landfood = random.sample(landfood, 3)
    else:
        print(
            "Somehow we ended up with no seafood meals and two or less "
            "landfood meals. Can't do anything with nothing. Exiting."
        )
        sys.exit()
    return landfood + seafood


def veggie_checker(meals: list, sides: dict, veggies: list = veggies) -> dict:
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
        meal = info["obj"][
            next(iter(info["obj"]))
        ]  # where meal is elements of hhursev recipe-scraper object dict

        title = meal["title"]
        if info["type"] == "combo_main":
            title = f"Main: {title}"
        elif info["type"] == "combo_side":
            title = f"Side: {title}"
        title = '\t\t<div class="card">\n' f"\t\t\t<h1>{title}</h1>\n"

        try:
            servings = f'\t\t\t<i>{meal["yields"]}'
        except Exception:
            servings = "\t\t\t<i>servings unknown"

        host = f' | {meal["site_name"]}</i>'

        title_servings = title + servings + host

        image = (
            '<div class="polaroid">\n'
            f'\t\t\t\t<img src={meal["image"]} alt="{meal["title"]} from {meal["host"]}" />\n'
            "\t\t\t</div>"
        )

        ingredients = ["\t\t\t\t<li>" + i + "</li>" for i in meal["ingredients"]]
        ingredients = "\n".join(ingredients)
        ingredients = (
            "\t\t\t<h2>Ingredients</h2>\n" f"\t\t\t<ul>\n{ingredients}\n\t\t\t</ul>"
        )

        instructions = (
            "\t\t\t<h2>Instructions</h2>\n"
            f'\t\t\t<p>{meal["instructions"]}</p>\n\t\t</div>\n'
        )

        container = "\n".join([title_servings, image, ingredients, instructions])
        html = html + container

    # some logic to handle calculating and displaying elapsed time
    elapsed_time = time.time() - start
    if elapsed_time > 1:
        elapsed_time = f"{elapsed_time:.2f} seconds"  # as time in seconds
    else:
        elapsed_time = (
            f"{elapsed_time * 1000:.0f}ms"  # convert from seconds to milliseconds
        )

    pretty = (
        f"{html}"
        f'\t\t<p style="color: #888;text-align: center;">Wowza! We found '
        f"{len(unused_main_recipes) + len(unused_side_recipes)} recipes! These {len(meals)} were "
        f"selected at random for your convenience and your family's delight. "
        f"It took {elapsed_time} to do this using v14.1."
        f"</p>\n</body>\n</html>"
    )
    return pretty


def mailer(content: str, debug_mode: bool) -> None:
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
    # server.set_debuglevel(1)  # uncomment this line for more verbose terminal output
    server.send_message(msg)
    server.quit()


# START TIMER
start_time = time.time()

# FILENAME CONSTANTS
unused_mains_filename = "unused_mains_recipes.json"
unused_sides_filename = "unused_sides_recipes.json"
failed_filename = "failed_recipes.json"
used_filename = "used_recipes.json"

debug_mode = check_debug_mode()
if debug_mode:
    selection = debug_list_selection()
    websites = {"debugging": selection}  # redifine websites list for debug session
    unused_main_recipes, unused_side_recipes, scraped_mains, scraped_sides = (
        {},
        {},
        {},
        {}
    )
    unused_main_recipes = load_json(unused_mains_filename)

else:
    # LOAD PREVIOUSLY COLLECTED DATA
    print("Loading previously collected data")
    unused_main_recipes = load_json(unused_mains_filename)
    failed_recipes = load_json(failed_filename)
    used_recipes = load_json(used_filename)

    # CHECK RECENCY OF PREVIOUSLY COLLECTED DATA
    # for this instance, files are considered old after 12 hours
    if is_file_old(unused_mains_filename, 12):
        print(unused_mains_filename, 'is old, getting fresh data')
        # SCRAPE FRESH DATA IF EXISTING DATA IS OLD
        unused_main_recipes = get_fresh_data(websites)
        save_json(unused_mains_filename, unused_main_recipes)

    # SORT BY PROTEIN AND RETURN LIST OF THREE RANDOM MEALS
    print("Getting meals with select proteins at random")
    if len(unused_main_recipes) >= 3:
        meals = random.sample(list(unused_main_recipes), 3)
    else:
        print('not enough meals to proceed. exiting.')
        sys.exit()

    """
    # ENSURE MEALS HAVE ADEQUATE VEGGIES OR ADD A SIDE
    print("Checking for veggies")
    meals = veggie_checker(randomized_meals, unused_side_recipes)
    """

    # PRETTYIFY THE MEALS INTO EMAILABLE HTML BODY
    print("Prettifying meals into HTML")
    pretty = prettify(meals, start_time)

    # SEND EMAIL
    print("Emailing recipients")
    mailer(pretty, debug_mode)

    # UPDATE THE RESOURCE FILES BEFORE SAVING OUT
    date = datetime.today().strftime("%Y-%m-%d")
    for meal in meals:
        try:
            url = next(iter(meal["obj"]))
            used_recipes[url] = date
            if url in unused_main_recipes:
                del unused_main_recipes[url]
            else:
                raise KeyError
        except KeyError:
            print(f"{url} was not in the main or side lists, so not removing")
    print(
        f"main {len(unused_main_recipes)} final"
    )

    # SAVE OUT DICTIONARIES AS FILES FOR REUSE
    print("Saving out files")
    save_json(unused_mains_filename, unused_main_recipes)
    save_json(failed_filename, failed_recipes)
    save_json(used_filename, used_recipes)
