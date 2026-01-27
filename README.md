# TRWHytale-Mod-Patcher
Basic scripts to unpack and patch Hytale mods. Comes with some patches for various mods already to be used in conjunction with [TRWHytale](https://github.com/pinapelz/TRWHytale)

The motivation is that there are many mods which are released under a proprietary license, however this also restricts re-distribution of modified versions for personal use.

# Docs
`make_bin_diff.py` - Generates a binary diff for a file, useful for applying patches onto binary data (i.e PNG) if editing a texture
`patches.create_temp_dir_for_modification` - Creates a temporary working directory for modifying a zip mod
`patches.rezip_temp_dir_into_patched`  - Re-zips the temporary directory back into a zip mod

1. Download the original mod and place it into a `mods` folder
2. Install `uv` for Python and run `uv sync` to install dependencies
3. Run `uv run build_external_mods.py` while in this repo's root directory

Generated patched mods will be in `mods/patched`

## [Ymmersive Melodies](https://www.curseforge.com/hytale/mods/ymmersive-melodies/download)
- Removed the default server-side songs and added some "special" ones

## [SNIP3'S Food Pack](https://www.curseforge.com/hytale/mods/snip3s-food-pack)
- Removed some of the food items, kept fries and pizza
- Removed all pastas, there is now only Spaghetti (with higher T4 health/stamina regen + insta-health)

## [Epic's Labubu Pets](https://www.curseforge.com/hytale/mods/epics-labubu-pets)
- Patches in correct audio files for Blue and Red Labubus
- Make Labubus much more expensive to craft

## [Ryozu's Water Well](https://www.curseforge.com/hytale/mods/well-water)
- Changed namespace/item_id in case there is a conflict in the future
