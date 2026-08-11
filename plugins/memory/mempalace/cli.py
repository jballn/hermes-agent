import argparse
import json
import sys
import logging
import os
from typing import List, Dict, Any
from pathlib import Path

# Import the new wrapper instead of the legacy DB class
from .storage import MemPalaceWrapper

logger = logging.getLogger(__name__)

def get_db_path(hermes_home: str) -> Path:
    """
    Determines the palace path based on user configuration or default.
    """
    config_path = Path(hermes_home) / "mempalace_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                return Path(hermes_home) / config.get("storage_path", "mempalace_db")
        except Exception as e:
            logger.warning(f"Could not read mempalace_config.json ({e}), using default.")
    
    return Path(hermes_home) / "mempalace_db"

def main():
    parser = argparse.ArgumentParser(description="MemPalace CLI - Manage your verbatim memory via Hermes.")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Create Wing
    wing_parser = subparsers.add_parser("create-wing", help="Create a new top-level category (Wing)")
    wing_parser.add_argument("name", type=str, help="The name of the wing.")
    wing_parser.add_argument("-d", "--description", type=str, default="", help="Description of the wing.")

    # List Wings
    list_wings_parser = subparsers.add_parser("list-wings", help="List all available wings and their IDs.")

    # Create Room
    room_parser = subparsers.add_parser("create-room", help="Create a room within a wing.")
    room_parser.add_argument("wing_name", type=str, required=True, help="The name of the parent wing.")
    room_parser.add_argument("room_name", type=str, required=True, help="The name of the room.")
    room_parser.add_argument("-d", "--date", type=str, default="", help="Optional date grouping (e.g. 2026-01).")

    # Inspect Drawer
    inspect_parser = subparsers.add_parser("inspect-drawer", help="Inspect the verbatim content of a specific drawer.")
    inspect_parser.add_argument("room_name", type=str, required=True, help="The name of the room containing the drawer.")
    inspect_parser.add_argument("drawer_id", type=int, required=True, help="The unique ID of the drawer.")

    # Status
    status_parser = subparsers.add_parser("status", help="Show current palace statistics.")

    args = parser.parse_args()

    # Resolve environment variables
    hermes_home = os.environ.get("HERMES_HOME", "/home/dock/.hermes")
    db_path = get_db_path(hermes_home)
    
    try:
        wrapper = MemPalaceWrapper(db_path)

        if args.command == "create-wing":
            wid = wrapper.create_wing(args.name, args.description)
            print(f"Successfully created wing '{args.name}' (ID: {wid})")

        elif args.command == "list-wings":
            wings = wrapper.get_all_wings()
            if not wings:
                print("No wings found.")
            else:
                for w in wings:
                    print(f"[{w['id']}] {w['name']}")

        elif args.command == "create-room":
            # Find wing ID by name
            all_wings = wrapper.get_all_wings()
            wing_id = next((w["id"] for w in all_wings if w["name"] == args.wing_name), None)
            
            if wing_id is None:
                print(f"Error: Wing '{args.wing_name}' not found.")
                sys.exit(1)
            
            rid = wrapper.create_room(wing_id, args.room_name, args.date)
            print(f"Successfully created room '{args.room_name}' in wing '{args.wing_name}' (ID: {rid})")

        elif args.command == "inspect-drawer":
            # Find the correct room ID first by name across all wings
            all_wings = wrapper.get_all_wings()
            target_room_id = None
            for wing in all_wings:
                rooms = wrapper.get_rooms_for_wing(wing["id"])
                for r in rooms:
                    if r["name"] == args.room_name:
                        target_room_id = r["id"]
                        break
                if target_room_id is not None: break
            
            if target_room_id is None:
                print(f"Error: Room '{args.room_name}' not found.")
                sys.exit(1)

            drawers = wrapper.get_drawers_for_room(target_room_id)
            drawer = next((d for d in drawers if d["id"] == args.drawer_id), None)
            
            if drawer:
                print(f"--- Drawer {args.drawer_id} (Room: {args.room_name}) ---")
                print(f"AAAK Summary: {drawer['aaak_summary']}")
                print(f"Verbatim Content:\n{drawer['content']}")
            else:
                print(f"Error: Drawer ID {args.drawer_id} not found in room '{args.room_name}'.")

        elif args.command == "status":
            wings = wrapper.get_all_wings()
            print(f"Wings Count: {len(wings)}")
            for w in wings:
                rooms = wrapper.get_rooms_for_wing(w['id'])
                print(f" - {w['name']}: {len(rooms)} rooms")

        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"CLI Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
