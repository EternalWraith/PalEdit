import copy
import json
import os
import sys
import traceback
from enum import Enum
import tkinter
import uuid
import copy
import math

module_dir = os.path.dirname(os.path.realpath(__file__))
if not os.path.exists("%s/resources/data/elements.json" % module_dir) and getattr(sys, 'frozen', False):
    # for some reason os.path when compiled with CxFreeze bugs out the program. Will look into it.
    module_dir = os.path.dirname(sys.executable)

try:
    from palworld_pal_edit.EmptyObjectHandler import *
except:
    from EmptyObjectHandler import *

suitnames = ["EmitFlame",
        "Watering",
        "Seeding",
        "GenerateElectricity",
        "Handcraft",
        "Collection",
        "Deforest",
        "Mining",
        "OilExtraction",
        "ProductMedicine",
        "Cool",
        "Transport",
        "MonsterFarm"]

xpthresholds = [
    0,
    25,
    56,
    93,
    138,
    207,
    306,
    440,
    616,
    843,
    1131,
    1492,
    1941,
    2495,
    3175,
    4007,
    5021,
    6253,
    7747,
    9555,
    11740,
    14378,
    17559,
    21392,
    26007,
    31561,
    38241,
    46272,
    55925,
    67524,
    81458,
    98195,
    118294,
    142429,
    171406,
    206194,
    247955,
    298134,
    358305,
    430525,
    517205,
    621236,
    746089,
    895928,
    1075751,
    1291554,
    1550533,
    1861323,
    2234286,
    2681857,
    3218908,
    3863445,
    4636905,
    5565072,
    6678888,
    8015483,
    9619412,
    11544143,
    13853835,
    16625481,
    19951472,
    23942677,
    28732138,
    34479507,
    41376365,
    49652610,
    59584120,
    71501947,
    85803355,
    102965061,
    123559123,
    148272013,
    177927497,
    213514093,
    256218024,
    307462756,
    368956450,
    442748899,
    531299853,
    637561014,
    765074422,
    918090527,
    1101709869,
    1322053095,
    1586464981,
    1903759260,
    2147483647
]
while len(xpthresholds) < 80:
    xpthresholds.append(xpthresholds[-1])

xpthresholds = []
with open("%s/resources/data/levels.json" % (module_dir), "r",
              encoding="utf8") as levelfile:
    lvl = json.loads(levelfile.read())
    xpthresholds = lvl["values"]

trustthresholds = []
with open("%s/resources/data/friendship.json" % (module_dir), "r",
              encoding="utf8") as trustfile:
    trust = json.loads(trustfile.read())
    trustthresholds = trust["values"]



class PalGender(Enum):
    MALE = "#02A3FE"
    FEMALE = "#EC49A6"
    UNKNOWN = "darkgrey"


class PalObject:
    def __init__(self, name, code_name, primary, secondary="None", human=False, tower=False, scaling=None, trustscale=None, suits={}):
        self._name = name
        self._code_name = code_name
        self._img = None
        self._primary = primary
        self._secondary = secondary
        self._human = human
        self._tower = tower
        self._scaling = scaling
        self._trustscale = trustscale
        self._suits = suits

    def GetName(self):
        return PalSpecies[self._code_name]._name # Update PalEdit.listdisplay

    def GetCodeName(self):
        return self._code_name

    def IsTower(self):
        return self._tower

    def GetImage(self):
        if self._img == None:
            n = self.GetCodeName()
            print(n)
            if self._human:
                n = n.split("_")
                n.pop(0)
                while len(n) > 0:
                    nn = "_".join(n)
                    try:
                        self._img = tkinter.PhotoImage(file=f'{module_dir}/resources/humans/T_BOSS_NPC_{nn}.png')
                        break
                    except:
                        n.pop(len(n)-1)
                        
                if self._img == None:
                    self._img = tkinter.PhotoImage(file=f'{module_dir}/resources/pals/T_CommonHuman_icon_normal.png')
            else:
                
                n = "PlantSlime" if "PlantSlime" in self.GetCodeName() else n
                n = n.replace("RAID_", "").replace("_2","").replace("_otomo","")
                # self._img = ImageTk.PhotoImage(Image.open(module_dir+f'/resources/{n}.png').resize((240,240)))
                try:
                    print(f"T_{n}_icon_normal.png")
                    self._img = tkinter.PhotoImage(file=f'{module_dir}/resources/pals/T_{n}_icon_normal.png')
                except:
                    self._img = tkinter.PhotoImage(file=f'{module_dir}/resources/pals/#ERROR.png')
        return self._img

    def GetPrimary(self):
        return self._primary

    def GetSecondary(self):
        return self._secondary

    def GetScaling(self):
        return self._scaling

    def GetTrustScale(self):
        return self._trustscale

    def IsHuman(self):
        return self._human


