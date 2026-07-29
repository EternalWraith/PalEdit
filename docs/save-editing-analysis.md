# Palworld save editing — developer analysis

This note documents how this fork reads and writes Palworld **1.0** save files,
which files are supported today, and what a full **world save (`Level.sav`)**
editor would still need. It's aimed at contributors; end-user instructions live
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
(the pals), `CharacterContainerSaveData` (box/slot placement) and — historically
— `GroupSaveDataMap` (guilds). See §5 for why the last one is now a problem.

## 3. `GlobalPalStorage.sav` — the Global Palbox (supported)

This is the file the fork targets and the only one verified end-to-end.

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

## 5. `Level.sav` — world saves (analysis; not yet enabled)

The world-save code path exists (`loaddata`'s non-storage branch +
`PalInfo.PalGuid`) and is structurally aligned with 1.0: same
`worldSaveData.CharacterSaveParameterMap` / `CharacterContainerSaveData` /
`GroupSaveDataMap`, same player/pal model.

### The one blocker

Loading a real 1.0 `Level.sav` fails while **decoding `GroupSaveDataMap`**:

```
palworld_save_tools/rawdata/group.py -> Exception("Warning: EOF not reached")
```

1.0 appended trailing bytes to each guild entry that the vendored decoder
doesn't consume (psp handles this in `guild.rs` + `guild_tail.rs`). Everything
else — compression, all other maps, the per-pal model — already works.

### The minimal fix (proven, not yet merged)

Add `.worldSaveData.GroupSaveDataMap` to the skip-decode set. The guild data is
then preserved as raw bytes and written back verbatim. With only that change, a
real 1.0 world fixture loaded **every pal (~2,150) and all 10 players** and
completed a no-edit save round-trip.

Verified against psp's fixtures:
`psp-reference/tests/fixtures/saves/v1_relics/` (and `v1_stats`,
`reference_saves`) — real 1.0 `Level.sav` files with a `Players/` folder.

### Trade-offs to resolve before shipping world support

1. **Guild-dependent writes.** `PalGuid`'s group helpers
   (`AddGroupSaveData`, …), used by world-mode clone/add to register a new pal
   in a guild, can't run against raw-bytes groups. Editing *existing* world
   pals is unaffected; adding/cloning into a world would need those paths
   guarded (or the full guild parser, below).
2. **Performance.** GVAS parsing is pure Python; the 2.3 MB test world is fine,
   but a large real world may be slow.

### Fuller option

Port psp's 1.0 guild parsing (`guild.rs` + `guild_tail.rs`) into a Python
`rawdata/group.py` decoder. This restores full guild editing (including
world-mode add/clone) at the cost of a nontrivial binary-format port.

## 6. Status summary

| Save file                | Load | Edit existing | Add / clone | Notes |
|--------------------------|------|---------------|-------------|-------|
| `GlobalPalStorage.sav`   | ✅   | ✅            | ✅          | Fully supported & round-trip verified |
| `Level.sav` (world)      | ⛔→✅* | ✅*          | ⚠️          | *with the §5 skip-decode fix; add/clone needs guild handling |
| `Players/<guid>.sav`     | ✅   | n/a           | n/a         | Loaded for player names in world mode |

The Global Palbox is the tested, recommended path today. World-save support is
diagnosed and a small change away from loading + editing existing pals; it's
left off until the trade-offs in §5 are handled.
