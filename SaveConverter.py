#!/usr/bin/env python3

import argparse
import json, orjson
import os
from lib.gvas import GvasFile
from lib.noindent import CustomEncoder
from lib.palsav import compress_gvas_to_sav, decompress_sav_to_gvas
from lib.paltypes import PALWORLD_CUSTOM_PROPERTIES, PALWORLD_TYPE_HINTS

### Credit for this file and all those within "lib" belong to "cheahjs" on Github
### https://github.com/cheahjs/palworld-save-tools


def main():
    parser = argparse.ArgumentParser(
        prog="palworld-save-tools",
        description="Converts Palworld save files to and from JSON",
    )
    parser.add_argument("filename")
    parser.add_argument(
        "--to-json",
        action="store_true",
        help="Override heuristics and convert SAV file to JSON",
    )
    parser.add_argument(
        "--from-json",
        action="store_true",
        help="Override heuristics and convert JSON file to SAV",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: <filename>.json or <filename>.sav)",
    )
    parser.add_argument("--minify-json", action="store_true", help="Minify JSON output")
    args = parser.parse_args()

    if args.to_json and args.from_json:
        print("Cannot specify both --to-json and --from-json")
        exit(1)

    if not os.path.exists(args.filename):
        print(f"{args.filename} does not exist")
        exit(1)
    if not os.path.isfile(args.filename):
        print(f"{args.filename} is not a file")
        exit(1)

    if args.to_json or args.filename.endswith(".sav"):
        if not args.output:
            output_path = args.filename + ".json"
        else:
            output_path = args.output
        convert_sav_to_json(args.filename, output_path, args.minify_json)

    if args.from_json or args.filename.endswith(".json"):
        if not args.output:
            output_path = args.filename.replace(".json", "")
        else:
            output_path = args.output
        if os.path.exists(output_path):
            print(f"{output_path} already exists, this will overwrite the file")
            if not confirm_prompt("Are you sure you want to continue?"):
                exit(1)
        convert_json_to_sav(args.filename, output_path)


def convert_sav_to_json(filename, output_path, minify):
    print(f"Converting {filename} to JSON, saving to {output_path}")
    if os.path.exists(output_path):
        print(f"{output_path} already exists, this will overwrite the file")
    print(f"Decompressing sav file")
    with open(filename, "rb") as f:
        data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
    print(f"Loading GVAS file")
    gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)
    print(f"Writing JSON to {output_path}")
    with open(output_path, "wb") as f:
        f.write(orjson.dumps(gvas_file.dump(), option = orjson.OPT_INDENT_2))
        #indent = None if minify else "\t"
        #json.dump(gvas_file.dump(), f, indent=indent, cls=CustomEncoder)


def convert_json_to_sav(filename, output_path):
    print(f"Converting {filename} to SAV, saving to {output_path}")
    if os.path.exists(output_path):
        print(f"{output_path} already exists, this will overwrite the file")
    print(f"Loading JSON from {filename}")
    with open(filename, "r", encoding="utf8") as f:
        #data = json.load(f)
        data = orjson.loads(f.read())
    gvas_file = GvasFile.load(data)
    print(f"Compressing SAV file")
    if (
        "Pal.PalWorldSaveGame" in gvas_file.header.save_game_class_name
        or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name
    ):
        save_type = 0x32
    else:
        save_type = 0x31
    sav_file = compress_gvas_to_sav(
        gvas_file.write(PALWORLD_CUSTOM_PROPERTIES), save_type
    )
    print(f"Writing SAV file to {output_path}")
    with open(output_path, "wb") as f:
        f.write(sav_file)


def confirm_prompt(question: str) -> bool:
    reply = None
    while reply not in ("y", "n"):
        reply = input(f"{question} (y/n): ").casefold()
    return reply == "y"


if __name__ == "__main__":
    main()
