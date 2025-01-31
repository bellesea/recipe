import streamlit as st
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import os
import requests
from googlemaps import Client

# Part A: Getting Data from an API
def fetch_nutrition_data(ingredient: str) -> Dict:
    """
    Fetch nutrition data for a given ingredient from the USDA FoodData Central API.
    """
    api_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    api_key = (
        os.environ.get("USDA_API_KEY")
        if os.environ.get("USDA_API_KEY")
        else st.secrets["USDA_API_KEY"]
    )
    params = {
        "query": ingredient,
        "api_key": api_key,
        "pageSize": 1,
    }
    response = requests.get(api_url, params=params, verify=False)
    if response.status_code == 200:
        data = response.json()
        return data.get("foods", [{}])[
            0
        ]  # Return the first result or an empty dictionary
    else:
        st.error("Failed to fetch data from USDA API.")
        return {}


# Part B: Scraping Data from a Website
def scrape_recipes(query: str) -> List[Dict]:
    """
    Scrape recipes for a given query from a public recipe website (e.g., AllRecipes).
    """
    base_url = f"https://www.allrecipes.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(base_url, headers=headers, verify=False)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        recipes = []
        for card in soup.select(
            "a.comp.mntl-card-list-card--extendable"
        ):  # Updated selector based on the provided HTML structure
            title_elem = card.select_one(".card__title-text")
            if title_elem:
                title = title_elem.text.strip()
                link = card["href"]  # Use the href attribute of the <a> tag
                recipes.append({"title": title, "link": link})
        return recipes
    elif response.status_code == 404:
        st.error(
            "The requested page was not found (404). Please check the URL structure."
        )
        return []
    else:
        st.error(
            f"Failed to scrape data from the recipe website. Status code: {response.status_code}"
        )
        return []


def get_ingredients(recipe):
    base_url = f"{recipe['link']}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(base_url, headers=headers, verify=False)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        ingredients = soup.find_all(
            "li", class_="mm-recipes-structured-ingredients__list-item"
        )
        ingredient_list = []
        calorie = soup.find_all(
            "td",
            class_="mm-recipes-nutrition-facts-summary__table-cell text-body-100-prominent",
        )

        if calorie:
            calorie_value = calorie[0].get_text(strip=True)
            recipe["calorie"] = calorie_value
        else:
            recipe["calorie"] = None

        for ingredient in ingredients:
            # quantity = ingredient.select_one("span[data-ingredient-quantity]").text.strip()
            # unit = ingredient.select_one("span[data-ingredient-unit]").text.strip()
            name = ingredient.select_one("span[data-ingredient-name]").text.strip()
            ingredient_list.append(name)

        recipe["ingredient"] = ingredient_list
    elif response.status_code == 404:
        st.error(
            "The requested page was not found (404). Please check the URL structure."
        )
    else:
        st.error(
            f"Failed to scrape data from the recipe website. Status code: {response.status_code}"
        )

    return recipe

def get_current_location(google_api_key):
    gmaps = Client(key=google_api_key)
    geocode_result = gmaps.geolocate()
    location = geocode_result.get("location", {})
    return location.get("lat"), location.get("lng")

def search_google_restaurants(google_api_key, latitude, longitude, radius=8047):  # 5 miles in meters
    gmaps = Client(key=google_api_key)
    places_result = gmaps.places_nearby(
        location=(latitude, longitude),
        radius=radius,
        type="restaurant"
    )
    return places_result.get("results", [])