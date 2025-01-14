import streamlit as st
import requests
import sqlite3
from bs4 import BeautifulSoup
from typing import List, Dict
import uuid

# Part A: Getting Data from an API
def fetch_nutrition_data(ingredient: str) -> Dict:
    """
    Fetch nutrition data for a given ingredient from the USDA FoodData Central API.
    """
    api_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "query": ingredient,
        "api_key": "", # ADD API KEY
        "pageSize": 1
    }
    response = requests.get(api_url, params=params, verify=False)
    if response.status_code == 200:
        data = response.json()
        return data.get("foods", [{}])[0]  # Return the first result or an empty dictionary
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
        for card in soup.select("a.comp.mntl-card-list-card--extendable"):  # Updated selector based on the provided HTML structure
            title_elem = card.select_one(".card__title-text")
            if title_elem:
                title = title_elem.text.strip()
                link = card['href']  # Use the href attribute of the <a> tag
                recipes.append({"title": title, "link": link})
        return recipes
    elif response.status_code == 404:
        st.error("The requested page was not found (404). Please check the URL structure.")
        return []
    else:
        st.error(f"Failed to scrape data from the recipe website. Status code: {response.status_code}")
        return []


def get_ingredients(recipe):
    base_url = f"{recipe['link']}"
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(base_url, headers=headers, verify=False)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        ingredients = soup.find_all("li", class_="mm-recipes-structured-ingredients__list-item")
        ingredient_list = []
        calorie = soup.find_all("td", class_="mm-recipes-nutrition-facts-summary__table-cell text-body-100-prominent")

        if calorie:
            calorie_value = calorie[0].get_text(strip=True)
            recipe['calorie'] = calorie_value
        else:
            recipe['calorie'] = None
        
        for ingredient in ingredients:
            # quantity = ingredient.select_one("span[data-ingredient-quantity]").text.strip()
            # unit = ingredient.select_one("span[data-ingredient-unit]").text.strip()
            name = ingredient.select_one("span[data-ingredient-name]").text.strip()
            ingredient_list.append(name)

        recipe["ingredient"] = ingredient_list      
    elif response.status_code == 404:
        st.error("The requested page was not found (404). Please check the URL structure.")
    else:
        st.error(f"Failed to scrape data from the recipe website. Status code: {response.status_code}")

    return recipe


