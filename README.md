## Intro

This script was built to take a link to a notion meal plan (inline DB containing meal names) and a grocery list (empty inline DB), and populate the grocery list with the ingredients for the meals in the meal plan.
This was built and expanded with a few features in a very adhoc manner, so the coding style is not perfect, should be lots of room for improvement.

## Setup

There is some setup required in Notion, including having a list of recipies with ingredients tables included, as well as the mealplan and grocery list pages.

To run the script, first create a python virtual environment:

python3 -m venv venv

Then, with the venv activated, install the requirements:

pip install -r requirements.txt

After this, you should be good to run the script. In vscode you can simply press F5, this may vary in other editors, or from the command line, after activating the virtual environment you can run the following:

python3 notion_grocery_list_generator.py
