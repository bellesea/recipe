from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base
import pandas as pd

Base = declarative_base()  # create base Python class for models to inherit from

"""
┌─────────────────────────────┐          ┌─────────────────────────────────┐
│           recipe            │          │           ingredient            │
├─────────────────────────────┤          ├─────────────────────────────────┤
│ recipe_id (PK, Integer)     │  1    *  │ ingredient_id (PK, Integer)    │
│ title (String, NOT NULL)    │ <------> │ recipe_id (FK -> recipe_id)    │
│ link (String, NOT NULL,     │          │ ingredient (String, NOT NULL)  │
│             UNIQUE)         │          │ nutrition_data (Text)          │
│ calorie (Integer)           │          └─────────────────────────────────┘
└─────────────────────────────┘
"""
class Recipe(Base):
    __tablename__ = "recipe"
    recipe_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False, unique=True)
    calorie = Column(Integer, nullable=True)
    ingredients = relationship("Ingredient", back_populates="recipe")

    @staticmethod
    def get_recipe_by_ingredients(db: Session, ingredients: list) -> pd.DataFrame:
        """
        Returns Pandas dataframe with all recipes that have an ingredient in the Ingredients list
        Sorted by the "match rate", i.e. how many ingredients match

        (not the most optimal for now...)
        """
        query = (
            db.query(Recipe)
            .join(Ingredient)
            .filter(Ingredient.ingredient.in_(ingredients))
        )
        recipes = query.all()

        results = []
        for recipe in recipes:
            matched_ingredients = [
                ing for ing in recipe.ingredients if ing.ingredient in ingredients
            ]
            results.append(
                {
                    "recipe_id": recipe.recipe_id,
                    "title": recipe.title,
                    "link": recipe.link,
                    "calorie": recipe.calorie,
                    "match_rate": len(matched_ingredients) / len(ingredients),
                }
            )
        if results:
            return pd.DataFrame(results).sort_values(by="match_rate", ascending=False)
        else:
            return pd.DataFrame(
                columns=["recipe_id", "title", "link", "calorie", "match_rate"]
            )

    @staticmethod
    def get_recipe_by_calorie(db: Session, calorie: Integer) -> pd.DataFrame:
        """
        Returns Pandas dataframe with all recipes <= given calorie
        """
        query = db.query(Recipe).filter(Recipe.calorie <= calorie)
        recipes = query.all()
        results = [
            {
                "recipe_id": r.recipe_id,
                "title": r.title,
                "link": r.link,
                "calorie": r.calorie,
            }
            for r in recipes
        ]
        return pd.DataFrame(results).sort_values(by="calorie")

    @staticmethod
    def get_all_recipes(db: Session) -> pd.DataFrame:
        """
        Returns Pandas dataframe with all recipes
        """
        recipes = db.query(Recipe).all()
        results = [
            {
                "recipe_id": r.recipe_id,
                "title": r.title,
                "link": r.link,
                "calorie": r.calorie,
            }
            for r in recipes
        ]
        return pd.DataFrame(results)

    @staticmethod
    def get_by_recipe_id(db, recipe_id):
        """retrieves recipe obj given recipe_id"""
        return db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()

    @staticmethod
    def delete_by_recipe_id(db, recipe_id):
        """Deletes recipe obj given recipe_id"""
        recipe = Recipe.get_by_recipe_id(db, recipe_id)
        if recipe:
            db.delete(recipe)
            db.commit()


class Ingredient(Base):
    __tablename__ = "ingredient"
    ingredient_id = Column(Integer, primary_key=True)
    recipe_id = Column(String, ForeignKey("recipe.recipe_id"), nullable=False)
    ingredient = Column(String, nullable=False)
    nutrition_data = Column(Text, nullable=True)
    recipe = relationship("Recipe", back_populates="ingredients")

    @staticmethod
    def get_ingredients_by_recipe_id(db: Session, recipe_id: str):
        return db.query(Ingredient).filter(Ingredient.recipe_id == recipe_id).all()