class PalEntity:

    def __init__(self, data):
        global logger

        self._data = data
        self._obj = data['value']['RawData']['value']['object']['SaveParameter']['value']
        data['value']['RawData']['value']["unknown_bytes"] = ""
        data['value']['RawData']['value']["trailing_bytes"] = ""
        if ('CustomVersionData' in data['value']):
            data['value']['CustomVersionData']['value']["values"] = ""

        self.owner = ""
        if "SlotId" in self._obj:
            self.owner = self._obj["SlotId"]['value']["ContainerId"]['value']['ID']['value']

        # Palworld 1.0 writes IsPlayer=False on every pal, so key presence
        # alone no longer identifies a player character
        if (
                "IsPlayer" in self._obj
                and self._obj["IsPlayer"].get("value") is not False
        ):
            raise Exception("This is a player character")

        if not "IsRarePal" in self._obj:
            self._obj["IsRarePal"] = copy.deepcopy(EmptyRarePalObject)
        self.isLucky = self._obj["IsRarePal"]['value']

        typename = self._obj['CharacterID']['value']
        # print(f"Debug: typename1 - {typename}")

        self.isBoss = False
        ogtypename = typename
        if typename[:5].lower() == "boss_":
            typename = typename[5:]  # if first 5 characters match boss_ then cut the first 5 characters off
            # typename = typename.replace("BOSS_", "") # this causes bugs
            self.isBoss = True if not self.isLucky else False
            if typename == "LazyCatFish":  # BOSS_LazyCatFish and LazyCatfish
                typename = "LazyCatfish"

        # print(f"Debug: typename2 - '{typename}'")
        # Match the species by CharacterID, tolerating a casing difference
        # between the save and our data. Unreal treats these names
        # case-insensitively, so e.g. the game's "SheepBall" (Lamball) resolves
        # to a data key stored as "Sheepball" instead of failing to load. This
        # replaces the old per-species SheepBall fix-up and covers any pal
        # whose data casing drifts from the save.
        if typename not in PalSpecies and typename.lower() in PalSpeciesLower:
            typename = PalSpeciesLower[typename.lower()]

        self.isBossRush = False
        if "_BossRush" in typename:
            typename = typename.replace("_BossRush", "")
            self.isBossRush = True

        self._type = PalSpecies[typename]
        if self.IsHuman() and ogtypename[:5].lower() == "boss_":
            if ogtypename in PalSpecies:
                self._type = PalSpecies[ogtypename]
                self.isBoss = False
        logger.debug(f"Created Entity of type {typename}: {self._type} - Lucky: {self.isLucky} Boss: {self.isBoss}")

        if "Gender" in self._obj:
            if self._obj['Gender']['value']['value'] == "EPalGenderType::Male":
                self._gender = "Male ♂"
            else:
                self._gender = "Female ♀"
        else:
            self._gender = "Unknown"

        #self._workspeed = self._obj['CraftSpeed']['value']

        if not "Talent_HP" in self._obj:
            self._obj['Talent_HP'] = copy.deepcopy(EmptyTalentObject)
            self._talent_hp = 0  # we set 0, so if its not changed it should be removed by the game again.
        self._talent_hp = self._obj['Talent_HP']['value']["value"]

        # Palworld 1.0 uses a single attack IV (Talent_Shot); the separate
        # melee IV was removed and palworld-save-pal never reads or writes it.
        # Drop any leftover Talent_Melee on load so re-saving matches 1.0, and
        # don't write it.
        self._obj.pop("Talent_Melee", None)

        if not "bIsAwakening" in self._obj:
            self._obj["bIsAwakening"] = copy.deepcopy(EmptyAwakeningObject)

        if not "Talent_Shot" in self._obj:
            self._obj['Talent_Shot'] = copy.deepcopy(EmptyTalentObject)
        self._ranged = self._obj['Talent_Shot']['value']["value"]

        if not "Talent_Defense" in self._obj:
            self._obj['Talent_Defense'] = copy.deepcopy(EmptyTalentObject)
        self._defence = self._obj['Talent_Defense']['value']["value"]

        if not "Rank" in self._obj:
            self._obj['Rank'] = copy.deepcopy(EmptyRankObject)
        self._rank = self._obj['Rank']['value']['value']

        if "FriendshipPoint" not in self._obj:
            self._obj["FriendshipPoint"] = copy.deepcopy(EmptyTrustObject)
        self._trust = self._obj["FriendshipPoint"]["value"]
        tl = self.GetTrustLevel()
        self.extratrust = self._trust - trustthresholds[tl+3]

        # Fix broken ranks
        if self.GetRank() < 1 or self.GetRank() > 5:
            self.SetRank(1)

        if not "PassiveSkillList" in self._obj:
            self._obj['PassiveSkillList'] = copy.deepcopy(EmptySkillObject)
        self._skills = self._obj['PassiveSkillList']['value']['values']
        self.CleanseSkills()

        if not "Level" in self._obj:
            self._obj['Level'] = copy.deepcopy(EmptyLevelObject)
        self._level = self._obj['Level']['value']['value']

        if not "Exp" in self._obj:
            self._obj['Exp'] = copy.deepcopy(EmptyExpObject)
        # We don't store Exp yet

        self._nickname = ""
        if "NickName" in self._obj:
            self._nickname = self._obj['NickName']['value']

        self.isTower = self._type.IsTower()

        self._storedLocation = self._obj['SlotId']
        self.storageId = self._storedLocation["value"]["ContainerId"]["value"]["ID"]["value"]
        self.storageSlot = self._storedLocation["value"]["SlotIndex"]["value"]

        if not "EquipWaza" in self._obj:
            self._obj["EquipWaza"] = copy.deepcopy(EmptyMovesObject)

        if not "MasteredWaza" in self._obj:
            self._obj["MasteredWaza"] = copy.deepcopy(EmptyMovesObject)

        # EquipWaza = the equipped moves; MasteredWaza = moves taught BEYOND the
        # species' natural level-up learnset (fruit skills). The game derives
        # natural moves from species + level, so they must NOT be written into
        # MasteredWaza. _learntMoves is a display-only pool rebuilt by
        # CleanseAttacks; it is never written to the save.
        self._equipMoves = self._obj["EquipWaza"]["value"]["values"]
        self._masteredMoves = self._obj["MasteredWaza"]["value"]["values"]
        self._learntMoves = []
        self.CleanseAttacks()

        if not "Hp" in self._obj:
            self._obj["Hp"] = copy.deepcopy(EmptyHpObject)
        self.UpdateMaxHP()

        if "GotWorkSuitabilityAddRankList" not in self._obj:
            self._obj["GotWorkSuitabilityAddRankList"] = copy.deepcopy(EmptyGotWorkObject)
        self.AddSuits = self._obj["GotWorkSuitabilityAddRankList"]
        # The game only records work-suitability bonuses that are non-zero.
        # A zero-rank entry for every suitability (13 per pal) can interfere
        # with in-game work assignment, so prune zero-rank entries on load to
        # match what the game itself writes; SetSuit re-creates an entry only
        # when a real bonus is set.
        self.AddSuits["value"]["values"] = [
            x for x in self.AddSuits["value"]["values"] if x["Rank"]["value"] != 0
        ]
        # CraftSpeeds is a pre-1.0 field; 1.0 saves don't have it. Drop it on
        # load so re-saving matches the current format.
        self._obj.pop("CraftSpeeds", None)

    def IsAwakened(self):
        return self._obj["bIsAwakening"]["value"]

    def SetAwakened(self, value=None):
        if value == None:
            self._obj["bIsAwakening"]["value"] = (not self._obj["bIsAwakening"]["value"])
        else:
            self._obj["bIsAwakening"]["value"] = value
                
                
    def GetSuit(self, suit):
        for i in self.AddSuits["value"]["values"]:
            if i["WorkSuitability"]["value"]["value"] == f"EPalWorkSuitability::{suit}":
                return i["Rank"]["value"]
        return 0

    def SetSuit(self, suit, value):
        key = f"EPalWorkSuitability::{suit}"
        entries = self.AddSuits["value"]["values"]
        for i in entries:
            if i["WorkSuitability"]["value"]["value"] == key:
                if value == 0:
                    entries.remove(i)  # drop the entry rather than store a zero
                else:
                    i["Rank"]["value"] = value
                return
        if value != 0:
            t = copy.deepcopy(EmptyWorkObject)
            t["WorkSuitability"]["value"]["value"] = key
            t["Rank"]["value"] = value
            entries.append(t)

    def SetTrust(self, level):
        if level < -3 or level > 10: return

        # Need to add a way to maintain current friendship points between levels
        xt = trustthresholds[level+3]
        if level + 3 < len(trustthresholds):
            xt += self.extratrust
        self._obj["FriendshipPoint"]["value"] = self._trust = xt

    def GetTrust(self):
        xt = self._trust
        if self.GetTrustLevel() + 3 < len(trustthresholds):
            xt -= self.extratrust
        return xt

    def GetTrustLevel(self):
        for i in range(len(trustthresholds)):
            if trustthresholds[i] > self._trust:
                return (i-1) -3
        return (len(trustthresholds)-1)-3

    def IsHuman(self):
        return self._type._human

    def IsTower(self):
        return self._type._tower

    def SwapGender(self):
        if self._obj['Gender']['value']['value'] == "EPalGenderType::Male":
            self._obj['Gender']['value']['value'] = "EPalGenderType::Female"
            self._gender = "Female ♀"
        else:
            self._obj['Gender']['value']['value'] = "EPalGenderType::Male"
            self._gender = "Male ♂"

    def CleanseSkills(self):
        i = 0
        while i < len(self._skills):
            if self._skills[i].lower() == "none":
                self._skills.pop(i)
            else:
                i += 1

    def GetAvailableSkills(self):
        avail_skills = []
        for skill_codename in SkillExclusivity:
            if skill_codename == '':
                continue
            if SkillExclusivity[skill_codename] is None or self._type.GetCodeName() in SkillExclusivity[skill_codename]:
                avail_skills.append(skill_codename)

        avail_skills.sort(key=lambda e: PalAttacks[e])
        if "EPalWazaID::None" in avail_skills:
            avail_skills.remove("EPalWazaID::None")
        return avail_skills

    def _naturalMoves(self):
        """Moves the species learns by levelling, up to this pal's level."""
        learnset = PalLearnSet.get(self._type.GetCodeName(), {})
        return [m for m in learnset
                if self._level >= learnset[m] and m in PalAttacks]

    def _validMove(self, m):
        if m in ("None", "EPalWazaID::None") or "MAX" in m:
            return False
        excl = SkillExclusivity.get(m)
        return excl is None or self._type.GetCodeName() in excl

    def CleanseAttacks(self):
        """Rebuild the display move-pool and keep the save's move lists valid.

        MasteredWaza is pruned to only the *taught extras* (valid moves that
        are not part of the natural learnset); natural learnset moves are the
        game's to grant and must not be persisted there. EquipWaza is pruned of
        invalid moves. _learntMoves is a display-only union and is never saved.
        """
        natural = self._naturalMoves()
        # Prune MasteredWaza against the FULL species learnset (every level),
        # not just moves already learnable at this level: any learnset move is
        # the game's to grant and does not belong in MasteredWaza. This also
        # clears any learnset moves an earlier build may have stored here.
        full_learnset = set(PalLearnSet.get(self._type.GetCodeName(), {}))
        self._masteredMoves[:] = [m for m in self._masteredMoves
                                  if self._validMove(m) and m not in full_learnset]
        self._equipMoves[:] = [m for m in self._equipMoves if self._validMove(m)]
        pool = []
        for m in natural + self._masteredMoves + self._equipMoves:
            if m not in pool:
                pool.append(m)
        self._learntMoves[:] = pool

    def GetType(self):
        return self._type

    def SetType(self, value):
        self._obj['CharacterID']['value'] = ("BOSS_" if (self.isBoss or self.isLucky) and not self.IsHuman() else "") + value
        self._type = PalSpecies[value]
        self.CleanseAttacks()
        # NOTE: earlier versions also wrote a "CraftSpeeds" field here with the
        # new species' work ranks. Palworld 1.0 saves have no such field (the
        # game derives work suitability from species data + the
        # GotWorkSuitabilityAddRankList bonuses), so it is no longer written.

    def GetObject(self) -> PalObject:
        return self._type

    def GetGender(self):
        return self._gender

    #def GetWorkSpeed(self):
        #return self._workspeed

    #def SetWorkSpeed(self, value):
        #self._obj['CraftSpeed']['value'] = self._workspeed = value

    def SetAttack(self, mval, rval):
        # 1.0 has a single attack IV (Talent_Shot); melee is ignored
        self._obj['Talent_Shot']['value']["value"] = self._ranged = rval

    def GetTalentHP(self):
        return self._talent_hp

    def SetTalentHP(self, value):
        self._obj['Talent_HP']['value']["value"] = self._talent_hp = value

    # the soul bonus, 1 -> 3%, 10 -> 30%
    def GetRankHP(self):
        if "Rank_HP" in self._obj:
            return self._obj["Rank_HP"]["value"]["value"]
        return 0

    def GetRankAttack(self):
        if "Rank_Attack" in self._obj:
            return self._obj["Rank_Attack"]["value"]["value"]
        return 0

    def GetRankDefence(self):
        if "Rank_Defence" in self._obj:
            return self._obj["Rank_Defence"]["value"]["value"]
        return 0

    def GetRankWorkSpeed(self):
        if "Rank_CraftSpeed" in self._obj:
            return self._obj["Rank_CraftSpeed"]["value"]["value"]
        return 0

    def SetRankHP(self, value):
        if not "Rank_HP" in self._obj:
            self._obj["Rank_HP"] = copy.deepcopy(EmptySoulObject)
        self._obj["Rank_HP"]["value"]["value"] = value

    def SetRankAttack(self, value):
        if not "Rank_Attack" in self._obj:
            self._obj["Rank_Attack"] = copy.deepcopy(EmptySoulObject)
        self._obj["Rank_Attack"]["value"]["value"] = value

    def SetRankDefence(self, value):
        if not "Rank_Defence" in self._obj:
            self._obj["Rank_Defence"] = copy.deepcopy(EmptySoulObject)
        self._obj["Rank_Defence"]["value"]["value"] = value

    def SetRankWorkSpeed(self, value):
        if not "Rank_CraftSpeed" in self._obj:
            self._obj["Rank_CraftSpeed"] = copy.deepcopy(EmptySoulObject)
        self._obj["Rank_CraftSpeed"]["value"]["value"] = value

    def GetMaxHP(self):
        del self._obj['MaxHP']
        return # We dont need to get this anymore; its gone
    
        #return self._obj['MaxHP']['value']['Value']['value']

    def CalculateIngameStats(self, baseline=False):
        if self.GetObject().IsHuman():
            return {"HP": 1, "PHY": 0, "MAG": 0, "DEF": 0}
        """Computed in-game stats. With baseline=True, use the level-only
        values (IV 0, souls 0, condensation rank 1) — the 'standard' stats for
        this species at this level, for comparing against the pal's actual."""
        LEVEL = self.GetLevel()
        SCALING = self.GetObject().GetScaling()
        TRUST = self.GetObject().GetTrustScale()
        talent_hp = 0 if baseline else self.GetTalentHP()
        talent_at = 0 if baseline else self.GetAttackMelee()
        talent_rn = 0 if baseline else self.GetAttackRanged()
        talent_df = 0 if baseline else self.GetDefence()
        soul_hp = 0 if baseline else self.GetRankHP()
        soul_at = 0 if baseline else self.GetRankAttack()
        soul_df = 0 if baseline else self.GetRankDefence()
        rank = 1 if baseline else self.GetRank()
        fren = 1 if baseline else self.GetTrustLevel()

        if SCALING == None:
            print(self.GetObject().GetName())
        HP_SCALE = SCALING["HP"]
        if self.isBoss and "HP_BOSS" in SCALING:
            HP_SCALE = SCALING["HP_BOSS"]
        HP_IV = talent_hp * 0.3 / 100
        HP_SOUL = soul_hp * 0.03
        HP_RANK = (rank - 1) * 0.05

        HP_STAT = math.floor(500 + 5 * LEVEL + (HP_SCALE + TRUST["HP"] * fren) * 0.5 * LEVEL * (1 + HP_IV))
        HP_STAT = math.floor(HP_STAT * (1 + HP_SOUL) * (1 + HP_RANK))

        AT_SCALE = SCALING["PHY"]
        AT_IV = talent_at * 0.3 / 100
        AT_SOUL = soul_at * 0.03
        AT_RANK = (rank - 1) * 0.05

        AT_STAT = math.floor(100 + (AT_SCALE + TRUST["ATK"] * fren) * 0.075 * LEVEL * (1 + AT_IV))
        AT_STAT = math.floor(AT_STAT * (1 + AT_SOUL) * (1 + AT_RANK))

        MT_SCALE = SCALING["MAG"]
        MT_IV = talent_rn * 0.3 / 100
        MT_SOUL = soul_at * 0.03
        MT_RANK = (rank - 1) * 0.05

        MT_STAT = math.floor(100 + (MT_SCALE + TRUST["ATK"] * fren) * 0.075 * LEVEL * (1 + MT_IV))
        MT_STAT = math.floor(MT_STAT * (1 + MT_SOUL) * (1 + MT_RANK))

        DF_SCALE = SCALING["DEF"]
        DF_IV = talent_df * 0.3 / 100
        DF_SOUL = soul_df * 0.03
        DF_RANK = (rank - 1) * 0.05

        DF_STAT = math.floor(50 + (DF_SCALE + TRUST["DEF"] * fren) * 0.075 * LEVEL * (1 + DF_IV))
        DF_STAT = math.floor(DF_STAT * (1 + DF_SOUL) * (1 + DF_RANK))
        return {"HP": HP_STAT, "PHY": AT_STAT, "MAG": MT_STAT, "DEF": DF_STAT}


    def UpdateMaxHP(self):
        self._obj['Hp']['value']['Value']['value'] = self.CalculateIngameStats()["HP"] * 1000
        return #this seems to be handled by the game itself now; impressive
        
        if self.IsTower() or self.IsHuman():
            return
        new_hp = self.CalculateIngameStats()["HP"]
        self._obj['MaxHP']['value']['Value']['value'] = new_hp * 1000
        self._obj['Hp']['value']['Value']['value'] = new_hp * 1000

    def OLD_UpdateMaxHP(self, changes: dict, hp_scaling=None) -> bool:
        # do not manually pass in hp_scaling unless you are 100% sure that the value is correct!
        factors = {
            'level': self.GetLevel(),
            'rank': self.GetRank(),
            'hp_rank': self.GetRankHP(),
            'hp_iv': self.GetTalentHP()
        }

        old_hp = self.GetMaxHP()
        if hp_scaling is None:
            # assume old MaxHP is valid
            possible_hp_scaling = (old_hp / 1000 - 500 - 5 * factors['level']) / (
                    0.5 * factors['level'] * (1 + factors['hp_iv'] * 0.3 / 100) * (
                    1 + factors['hp_rank'] * 3 / 100) * (1 + (factors['rank'] - 1) * 5 / 100))
            print("--------")
            print("Derived Specie HP Scaling (from og MaxHP): %s" % possible_hp_scaling)
            hp_scaling = possible_hp_scaling
            specie_scaling = self.GetObject().GetScaling()
            if specie_scaling:
                bossKey = "HP_BOSS"
                key = "HP"
                if self.isBoss and bossKey in specie_scaling:
                    hp_scaling = specie_scaling[bossKey]
                else:
                    hp_scaling = specie_scaling[key]
                    if self.isBoss and abs(possible_hp_scaling - hp_scaling) > 1 and 'species' not in changes:
                        return (possible_hp_scaling, hp_scaling)
                print("%s HP Scaling: %s" % (self.GetName(), hp_scaling))
            else:
                print("HP scaling data missing, using derived value.")
        print("Calculating MaxHP using the following stats:")
        for valkey in factors:
            if valkey in changes:
                factors[valkey] = changes[valkey]
            print("- %s: %s" % (valkey, factors[valkey]))
        print("- hp_scaling: %s" % hp_scaling)

        new_hp = int((500 + 5 * factors['level'] + hp_scaling * 0.5 * factors['level'] * (
                1 + factors['hp_iv'] * 0.3 / 100) * (1 + factors['hp_rank'] * 3 / 100) * (
                              1 + (factors['rank'] - 1) * 5 / 100))) * 1000
        self._obj['MaxHP']['value']['Value']['value'] = new_hp
        self._obj['Hp']['value']['Value']['value'] = new_hp
        print("%s MaxHP: %s -> %s" % (self.GetFullName(), old_hp, new_hp))

    def GetAttackMelee(self):
        # 1.0 has no melee IV; the attack stat uses Talent_Shot. Mirror it so
        # CalculateIngameStats stays correct without a Talent_Melee field.
        return self._ranged

    def SetAttackMelee(self, value):
        # melee IV was removed in 1.0; keep the single attack IV (Talent_Shot)
        self.SetAttackRanged(value)

    def GetAttackRanged(self):
        return self._ranged

    def SetAttackRanged(self, value):
        self._obj['Talent_Shot']['value']["value"] = self._ranged = value

    def GetDefence(self):
        return self._defence

    def SetDefence(self, value):
        self._obj['Talent_Defense']['value']["value"] = self._defence = value

    def GetName(self):
        return self.GetObject().GetName()

    def GetCodeName(self):
        return self.GetObject().GetCodeName()

    def GetImage(self):
        return self.GetObject().GetImage()

    def GetPrimary(self):
        return self.GetObject().GetPrimary()

    def GetSecondary(self):
        return self.GetObject().GetSecondary()

    def GetSkills(self):
        self.CleanseSkills()
        return self._skills

    def SkillCount(self):
        return len(self._skills)

    def SetSkill(self, slot, skill):
        print("set slot %d  -> %s" % (slot, skill))
        if slot > len(self._skills) - 1:
            self._skills.append(skill)
        else:
            self._skills[slot] = skill

    def SetAttackSkill(self, slot, attack):
        # equipping a move the pal doesn't learn naturally requires it to be
        # recorded as a taught (mastered) move so the game accepts it
        if (attack not in ("None", "EPalWazaID::None")
                and attack not in self._naturalMoves()
                and attack not in self._masteredMoves):
            self._masteredMoves.append(attack)
        if slot > len(self._equipMoves) - 1:
            self._equipMoves.append(attack)
        else:
            self._equipMoves[slot] = attack
        self.CleanseAttacks()

    def GetOwner(self):
        return self.owner

    def GetLevel(self):
        return self._level

    def SetLevel(self, value):
        # We need this check until we fix adding missing nodes
        if "Level" in self._obj and "Exp" in self._obj:
            self._obj['Level']['value']["value"] = self._level = value
            self._obj['Exp']['value'] = xpthresholds[value - 1]
            self.CleanseAttacks()  # self.SetLevelMoves()
        else:
            print(f"[ERROR:] Failed to update level for: '{self.GetName()}'")

    ##    def SetLevelMoves(self):
    ##        value = self._level
    ##        self._obj["MasteredWaza"]["value"]["values"] = self._learntMoves = self._learntBackup[:]
    ##        for i in PalLearnSet[self._type.GetCodeName()]:
    ##            if value >= PalLearnSet[self._type.GetCodeName()][i]:
    ##                if not find(i) in self._obj["MasteredWaza"]["value"]["values"]:
    ##                    self._obj["MasteredWaza"]["value"]["values"].append(find(i))
    ##            elif find(i) in self._obj["MasteredWaza"]["value"]["values"]:
    ##                self._obj["MasteredWaza"]["value"]["values"].remove(find(i))
    ##
    ##        for i in self._equipMoves:
    ##            if not matches(self._type.GetCodeName(), i):
    ##                self._equipMoves.remove(i)
    ##                self._obj["EquipWaza"]["value"]["values"] = self._equipMoves
    ##            elif not i in self._obj["MasteredWaza"]["value"]["values"]:
    ##                self._obj["MasteredWaza"]["value"]["values"].append(i)
    ##
    ##        self._learntMoves = self._obj["MasteredWaza"]["value"]["values"]
    ##        print("------")
    ##        for i in self._learntMoves:
    ##            print(i)

    def GetRank(self):
        return self._rank

    def SetRank(self, value):
        if "Rank" in self._obj:
            self._obj['Rank']['value']["value"] = self._rank = value
            # we dont +1 here, since we have methods to patch rank in PalEdit.py
        else:
            print(
                f"[ERROR:] Failed to update rank for: '{self.GetName()}'")  # we probably could get rid of this line, since you add rank if missing - same with level

    def PurgeAttack(self, slot):
        # unequip: the move stays known; just clear the equip slot
        if slot >= len(self._equipMoves):
            return
        self._equipMoves.pop(slot)
        self.CleanseAttacks()

    def StripAttack(self, name):
        # forget a move entirely: drop it from equipped and taught lists. A
        # natural learnset move can't truly be forgotten (the game re-grants
        # it), so it simply reappears in the display after CleanseAttacks.
        name = name.replace("⚔", "").replace("🏹", "")
        if name in self._equipMoves:
            self._equipMoves.remove(name)
        if name in self._masteredMoves:
            self._masteredMoves.remove(name)
        self.CleanseAttacks()

    def FruitAttack(self, name):
        # teach a move: only non-natural moves need recording in MasteredWaza
        if name in ("None", "EPalWazaID::None") or not name:
            return
        if name not in self._naturalMoves() and name not in self._masteredMoves:
            self._masteredMoves.append(name)
        self.CleanseAttacks()

    def RemoveSkill(self, slot):
        if slot < len(self._skills):
            self._skills.pop(slot)

    def RemoveAttack(self, slot):
        if slot < len(self._equipMoves):
            self._equipMoves.pop(slot)
        self.CleanseAttacks()

    def GetNickname(self):
        return self.GetName() if self._nickname == "" else self._nickname

    def SetNickname(self, value):
        """Set (or clear, with "") the pal's custom name.

        Writes both NickName and, in Palworld 1.0, FilteredNickName — the
        game shows the filtered copy, so they must stay in sync. Creating
        either key when absent keeps older/world saves working too."""
        value = value or ""
        self._nickname = value
        for key in ("NickName", "FilteredNickName"):
            if key in self._obj:
                self._obj[key]['value'] = value
            elif value != "" or key == "NickName":
                self._obj[key] = {'id': None, 'value': value, 'type': 'StrProperty'}

    def GetFullName(self):
        return self.GetObject().GetName() + (" 💀" if self.isBoss else "") + (
            " ✨" if self.isLucky else "") + (" (Boss Rush)" if self.isBossRush else "") + (f" - '{self._nickname}'" if not self._nickname == "" else "")

    def SetLucky(self, v=True):
        self._obj["IsRarePal"]['value'] = self.isLucky = v
        self.SetType(self._type.GetCodeName())
        if v:
            if self.isBoss:
                self.isBoss = False

    def SetBoss(self, v=True):
        self.isBoss = v
        self.SetType(self._type.GetCodeName())
        if v:
            if self.isLucky:
                self.SetLucky(False)

    def GetEquippedMoves(self):
        return self._equipMoves

    def GetLearntMoves(self):
        return self._learntMoves

    def InitializationPal(self, newguid, player, group, slot, owneruid):
        self._data['key']['PlayerUId']['value'] = owneruid
        self._obj["OwnerPlayerUId"] = {
                "struct_type": "Guid",
                "struct_id": "00000000-0000-0000-0000-000000000000",
                "id": None,
                "value": player,
                "type": "StructProperty"
        }
        self._obj["OldOwnerPlayerUIds"]['value']['values'] = [player]
        self.SetPalInstanceGuid(newguid)
        self.SetSlotGuid(slot)
        self.SetGroupGuid(group)

    def GetGroupGuid(self):
        return self._data['value']['RawData']['value']['group_id']

    def SetGroupGuid(self, v: str):
        self._data['value']['RawData']['value']['group_id'] = v

    def GetSlotGuid(self):
        return self._obj['SlotId']['value']['ContainerId']['value']['ID']['value']

    def SetSlotGuid(self, v: str):
        self._obj['SlotId']['value']['ContainerId']['value']['ID']['value'] = v

    def GetSlotIndex(self):
        return self._obj['SlotId']['value']['SlotIndex']['value']

    def SetSoltIndex(self, v: int):
        self._obj['SlotId']['value']['SlotIndex']['value'] = v

    def GetPalInstanceGuid(self):
        return self._data['key']['InstanceId']['value']

    def SetPalInstanceGuid(self, v: str):
        self._data['key']['InstanceId']['value'] = v

    def GetOwner(self):
        return self._data['key']['PlayerUId']['value']


