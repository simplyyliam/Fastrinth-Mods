import os
import requests

# Directory to save downloaded mods
SAVE_DIRECTORY = "1.20.1"

# Loader and game version to filter by
LOADER = "fabric"  # Example: "fabric" or "forge"
GAME_VERSION = "1.21.11"  # Example: "1.20.1"

# Ensure the save directory exists
os.makedirs(SAVE_DIRECTORY, exist_ok=True)

def search_mod(mod_name):
    """
    Searches for a mod on Modrinth by its name and returns the slug.
    """
    try:
        response = requests.get(f"https://api.modrinth.com/v2/search", params={"query": mod_name})
        response.raise_for_status()
        results = response.json().get("hits", [])

        if not results:
            print(f"No mod found with the name '{mod_name}'.")
            return None

        # Select the first result (or add logic to handle multiple results)
        mod_slug = results[0]["slug"]
        mod_title = results[0]["title"]
        print(f"Found mod: {mod_title} (Slug: {mod_slug})")
        return mod_slug

    except Exception as e:
        print(f"Failed to search for mod '{mod_name}': {e}")
        return None

def is_mod_downloaded(file_name):
    """
    Checks if the mod has already been downloaded by looking for the file in the save directory.
    """
    file_path = os.path.join(SAVE_DIRECTORY, file_name)
    return os.path.exists(file_path)

def download_mod(slug, loader, game_version):
    try:
        # Fetch the mod information
        response = requests.get(f"https://api.modrinth.com/v2/project/{slug}/version")
        response.raise_for_status()
        versions = response.json()

        if not versions:
            print(f"No versions found for {slug}.")
            return

        print(f"Found {len(versions)} versions for {slug}.")

        # Filter versions by loader and game version
        filtered_versions = [
            version for version in versions
            if loader in version["loaders"] and game_version in version["game_versions"]
        ]

        if not filtered_versions:
            print(f"No matching versions found for {slug} with loader {loader} and game version {game_version}.")
            return

        # Use the latest matching version
        latest_version = filtered_versions[0]
        print(f"Using version {latest_version['version_number']} for {slug}")

        # Get the file URL
        file_url = latest_version["files"][0]["url"]
        file_name = latest_version["files"][0]["filename"]

        # Check if the mod is already downloaded
        if is_mod_downloaded(file_name):
            print(f"{file_name} already exists in the directory. Skipping download.")
            return

        # Download the file
        print(f"Downloading {file_name}...")
        file_response = requests.get(file_url)
        file_response.raise_for_status()

        # Save the file
        file_path = os.path.join(SAVE_DIRECTORY, file_name)
        with open(file_path, "wb") as file:
            file.write(file_response.content)
        print(f"Downloaded {file_name} to {SAVE_DIRECTORY}")

    except Exception as e:
        print(f"Failed to download {slug}: {e}")

def main():
    # List of mod names to search and download
    mod_names = [
        "Advancement Plaques",
        "artifacts",
        "Auditory",
        "Better Advancements",
        "Better Mending",
        "Better Third Person",
        "BetterGrassify",
        "bosses-of-mass-destruction",
        "Bridging Mod",
        "Camera Overhaul",
        "Cloth Config API",
        "Cobweb",
        "Comforts",
        "Connectable Chains",
        "Cristal Lib",
        "ct-overhaul-village",
        "Data Loader",
        "Diagonal Fences",
        "Diagonal Walls",
        "Diagonal Windows",
        "Dungeons and Taverns",
        "Easy Elytra Takeoff",
        "Eating Animations",
        "Entity Model Features",
        "Entity Texture Features",
        "explorify",
        "FallingTree",
        "Farmers Delight Refabricated",
        "First Person Model",
        "friends-and-foes",
        "Horse Buff",
        "Iceberg",
        "immersivethunder",
        "Incendium",
        "Invmove",
        "Jamlib",
        "kiwi",
        "Legendary Tooltips",
        "mes-moogs-end-structures",
        "moogs-voyager-structures",
        "More Mob Varients",
        "M.R.U",
        "Not Enough Animation",
        "Nullscape",
        "owo-lib",
        "Particular",
        "philips-ruins",
        "plasmo-voice",
        "Prism",
        "Reforged",
        "RightClickHarvest",
        "Scalablelux",
        "snow-real-magic",
        "Sounds",
        "soul-fire",
        "sparsestructures",
        "Spell Power",
        "Structory",
        "SuperBetterGrass",
        "Tectonic",
        "Towns and Towers",
        "Trade Cycling",
        "trinkets",
        "UNionLib",
        "libraryferret",
        "pehkui",
        "fabric-language-kotlin",
        "resourceful-config",
        "geckolib",
        "knight-lib",
        "moreculling",
        "alloy-forgery",
        "azurelib-armor",
        "sushi-bar",
        "origins",
        "extra-rpg-attributes",
        "azurelib",
        "more-spell-attributes-more-magic-series",
        "lithostitched",
        "Vanilla Refresh",
        "villager-names-serilum",
        "resourceful-lib",
        "Visuality",
        "waystones",
        "when-dungeons-arise",
        "yungs-better-caves",
        "yungs-better-desert-temples",
        "yungs-better-dungeons",
        "yungs-better-end-island",
        "yungs-better-jungle-temples",
        "yungs-better-mineshafts",
        "yungs-better-nether-fortresses",
        "yungs-better-ocean-monuments",
        "yungs-better-strongholds",
        "yungs-better-structures",
        "yungs-better-villages",
        "yungs-better-witch-huts",
        "yungs-bridges",
        "yungs-extras",
        "amendments",
        "archers",
        "azurelib",
        "balm-fabric",
        "bookshelf",
        "gazebo",
        "geckolib",
        "jewelry",
        "iris",
        "indium",
        "lithium",
        "sodium",
        "lithostitched",
        "sodium-extra",
        "modernfix",
        "reeses-sodium-options",
        "moreculling",
        "niftycarts",
        "noisium",
        "noxesium",
        "paladins",
        "smartfarmers",
        "spell-engine",
        "supplementaries",
        "thepa-structures",
        "cardinal-components",
        "player-animator",
        "moonlight-lib",
        "carryon",
        "camerapture",
        "ketkets-furnicraft",
        "immersive-aircraft",
        "village-taverns",
        "rogues",
        "wizards",
        "runes",
        "elytratrims",
        "wi-zoom",
        "forge-config-api-port",
        "collective",
        "better-villages",
        "puzzleslib",
        "yungs-api",
        "clumps",
        "iron-chests",
        "better-nether-map",
        "mythicmetals",
        "modern-industrialization",
        "create-fabric",
        "summoning-rituals",
        "just-give",
        "item-filters",
        "jade",
        "cull-leaves",
        "adaptive-tooltips",
        "arcanus",
        "trading-post",
        "campsite",
        "playerex",
        "mythic-upgrades",
        "occultism",
        "knight-quest",
        "mythic-mounts",
        "epic-knights",
        "umu-backpack",
        "bewitchment",
        "better-combat",
        "spellblade-next",
        "affinity",
        "tool-leveling",
        "fwaystones",
        "useless-reptile",
        "elytra-slot",
        "architectury",
        "l2weaponry",
        "l2complements",
        "mc-dungeons-weapons",

    ]

    for mod_name in mod_names:
        print(f"Searching for mod: {mod_name}")
        mod_slug = search_mod(mod_name)
        if mod_slug:
            print(f"Fetching mod: {mod_slug}")
            download_mod(mod_slug, LOADER, GAME_VERSION)

if __name__ == "__main__":
    main()
