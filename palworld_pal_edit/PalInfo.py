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
    2147483647,
    2147483647,
    2147483647,
    2147483647,
    2147483647,
    2147483647,
    2147483647,
    2147483647,
    2147483647,
    2147483647,
    2147483647,
    2147483647,
    2147483647,
    2147483647
]
if len(xpthresholds) < 60:
    raise Exception("Something is wrong with the thresholds")


class PalGender(Enum):
    MALE = "#02A3FE"
    FEMALE = "#EC49A6"
    UNKNOWN = "darkgrey"


class PalObject:
    def __init__(self, name, code_name, primary, secondary="None", human=False, tower=False, scaling=None, suits={}):
        self._name = name
        self._code_name = code_name
        self._img = None
        self._primary = primary
        self._secondary = secondary
        self._human = human
        self._tower = tower
        self._scaling = scaling
        self._suits = suits

    def GetName(self):
        return PalSpecies[self._code_name]._name # Update PalEdit.listdisplay

    def GetCodeName(self):
        return self._code_name

    def IsTower(self):
        return self._tower

    def GetImage(self):
        if self._img == None:
            n = self.GetCodeName() if not self._human else "CommonHuman"
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


class PalEntity:

    def __init__(self, data):
        global logger

        self._data = data
        self._obj = data['value']['RawData']['value']['object']['SaveParameter']['value']

        self.owner = ""
        if "SlotID" in self._obj:
            self.owner = self._obj["SlotID"]['value']["ContainerId"]['value']['ID']['value']

        if "IsPlayer" in self._obj:
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
        if typename.lower() == "sheepball":
            print(typename)
            typename = "SheepBall"

            # Strangely, Boss and Lucky Lamballs have camelcasing
            # Regular ones... don't
        # print(f"Debug: typename3 - '{typename}'")

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

        if not "Talent_Melee" in self._obj:
            self._obj['Talent_Melee'] = copy.deepcopy(EmptyTalentObject)
        self._melee = self._obj['Talent_Melee']['value']["value"]

        if not "Talent_Shot" in self._obj:
            self._obj['Talent_Shot'] = copy.deepcopy(EmptyTalentObject)
        self._ranged = self._obj['Talent_Shot']['value']["value"]

        if not "Talent_Defense" in self._obj:
            self._obj['Talent_Defense'] = copy.deepcopy(EmptyTalentObject)
        self._defence = self._obj['Talent_Defense']['value']["value"]

        if not "Rank" in self._obj:
            self._obj['Rank'] = copy.deepcopy(EmptyRankObject)
        self._rank = self._obj['Rank']['value']['value']

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

        self._storedLocation = self._obj['SlotID']
        self.storageId = self._storedLocation["value"]["ContainerId"]["value"]["ID"]["value"]
        self.storageSlot = self._storedLocation["value"]["SlotIndex"]["value"]

        if not "EquipWaza" in self._obj:
            self._obj["EquipWaza"] = copy.deepcopy(EmptyMovesObject)

        if not "MasteredWaza" in self._obj:
            self._obj["MasteredWaza"] = copy.deepcopy(EmptyMovesObject)

        self._learntMoves = self._obj["MasteredWaza"]["value"]["values"]
        self._equipMoves = self._obj["EquipWaza"]["value"]["values"]

        self.CleanseAttacks()
        if not "Hp" in self._obj:
            self._obj["Hp"] = copy.deepcopy(EmptyHpObject)
        self.UpdateMaxHP()

        if "GotWorkSuitabilityAddRankList" not in self._obj:
            self._obj["GotWorkSuitabilityAddRankList"] = copy.deepcopy(EmptyGotWorkObject)
        self.AddSuits = self._obj["GotWorkSuitabilityAddRankList"]
        for i in suitnames:
            if i not in self.AddSuits:
                t = copy.deepcopy(EmptyWorkObject)
                t["WorkSuitability"]["value"]["value"] = f"EPalWorkSuitability::{i}"
                self.AddSuits["value"]["values"].append(t)
                
                
        
        

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
        avail_skills.remove("None")
        return avail_skills

    def CleanseAttacks(self):
        i = 0
        while i < len(self._learntMoves):
            remove = False
            if self._learntMoves[i] in ["None", "EPalWazaID::None"]:
                remove = True
            else:
                # Check skill has Exclusivity
                if not (SkillExclusivity[self._learntMoves[i]] is None):
                    if not self._type.GetCodeName() in SkillExclusivity[self._learntMoves[i]]:
                        remove = True
                # Check level are available for Skills
                if self._learntMoves[i] in PalLearnSet[self._type.GetCodeName()]:
                    if not self._level >= PalLearnSet[self._type.GetCodeName()][self._learntMoves[i]]:
                        if not self._learntMoves[i] in self._equipMoves:
                            remove = True

            if remove:
                if self._learntMoves[i] in self._equipMoves:
                    self._equipMoves.remove(self._learntMoves[i])
                self._learntMoves.pop(i)
            else:
                i += 1

        for skill_CodeName in PalLearnSet[self._type.GetCodeName()]:
            if not skill_CodeName in self._learntMoves:
                if PalLearnSet[self._type.GetCodeName()][skill_CodeName] <= self._level:
                    self._learntMoves.append(skill_CodeName)

        for i in self._equipMoves:
            if not i in self._learntMoves:
                self._learntMoves.append(i)

    def GetType(self):
        return self._type

    def SetType(self, value):
        self._obj['CharacterID']['value'] = ("BOSS_" if (self.isBoss or self.isLucky) and not self.IsHuman() else "") + value
        self._type = PalSpecies[value]
        self.CleanseAttacks()

        if self.IsHuman(): return
        
        ss = copy.deepcopy(EmptySuitObject)
        for i in ss["value"]["values"]:
            t = i["WorkSuitability"]["value"]["value"].split("::")[1]
            i["Rank"]["value"] = self._type._suits[t]
        self._obj["CraftSpeeds"] = ss

    def GetObject(self) -> PalObject:
        return self._type

    def GetGender(self):
        return self._gender

    #def GetWorkSpeed(self):
        #return self._workspeed

    #def SetWorkSpeed(self, value):
        #self._obj['CraftSpeed']['value'] = self._workspeed = value

    def SetAttack(self, mval, rval):
        self._obj['Talent_Melee']['value']["value"] = self._melee = mval
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

    def CalculateIngameStats(self):
        LEVEL = self.GetLevel()
        SCALING = self.GetObject().GetScaling()

        HP_SCALE = SCALING["HP"]
        if self.isBoss and "HP_BOSS" in SCALING:
            HP_SCALE = SCALING["HP_BOSS"]
        HP_IV = self.GetTalentHP() * 0.3 / 100
        HP_SOUL = self.GetRankHP() * 0.03
        HP_RANK = (self.GetRank() - 1) * 0.05
        HP_BONUS = 0

        HP_STAT = math.floor(500 + 5 * LEVEL + HP_SCALE * 0.5 * LEVEL * (1 + HP_IV))
        HP_STAT = math.floor(HP_STAT * (1 + HP_BONUS) * (1 + HP_SOUL) * (1 + HP_RANK))

        AT_SCALE = SCALING["PHY"]
        AT_IV = self.GetAttackMelee() * 0.3 / 100
        AT_SOUL = self.GetRankAttack() * 0.03
        AT_RANK = (self.GetRank() - 1) * 0.05
        AT_BONUS = 0

        AT_STAT = math.floor(100 + AT_SCALE * 0.075 * LEVEL * (1 + AT_IV))
        AT_STAT = math.floor(AT_STAT * (1 + AT_BONUS) * (1 + AT_SOUL) * (1 + AT_RANK))

        MT_SCALE = SCALING["MAG"]
        MT_IV = self.GetAttackRanged() * 0.3 / 100
        MT_SOUL = self.GetRankAttack() * 0.03
        MT_RANK = (self.GetRank() - 1) * 0.05
        MT_BONUS = 0

        MT_STAT = math.floor(100 + MT_SCALE * 0.075 * LEVEL * (1 + MT_IV))
        MT_STAT = math.floor(MT_STAT * (1 + MT_BONUS) * (1 + MT_SOUL) * (1 + MT_RANK))

        DF_SCALE = SCALING["DEF"]
        DF_IV = self.GetDefence() * 0.3 / 100
        DF_SOUL = self.GetRankDefence() * 0.03
        DF_RANK = (self.GetRank() - 1) * 0.05
        DF_BONUS = 0

        DF_STAT = math.floor(50 + DF_SCALE * 0.075 * LEVEL * (1 + DF_IV))
        DF_STAT = math.floor(DF_STAT * (1 + DF_BONUS) * (1 + DF_SOUL) * (1 + DF_RANK))
        return {"HP": HP_STAT, "PHY": AT_STAT, "MAG": MT_STAT, "DEF": DF_STAT}


    def UpdateMaxHP(self):
        return #this seems to be handled by the game itself now; impressive
        
        if self.IsTower() or self.IsHuman():
            return
        new_hp = self.CalculateIngameStats()["HP"]
        self._obj['MaxHP']['value']['Value']['value'] = new_hp * 1000
        self._obj['HP']['value']['Value']['value'] = new_hp * 1000

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
        self._obj['HP']['value']['Value']['value'] = new_hp
        print("%s MaxHP: %s -> %s" % (self.GetFullName(), old_hp, new_hp))

    def GetAttackMelee(self):
        return self._melee

    def SetAttackMelee(self, value):
        self._obj['Talent_Melee']['value']["value"] = self._melee = value

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
        if slot >= len(self._equipMoves):
            return
        p = self._equipMoves.pop(slot)
        if not p in PalLearnSet[self.GetCodeName()]:
            self._learntMoves.remove(p)
        else:
            if PalLearnSet[self.GetCodeName()][p] > self.GetLevel():
                self._learntMoves.remove(p)

    def StripAttack(self, name):
        name = name.replace("⚔","").replace("🏹","")
        print(name)
        print(self._learntMoves)
        strip = False
        if not name in self._equipMoves:
            if not name in PalLearnSet[self.GetCodeName()]:
                strip = True
            elif PalLearnSet[self.GetCodeName()][name] > self.GetLevel():
                strip = True
        if strip:
            self._learntMoves.remove(name)

    def FruitAttack(self, name):
        if not name in self._learntMoves:
            self._learntMoves.append(name)

    def RemoveSkill(self, slot):
        if slot < len(self._skills):
            self._skills.pop(slot)

    def RemoveAttack(self, slot):
        if slot < len(self._equipMoves):
            self._equipMoves.pop(slot)
        self.CleanseAttacks()

    def GetNickname(self):
        return self.GetName() if self._nickname == "" else self._nickname

    def GetFullName(self):
        return self.GetObject().GetName() + (" 💀" if self.isBoss else "") + (
            " ✨" if self.isLucky else "") + (f" - '{self._nickname}'" if not self._nickname == "" else "")

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
        return self._obj['SlotID']['value']['ContainerId']['value']['ID']['value']

    def SetSlotGuid(self, v: str):
        self._obj['SlotID']['value']['ContainerId']['value']['ID']['value'] = v

    def GetSlotIndex(self):
        return self._obj['SlotID']['value']['SlotIndex']['value']

    def SetSoltIndex(self, v: int):
        self._obj['SlotID']['value']['SlotIndex']['value'] = v

    def GetPalInstanceGuid(self):
        return self._data['key']['InstanceId']['value']

    def SetPalInstanceGuid(self, v: str):
        self._data['key']['InstanceId']['value'] = v

    def GetOwner(self):
        return self._data['key']['PlayerUId']['value']