class PalGuid:
    def __init__(self, data):
        self._data = data
        self._CharacterSaveParameterMap = \
            data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        self._CharacterContainerSaveData = \
            data['properties']['worldSaveData']['value']['CharacterContainerSaveData']['value']
        self._GroupSaveDataMap = data['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']

    def GetPlayerslist(self):
        players = list(filter(lambda x: x['value'].get('IsPlayer', {}).get('value') is True, [
            {'uid': x['key']['PlayerUId'],
             'value': x['value']['RawData']['value']['object']['SaveParameter']['value']
             } for x in self._CharacterSaveParameterMap]))

        out = {}
        for x in players:
            g = str(x['uid']['value'])
            if g.replace("0", "").replace("-", "") == "1":
                out[x['value']['NickName']['value'] + " (HOST)"] = g
            elif not x['value']['NickName']['value'] in out:
                out[x['value']['NickName']['value']] = g
            else:
                v = 2
                while f"{x['value']['NickName']['value']} #{v}" in out:
                    v += 1
                out[x['value']['NickName']['value'] + f" #{v}"] = g
            
        return out #{x['value']['NickName']['value']: str(x['uid']['value']) for x in players}

    def ConvertGuid(guid_str):
        guid_str = guid_str
        guid = uuid.UUID(guid_str)
        guid_bytes = guid.bytes
        guid_list = [b for b in guid_bytes]
        result_list = [0] * 16
        for n in range(0, len(guid_list), 4):
            result_list.extend(guid_list[n:n + 4][::-1])
        result_list.append(0)
        result_list[12] = 1
        return result_list

    ZERO_GUID = "00000000-0000-0000-0000-000000000000"

    @staticmethod
    def _same_guid(left, right):
        return str(left).lower() == str(right).lower()

    @staticmethod
    def _is_unambiguously_non_player(save_parameter):
        if not isinstance(save_parameter, dict):
            return False
        if 'IsPlayer' not in save_parameter:
            return True
        marker = save_parameter['IsPlayer']
        return isinstance(marker, dict) and marker.get('value') is False

    @staticmethod
    def _validated_group_handles(group):
        try:
            handles = group['value']['RawData']['value'][
                'individual_character_handle_ids']
        except (KeyError, TypeError):
            return None
        if not isinstance(handles, list):
            return None
        for handle in handles:
            if (
                    not isinstance(handle, dict)
                    or not ({'guid', 'instance_id'} & handle.keys())
            ):
                return None
        return handles

    def _pal_guid_in_use(self, pal_guid):
        try:
            if any(
                    self._same_guid(
                        entry['key']['InstanceId']['value'], pal_guid)
                    for entry in self._CharacterSaveParameterMap
            ):
                return True
            for container in self._CharacterContainerSaveData:
                for slot in container['value']['Slots']['value']['values']:
                    if self._same_guid(
                            slot['RawData']['value']['instance_id'], pal_guid):
                        return True
            for group in self._GroupSaveDataMap:
                handles = self._validated_group_handles(group)
                if handles is None:
                    return True
                if any(self._handle_matches_pal(handle, pal_guid)
                       for handle in handles):
                    return True
        except (KeyError, TypeError):
            return True
        return False

    def _find_container(self, slot_guid):
        matches = [
            entry for entry in self._CharacterContainerSaveData
            if self._same_guid(entry['key']['ID']['value'], slot_guid)
        ]
        return matches[0] if len(matches) == 1 else None

    def _find_group(self, group_guid):
        matches = [
            entry for entry in self._GroupSaveDataMap
            if self._same_guid(entry['key'], group_guid)
        ]
        return matches[0] if len(matches) == 1 else None

    def _slot_template(self, container):
        slots = container['value']['Slots']['value']['values']
        if slots:
            return slots[0]
        for entry in self._CharacterContainerSaveData:
            other_slots = entry['value']['Slots']['value']['values']
            if other_slots:
                return other_slots[0]
        return None

    @staticmethod
    def _container_capacity(container):
        """Return (capacity, occupied indexes) only for a structurally valid container."""
        try:
            slot_num = container['value']['SlotNum']['value']
            slots = container['value']['Slots']['value']['values']
            indexes = [slot['SlotIndex']['value'] for slot in slots]
        except (KeyError, TypeError):
            return None
        if (
                not isinstance(slot_num, int)
                or slot_num < 0
                or len(slots) > slot_num
                or len(set(indexes)) != len(indexes)
                or any(not isinstance(index, int) or index < 0 or index >= slot_num
                       for index in indexes)
        ):
            return None
        return slot_num, set(indexes)

    def GetContainerSlot(self, slot_guid, pal_guid):
        container = self._find_container(slot_guid)
        if container is None:
            return None
        for slot in container['value']['Slots']['value']['values']:
            instance_id = slot['RawData']['value']['instance_id']
            if self._same_guid(instance_id, pal_guid):
                return slot
        return None

    def SetContainerSave(self, SoltGuid: str, SlotIndex: int, PalGuid: str):
        if any(self._same_guid(guid, self.ZERO_GUID) for guid in [SoltGuid, PalGuid]):
            return False
        container = self._find_container(SoltGuid)
        if container is None:
            return False
        capacity = self._container_capacity(container)
        if capacity is None:
            return False
        slot_num, occupied = capacity
        slots = container['value']['Slots']['value']['values']
        if SlotIndex < 0 or SlotIndex >= slot_num:
            return False
        if SlotIndex in occupied:
            return False
        if self.GetContainerSlot(SoltGuid, PalGuid) is not None:
            return False
        template = self._slot_template(container)
        if template is None:
            return False
        slot = copy.deepcopy(template)
        slot['SlotIndex']['value'] = SlotIndex
        slot['RawData']['value']['player_uid'] = self.ZERO_GUID
        slot['RawData']['value']['instance_id'] = PalGuid
        slots.append(slot)
        return True

    def RemovePal(self, SoltGuid: str, SlotIndex: int, PalGuid: str):
        if any(self._same_guid(guid, self.ZERO_GUID) for guid in [SoltGuid, PalGuid]):
            return False
        container = self._find_container(SoltGuid)
        if container is None:
            return False
        slots = container['value']['Slots']['value']['values']
        for index, slot in enumerate(slots):
            if (
                    slot['SlotIndex']['value'] == SlotIndex
                    and self._same_guid(slot['RawData']['value']['instance_id'], PalGuid)
            ):
                slots.pop(index)
                return True
        return False
        

    def AddGroupSaveData(self, GroupGuid: str, PalGuid: str):
        if any(self._same_guid(guid, self.ZERO_GUID) for guid in [GroupGuid, PalGuid]):
            return False
        group = self._find_group(GroupGuid)
        handles = self._validated_group_handles(group) if group is not None else None
        if (
                handles is None
                or self.GroupContainsPal(GroupGuid, PalGuid)
        ):
            return False
        handles.append({"guid": self.ZERO_GUID, "instance_id": PalGuid})
        return True

    def _handle_matches_pal(self, handle, pal_guid):
        guid = handle.get('guid', self.ZERO_GUID)
        instance_id = handle.get('instance_id', self.ZERO_GUID)
        return (
            self._same_guid(guid, self.ZERO_GUID)
            and self._same_guid(instance_id, pal_guid)
        ) or (
            self._same_guid(instance_id, self.ZERO_GUID)
            and self._same_guid(guid, pal_guid)
        )

    def GroupContainsPal(self, GroupGuid: str, PalGuid: str):
        group = self._find_group(GroupGuid)
        handles = self._validated_group_handles(group) if group is not None else None
        if handles is None:
            return False
        return any(self._handle_matches_pal(handle, PalGuid) for handle in handles)

    def RemoveGroupSaveData(self, GroupGuid: str, PalGuid: str):
        if any(self._same_guid(guid, self.ZERO_GUID) for guid in [GroupGuid, PalGuid]):
            return False
        group = self._find_group(GroupGuid)
        handles = self._validated_group_handles(group) if group is not None else None
        if handles is None:
            return False
        for index, handle in enumerate(handles):
            if self._handle_matches_pal(handle, PalGuid):
                handles.pop(index)
                return True
        return False

    def GetSoltMaxCount(self, SoltGuid: str):
        if self._same_guid(SoltGuid, self.ZERO_GUID):
            return 0
        container = self._find_container(SoltGuid)
        if container is not None:
            return container['value']['SlotNum']['value']
        return 0

    def GetEmptySlotIndex(self, SoltGuid: str):
        if self._same_guid(SoltGuid, self.ZERO_GUID):
            return -1
        container = self._find_container(SoltGuid)
        if container is not None:
            capacity = self._container_capacity(container)
            if capacity is None:
                return -1
            slot_num, occupied = capacity
            for index in range(slot_num):
                if index not in occupied:
                    return index
        return -1

    @staticmethod
    def _pal_entry_fields(entry):
        raw_data = entry['value']['RawData']['value']
        save_parameter = raw_data['object']['SaveParameter']['value']
        return raw_data, save_parameter

    def InsertPal(self, source, player_guid, group_guid, slot_guid, owner_uid,
                  new_guid=None):
        """Insert a copied pal and all world references as one checked operation."""
        if any(value is None for value in [source, player_guid, group_guid, slot_guid]):
            return None
        try:
            source_player_uid = source['key']['PlayerUId']['value']
        except (KeyError, TypeError):
            return None
        if (
                not self._same_guid(source_player_uid, self.ZERO_GUID)
                or not self._same_guid(owner_uid, self.ZERO_GUID)
        ):
            return None
        if self._find_container(slot_guid) is None or self._find_group(group_guid) is None:
            return None
        slot_index = self.GetEmptySlotIndex(slot_guid)
        if slot_index < 0:
            return None
        new_guid = str(new_guid or uuid.uuid4())
        if self._pal_guid_in_use(new_guid):
            return None

        inserted = copy.deepcopy(source)
        try:
            raw_data, save_parameter = self._pal_entry_fields(inserted)
            if not self._is_unambiguously_non_player(save_parameter):
                return None
            inserted['key']['PlayerUId']['value'] = self.ZERO_GUID
            inserted['key']['InstanceId']['value'] = new_guid
            save_parameter['OwnerPlayerUId']['value'] = player_guid
            save_parameter['OldOwnerPlayerUIds']['value']['values'] = [player_guid]
            raw_data['group_id'] = group_guid
            slot_id = save_parameter['SlotId']['value']
            slot_id['ContainerId']['value']['ID']['value'] = slot_guid
            slot_id['SlotIndex']['value'] = slot_index
        except (KeyError, TypeError):
            return None

        container = self._find_container(slot_guid)
        group = self._find_group(group_guid)
        slots = container['value']['Slots']['value']['values']
        handles = group['value']['RawData']['value'][
            'individual_character_handle_ids']
        character_count = len(self._CharacterSaveParameterMap)
        slot_count = len(slots)
        handle_count = len(handles)
        try:
            if not self.SetContainerSave(slot_guid, slot_index, new_guid):
                raise ValueError("Container insertion failed after preflight.")
            if not self.AddGroupSaveData(group_guid, new_guid):
                raise ValueError("Guild insertion failed after preflight.")
            self._CharacterSaveParameterMap.append(inserted)
        except Exception:
            del self._CharacterSaveParameterMap[character_count:]
            del slots[slot_count:]
            del handles[handle_count:]
            return None
        return inserted

    def InsertPals(self, sources, player_guid, group_guid, slot_guid, owner_uids,
                   new_guids=None):
        """Insert a batch only when every source can be placed safely."""
        sources = list(sources)
        owner_uids = list(owner_uids)
        if not sources or len(sources) != len(owner_uids):
            return None
        if any(not self._same_guid(owner_uid, self.ZERO_GUID)
               for owner_uid in owner_uids):
            return None
        container = self._find_container(slot_guid)
        if container is None or self._find_group(group_guid) is None:
            return None
        capacity = self._container_capacity(container)
        if capacity is None:
            return None
        slot_num, occupied = capacity
        if slot_num - len(occupied) < len(sources) or self._slot_template(container) is None:
            return None

        if new_guids is None:
            new_guids = [str(uuid.uuid4()) for _ in sources]
        else:
            new_guids = [str(value) for value in new_guids]
        if len(new_guids) != len(sources) or len(set(new_guids)) != len(new_guids):
            return None
        if any(self._pal_guid_in_use(value) for value in new_guids):
            return None

        for source in sources:
            try:
                _, save_parameter = self._pal_entry_fields(copy.deepcopy(source))
                if (
                        not self._same_guid(
                            source['key']['PlayerUId']['value'], self.ZERO_GUID)
                        or not self._is_unambiguously_non_player(save_parameter)
                ):
                    return None
                save_parameter['OwnerPlayerUId']['value']
                save_parameter['OldOwnerPlayerUIds']['value']['values']
                save_parameter['SlotId']['value']['ContainerId']['value']['ID']['value']
                save_parameter['SlotId']['value']['SlotIndex']['value']
            except (KeyError, TypeError):
                return None

        slots = container['value']['Slots']['value']['values']
        group = self._find_group(group_guid)
        handles = group['value']['RawData']['value'][
            'individual_character_handle_ids']
        character_count = len(self._CharacterSaveParameterMap)
        slot_count = len(slots)
        handle_count = len(handles)
        inserted = []
        try:
            for source, owner_uid, new_guid in zip(sources, owner_uids, new_guids):
                entry = self.InsertPal(
                    source, player_guid, group_guid, slot_guid, owner_uid, new_guid)
                if entry is None:
                    raise ValueError("Pal insertion failed after preflight.")
                inserted.append(entry)
        except Exception:
            del self._CharacterSaveParameterMap[character_count:]
            del slots[slot_count:]
            del handles[handle_count:]
            return None
        return inserted

    def DeletePalEntry(self, entry, acting_player_guid):
        """Delete a pal only when its character and container references agree."""
        if entry not in self._CharacterSaveParameterMap or acting_player_guid is None:
            return False
        try:
            raw_data, save_parameter = self._pal_entry_fields(entry)
            if (
                    not self._same_guid(
                        entry['key']['PlayerUId']['value'], self.ZERO_GUID)
                    or not self._is_unambiguously_non_player(save_parameter)
                    or not self._same_guid(
                        save_parameter['OwnerPlayerUId']['value'],
                        acting_player_guid)
            ):
                return False
            pal_guid = entry['key']['InstanceId']['value']
            group_guid = raw_data['group_id']
            slot_id = save_parameter['SlotId']['value']
            slot_guid = slot_id['ContainerId']['value']['ID']['value']
            slot_index = slot_id['SlotIndex']['value']
        except (KeyError, TypeError):
            return False
        matching_entries = sum(
            self._same_guid(
                candidate['key']['InstanceId']['value'], pal_guid)
            for candidate in self._CharacterSaveParameterMap
        )
        if matching_entries != 1:
            return False
        container = self._find_container(slot_guid)
        if container is None:
            return False
        matching_slots = []
        try:
            for candidate_container in self._CharacterContainerSaveData:
                for candidate_slot in candidate_container[
                        'value']['Slots']['value']['values']:
                    if self._same_guid(
                            candidate_slot['RawData']['value']['instance_id'],
                            pal_guid):
                        matching_slots.append((candidate_container, candidate_slot))
        except (KeyError, TypeError):
            return False
        if len(matching_slots) != 1:
            return False
        matched_container, slot = matching_slots[0]
        if (
                matched_container is not container
                or slot['SlotIndex']['value'] != slot_index
        ):
            return False
        group = self._find_group(group_guid)
        if group is None:
            return False
        matching_handles = []
        for candidate_group in self._GroupSaveDataMap:
            handles = self._validated_group_handles(candidate_group)
            if handles is None:
                return False
            for handle in handles:
                if self._handle_matches_pal(handle, pal_guid):
                    matching_handles.append(candidate_group['key'])
        if (
                len(matching_handles) != 1
                or not self._same_guid(matching_handles[0], group_guid)
        ):
            return False

        slots = container['value']['Slots']['value']['values']
        handles = group['value']['RawData']['value'][
            'individual_character_handle_ids']
        handle = next(
            candidate for candidate in handles
            if self._handle_matches_pal(candidate, pal_guid))
        character_index = self._CharacterSaveParameterMap.index(entry)
        slot_position = slots.index(slot)
        handle_position = handles.index(handle)
        try:
            if not self.RemovePal(slot_guid, slot_index, pal_guid):
                raise ValueError("Container removal failed after preflight.")
            if not self.RemoveGroupSaveData(group_guid, pal_guid):
                raise ValueError("Guild removal failed after preflight.")
            self._CharacterSaveParameterMap.remove(entry)
        except Exception:
            if not any(candidate is entry
                       for candidate in self._CharacterSaveParameterMap):
                self._CharacterSaveParameterMap.insert(character_index, entry)
            if not any(candidate is slot for candidate in slots):
                slots.insert(slot_position, slot)
            if not any(candidate is handle for candidate in handles):
                handles.insert(handle_position, handle)
            return False
        return True

    def GetAdminGuid(self):
        for e in self._GroupSaveDataMap:
            if "admin_player_uid" in e['value']['RawData']['value']:
                return e['value']['RawData']['value']['admin_player_uid']

    def GetAdminGroupGuid(self):
        for e in self._GroupSaveDataMap:
            if "admin_player_uid" in e['value']['RawData']['value']:
                return e['key']

    def GetGroupGuid(self, playerguid):        
        matches = []
        for e in self._GroupSaveDataMap:
            if "players" in e['value']['RawData']['value']:
                for player in e['value']['RawData']['value']['players']:
                    if player['player_uid'] == playerguid:
                        matches.append(e['key'])
        return matches[0] if len(matches) == 1 else None

    def RemanePlayer(self, PlayerGuid: str, NewName: str):
        for e in self._GroupSaveDataMap:
            if "players" in e['value']['RawData']['value']:
                for p in e['value']['RawData']['value']['players']:
                    if p['player_uid'] == PlayerGuid:
                        p['player_info']['player_name'] = NewName

    def Save(self, svdata):
        if 'properties' in svdata:
            svdata['properties']['worldSaveData']['value']['CharacterContainerSaveData'][
                'value'] = self._CharacterContainerSaveData
            svdata['properties']['worldSaveData']['value']['GroupSaveDataMap']['value'] = self._GroupSaveDataMap
        return svdata


