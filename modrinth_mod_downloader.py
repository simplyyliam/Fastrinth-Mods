"""
Modrinth Mod Downloader
A tool to automatically search and download Minecraft mods from Modrinth API.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ModrinthConfig:
    """Configuration settings for the mod downloader."""
    
    def __init__(
        self,
        save_directory: str = "mods",
        loader: str = "fabric",
        game_version: str = "1.21.11",
        api_base_url: str = "https://api.modrinth.com/v2"
    ):
        self.save_directory = Path(save_directory)
        self.loader = loader
        self.game_version = game_version
        self.api_base_url = api_base_url
        
        # Create directory if it doesn't exist
        self.save_directory.mkdir(parents=True, exist_ok=True)


class ModrinthDownloader:
    """Handles searching and downloading mods from Modrinth."""
    
    def __init__(self, config: ModrinthConfig):
        self.config = config
        self.session = self._create_session()
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging for the downloader."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def search_mod(self, mod_name: str) -> Optional[Dict]:
        """
        Search for a mod on Modrinth by name.
        
        Args:
            mod_name: The name of the mod to search for
            
        Returns:
            Dictionary containing mod information or None if not found
        """
        try:
            response = self.session.get(
                f"{self.config.api_base_url}/search",
                params={"query": mod_name},
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json().get("hits", [])
            
            if not results:
                self.logger.warning(f"No mod found with name '{mod_name}'")
                return None
            
            # Return the first (most relevant) result
            mod_info = results[0]
            self.logger.info(
                f"Found mod: {mod_info['title']} (Slug: {mod_info['slug']})"
            )
            return mod_info
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to search for mod '{mod_name}': {e}")
            return None
    
    def is_mod_downloaded(self, file_name: str) -> bool:
        """
        Check if a mod file already exists in the save directory.
        
        Args:
            file_name: Name of the mod file
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self.config.save_directory / file_name
        return file_path.exists()
    
    def get_compatible_version(self, slug: str) -> Optional[Dict]:
        """
        Find the latest compatible version for the configured loader and game version.
        
        Args:
            slug: The mod's slug identifier
            
        Returns:
            Version information dictionary or None if no compatible version found
        """
        try:
            response = self.session.get(
                f"{self.config.api_base_url}/project/{slug}/version",
                timeout=10
            )
            response.raise_for_status()
            
            versions = response.json()
            
            if not versions:
                self.logger.warning(f"No versions found for mod '{slug}'")
                return None
            
            # Filter versions by loader and game version
            compatible_versions = [
                version for version in versions
                if (self.config.loader in version["loaders"] and 
                    self.config.game_version in version["game_versions"])
            ]
            
            if not compatible_versions:
                self.logger.warning(
                    f"No compatible versions found for '{slug}' "
                    f"(Loader: {self.config.loader}, "
                    f"Game Version: {self.config.game_version})"
                )
                return None
            
            # Return the latest compatible version
            latest_version = compatible_versions[0]
            self.logger.info(
                f"Found compatible version {latest_version['version_number']} "
                f"for '{slug}'"
            )
            return latest_version
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch versions for '{slug}': {e}")
            return None
    
    def download_mod(self, slug: str) -> bool:
        """
        Download a mod by its slug identifier.
        
        Args:
            slug: The mod's slug identifier
            
        Returns:
            True if download successful, False otherwise
        """
        version_info = self.get_compatible_version(slug)
        
        if not version_info:
            return False
        
        try:
            # Get the primary file from the version
            file_info = version_info["files"][0]
            file_url = file_info["url"]
            file_name = file_info["filename"]
            
            # Check if already downloaded
            if self.is_mod_downloaded(file_name):
                self.logger.info(
                    f"'{file_name}' already exists. Skipping download."
                )
                return True
            
            # Download the file
            self.logger.info(f"Downloading '{file_name}'...")
            response = self.session.get(file_url, timeout=30)
            response.raise_for_status()
            
            # Save to disk
            file_path = self.config.save_directory / file_name
            file_path.write_bytes(response.content)
            
            self.logger.info(
                f"Successfully downloaded '{file_name}' to "
                f"'{self.config.save_directory}'"
            )
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to download mod '{slug}': {e}")
            return False
    
    def download_mods_from_list(self, mod_names: List[str]) -> Dict[str, bool]:
        """
        Download multiple mods from a list of names.
        
        Args:
            mod_names: List of mod names to download
            
        Returns:
            Dictionary mapping mod names to success status
        """
        results = {}
        
        for mod_name in mod_names:
            self.logger.info(f"Processing mod: '{mod_name}'")
            
            mod_info = self.search_mod(mod_name)
            if not mod_info:
                results[mod_name] = False
                continue
            
            slug = mod_info["slug"]
            success = self.download_mod(slug)
            results[mod_name] = success
        
        return results
    
    def print_summary(self, results: Dict[str, bool]) -> None:
        """
        Print a summary of download results.
        
        Args:
            results: Dictionary mapping mod names to success status
        """
        total = len(results)
        successful = sum(1 for success in results.values() if success)
        failed = total - successful
        
        self.logger.info("\n" + "=" * 50)
        self.logger.info("DOWNLOAD SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total mods processed: {total}")
        self.logger.info(f"Successfully downloaded: {successful}")
        self.logger.info(f"Failed: {failed}")
        
        if failed > 0:
            self.logger.info("\nFailed mods:")
            for mod_name, success in results.items():
                if not success:
                    self.logger.info(f"  - {mod_name}")


def main():
    """Main entry point for the script."""
    
    # Configuration
    config = ModrinthConfig(
        save_directory="1.20.1",
        loader="fabric",
        game_version="1.21.11"
    )
    
    # List of mods to download
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
        "balm-fabric",
        "bookshelf",
        "gazebo",
        "jewelry",
        "iris",
        "indium",
        "lithium",
        "sodium",
        "sodium-extra",
        "modernfix",
        "reeses-sodium-options",
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
    
    # Create downloader and process mods
    downloader = ModrinthDownloader(config)
    results = downloader.download_mods_from_list(mod_names)
    downloader.print_summary(results)


if __name__ == "__main__":
    main()