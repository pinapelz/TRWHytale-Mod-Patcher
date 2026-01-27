import patches
import os

def get_all_mod_sources() -> list:
    os.makedirs("mods", exist_ok=True)
    output_dir = "mods/patched"
    os.makedirs(output_dir, exist_ok=True)
    import shutil
    for entry in os.listdir(output_dir):
        path = os.path.join(output_dir, entry)
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception:
            pass
    files = [f for f in os.listdir("mods") if os.path.isfile(os.path.join("mods", f))]
    return files

def main():
    mods = get_all_mod_sources()
    for mod_file_name in mods:
        mod_path = f"mods/{mod_file_name}"
        if "trw" in mod_file_name:
            continue
        if "ymmersive-melodies" in mod_file_name:
            print("[PATCHER] Found ymmersive-melodies mod -> Swapping default songs")
            patches.ymmersive_melodies_patch_new_default_songs(mod_path)
        elif "SNIP3_FoodPack" in mod_file_name and mod_file_name.endswith(".zip"):
            print("Found SNIP3'S Food Pack -> Cleaning + Generating Spaghetti")
            patches.snip3_foodpack_apply_patch(mod_path)
        elif "EpicsLabubuPets" in mod_file_name:
            print("Found Labubu Mod, Making it expensive like the real stuff")
            patches.epics_labubu_patch(mod_path)
        elif mod_file_name.startswith("Wellwater"):
            print("Found Ryozu's Water Well Mod. Moving ItemId")
            patches.ryozu_well_water(mod_path)
        else:
            print(f"[WARNING] {mod_file_name} not recognized")

if __name__ == "__main__":
    main()
