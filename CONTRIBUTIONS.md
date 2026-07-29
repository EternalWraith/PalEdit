# Changes in this fork

Fork of EternalWraith/PalEdit, updated for the Palworld 1.0 release and
extended with editor features and save-safety fixes. Each item below is a
self-contained branch merged into `main`, so changes can be cherry-picked
individually.

## Palworld 1.0 support

- Read and write the 1.0 save format (Oodle-compressed `PlM`, save type
  0x31), preserving the original compression on save.
- Load `GlobalPalStorage.sav` (the 1.0 Global Palbox), not just `Level.sav`.
- Fix every pal failing to load in 1.0 saves (1.0 writes `IsPlayer: false` on
  each pal; detection now checks the value instead of key presence).
- Refresh all game data for 1.0: new species, movesets, stat scaling, work
  suitabilities, attacks, and passive skills, plus new-pal icons.
- Raise the level cap to 80 and add the rank-5 passive tier.

## Editor features

- Add, clone, and delete pals in the Global Palbox. New pals start as a
  default species and can be re-typed from there.
- Edit pal nicknames (updates both `NickName` and the 1.0 `FilteredNickName`).
- Searchable attack picker with a tier toggle (learnset / fruit-teachable /
  all), element filter, and damage sort. Each move is tinted by its element so
  the list reads at a glance. The "add a move" box under the moveset opens the
  same picker (the ➕ button still commits the staged move).
- Searchable passive picker grouped by effect (Attack, Defense, Work, etc.),
  with a per-passive effect description and a natural-only / all toggle. The
  four slots in the passive-preset editor use the same picker, pal-agnostically
  (any passive can go into a preset).
- Automatic save backup: the loaded save is copied to a `PalEdit-backups`
  folder before the first write of each editing session.
- Pal-list filter bar: name search, element filter, and a category toggle
  (Natural / Tower Bosses / Unobtainable / NPCs), keeping catchable merchants
  and other NPCs visible and grouped rather than hidden.
- Searchable species browser, opened from the species selector button (which
  replaces the long scrolling dropdown): name/code search, element and
  category filters, a multi-toggle work-suitability filter (find species with
  a base in one or more work types), and an NPC-type filter (Merchant, Hunter,
  Believer, Police, Scientist, Soldier, etc.). Rows show the code alongside
  the name so catchable NPCs/merchants are identifiable by their real names.
- Hide the stale-player warning when editing the Global Palbox, where it does
  not apply.

- Work suitabilities editable up to 10 (mutations exceed the old cap of 5),
  with grey/green/red feedback: grey at the species base, green when raised
  within the normal range, red in the excessive 6-10 range.
- Accurate passive descriptions generated from each passive's effects (e.g.
  Lucky -> "Attack +15%, Defense +15%, Work Speed +20%") shown on hover in the
  picker and main window.
- A detailed stats/potential breakdown popup, now editable in place: combat
  stats vs the level standard (colour-coded delta), plus spinboxes for the IVs
  (0-100), the four souls (0-20) and condensation (shown as the in-game 0-4
  stars). An edit updates the pal and the main window together, and the combat
  column re-computes so you can watch a stat move as you tune it.
- The level at the top of the pal panel can be typed directly as well as
  stepped with the ➖ / ➕ buttons; typed input is clamped to 1..level cap and
  the field and buttons always agree.

## Fixes

Work-suitability, move, and species-change handling were audited against the
public 1.0 editor *palworld-save-pal* to confirm the correct 1.0 field model.

- Fix work-suitability corruption. Pals could lose their farming/grazing/
  kindling behaviour because opening and saving added a zero-rank entry to
  `GotWorkSuitabilityAddRankList` for every suitability (13 unused entries per
  pal). Zero-rank entries are now pruned on load and never written; a
  suitability entry is created only for a real, non-zero bonus. Loading a
  previously affected save and re-saving removes the extra entries.
- Fix work suitabilities "flip-flopping" between pals: on selecting a pal, the
  suitability controls set their value before their minimum, so a stale
  minimum from the previous pal could clamp and later write a wrong value. The
  range is now set before the value, and the write-back is skipped during
  selection refresh.
- Remove the pre-1.0 `CraftSpeeds` field. `SetType` wrote this field on every
  species change; 1.0 saves have no such field and the game derives work
  suitability from species data plus `GotWorkSuitabilityAddRankList`. It is no
  longer written and is stripped on load.
- Correct `MasteredWaza` handling. The move list was being filled with the
  whole species learnset on load, so opening and saving added extra "mastered"
  moves to every pal. `MasteredWaza` now holds only moves taught beyond the
  natural learnset (matching the game); the displayed move pool is derived and
  never written. Previously affected lists are cleaned on load.
- Remove the pre-1.0 `Talent_Melee` IV. 1.0 pals have a single attack IV
  (`Talent_Shot`); the melee IV was dropped. It was being added to every pal
  on load. It is now only touched on legacy saves that already have it.
- Match a pal's species case-insensitively. The species lookup keyed on the
  exact `CharacterID`, so a pal whose data casing differed from the save (e.g.
  the game's `SheepBall`/Lamball vs a data key `Sheepball`) failed to load and
  was dropped into the Unknown list. Since Unreal treats these names
  case-insensitively, `LoadPals` now keeps a lowercased index and `PalEntity`
  falls back to it, so those pals load normally.

With the above, opening a 1.0 save and saving it back without editing anything
is now a no-op: a field-by-field diff of every pal shows nothing added,
removed, or changed. Previously each such open/save injected `CraftSpeeds`,
zero-rank work-suitability entries, learnset moves into `MasteredWaza`, and
`Talent_Melee` — which is what corrupted pals.
