"""Regenerate PalEdit resource data for the current Palworld version.

Source: JSON game-data dumps maintained in the oMaN-Rod/palworld-save-pal
repo (kept current with game patches). This script downloads them into
./psp_data_cache/ (gitignored) on first run, then rewrites, under
palworld_pal_edit/resources/data:

  - pals/<CodeName>.json          per-species files (types, moveset, scaling,
                                  work suitabilities, Human flag)
  - attacks/*.json                per-attack files (element, power, category)
  - passives.json                 passive rating table
  - <lang>/pals.json etc.         localized display names (en-GB, it-IT, zh-CN)

Usage:
    python update_data.py           # refresh data JSONs (downloads if needed)
    python update_data.py --fetch   # force re-download of source data first
    python update_data.py --icons   # also fetch missing pal icons from
                                    # cdn.paldb.cc and alias variant icons

Existing files are never deleted and unknown extra keys in them (e.g.
RaidMoveset) are preserved, so PalEdit-only entries survive refreshes.

After running, sanity-check with:
    python -c "import sys; sys.path.insert(0,'.'); import palworld_pal_edit.PalInfo as P; \
               print(len(P.PalSpecies), len(P.PalAttacks), len(P.PalPassives))"
"""
import io
import json
import os
import re
import shutil
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ROOT, "palworld_pal_edit", "resources", "data")
ICON_DIR = os.path.join(ROOT, "palworld_pal_edit", "resources", "pals")
CACHE = os.path.join(ROOT, "psp_data_cache")

PSP_RAW = "https://raw.githubusercontent.com/oMaN-Rod/palworld-save-pal/main/data/json"
PALDB_CDN = "https://cdn.paldb.cc/image/Pal/Texture/PalIcon/Normal"

# PalEdit lang dir -> psp l10n dir
LANG_MAP = {"en-GB": "en", "it-IT": "it", "zh-CN": "zh-Hans"}

SOURCES = ["pals.json", "active_skills.json", "passive_skills.json"] + [
    f"l10n/{lang}/{name}.json"
    for lang in LANG_MAP.values()
    for name in ("pals", "active_skills", "passive_skills")
]


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "PalEdit-data-updater"})
    return urllib.request.urlopen(req, timeout=timeout).read()


def download_sources(force=False):
    for rel in SOURCES:
        dst = os.path.join(CACHE, rel.replace("/", "_"))
        if os.path.exists(dst) and not force:
            continue
        os.makedirs(CACHE, exist_ok=True)
        print(f"downloading {rel} ...")
        with open(dst, "wb") as f:
            f.write(fetch(f"{PSP_RAW}/{rel}"))


