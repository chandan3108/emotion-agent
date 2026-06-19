import asyncio
from backend.games_logic import fetch_recipe_from_api

async def main():
    print("Fetching 'Biryani' from TheMealDB...")
    recipe = await fetch_recipe_from_api("Biryani")
    print("\nResult for Biryani:")
    print("Name:", recipe.get("name"))
    print("Ingredients count:", len(recipe.get("ingredients", [])))
    print("Steps count:", len(recipe.get("steps", [])))

    print("\nFetching random recipe from TheMealDB...")
    recipe_rand = await fetch_recipe_from_api("")
    print("\nResult for random:")
    print("Name:", recipe_rand.get("name"))
    print("Ingredients count:", len(recipe_rand.get("ingredients", [])))
    print("Steps count:", len(recipe_rand.get("steps", [])))

if __name__ == "__main__":
    asyncio.run(main())