class PalPlayerEntity:
    def __init__(self, data):
        self._data = data
        self._obj = self._data['properties']['SaveData']['value']
        self._record = self._obj['RecordData']['value']
        self._inventoryinfo = self._obj['InventoryInfo']['value']

    def GetPlayerGuid(self):
        return self._obj['PlayerUId']['value']

    def GetPlayerIndividualId(self):
        return self._obj['IndividualId']['value']['InstanceId']['value']

    def GetTravelPalInventoryGuid(self):
        return self._obj['OtomoCharacterContainerId']['value']['ID']['value']

    def GetPalStorageGuid(self):
        return self._obj['PalStorageContainerId']['value']['ID']['value']

    def GetCommonItemInventoryGuid(self):
        self._inventoryinfo['CommonContainerId']['value']['ID']['value']

    def GetKeyItemInventoryGuid(self):
        self._inventoryinfo['EssentialContainerId']['value']['ID']['value']

    def GetWeaponLoadOutInventoryGuid(self):
        self._inventoryinfo['WeaponLoadOutContainerId']['value']['ID']['value']

    def GetFoodInventoryGuid(self):
        self._inventoryinfo['FoodEquipContainerId']['value']['ID']['value']

    def GetPlayerEquipArmorGuid(self):
        self._inventoryinfo['PlayerEquipArmorContainerId']['value']['ID']['value']

    def SetLifmunkEffigyCount(self, v: int):
        if 'RelicPossessNum' in self._record:
            self._record['RelicPossessNum']['value'] = v
        else:
            self._record['RelicPossessNum'] = {'id': None, 'value': v, 'type': 'IntProperty'}

    def SetTechnologyPoint(self, v: int):
        self._obj['TechnologyPoint']['value'] = v

    def SetAncientTechnologyPoint(self, v: int):
        self._obj['bossTechnologyPoint']['value'] = v

    def dump(self):
        return self._data