def cache(rel):
    path = os.path.join(CACHE, rel.replace("/", "_"))
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def jload(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def jsave(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=4)


def update_pals(psp_pals):
    paldir = os.path.join(RES, "pals")
    added = updated = 0
    for code, e in psp_pals.items():
        if e.get("disabled"):
            continue
        path = os.path.join(paldir, f"{code}.json")
        old = jload(path) if os.path.exists(path) else {}
        is_pal = bool(e.get("is_pal"))
        innate = e.get("passive_skills") or []

        out = dict(old)  # preserve unknown extra keys
        out["CodeName"] = code
        els = e.get("element_types") or []
        if not is_pal and not els:
            out["Type"] = ["None"]
        else:
            out["Type"] = [els[0] if els else "Normal",
                           els[1] if len(els) > 1 else "None"]
        out["Moveset"] = {
            f"EPalWazaID::{k}": v
            for k, v in sorted((e.get("skill_set") or {}).items(), key=lambda kv: kv[1])
        }
        out.setdefault("RaidMoveset", old.get("RaidMoveset", {}))
        if is_pal:
            sc = e.get("scaling") or {}
            out["Scaling"] = {
                "HP": sc.get("hp", 100),
                "PHY": sc.get("attack", 100),
                "MAG": sc.get("attack", 100),
                "DEF": sc.get("defense", 100),
            }
            out["Suitabilities"] = e.get("work_suitability") or {}
            out["InnatePassives"] = innate
            # DeckIndex >= 0 means the species is catchable (in the Paldeck)
            out["DeckIndex"] = e.get("pal_deck_index", -1)
            out["TowerBoss"] = bool(e.get("is_tower_boss"))
        out["Human"] = not is_pal

        if old != out:
            added, updated = (added + 1, updated) if not old else (added, updated + 1)
            jsave(path, out)
    print(f"pals: {added} added, {updated} updated")


def update_attacks(psp_attacks, psp_pals):
    # Species-exclusive moves: a Unique_ move belongs to the species whose
    # skill_set contains it. PalInfo.GetAvailableSkills hides moves whose
    # "Exclusive" list doesn't include the pal's codename.
    owners = {}
    for pal_code, e in psp_pals.items():
        for waza in (e.get("skill_set") or {}):
            code = f"EPalWazaID::{waza}"
            if "Unique_" in code:
                owners.setdefault(code, []).append(pal_code)
    # some unique moves appear in no learnset (granted situationally);
    # fall back to the species encoded in the id: Unique_<PalCode>_<Move>
    for code in psp_attacks:
        if "Unique_" in code and code not in owners:
            parts = code.split("Unique_", 1)[1].split("_")
            for ln in range(len(parts) - 1, 0, -1):
                cand = "_".join(parts[:ln])
                if cand in psp_pals:
                    owners[code] = [cand]
                    break
                near = [s for s in psp_pals if s.startswith(cand)]
                if near:
                    owners[code] = near
                    break

    atkdir = os.path.join(RES, "attacks")
    by_code = {jload(os.path.join(atkdir, fn))["CodeName"]: fn for fn in os.listdir(atkdir)}
    added = updated = 0
    for code, e in psp_attacks.items():
        fn = by_code.get(code, code.replace("EPalWazaID::", "") + ".json")
        path = os.path.join(atkdir, fn)
        old = jload(path) if os.path.exists(path) else {}
        out = dict(old)
        out["CodeName"] = code
        out["Type"] = e.get("element", "Normal")
        out["Power"] = e.get("power", 0)
        out["Category"] = e.get("type", "Shot")
        if code in owners:
            out["Exclusive"] = sorted(owners[code])
        if old != out:
            added, updated = (added + 1, updated) if not old else (added, updated + 1)
            jsave(path, out)
    print(f"attacks: {added} added, {updated} updated, {len(owners)} exclusive")


# broad, user-facing buckets a passive's effects fall into, matched by
# substring against psp effect `type` values (checked in order)
PASSIVE_GROUP_RULES = [
    ("Attack", ("Attack", "ElementBoost")),
    ("Defense", ("Defense", "ElementResist", "MaxHP", "Shield")),
    ("Work", ("CraftSpeed", "CollectItem", "Work", "Logging", "Mining",
              "Watering", "Planting", "Kindling", "Cooling", "Transport",
              "Generate", "Medicine", "Handiwork", "Farming")),
    ("Movement", ("MoveSpeed", "Jump", "Dash", "Ride")),
    ("Utility", ("Sanity", "FullStomatch", "FullStomach", "Hunger", "Temperature",
                 "MaxInventoryWeight", "Capture", "Exp", "Homing", "Recovery")),
]


def _passive_group(psp_entry):
    """Classify a passive by its first meaningful effect type."""
    for eff in psp_entry.get("effects", []):
        etype = eff.get("type") or ""
        if etype in ("", "None"):
            continue
        for group, needles in PASSIVE_GROUP_RULES:
            if any(n in etype for n in needles):
                return group
        return "Other"
    return "Other"


# passive effect type -> readable label, for generating accurate descriptions
EFFECT_LABELS = {
    "ShotAttack": "Attack", "Defense": "Defense", "CraftSpeed": "Work Speed",
    "MoveSpeed": "Move Speed", "MaxHP": "Max HP", "MaxInventoryWeight": "Carry Weight",
    "Logging": "Logging", "Mining": "Mining", "CollectItem": "Gathering",
    "LifeSteal": "Life Steal", "BreedSpeed": "Breeding Speed",
    "PalEggHatchingSpeed": "Egg Hatching", "PalExp_Increase": "Pal EXP",
    "PalSP_Increase": "Partner Skill", "JumpCount_Increase": "Jumps",
    "JumpPower_Increase": "Jump Power", "ActiveSkillCoolTime_Decrease": "Skill Cooldown",
    "Sanity_Decrease": "Sanity Drain", "FullStomatch_Decrease": "Hunger Rate",
    "ShopBuyPrice_Money_Increase": "Buy Price", "ShopSellPrice_Money_Increase": "Sell Price",
    "TemperatureResist_Cold": "Cold Resistance", "TemperatureResist_Heat": "Heat Resistance",
    "Nocturnal": "Nocturnal", "NonKilling": "Non-lethal Attacks",
}


def _effect_label(etype):
    if etype in EFFECT_LABELS:
        return EFFECT_LABELS[etype]
    if etype.startswith("ElementBoost_"):
        return etype.split("_", 1)[1] + " Attack"
    if etype.startswith("ElementResist_"):
        return etype.split("_", 1)[1] + " Resistance"
    return etype


def passive_effect_desc(psp_entry):
    """Readable summary of what a passive adjusts, e.g. 'Attack +15%,
    Defense +15%, Work Speed +20%', built from its effects."""
    parts = []
    for eff in (psp_entry or {}).get("effects", []):
        t, v = eff.get("type"), eff.get("value", 0)
        if not t or t == "None" or not v:
            continue
        val = int(v) if float(v).is_integer() else v
        parts.append(f"{_effect_label(t)} {'+' if v > 0 else ''}{val}%")
    return ", ".join(parts)


def update_passives(psp_passives):
    ppath = os.path.join(RES, "passives.json")
    passives = jload(ppath)
    added = sum(1 for c in psp_passives if c not in passives)
    for code, e in psp_passives.items():
        # Rollable: can appear on wild/lucky pals; anything else is only
        # legal on species that list it in InnatePassives. Group buckets the
        # passive by effect for the grouped picker.
        passives[code] = {
            "Rating": str(e.get("rank", 1)),
            "Rollable": bool(e.get("add_pal") or e.get("add_rare_pal")),
            "Group": _passive_group(e),
        }
    jsave(ppath, passives)
    print(f"passives: {added} added, total {len(passives)}")
    return passives


def update_l10n(psp_pals, psp_attacks, passives, psp_passives):
    for pe_lang, psp_lang in LANG_MAP.items():
        ldir = os.path.join(RES, pe_lang)
        if not os.path.isdir(ldir):
            continue
        loc_pals = cache(f"l10n/{psp_lang}/pals.json")
        loc_atk = cache(f"l10n/{psp_lang}/active_skills.json")
        loc_pas = cache(f"l10n/{psp_lang}/passive_skills.json")

        cur = jload(os.path.join(ldir, "pals.json"))
        for code in psp_pals:
            name = loc_pals.get(code, {}).get("localized_name")
            if name and name != "en_text":
                cur[code] = name
            else:
                cur.setdefault(code, code)
        jsave(os.path.join(ldir, "pals.json"), cur)

        cur = jload(os.path.join(ldir, "attacks.json"))
        for code in psp_attacks:
            name = loc_atk.get(code, {}).get("localized_name")
            if name and name != "en_text":
                cur[code] = name
            else:
                cur.setdefault(code, code.replace("EPalWazaID::", ""))
        jsave(os.path.join(ldir, "attacks.json"), cur)

        # NOTE: PalInfo.LoadPassives does l[code]["Name"] unguarded, so every
        # key in passives.json MUST exist in each lang's passives.json.
        cur = jload(os.path.join(ldir, "passives.json"))
        for code in passives:
            loc = loc_pas.get(code, {})
            name, desc = loc.get("localized_name"), loc.get("description")
            # Prefer an accurate effect summary (English) over the often-vague
            # localized blurb ("Lucky" -> "Attack +15%, Defense +15%, ...").
            eff = passive_effect_desc(psp_passives.get(code)) if pe_lang == "en-GB" else ""
            if name and name != "en_text":
                # accurate effect summary first; fall back to the localized
                # blurb for passives that have no numeric effects
                cur[code] = {"Name": name, "Description": eff or desc or name}
            else:
                cur.setdefault(code, {"Name": code, "Description": eff or code})
        jsave(os.path.join(ldir, "passives.json"), cur)
        print(f"l10n {pe_lang} refreshed")


def update_icons():
    """Fetch missing T_<Code>_icon_normal.png icons.

    PalInfo.GetImage resolves non-human icons as T_{code}_icon_normal.png
    after stripping RAID_ and _2 (see PalInfo.py). Variants with no icon of
    their own (GYM_/PREDATOR_/Oilrig/...) get a copy of their base pal's
    icon. Anything still missing falls back to #ERROR.png at runtime.
    """
    sys.path.insert(0, ROOT)
    import palworld_pal_edit.PalInfo as PalInfo

    icons = set(os.listdir(ICON_DIR))
    need = set()
    for code, obj in PalInfo.PalSpecies.items():
        if obj._human:
            continue
        n = "PlantSlime" if "PlantSlime" in code else code
        n = n.replace("RAID_", "").replace("_2", "")
        if f"T_{n}_icon_normal.png" not in icons:
            need.add(n)

    from PIL import Image
    ok, miss = 0, []
    for n in sorted(need):
        try:
            data = fetch(f"{PALDB_CDN}/T_{n}_icon_normal.webp", timeout=15)
            Image.open(io.BytesIO(data)).convert("RGBA").save(
                os.path.join(ICON_DIR, f"T_{n}_icon_normal.png"))
            ok += 1
        except Exception:
            miss.append(n)
        time.sleep(0.15)
    icons = set(os.listdir(ICON_DIR))

    aliased, still = 0, []
    for n in miss:
        base = n
        for pre in ("GYM_", "PREDATOR_", "POLICE_", "SUMMON_"):
            if base.startswith(pre):
                base = base[len(pre):]
        base = re.sub(r"_(Oilrig|Tower|Avatar|Servant|Otomo|Max|Min|Flower)$", "", base)
        base = re.sub(r"_Quest(_(Enemy|Friend))?$", "", base)
        src = f"T_{base}_icon_normal.png"
        if src in icons and base != n:
            shutil.copyfile(os.path.join(ICON_DIR, src),
                            os.path.join(ICON_DIR, f"T_{n}_icon_normal.png"))
            aliased += 1
        else:
            still.append(n)
    print(f"icons: {ok} downloaded, {aliased} aliased, {len(still)} unavailable")
    if still:
        print("  no icon (uses #ERROR.png):", ", ".join(still))


def main():
    download_sources(force="--fetch" in sys.argv)
    psp_pals = cache("pals.json")
    psp_attacks = cache("active_skills.json")
    psp_passives = cache("passive_skills.json")

    update_pals(psp_pals)
    update_attacks(psp_attacks, psp_pals)
    passives = update_passives(psp_passives)
    update_l10n(psp_pals, psp_attacks, passives, psp_passives)
    if "--icons" in sys.argv:
        update_icons()


if __name__ == "__main__":
    main()
