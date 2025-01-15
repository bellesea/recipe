import streamlit as st
from src.config import Session
from src.data_fetch import scrape_recipes
from src.db_operations import store_data_in_db, fetch_ingredients_with_nutrition
from src.models import Recipe

st.title("All in one meal planning app")
st.write(
    "If this is your first time, go to the 'Browse More Recipes' Section to add new recipes!"
)
st.header("My Stored Recipes  ღ'ᴗ'ღ")

###### Filter Recipes by Calorie Limit ######
st.subheader("Filter Recipes by Calorie")
calorie_limit = st.slider("Select maximum calories", 0, 1000, 500)

if st.button("Find Recipes Under Calorie Limit"):
    with Session() as db:
        # Check if the recipe table is not empty
        if db.query(Recipe).count() > 0:
            recipes = Recipe.get_recipe_by_calorie(db, calorie_limit)
            if not recipes.empty:
                st.dataframe(recipes)
            else:
                st.warning("No recipes found under this calorie limit.")
        else:
            st.warning("No recipes available to filter.")

###### Fetch Ingredients and Nutrition ######
st.subheader("Fetch Ingredients and Nutrition Data")
recipe_id = st.text_input("Enter Recipe ID:")

if st.checkbox("Fetch Ingredients"):
    if recipe_id:
        with Session() as db:
            fetch_ingredients_with_nutrition(db, recipe_id)
    else:
        st.warning("Please enter a valid Recipe ID.")

###### st.subheader("Recipe Recommendation by Ingredient") ######
desired_ingredients = st.text_input(
    "Enter desired ingredients (comma-separated):", ""
).split(",")
with Session() as db:
    recipes_df = Recipe.get_recipe_by_ingredients(db, desired_ingredients)
    st.dataframe(recipes_df)


###### Show All Recipes ######
st.subheader("All Recipes")
if st.checkbox("Show ALL My Recipes"):
    with Session() as db:
        recipes = Recipe.get_all_recipes(db)
        if not recipes.empty:
            st.subheader("Stored Recipes:")
            st.dataframe(recipes)
        else:
            st.warning("No recipes stored yet!")

###### Search and Add Recipes ######
st.header("Browse More Recipes")
st.write("& add them to your list!")
query = st.text_input("Enter a recipe query (e.g., 'vegetarian'):", "vegetarian")

# Initialize session state for buttons
if "search_clicked" not in st.session_state:
    st.session_state.search_clicked = False

if "add_recipe_clicked" not in st.session_state:
    st.session_state.add_recipe_clicked = False

# Handle Search Button
if st.button("Search :eyes:"):
    st.session_state.search_clicked = True
    st.session_state.add_recipe_clicked = False

if st.session_state.search_clicked:
    st.subheader("Fetching recipes...")
    recipes = scrape_recipes(query)  # Fetch recipes
    if recipes:
        with Session() as db:
            for recipe in recipes:
                st.markdown(f"**{recipe['title']}**")
                st.markdown(f"[View Recipe]({recipe['link']})")
                if st.button(
                    f"Add {recipe['title']} to My Recipes", key=f"add_{recipe['link']}"
                ):
                    st.caption("takes a while (api call...)")
                    st.session_state.add_recipe_clicked = True
                    recipe["recipe_id"] = recipe["link"].split("/")[-1]
                    store_data_in_db(db, recipe)
                    st.success(f"{recipe['title']} has been added to your recipes!")
                    st.session_state.add_recipe_clicked = False
    else:
        st.warning("No recipes found for your query. Try another search term.")