class PalStoragePlayer:
    """Pseudo-player used when editing GlobalPalStorage.sav (Palworld 1.0
    Global Palbox), which has no player or container data."""

    def __init__(self, guid="00000000-0000-0000-0000-000000000000"):
        self._guid = guid

    def GetPlayerGuid(self):
        return self._guid

    def GetTravelPalInventoryGuid(self):
        return None

    def GetPalStorageGuid(self):
        return None


with open("%s/resources/data/elements.json" % (module_dir), "r", encoding="utf8") as elementfile:
    PalElements = {}
    for i in json.loads(elementfile.read())["values"]:
        PalElements[i['Name']] = i['Color']

PalSpecies = {}
# lowercase CodeName -> canonical CodeName, so a save's CharacterID can be
# matched case-insensitively (Unreal FNames compare without regard to case)
PalSpeciesLower = {}
# PalLearnSet: Pal Skills require Level
PalLearnSet = {}


def LoadPals(lang="en-GB"):
    global PalSpecies, PalLearnSet, PalSpeciesLower

    if lang == "":
        lang = "en-GB"

    if lang is not None and not os.path.exists(f"%s/resources/data/{lang}/pals.json" % (module_dir)):
        lang = "en-GB"
    
    #with open("%s/resources/data/pals.json" % (module_dir), "r",
              #encoding="utf8") as datafile:

        
    with open(f"%s/resources/data/{lang}/pals.json" % (module_dir), "r",
              encoding="utf8") as palfile:

        d = {"values": []}

        for path, folders, files in os.walk("%s/resources/data/pals" % (module_dir)):
            for filename in files:
                with open(f"%s/resources/data/pals/{filename}" % (module_dir), "r") as pf:
                    d["values"].append(json.loads(pf.read()))
                    
        PalSpecies = {}
        PalLearnSet = {}

        #d = json.loads(datafile.read())
        l = json.loads(palfile.read())
        
        for i in d["values"]:
            h = i["Human"] if "Human" in i else False
            t = "Tower" in i
            p = i["Type"][0]
            s = "None"
            if len(i["Type"]) == 2:
                s = i["Type"][1]
            PalSpecies[i["CodeName"]] = PalObject(l[i["CodeName"]] if i["CodeName"] in l else i["CodeName"], i["CodeName"], p, s, h, t,
                                                  i["Scaling"] if "Scaling" in i else None,
                                                  i["Trust"] if "Trust" in i else None,
                                                  i["Suitabilities"] if "Suitabilities" in i else {})
            PalSpecies[i["CodeName"]]._innate_passives = i.get("InnatePassives", [])
            PalSpecies[i["CodeName"]]._deck_index = i.get("DeckIndex", -1)
            PalSpecies[i["CodeName"]]._tower_boss = i.get("TowerBoss", False)
            if t:
                PalSpecies[i["CodeName"]]._suits = PalSpecies[i["CodeName"].replace("GYM_", "")]._suits
                PalSpecies[i["CodeName"]]._scaling = PalSpecies[i["CodeName"].replace("GYM_", "")]._scaling
                PalSpecies[i["CodeName"]]._trustscale = PalSpecies[i["CodeName"].replace("GYM_", "")]._trustscale
            PalLearnSet[i["CodeName"]] = i["Moveset"] if not t else PalLearnSet[i["CodeName"].replace("GYM_", "")]

        # index by lowercased CodeName for the case-insensitive lookup below
        PalSpeciesLower = {code.lower(): code for code in PalSpecies}


