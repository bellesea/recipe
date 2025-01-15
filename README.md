# CS 248 Example Code
Work In Process
## Getting Started
Clone the repository and cd into it.

1. Install the required packages:
```
pip install -r requirements.txt
```
2. Create a new file at the root directory called .env (Note the dot at the front). Add the line (without < and >)
```
USDA_API_KEY=<your usda api key>
```
to the .env file.

## Running Locally
Launch Streamlit locally:
```
streamlit run landing_page.py
```

## Project Structure
`src/models.py`
- Contains SQLAlchemy model definitions (Recipe and Ingredient) and related methods that are closely tied to these models.

`src/db_operations.py`
- Handles database operations that involve interactions with the models but are not inherently tied to the Recipe or Ingredient classes.

`src/data_fetching.py`
- Contains functions that handle external data fetching, such as scraping and API calls.

`src/config.py`
- Initialize DB & Loads env variable

`landing_page.py`
- Streamlit app that ties together the functionality. Main Entry Point.

## Comments
Code is formatted with `Black Formatter`
