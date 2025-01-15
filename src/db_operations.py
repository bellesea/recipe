from sqlalchemy.orm import Session
from src.models import Recipe, Ingredient
from src.data_fetch import get_ingredients, fetch_nutrition_data
import streamlit as st


def store_data_in_db(db: Session, recipe: dict):
    """
    Store recipe and its ingredients in the database.
    """
    # Check if the recipe already exists
    existing_recipe = db.query(Recipe).filter_by(link=recipe["link"]).first()
    if existing_recipe:
        print(f"Recipe '{recipe['title']}' already exists in the database.")
        return "saved_prev"

    # Fetch ingredients
    recipe = get_ingredients(recipe)

    # Create and store a new Recipe
    new_recipe = Recipe(
        title=recipe["title"],
        link=recipe["link"],
        calorie=recipe["calorie"],
    )
    db.add(new_recipe)
    db.flush()  # Flush to generate an autoincremented recipe_id for the new recipe

    # Store ingredients
    for ingredient_name in recipe["ingredient"]:
        nutrition_data = fetch_nutrition_data(ingredient_name)
        ingredient = Ingredient(
            recipe_id=new_recipe.recipe_id,  # Use the autoincremented ID
            ingredient=ingredient_name,
            nutrition_data=str(nutrition_data),
        )
        db.add(ingredient)

    db.commit()


def fetch_ingredients_with_nutrition(db: Session, recipe_id: str):
    """
    Fetch ingredients and their nutrition data for a given recipe ID.
    """
    ingredients = db.query(Ingredient).filter_by(recipe_id=recipe_id).all()

    for ingredient in ingredients:
        nutrition_data = eval(ingredient.nutrition_data)
        st.write(f"Ingredient: {ingredient.ingredient}")
        if nutrition_data:
            significant_nutrients = [
                f"{nutrient['nutrientName']}: {nutrient['value']} {nutrient['unitName']}"
                for nutrient in nutrition_data.get("foodNutrients", [])
                if int(nutrient["value"]) > 0
            ]
            st.write(
                ", ".join(significant_nutrients) or "No significant nutrients found."
            )
        else:
            st.write("No nutrition data available.")