LoadPals()

PalPassives = {}
PassiveDescriptions = {}
PassiveRating = {}
PassiveRollable = {}
PassiveGroup = {}


def LoadPassives(lang="en-GB"):
    global PalPassives, PassiveDescriptions, PassiveRating, PassiveRollable, PassiveGroup

    PalPassives = {}
    PassiveDescriptions = {}
    PassiveRating = {}
    PassiveRollable = {}
    PassiveGroup = {}

    if lang == "":
        lang = "en-GB"

    if lang is not None and not os.path.exists(f"%s/resources/data/{lang}/passives.json" % (module_dir)):
        lang = "en-GB"

    with open("%s/resources/data/passives.json" % (module_dir), "r",
              encoding="utf8") as datafile:
        with open(f"%s/resources/data/{lang}/passives.json" % (module_dir), "r",
                  encoding="utf8") as passivefile:

            d = json.loads(datafile.read())
            l = json.loads(passivefile.read())

            for i in d:
                code = i
                PalPassives[code] = l[code]["Name"]
                PassiveDescriptions[code] = l[code]["Description"]
                PassiveRating[code] = d[i]["Rating"]
                # default True so passives without data are never hidden
                PassiveRollable[code] = d[i].get("Rollable", True)
                PassiveGroup[code] = d[i].get("Group", "Other")
                #print(i, l[code]["Name"])
            PalPassives = dict(sorted(PalPassives.items()))

