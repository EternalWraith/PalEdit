# Palworld save editing — developer analysis

This note documents how this fork reads and writes Palworld **1.0** save files
and the integrity rules used for **world save (`Level.sav`)** editing. It's aimed at contributors; end-user instructions live
in the [README](../README.md).

Reference implementations consulted throughout:

- The vendored **`palworld_save_tools/`** (GVAS reader/writer + compression).
- **oMaN-Rod/palworld-save-pal** ("psp"), a maintained Rust 1.0 editor — used
  as a mechanics reference (`psp-core/src/domain/{world,containers,guild,pal}.rs`).

## 1. File formats and compression

A `.sav` file is a small header followed by a compressed **GVAS** blob. The
header carries a magic string at offset 8 and a one-byte save type:

| Magic | Save type | Meaning                        |
|-------|-----------|--------------------------------|
| `PlZ` | `0x32`    | zlib (double-zlib) — pre-1.0   |
| `PlM` | `0x31`    | Oodle — **Palworld 1.0**       |
| `CNK` | `0x30`    | chunked zlib (Xbox)            |

`palworld_save_tools/compressor` detects and handles all three, so
`decompress_sav_to_gvas(data) -> (raw_gvas, save_type)` works for 1.0 saves out
of the box. `loadfile` stashes `save_type` and `savefile` reuses it, so a
round-trip preserves the original container (verified byte-identical for an
unmodified `GlobalPalStorage.sav`). Compression is **not** a blocker for any
save type.

## 2. GVAS parsing and the skip-decode strategy

`GvasFile.read(raw, PALWORLD_TYPE_HINTS, custom_properties)` walks the property
tree. Some properties are stored as opaque byte blobs that need bespoke
decoders (`palworld_save_tools/rawdata/*`). An editor only needs to *decode*
the data it edits; everything else can be kept as raw bytes and written back
untouched.

`PalEdit.py` builds `PALEDIT_PALWORLD_CUSTOM_PROPERTIES` from the base set and
marks the large, editor-irrelevant world maps as `(skip_decode, skip_encode)`:

- `MapObjectSaveData`, `FoliageGridSaveDataMap`,
  `MapObjectSpawnerInStageSaveData`, `DynamicItemSaveData`,
  `ItemContainerSaveData`.

It intentionally **decodes** the maps it works with: `CharacterSaveParameterMap`
(the pals), `CharacterContainerSaveData` (box/slot placement) and
`GroupSaveDataMap` (guilds).

## 3. `GlobalPalStorage.sav` — the Global Palbox (supported)

This file remains the simplest editing path and is verified end-to-end.

- Top-level property is a flat `SaveParameterArray` of **960 slots**; each slot
  is `{ SaveParameter, InstanceId }`. An empty slot has `CharacterID == "None"`
  and `SlotIndex == -1`.
- There is **no** `worldSaveData` — no containers, guilds or player data.
- `loaddata` wraps each occupied slot into the `Level.sav` entry shape so
  `PalEntity` mutates the same dicts by reference and edits flow back on save.
- Add / clone / delete operate directly on the flat array
  (`palguidmanager is None`): claim a `CharacterID == "None"` slot, deep-copy
  the `SaveParameter`, assign a fresh `InstanceId`.

**Save-safety methodology** (used for every change): load → save → parse both
and diff every pal field. A no-edit open+save must change *nothing*. This proved
out the 1.0 field fixes (see §6) and is the bar any new write path should meet.

## 4. Per-pal `SaveParameter` model (1.0)

Handled in `PalInfo.PalEntity`. The 1.0-specific points that bit us:

- **Player vs pal.** 1.0 writes `IsPlayer: false` on every pal; detection must
  check the *value*, not key presence (psp: `world::entry_is_player`).
- **Attack IV.** 1.0 has a single attack IV, `Talent_Shot`; the old
  `Talent_Melee` was removed and is dropped on load.
- **Moves.** `MasteredWaza` holds only moves taught *beyond* the species'
  natural learnset; the natural learnset is the game's to grant. The displayed
  move pool is derived and never written.
- **Work suitability.** Stored only as non-zero entries in
  `GotWorkSuitabilityAddRankList`; zero-rank entries are pruned.
- **No `CraftSpeeds`.** 1.0 derives work speed from species data + soul ranks;
  the pre-1.0 `CraftSpeeds` field is not written.
- **Species match is case-insensitive.** A save's `CharacterID` is matched
  against species data case-insensitively (Unreal FNames ignore case), so e.g.
  the game's `SheepBall` resolves to a data key stored as `Sheepball`.

## 5. `Level.sav` world saves

The vendored `rawdata/group.py` decoder now handles both pre-update and
post-update guild tails, including markers, chest roles, player roles,
permissions and trailing bytes. PalEdit therefore keeps
`CharacterSaveParameterMap`, `CharacterContainerSaveData` and
`GroupSaveDataMap` decoded while editing.

World writes use these rules:

1. A new or cloned Pal receives a fresh instance GUID and the first free index
   below the target container's `SlotNum`.
2. The character-map entry, character-container slot and guild handle are
   added together. Batch imports preflight every source and available slot.
3. Deletion proceeds only when the character's `SlotId` agrees with a container
   slot holding the same instance GUID. It then removes the matching guild
   handle and character entry.
4. Missing `Players/<guid>.sav` files disable import and clone for that player.
   PalEdit does not guess a Palbox container.
5. Before replacing the file, PalEdit serializes, compresses, decompresses and
   reparses the generated save. It writes through a same-folder temporary file,
   verifies that the loaded target has not changed, and atomically replaces it.
   As with other portable compare-then-replace workflows, an uncooperative
   writer could still race in the narrow interval between verification and
   replacement.
6. PalEdit caps both compressed save input and decompressed GVAS output at
   512 MiB. The zlib decoder enforces the output cap while expanding data, and
   the Oodle decoder rejects an oversized declared output length before native
   allocation. The same limits apply to matching player saves.

The implementation is verified against psp's public
`tests/fixtures/saves/v1_relics/Level.sav`. That fixture contains 2,167
character entries, 67 character containers, 17 groups and 17 players. A
clone reparses with all three new references. Deleting that clone restores the
original uncompressed GVAS bytes exactly.

## 6. Status summary

| Save file                | Load | Edit existing | Add / clone | Notes |
|--------------------------|------|---------------|-------------|-------|
| `GlobalPalStorage.sav`   | ✅   | ✅            | ✅          | Fully supported & round-trip verified |
| `Level.sav` (world)      | ✅   | ✅            | ✅          | Reference-safe import, clone and delete; round-trip verified |
| `Players/<guid>.sav`     | ✅   | n/a           | n/a         | Loaded for player names in world mode |

Both save paths are supported. Keep the matching `Players` folder beside a
world save and retain backups of the whole world directory.