class PalGuid:
    def __init__(self, data):
        self._data = data
        self._CharacterContainerSaveData = \
            data['properties']['worldSaveData']['value']['CharacterContainerSaveData']['value']
        self._GroupSaveDataMap = data['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']

    def GetPlayerslist(self):
        players = list(filter(lambda x: 'IsPlayer' in x['value'], [
            {'uid': x['key']['PlayerUId'],
             'value': x['value']['RawData']['value']['object']['SaveParameter']['value']
             } for x in self._data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']]))

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

    def SetContainerSave(self, SoltGuid: str, SlotIndex: int, PalGuid: str):
        if any(guid == "00000000-0000-0000-0000-000000000000" for guid in [SoltGuid, PalGuid]):
            return
        
        for e in self._CharacterContainerSaveData:
            if (e['key']['ID']['value'] == SoltGuid):
                v = len(e['value']['Slots']['value']['values'])-1

                n = copy.deepcopy(e['value']['Slots']['value']['values'][v])
                e['value']['Slots']['value']['values'].append(n)
                e['value']['Slots']['value']['values'][v+1]['SlotIndex']['value'] = SlotIndex
                e['value']['Slots']['value']['values'][v+1]['RawData']['value']['instance_id'] = PalGuid
                print(e['value']['Slots']['value']['values'][v+1])

    def RemovePal(self, SoltGuid: str, SlotIndex: int, PalGuid: str):
        if any(guid == "00000000-0000-0000-0000-000000000000" for guid in [SoltGuid, PalGuid]):
            return

        for e in self._CharacterContainerSaveData:
            if (e['key']['ID']['value'] == SoltGuid):
                for p in e['value']['Slots']['value']['values']:
                    if p['SlotIndex']['value'] == SlotIndex:
                        e['value']['Slots']['value']['values'].remove(p)
                        break
        

    def AddGroupSaveData(self, GroupGuid: str, PalGuid: str):
        if any(guid == "00000000-0000-0000-0000-000000000000" for guid in [GroupGuid, PalGuid]):
            return
        for e in self._GroupSaveDataMap:
            if (e['key'] == GroupGuid):
                for ee in e['value']['RawData']['value']['individual_character_handle_ids']:
                    if (ee['instance_id'] == PalGuid):
                        return
                tmp = {"guid": "00000000-0000-0000-0000-000000000001", "instance_id": PalGuid}
                e['value']['RawData']['value']['individual_character_handle_ids'].append(tmp)

    def RemoveGroupSaveData(self, GroupGuid: str, PalGuid: str):
        if any(guid == "00000000-0000-0000-0000-000000000000" for guid in [GroupGuid, PalGuid]):
            return
        for e in self._GroupSaveDataMap:
            if (e['key'] == GroupGuid):
                for ee in e['value']['RawData']['value']['individual_character_handle_ids']:
                    if (ee['instance_id'] == PalGuid):
                        e['value']['RawData']['value']['individual_character_handle_ids'].remove(ee)

    def GetSoltMaxCount(self, SoltGuid: str):
        if SoltGuid == "00000000-0000-0000-0000-000000000000":
            return 0
        for e in self._CharacterContainerSaveData:
            if (e['key']['ID']['value'] == SoltGuid):
                return len(e['value']['Slots']['value']['values'])

    def GetEmptySlotIndex(self, SoltGuid: str):
        print(SoltGuid)
        if SoltGuid == "00000000-0000-0000-0000-000000000000":
            return -1
        for e in self._CharacterContainerSaveData:
            if (e['key']['ID']['value'] == SoltGuid):
                print("Matched", SoltGuid)
                oc = []
                Solt = e['value']['Slots']['value']['values']
                for i in range(len(Solt)):
                    oc.append(Solt[i]['SlotIndex']['value'])
                    #if Solt[i]['RawData']['value']['instance_id'] == "00000000-0000-0000-0000-000000000000":
                       # return i
                print(oc)
                for i in range(0, 960):
                    if i not in oc:
                        return i
        return -1

    def GetAdminGuid(self):
        for e in self._GroupSaveDataMap:
            if "admin_player_uid" in e['value']['RawData']['value']:
                return e['value']['RawData']['value']['admin_player_uid']

    def GetAdminGroupGuid(self):
        for e in self._GroupSaveDataMap:
            if "admin_player_uid" in e['value']['RawData']['value']:
                return e['key']

    def GetGroupGuid(self, playerguid):        
        for e in self._GroupSaveDataMap:
            if "players" in e['value']['RawData']['value']:
                for player in e['value']['RawData']['value']['players']:
                    if player['player_uid'] == playerguid:
                        return e['key']

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


with open("%s/resources/data/elements.json" % (module_dir), "r", encoding="utf8") as elementfile:
    PalElements = {}
    for i in json.loads(elementfile.read())["values"]:
        PalElements[i['Name']] = i['Color']

PalSpecies = {}
# PalLearnSet: Pal Skills require Level
PalLearnSet = {}


def LoadPals(lang="en-GB"):
    global PalSpecies, PalLearnSet

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
                                                  i["Suitabilities"] if "Suitabilities" in i else {})
            if t:
                PalSpecies[i["CodeName"]]._suits = PalSpecies[i["CodeName"].replace("GYM_", "")]._suits
                PalSpecies[i["CodeName"]]._scaling = PalSpecies[i["CodeName"].replace("GYM_", "")]._scaling
            PalLearnSet[i["CodeName"]] = i["Moveset"] if not t else PalLearnSet[i["CodeName"].replace("GYM_", "")]


LoadPals()

PalPassives = {}
PassiveDescriptions = {}
PassiveRating = {}


def LoadPassives(lang="en-GB"):
    global PalPassives, PassiveDescriptions, PassiveRating

    PalPassives = {}
    PassiveDescriptions = {}
    PassiveRating = {}

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
                #print(i, l[code]["Name"])
            PalPassives = dict(sorted(PalPassives.items()))

LoadPassives()

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