LoadPassives()

def GetLegalPassives(species_code):
    """Passive codes a pal of this species can normally have: any passive
    that rolls on wild/lucky pals plus the species' innate passives."""
    innate = []
    if species_code in PalSpecies:
        innate = getattr(PalSpecies[species_code], "_innate_passives", [])
    return [c for c in PalPassives
            if c not in ("NONE", "UNKNOWN", "None", "Unknown")
            and (PassiveRollable.get(c, True) or c in innate)]

# PalAttacks CodeName -> Name
PalAttacks = {}
AttackPower = {}
AttackTypes = {}
AttackCats = {}
SkillExclusivity = {}


def LoadAttacks(lang="en-GB"):
    global PalAttacks, AttackPower, AttackTypes, AttackCats, SkillExclusivity

    if lang == "":
        lang = "en-GB"

    if lang is not None and not os.path.exists(f"%s/resources/data/{lang}/attacks.json" % (module_dir)):
        lang = "en-GB"

    #with open("%s/resources/data/attacks.json" % (module_dir), "r",
              #encoding="utf8") as datafile:
        
    with open(f"%s/resources/data/{lang}/attacks.json" % (module_dir), "r",
              encoding="utf8") as attackfile:
        PalAttacks = {}
        AttackPower = {}
        AttackTypes = {}
        AttackCats = {}
        SkillExclusivity = {}

        d = {}

        for path, folders, files in os.walk("%s/resources/data/attacks" % (module_dir)):
            for filename in files:
                with open(f"%s/resources/data/attacks/{filename}" % (module_dir), "r") as pf:
                    r = json.loads(pf.read())
                    d[r["CodeName"]] = r

        #d = json.loads(datafile.read())
        l = json.loads(attackfile.read())

        #debugOutput = d["values"]
        

        for i in d:
            code = i
            PalAttacks[code] = l[code] if code in l else code
            AttackPower[code] = d[i]["Power"]
            AttackTypes[code] = d[i]["Type"]
            AttackCats[code] = d[i]["Category"]
            if "Exclusive" in d[i]:
                SkillExclusivity[code] = d[i]["Exclusive"]
            else:
                SkillExclusivity[code] = None

        PalAttacks = dict(sorted(PalAttacks.items()))

LoadAttacks()


def find(name):
    for i in PalSpecies:
        if PalSpecies[i].GetName() == name:
            return i
    for i in PalPassives:
        if PalPassives[i] == name:
            return i
    for i in PalAttacks:
        if PalAttacks[i] == name:
            return i
    return "None"

if __name__ == "__main__":
    # Debug algorithms go here

    #from PIL import ImageTk, Image
    #Image.open(f'../assets/Bellanoir.png').resize((240, 240)).save(f"resources/pals/NightLady.png")
    #Image.open(f'../assets/Bellanoir Libero.png').resize((240, 240)).save(f"resources/pals/NightLady_Dark.png")

    #for i in PalSpecies:
        #print (i)    
    pass


def RecieveLogger(l):
    global logger
    logger = l