# Part C: Combining Data and Storing in a Database
def initialize_database():
    """
    Create or connect to a SQLite database and set up tables for recipes and ingredients.
    """
    conn = sqlite3.connect("new_recipes2.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            recipe_id INTEGER,
            calorie INT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient TEXT,
            nutrition_data TEXT,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id)
        )
    """)
    conn.commit()
    conn.close()

def store_data_in_db(recipe: Dict):
    """
    Store recipe and ingredient data into the SQLite database.
    """
    conn = sqlite3.connect("new_recipes2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recipes WHERE title = ? AND link = ?", (recipe['title'], recipe['link']))
    if cursor.fetchone()[0] > 0:
        print(f"Recipe '{recipe['title']}' already exists in the database.")
        conn.close()
        return 'saved_prev' # Skip the rest if the recipe already exists

    recipe = get_ingredients(recipe)
    recipe_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO recipes (title, link, recipe_id, calorie) VALUES (?, ?, ?, ?)", (recipe['title'], recipe['link'], recipe_id, recipe['calorie']))
    
    for ingredient in recipe["ingredient"]:
        nutrition_data = fetch_nutrition_data(ingredient)
        cursor.execute("INSERT INTO ingredients (recipe_id, ingredient, nutrition_data) VALUES (?, ?, ?)",
                       (recipe_id, ingredient, str(nutrition_data)))
    conn.commit()
    conn.close()

# Part D: Helper functions for streamlit
def fetch_ingredients_with_nutrition(recipe_id: int):
    """
    Fetch all ingredients for a given recipe ID and display the ingredient with nutrition data.
    """
    conn = sqlite3.connect("new_recipes2.db")
    cursor = conn.cursor()

    # Query to fetch ingredients and nutrition data for the given recipe ID
    cursor.execute("SELECT ingredient, nutrition_data FROM ingredients WHERE recipe_id = ?", (recipe_id,))
    ingredients = cursor.fetchall()

    if ingredients:
        for ingredient, nutrition_data in ingredients:
            nutrition_data = eval(nutrition_data)
            if nutrition_data:
                significant_nutrients = []

                for nutrient in nutrition_data['foodNutrients']:
                    if int(nutrient['value']) > 0:
                        # st.write(nutrient)
                        significant_nutrients.append({
                            'nutrientName': nutrient['nutrientName'],
                            'value': nutrient['value'],
                            'unit': nutrient['unitName']
                        })


                st.write(f"Ingredient: {ingredient}")
                if significant_nutrients:
                    total_nutrients = ""
                    for nutrient in significant_nutrients:
                        total_nutrients += f"{nutrient['nutrientName']}: {nutrient['value']} {nutrient['unit']}"
                    
                    st.write(total_nutrients)
                else:
                    st.write("No significant nutrients found.")
            else:
                st.write("No nutrition data")
    else:
        st.write("No ingredients found for this recipe.")

    conn.close()

@st.fragment
def show_recipe(title, link, recipe_id, calorie):
    state_key = f"recipe_{recipe_id}"
    if state_key not in st.session_state:
        st.session_state[state_key] = True
    
    if st.session_state[state_key]:
        st.write(f"**{title}**: [View Recipe]({link}) | {calorie} calories")
        with st.expander("Get ingredient and nutrition information"):
            fetch_ingredients_with_nutrition(recipe_id)
                
        if st.button(f"Delete Recipe :no_entry_sign:", key=recipe_id):  # Check if the checkbox is selected
            st.info("Deleting the recipe...")
            conn = sqlite3.connect("new_recipes2.db")
            cursor = conn.cursor()
            
            # Delete ingredients where recipe_id matches
            cursor.execute('DELETE FROM ingredients WHERE recipe_id = ?', (recipe_id,))
            
            # Delete the recipe where recipe_id matches
            cursor.execute('DELETE FROM recipes WHERE recipe_id = ?', (recipe_id,))
            
            # Commit the changes
            conn.commit()
            conn.close()
            st.success("Recipe deleted")
            st.session_state[state_key] = False
            # st.rerun()
    else:
        st.write("HII")
            
@st.fragment
def find_max_calorie():
    max_calories = st.slider("Select maximum calories", 0, 1000, 500)
    # Fetch the recipe data
    conn = sqlite3.connect("new_recipes2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, link, recipe_id, calorie FROM recipes")
    rows = cursor.fetchall()
    conn.close()
    st.subheader("Stored Recipes:")
    items = 0
    for title, link, recipe_id, calorie in rows:
        if calorie <= max_calories:
            items += 1
            st.write(f"**{title}**: [View Recipe]({link}) | {calorie} calories")

    if items == 0:
        st.warning("No recipes found with the selected calorie limit.")

@st.fragment
def add_recipe(recipe):
# Display recipe title and link    
    store_recipe = st.checkbox(f"Save **{recipe['title']}**: [View Recipe]({recipe['link']}) :yum:", key=recipe['link'])
    
    if store_recipe:  # Check if the checkbox is selected
        st.info("Storing recipe and ingredients in the database...")
        status = store_data_in_db(recipe)
        if (status == 'saved_prev'):
            st.info("Recipe already stored previously!")
        else:
            st.success(f"Stored recipe: {recipe['title']} successfully!")

@st.fragment
def find_recipe():
    st.session_state.find_recipe_displayed = False
    # Get the desired ingredients from the user
    desired_ingredients = st.text_input("Enter desired ingredients (comma-separated):", "").split(",")
    # Connect to the database
    conn = sqlite3.connect("new_recipes2.db")
    cursor = conn.cursor()
    
    # Prepare the SQL query using the `LIKE` operator for partial matches
    query = f"""
        SELECT r.title, r.link 
        FROM recipes r 
        JOIN ingredients i ON r.recipe_id = i.recipe_id 
        WHERE {" OR ".join("i.ingredient LIKE ?" for _ in desired_ingredients)}
        GROUP BY r.recipe_id
    """
    
    # Add wildcards (%) for partial matching
    search_terms = [f"%{ingredient.strip()}%" for ingredient in desired_ingredients if ingredient.strip()]
    
    # Execute the query
    if search_terms:
        cursor.execute(query, search_terms)
        results = cursor.fetchall()
        st.session_state.find_recipe_displayed = True
    else:
        results = []
    
    # Close the database connection
    conn.close()
    
    # Display the results
    if results:
        for title, link in results:
            st.write(f"**{title}**: [View Recipe]({link})")
    else:
        if st.session_state.find_recipe_displayed:
            st.warning("No recipes found matching the desired ingredients.")


# Part E: Creating the Web Application
def main():
    st.title("All in one meal planning app")

    st.header("Add Recipes")
    
    # Initialize the database
    initialize_database()

   # Search Bar
    query = st.text_input("Enter a recipe query (e.g., 'vegetarian'):", "vegetarian")

    st.session_state.recipes_displayed = False

    # Display "Search" or "Done" button based on the state
    if st.session_state.recipes_displayed == False:
        if st.button("Search :eyes:"):
            st.subheader("Fetching recipes...")
            st.session_state.recipes_displayed = True
            recipes = scrape_recipes(query)
            if recipes:
                for recipe in recipes:
                    add_recipe(recipe)
            else:
                st.warning("No recipes found for your query. Try another search term.")
            if st.button("Done &#x2705;"):
                st.session_state.recipes_displayed = False
                st.rerun()  # Rerun the app to clear the page

    # Search the Database
    st.header("My Recipes")
    st.session_state.my_recipes_displayed = False
    if st.button("Show my recipes"):
        st.session_state.my_recipes_displayed = True
        conn = sqlite3.connect("new_recipes2.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, link, recipe_id, calorie FROM recipes")
        rows = cursor.fetchall()
        conn.close()
        st.subheader("Stored Recipes:")
        for title, link, recipe_id, calorie in rows:
            show_recipe(title, link, recipe_id, calorie)
        if st.button("Hide my recipes :see_no_evil:"):
                st.session_state.recipes_displayed = False
                st.rerun()  # Rerun the app to clear the page

    # Provide Recommendations
    st.header("Recipe Recommendation")
    if st.button("Find recipe"):
        find_recipe()
        find_max_calorie()

if __name__ == "__main__":
    main()
