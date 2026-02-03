import zipfile
import os
import tempfile
import shutil

from make_bin_diff import apply_patch

import json

def load_json_file(path: str):
    """
    Load and return JSON data from the given file path.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def dump_json_file(data, path: str):
    """
    Dump data as JSON back to the same file. Writes to a temporary file
    and atomically replaces the target to avoid partial writes.
    """
    dirn = os.path.dirname(path)
    if dirn and not os.path.exists(dirn):
        os.makedirs(dirn, exist_ok=True)
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)

def create_temp_dir_for_modification(src_zip_path: str, paths: set = None, mode: str = 'keep'):
    temp_zip_path = src_zip_path + '.tmp'
    norm_paths = None
    if paths:
        norm_paths = set()
        for p in paths:
            np = p.replace(os.path.sep, '/')
            if np.startswith('./'):
                np = np[2:]
            norm_paths.add(np)
    with zipfile.ZipFile(src_zip_path, 'r') as src_zip:
        with zipfile.ZipFile(temp_zip_path, 'w') as dst_zip:
            for member in src_zip.namelist():
                if member.endswith('/'):
                    continue
                include = True
                if mode == 'keep':
                    if norm_paths:
                        include = member in norm_paths
                elif mode == 'remove':
                    if norm_paths and member in norm_paths:
                        include = False
                else:
                    include = True

                if not include:
                    continue
                try:
                    info = src_zip.getinfo(member)
                    data = src_zip.read(member)
                    info.filename = member
                    dst_zip.writestr(info, data)
                except KeyError:
                    dst_zip.writestr(member, src_zip.read(member))

    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(temp_zip_path, 'r') as z:
        z.extractall(temp_dir)
    return temp_dir, temp_zip_path

def rezip_temp_dir_into_patched(orig_zip_path: str, temp_dir_path: str):
    dirn = os.path.dirname(orig_zip_path)
    base = os.path.splitext(os.path.basename(orig_zip_path))[0]
    if dirn:
        new_path = os.path.join(dirn, 'patched', f"{base}-trw.zip")
    else:
        new_path = os.path.join('patched', f"{base}-trw.zip")
    parent = os.path.dirname(new_path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    with zipfile.ZipFile(new_path, 'w', compression=zipfile.ZIP_DEFLATED) as out_zip:
        for root, _, files in os.walk(temp_dir_path):
            for fname in files:
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, temp_dir_path)
                arcname = rel_path.replace(os.path.sep, '/')
                out_zip.write(full_path, arcname)
    return new_path


def ymmersive_melodies_patch_new_default_songs(jar_path: str):
    src_dir = os.path.join('patch_data', 'ymmersive_melodies')
    with zipfile.ZipFile(jar_path, 'r') as jar:
        temp_path = jar_path + '.tmp'
        with zipfile.ZipFile(temp_path, 'w') as temp_jar:
            for item in jar.namelist():
                if not item.startswith('Server/YmmersiveMelodies/'):
                    temp_jar.writestr(item, jar.read(item))
            if os.path.isdir(src_dir):
                for root, _, files in os.walk(src_dir):
                    for fname in files:
                        full_path = os.path.join(root, fname)
                        rel_path = os.path.relpath(full_path, src_dir)
                        arcname = os.path.join('Server', 'YmmersiveMelodies', rel_path).replace(os.path.sep, '/')
                        with open(full_path, 'rb') as f:
                            data = f.read()
                        temp_jar.writestr(arcname, data)
    dirn = os.path.dirname(jar_path)
    base = os.path.splitext(os.path.basename(jar_path))[0]
    new_name = "patched/" + base + '-trw.jar'
    new_path = os.path.join(dirn, new_name) if dirn else new_name
    os.replace(temp_path, new_path)

def snip3_foodpack_apply_patch(zip_path: str):
    kept_icons = ["Food_Fried_Potato.png", "Food_Pasta.png", "Food_Pizza_Cheese.png", "Food_Raw_Pasta.png", "Ingredient_Raw_Fries_Potato.png", "Ingredient_Raw_Pasta.png"]
    kept_item_data = ["Food_Fried_Potato.json", "Food_Pizza_Cheese.json", "Ingredient_Raw_Fries_Potato.json", "Ingredient_Raw_Pasta.json"]
    kept_models = ["Carbonara.png", "Cooked_Pasta.blockymodel", "Fried_Patato.blockymodel", "Fried_Potato.png", "Fries_Texture.png", "Pizza.blockymodel", "Pizza_Texture.png", "Potato_Fries.blockymodel", "Raw_Pasta.blockymodel", "Raw_Pasta_Texture.png"]
    kept_interactions = ["HealthRegen_TierCheck_T4.json","FruitVeggie_TierCheck_T4.json"]
    kept_effects = ["Food_Instant_Heal_T4.json", "FruitVeggie_Buff_T4.json", "HealthRegen_Buff_T4.json"]
    prefixes = {
        "Common/Icons/ItemsGenerated/": set(kept_icons),
        "Server/Item/Items/": set(kept_item_data),
        "Common/Items/Consumables/Food/": set(kept_models),
        "Server/Entity/Effects/": set(kept_effects),
        "Server/Item/Interactions/": set(kept_interactions)
    }
    keep_paths = set(["manifest.json"])
    for prefix, names in prefixes.items():
        for name in names:
            keep_paths.add(prefix + name)

    temp_dir = None
    temp_zip_path = None
    try:
        temp_dir, temp_zip_path = create_temp_dir_for_modification(zip_path, keep_paths, mode="keep")

        carbonara_path = os.path.join(temp_dir, "Common", "Items", "Consumables", "Food", "Carbonara.png")
        spaghetti_path = os.path.join(temp_dir, "Common", "Items", "Consumables", "Food", "Spaghetti.png")
        languages_dir = os.path.join(temp_dir, "Server", "Languages")

        if os.path.exists(carbonara_path):
            apply_patch("patch_data/snip3s_foodpack/CarbonaraToSpaghetti.patch", carbonara_path, spaghetti_path)
            try:
                if os.path.exists(carbonara_path):
                    os.remove(carbonara_path)
            except OSError:
                pass

        pasta_json_src = os.path.join('patch_data', 'snip3s_foodpack', 'Food_Pasta_Spaghetti.json')
        dest_dir = os.path.join(temp_dir, 'Server', 'Item', 'Items')
        dest_path = os.path.join(dest_dir, 'Food_Pasta_Spaghetti.json')
        manifest_json = load_json_file(os.path.join(temp_dir, 'manifest.json'))
        manifest_json["IncludesAssetPack"] = True
        dump_json_file(manifest_json, os.path.join(temp_dir, 'manifest.json'))
        t4_heal_file = os.path.join(temp_dir, 'Server', 'Entity', 'Effects', "Food_Instant_Heal_T4.json")
        t4_insta_heal_json = load_json_file(t4_heal_file)
        t4_insta_heal_json["StatModifiers"]["Health"] = 30
        dump_json_file(t4_insta_heal_json, t4_heal_file)

        try:
            if os.path.exists(pasta_json_src):
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copyfile(pasta_json_src, dest_path)
        except OSError:
            pass

        if os.path.exists(languages_dir):
            try:
                shutil.rmtree(languages_dir)
            except OSError:
                try:
                    os.rmdir(languages_dir)
                except OSError:
                    pass

        rezip_temp_dir_into_patched(zip_path, temp_dir)
    finally:
        try:
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
        except OSError:
            pass
        try:
            if temp_dir:
                shutil.rmtree(temp_dir)
        except OSError:
            pass

def epics_labubu_patch(zip_path: str):
    temp_dir, temp_zip_path = create_temp_dir_for_modification(zip_path)
    labubu_recepie_path = os.path.join(temp_dir, "Server","Item","Items","EggSpawner")
    shutil.copyfile("patch_data/labubu_pets/Epics_LabubuEgg_Basic.json", os.path.join(labubu_recepie_path, "Epics_LabubuEgg_Basic.json"))
    shutil.copyfile("patch_data/labubu_pets/Epics_LabubuEgg_Ears.json", os.path.join(labubu_recepie_path, "Epics_LabubuEgg_Ears.json"))
    shutil.copyfile("patch_data/labubu_pets/Epics_LabubuEgg_NoEars.json", os.path.join(labubu_recepie_path, "Epics_LabubuEgg_NoEars.json"))
    labubu_basic = load_json_file(os.path.join(temp_dir, 'Server', "Models", "Intelligent", "Kweebec", "LabubuBasic.json"))
    labubu_basic["AnimationSets"]["Idle"]["Animations"] = [{"Animation": "NPC/Intelligent/Kweebec_Sapling/Animations/LabubuIdle.blockyanim","Speed": 0.5, "SoundEventId": "SFX_Labubu_Alerted"}]
    dump_json_file(labubu_basic, os.path.join(temp_dir, 'Server', "Models", "Intelligent", "Kweebec", "LabubuBasic.json"))
    labubu_no_ears = load_json_file(os.path.join(temp_dir, 'Server', "Models", "Intelligent", "Kweebec", "LabubuNoEars.json"))
    labubu_no_ears["AnimationSets"]["Idle"]["Animations"] = [{"Animation": "NPC/Intelligent/Kweebec_Sapling/Animations/LabubuIdle.blockyanim","Speed": 0.5, "SoundEventId": "SFX_Labubu_Alerted"}]
    dump_json_file(labubu_no_ears, os.path.join(temp_dir, 'Server', "Models", "Intelligent", "Kweebec", "LabubuNoEars.json"))
    rezip_temp_dir_into_patched(zip_path, temp_dir)
    try:
        if temp_zip_path and os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
    except OSError:
        pass
    try:
        if temp_dir:
            shutil.rmtree(temp_dir)
    except OSError:
        pass


def patch_gambling(zip_path: str):
    temp_dir, temp_zip_path = create_temp_dir_for_modification(zip_path)
    npcs_dir = os.path.join(temp_dir, 'Server', 'Drops', 'NPCs')
    if os.path.exists(npcs_dir):
        try:
            shutil.rmtree(npcs_dir)
        except OSError:
            try:
                for root, dirs, files in os.walk(npcs_dir, topdown=False):
                    for fname in files:
                        try:
                            os.remove(os.path.join(root, fname))
                        except OSError:
                            pass
                    for dname in dirs:
                        try:
                            os.rmdir(os.path.join(root, dname))
                        except OSError:
                            pass
                try:
                    os.rmdir(npcs_dir)
                except OSError:
                    pass
            except Exception:
                pass

    slot_src = os.path.join('patch_data', 'gambling', 'SlotMachine_Droplist.json')
    slot_dest_dir = os.path.join(temp_dir, 'Server', 'Drops', 'Items')
    slot_dest = os.path.join(slot_dest_dir, 'SlotMachine_Droplist.json')
    try:
        if os.path.exists(slot_src):
            os.makedirs(slot_dest_dir, exist_ok=True)
            shutil.copyfile(slot_src, slot_dest)
    except OSError:
        pass

    claw_machine_src = os.path.join('patch_data', 'gambling', 'ClawMachine_Droplist.json')
    claw_machine_dest = os.path.join(slot_dest_dir, 'ClawMachine_Droplist.json')
    try:
        if os.path.exists(claw_machine_src):
            os.makedirs(slot_dest_dir, exist_ok=True)
            shutil.copyfile(claw_machine_src, claw_machine_dest)
    except OSError:
        pass

    token_src = os.path.join('patch_data', 'gambling', 'SlotToken.json')
    token_dest_dir = os.path.join(temp_dir, 'Server', 'Item', 'Items', 'Ingredient')
    token_dest = os.path.join(token_dest_dir, 'SlotToken.json')
    try:
        if os.path.exists(token_src):
            os.makedirs(token_dest_dir, exist_ok=True)
            shutil.copyfile(token_src, token_dest)
    except OSError:
        pass

    claw_src = os.path.join('patch_data', 'gambling', 'ClawTicket.json')
    claw_dest = os.path.join(token_dest_dir, 'ClawTicket.json')
    try:
        if os.path.exists(claw_src):
            os.makedirs(token_dest_dir, exist_ok=True)
            shutil.copyfile(claw_src, claw_dest)
    except OSError:
        pass

    rezip_temp_dir_into_patched(zip_path, temp_dir)
    try:
        if temp_zip_path and os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
    except OSError:
        pass
    try:
        if temp_dir:
            shutil.rmtree(temp_dir)
    except OSError:
        pass


def patch_violet_plushie(mod_path):
    temp_dir = None
    temp_zip_path = None
    try:
        temp_dir, temp_zip_path = create_temp_dir_for_modification(mod_path)
        src = os.path.join('patch_data', 'violet_plush', 'Bench_Violet_Plushie.json')
        dest_dir = os.path.join(temp_dir, 'Server', 'Item', 'Items', 'Bench')
        dest = os.path.join(dest_dir, 'Bench_Violet_Plushie.json')
        try:
            if os.path.exists(src):
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copyfile(src, dest)
        except OSError:
            pass

        rezip_temp_dir_into_patched(mod_path, temp_dir)
    finally:
        try:
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
        except OSError:
            pass
        try:
            if temp_dir:
                shutil.rmtree(temp_dir)
        except OSError:
            pass


def patch_teto_plush(mod_path):
    temp_dir = None
    temp_zip_path = None
    try:
        temp_dir, temp_zip_path = create_temp_dir_for_modification(mod_path)
        src = os.path.join('patch_data', 'teto_plush', 'Deco_Teto_Plush.json')
        dest_dir = os.path.join(temp_dir, 'Server', 'Item', 'Items', 'Deco')
        dest = os.path.join(dest_dir, 'Deco_Teto_Plush.json')
        try:
            if os.path.exists(src):
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copyfile(src, dest)
        except OSError:
            pass

        rezip_temp_dir_into_patched(mod_path, temp_dir)
    finally:
        try:
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
        except OSError:
            pass
        try:
            if temp_dir:
                shutil.rmtree(temp_dir)
        except OSError:
            pass

def patch_khaos(mod_path):
    temp_dir = None
    temp_zip_path = None
    try:
        temp_dir, temp_zip_path = create_temp_dir_for_modification(mod_path)
        src = os.path.join('patch_data', 'khaos_dungeon', 'PortalKey_Template.json')
        dest_dir = os.path.join(temp_dir, 'Server', 'Item', 'Items', 'Portal')
        dest = os.path.join(dest_dir, 'PortalKey_Template.json')
        try:
            if os.path.exists(src):
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copyfile(src, dest)
        except OSError:
            pass

        rezip_temp_dir_into_patched(mod_path, temp_dir)
    finally:
        try:
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
        except OSError:
            pass
        try:
            if temp_dir:
                shutil.rmtree(temp_dir)
        except OSError:
            pass


def patch_lucky_block(mod_path):
    temp_dir = None
    temp_zip_path = None
    try:
        temp_dir, temp_zip_path = create_temp_dir_for_modification(mod_path)
        src_lucky = os.path.join('patch_data', 'keke_lucky_block', 'lucky_block.json')
        src_unlucky = os.path.join('patch_data', 'keke_lucky_block', 'Unlucky_Block.json')
        src_loot_drop = os.path.join('patch_data', 'keke_lucky_block', 'Lucky_Block_Loot_Drop.json')
        dest_dir = os.path.join(temp_dir, 'Server', 'Item', 'Items')
        dest_lucky = os.path.join(dest_dir, 'lucky_block.json')
        dest_unlucky = os.path.join(dest_dir, 'Unlucky_Block.json')
        dest_drops_dir = os.path.join(temp_dir, 'Server', 'Drops')
        dest_loot_drop = os.path.join(dest_drops_dir, 'Lucky_Block_Loot_Drop.json')
        try:
            if os.path.exists(src_lucky):
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copyfile(src_lucky, dest_lucky)
            if os.path.exists(src_unlucky):
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copyfile(src_unlucky, dest_unlucky)
            # Replace the drops loot drop file if a patched version exists
            if os.path.exists(src_loot_drop):
                os.makedirs(dest_drops_dir, exist_ok=True)
                shutil.copyfile(src_loot_drop, dest_loot_drop)
        except OSError:
            pass

        rezip_temp_dir_into_patched(mod_path, temp_dir)
    finally:
        try:
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
        except OSError:
            pass
        try:
            if temp_dir:
                shutil.rmtree(temp_dir)
        except OSError:
            pass


def patch_walter_white(mod_path):
    temp_dir = None
    temp_zip_path = None
    try:
        temp_dir, temp_zip_path = create_temp_dir_for_modification(mod_path)
        src = os.path.join('patch_data', 'walter_white', 'WalterWhite_Merchant_Shop.json')
        dest_dir = os.path.join(temp_dir, 'Server', 'BarterShops')
        dest = os.path.join(dest_dir, 'WalterWhite_Merchant_Shop.json')
        try:
            if os.path.exists(src):
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copyfile(src, dest)
        except OSError:
            pass

        # Ensure the WalterWhite merchant NPC is marked invulnerable (case-insensitive removal of prior keys)
        npc_path = os.path.join(temp_dir, 'Server', 'NPC', 'Roles', 'Intelligent', 'Neutral', 'Kweebec', 'WalterWhite_Merchant.json')
        try:
            if os.path.exists(npc_path):
                try:
                    npc_data = load_json_file(npc_path)
                    if isinstance(npc_data, dict):
                        # Remove any existing invulnerable-style keys, then set canonical key
                        npc_data.pop('Invulnerable', None)
                        npc_data.pop('invulnerable', None)
                        npc_data['Invulnerable'] = True
                        dump_json_file(npc_data, npc_path)
                except Exception:
                    # If loading or writing fails, skip modification
                    pass
        except Exception:
            pass

        rezip_temp_dir_into_patched(mod_path, temp_dir)
    finally:
        try:
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
        except OSError:
            pass
        try:
            if temp_dir:
                shutil.rmtree(temp_dir)
        except OSError:
            pass


def patch_ressurectable_dinos(mod_path):
    temp_dir = None
    temp_zip_path = None
    try:
        temp_dir, temp_zip_path = create_temp_dir_for_modification(mod_path)
        items_dir = os.path.join(temp_dir, 'Server', 'Item', 'Items')
        if os.path.exists(items_dir):
            for root, _, files in os.walk(items_dir):
                for fname in files:
                    if not fname.lower().endswith('.json'):
                        continue
                    full_path = os.path.join(root, fname)
                    try:
                        data = load_json_file(full_path)
                        if isinstance(data, dict) and "Recipe" in data:
                            try:
                                data.pop("Recipe", None)
                                dump_json_file(data, full_path)
                            except OSError:
                                # If writing fails, skip this file
                                pass
                    except Exception:
                        # If loading/parsing fails, skip this file
                        pass

        rezip_temp_dir_into_patched(mod_path, temp_dir)
    finally:
        try:
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
        except OSError:
            pass
        try:
            if temp_dir:
                shutil.rmtree(temp_dir)
        except OSError:
            pass

def patch_overworld(mod_path):
    temp_dir = None
    temp_zip_path = None
    try:
        temp_dir, temp_zip_path = create_temp_dir_for_modification(mod_path)

        server_dir = os.path.join(temp_dir, 'Server')
        src_instances = os.path.join(server_dir, 'instances')
        dst_instances = os.path.join(server_dir, 'Instances')

        if os.path.exists(src_instances):
            try:
                # If the correct-cased target doesn't exist, a simple rename is fine.
                if not os.path.exists(dst_instances):
                    os.makedirs(os.path.dirname(dst_instances), exist_ok=True)
                    os.rename(src_instances, dst_instances)
                else:
                    # Merge contents from 'instances' into 'Instances'
                    for name in os.listdir(src_instances):
                        s = os.path.join(src_instances, name)
                        d = os.path.join(dst_instances, name)
                        try:
                            if os.path.exists(d):
                                # If destination exists, attempt to merge/replace sensibly.
                                if os.path.isdir(s) and os.path.isdir(d):
                                    # Move contents of directory s into directory d
                                    for root, dirs, files in os.walk(s):
                                        rel = os.path.relpath(root, s)
                                        target_root = os.path.join(d, rel) if rel != '.' else d
                                        os.makedirs(target_root, exist_ok=True)
                                        for f in files:
                                            try:
                                                shutil.move(os.path.join(root, f), os.path.join(target_root, f))
                                            except OSError:
                                                try:
                                                    shutil.copy2(os.path.join(root, f), os.path.join(target_root, f))
                                                except Exception:
                                                    pass
                                    # remove the source subtree
                                    try:
                                        shutil.rmtree(s)
                                    except OSError:
                                        pass
                                else:
                                    # For files or mismatched types, try to replace destination
                                    try:
                                        if os.path.isdir(d):
                                            shutil.rmtree(d)
                                        else:
                                            os.remove(d)
                                    except OSError:
                                        pass
                                    try:
                                        shutil.move(s, d)
                                    except OSError:
                                        try:
                                            if os.path.isdir(s):
                                                shutil.copytree(s, d)
                                                shutil.rmtree(s, ignore_errors=True)
                                            else:
                                                shutil.copy2(s, d)
                                                os.remove(s)
                                        except Exception:
                                            pass
                            else:
                                shutil.move(s, d)
                        except OSError:
                            # Best-effort fallback: try copying then removing source
                            try:
                                if os.path.isdir(s):
                                    shutil.copytree(s, d)
                                    shutil.rmtree(s, ignore_errors=True)
                                else:
                                    shutil.copy2(s, d)
                                    try:
                                        os.remove(s)
                                    except OSError:
                                        pass
                            except Exception:
                                pass
                    # finally, ensure the original folder is removed if empty
                    try:
                        if os.path.exists(src_instances):
                            shutil.rmtree(src_instances)
                    except OSError:
                        pass
            except OSError:
                pass

        # Replace Ore_Diamond_Overworld.json with the patched version if available
        src_ore = os.path.join('patch_data', 'overworld', 'Ore_Diamond_Overworld.json')
        dest_dir = os.path.join(temp_dir, 'Server', 'Item', 'Items')
        dest_ore = os.path.join(dest_dir, 'Ore_Diamond_Overworld.json')
        try:
            if os.path.exists(src_ore):
                os.makedirs(dest_dir, exist_ok=True)
                try:
                    if os.path.exists(dest_ore):
                        os.remove(dest_ore)
                except OSError:
                    pass
                shutil.copyfile(src_ore, dest_ore)
        except OSError:
            pass

        # Replace Server/Item/ItemsOverworld_Soil_Dirt.json with patched version if available
        src_soil = os.path.join('patch_data', 'overworld', 'Overworld_Soil_Dirt.json')
        dest_soil = os.path.join(temp_dir, 'Server', 'Item', 'Items','Overworld_Soil_Dirt.json')
        try:
            if os.path.exists(src_soil):
                os.makedirs(os.path.dirname(dest_soil), exist_ok=True)
                try:
                    if os.path.exists(dest_soil):
                        os.remove(dest_soil)
                except OSError:
                    pass
                shutil.copyfile(src_soil, dest_soil)
        except OSError:
            pass

        # Remove the "Recipe" key from Server/Item/Items/Overworld_Portal_Key.json if it exists
        portal_path = os.path.join(temp_dir, 'Server', 'Item', 'Items', 'Overworld_Portal_Key.json')
        try:
            if os.path.exists(portal_path):
                try:
                    portal_json = load_json_file(portal_path)
                    if isinstance(portal_json, dict) and "Recipe" in portal_json:
                        portal_json.pop("Recipe", None)
                        dump_json_file(portal_json, portal_path)
                except Exception:
                    # If loading or writing fails, skip modification
                    pass
        except Exception:
            pass

        rezip_temp_dir_into_patched(mod_path, temp_dir)
    finally:
        try:
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
        except OSError:
            pass
        try:
            if temp_dir:
                shutil.rmtree(temp_dir)
        except OSError:
            pass
