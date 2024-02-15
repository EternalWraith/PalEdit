import copy
import json
import os
import sys
import traceback
from enum import Enum
import tkinter
from EmptyObjectHandler import *
import uuid
import copy

module_dir = os.path.dirname(os.path.realpath(__file__))
if not os.path.exists("%s/resources/data/elements.json" % module_dir) and getattr(sys, 'frozen', False):
    # for some reason os.path when compiled with CxFreeze bugs out the program. Will look into it.
    module_dir = os.path.dirname(sys.executable)

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
    2681857
]
if len(xpthresholds) < 50:
    print("Something is wrong with the thresholds")


class PalGender(Enum):
    MALE = "#02A3FE"
    FEMALE = "#EC49A6"
    UNKNOWN = "darkgrey"



class PalObject:
    def __init__(self, name, code_name, primary, secondary="None", human=False, tower=False, scaling=None):
        self._name = name
        self._code_name = code_name
        self._img = None
        self._primary = primary
        self._secondary = secondary
        self._human = human
        self._tower = tower
        self._scaling = scaling

    def GetName(self):
        return self._name

    def GetCodeName(self):
        return self._code_name

    def IsTower(self):
        return self._tower

    def GetImage(self):
        if self._img == None:
            n = self.GetCodeName() if not self._human else "Human"
            # self._img = ImageTk.PhotoImage(Image.open(module_dir+f'/resources/{n}.png').resize((240,240)))
            self._img = tkinter.PhotoImage(file=f'{module_dir}/resources/pals/{n}.png')
        return self._img

    def GetPrimary(self):
        return self._primary

    def GetSecondary(self):
        return self._secondary

    def GetScaling(self):
        return self._scaling

class PalEntity:

    def __init__(self, data):
        self._data = data
        self._obj = data['value']['RawData']['value']['object']['SaveParameter']['value']

        self.owner = ""
        if "OwnerPlayerUId" in self._obj:
            self.owner = self._obj["OwnerPlayerUId"]['value']

        if "IsPlayer" in self._obj:
            raise Exception("This is a player character")

        if not "IsRarePal" in self._obj:
            self._obj["IsRarePal"] = copy.deepcopy(EmptyRarePalObject)
        self.isLucky = self._obj["IsRarePal"]['value']


        typename = self._obj['CharacterID']['value']
        # print(f"Debug: typename1 - {typename}")

        self.isBoss = False
        if typename[:5].lower() == "boss_":
            typename = typename[5:] # if first 5 characters match boss_ then cut the first 5 characters off
            # typename = typename.replace("BOSS_", "") # this causes bugs
            self.isBoss = True if not self.isLucky else False
            if typename == "LazyCatFish": # BOSS_LazyCatFish and LazyCatfish
                typename = "LazyCatfish"

        # print(f"Debug: typename2 - '{typename}'")
        if typename.lower() == "sheepball":
            typename = "Sheepball"

            # Strangely, Boss and Lucky Lamballs have camelcasing
            # Regular ones... don't
        # print(f"Debug: typename3 - '{typename}'")

        self._type = PalSpecies[typename]
        print(f"Created Entity of type {typename}: {self._type} - Lucky: {self.isLucky} Boss: {self.isBoss}")

        if "Gender" in self._obj:
            if self._obj['Gender']['value']['value'] == "EPalGenderType::Male":
                self._gender = "Male ♂"
            else:
                self._gender = "Female ♀"
        else:
            self._gender = "Unknown"

        self._workspeed = self._obj['CraftSpeed']['value']

        if not "Talent_HP" in self._obj:
            self._obj['Talent_HP'] = copy.deepcopy(EmptyMeleeObject)
            self._talent_hp = 0 # we set 0, so if its not changed it should be removed by the game again.
        self._talent_hp = self._obj['Talent_HP']['value']

        if not "Talent_Melee" in self._obj:
            self._obj['Talent_Melee'] = copy.deepcopy(EmptyMeleeObject)
        self._melee = self._obj['Talent_Melee']['value']

        if not "Talent_Shot" in self._obj:
            self._obj['Talent_Shot'] = copy.deepcopy(EmptyShotObject)
        self._ranged = self._obj['Talent_Shot']['value']

        if not "Talent_Defense" in self._obj:
            self._obj['Talent_Defense'] = copy.deepcopy(EmptyDefenceObject)
        self._defence = self._obj['Talent_Defense']['value']

        if not "Rank" in self._obj:
            self._obj['Rank'] = copy.deepcopy(EmptyRankObject)
        self._rank = self._obj['Rank']['value']

        # Fix broken ranks
        if self.GetRank() < 1 or self.GetRank() > 5:
            self.SetRank(1)

        if not "PassiveSkillList" in self._obj:
            self._obj['PassiveSkillList'] = copy.deepcopy(EmptySkillObject)
        self._skills = self._obj['PassiveSkillList']['value']['values']
        self.CleanseSkills()

        if not "Level" in self._obj:
            self._obj['Level'] = copy.deepcopy(EmptyLevelObject)
        self._level = self._obj['Level']['value']

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

        if not "MasteredWaza" in self._obj:
            self._obj["MasteredWaza"] = copy.deepcopy(EmptyMovesObject)



        self._learntMoves = self._obj["MasteredWaza"]["value"]["values"]
        self._equipMoves = self._obj["EquipWaza"]["value"]["values"]

        self.CleanseAttacks()


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
                i+=1

    def CleanseAttacks(self):
        i = 0
        while i < len(self._learntMoves):
            remove = False
            if not SkillExclusivity[self._learntMoves[i]] is None:
                if not self._type.GetCodeName() in SkillExclusivity[self._learntMoves[i]]:
                    remove = True

            if PalAttacks[self._learntMoves[i]] in PalLearnSet[self._type.GetCodeName()]:
                if not self._level >= PalLearnSet[self._type.GetCodeName()][PalAttacks[self._learntMoves[i]]]:
                    remove = True

            if remove:
                if self._learntMoves[i] in self._equipMoves:
                    self._equipMoves.remove(self._learntMoves[i])
                self._learntMoves.pop(i)
            else:
                i += 1

        for i in PalLearnSet[self._type.GetCodeName()]:
            if not find(i) in self._learntMoves:
                if PalLearnSet[self._type.GetCodeName()][i] <= self._level:
                    self._learntMoves.append(find(i))

        for i in self._equipMoves:
            if not i in self._learntMoves:
                self._learntMoves.append(i)

    def GetType(self):
        return self._type

    def SetType(self, value):
        self._obj['CharacterID']['value'] = ("BOSS_" if (self.isBoss or self.isLucky) else "") + value
        self._type = PalSpecies[value]
        self.CleanseAttacks()

    def GetObject(self) -> PalObject:
        return self._type

    def GetGender(self):
        return self._gender

    def GetWorkSpeed(self):
        return self._workspeed

    def SetWorkSpeed(self, value):
        self._obj['CraftSpeed']['value'] = self._workspeed = value

    def SetAttack(self, mval, rval):
        self._obj['Talent_Melee']['value'] = self._melee = mval
        self._obj['Talent_Shot']['value'] = self._ranged = rval

    def GetTalentHP(self):
        return self._talent_hp

    def SetTalentHP(self, value):
        self._obj['Talent_HP']['value'] = self._talent_hp = value

    # the soul bonus, 1 -> 3%, 10 -> 30%
    def GetRankHP(self):
        if "Rank_HP" in self._obj:
            return self._obj["Rank_HP"]["value"]
        return 0

    def GetRankAttack(self):
        if "Rank_Attack" in self._obj:
            return self._obj["Rank_Attack"]["value"]
        return 0

    # def GetRankDefense(self):
    #     # I haven't checked if this is the correct key.
    #     # unused
    #     if "Rank_Defense" in self._obj:
    #         return self._obj["Rank_Defense"]["value"]
    #     return 0

    # def GetRankCraftSpeed(self):
    #     # I haven't checked if this is the correct key.
    #     # unused
    #     if "Rank_CraftSpeed" in self._obj:
    #         return self._obj["Rank_CraftSpeed"]["value"]
    #     return 0

    def GetMaxHP(self):
        return self._obj['MaxHP']['value']['Value']['value']

    def UpdateMaxHP(self, changes: dict, hp_scaling=None) -> bool:
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
            possible_hp_scaling = (old_hp / 1000 - 500 - 5 * factors['level']) / (0.5 * factors['level'] * (1 + factors['hp_iv'] * 0.3 / 100) * (1 + factors['hp_rank'] * 3 / 100) * (1 + (factors['rank'] - 1) * 5 / 100))
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

        new_hp = int((500 + 5 * factors['level'] + hp_scaling * 0.5 * factors['level'] * (1 + factors['hp_iv'] * 0.3 / 100) * (1 + factors['hp_rank'] * 3 / 100) * (1 + (factors['rank'] - 1) * 5 / 100))) * 1000
        self._obj['MaxHP']['value']['Value']['value'] = new_hp
        print("%s MaxHP: %s -> %s" % (self.GetFullName(), old_hp, new_hp))


    def GetAttackMelee(self):
        return self._melee

    def SetAttackMelee(self, value):
        self._obj['Talent_Melee']['value'] = self._melee = value

    def GetAttackRanged(self):
        return self._ranged

    def SetAttackRanged(self, value):
        self._obj['Talent_Shot']['value'] = self._ranged = value

    def GetDefence(self):
        return self._defence

    def SetDefence(self, value):
        self._obj['Talent_Defense']['value'] = self._defence = value

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
        if slot > len(self._skills)-1:
            self._skills.append(skill)
        else:
            self._skills[slot] = skill

    def SetAttackSkill(self, slot, attack):
        if slot > len(self._equipMoves)-1:
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
            self._obj['Level']['value'] = self._level = value
            self._obj['Exp']['value'] = xpthresholds[value-1]
            self.CleanseAttacks() #self.SetLevelMoves()
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
            self._obj['Rank']['value'] = self._rank = value # we dont +1 here, since we have methods to patch rank in PalEdit.py
        else:
            print(f"[ERROR:] Failed to update rank for: '{self.GetName()}'") # we probably could get rid of this line, since you add rank if missing - same with level

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
        return self.GetObject().GetName() + (" 💀" if self.isBoss else "") + (" ♖" if self.isTower else "" ) + (" ✨" if self.isLucky else "") + (f" - '{self._nickname}'" if not self._nickname == "" else "")

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

    def InitializationPal(self, newguid, player, group, slot):
        self._data['key']['PlayerUId']['value'] = player
        self._obj["OwnerPlayerUId"]['value'] = player
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

class PalGuid:
    def __init__(self, data):
        self._data = data
        self._CharacterContainerSaveData = \
        data['properties']['worldSaveData']['value']['CharacterContainerSaveData']['value']
        self._GroupSaveDataMap = data['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']

    def GetPlayerslist(self):
        players = list(filter(lambda x: 'IsPlayer' in x['value'], [
            {'uid':x['key']['PlayerUId'],
             'value':x['value']['RawData']['value']['object']['SaveParameter']['value']
             } for x in self._data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']]))
        return {x['value']['NickName']['value']: str(x['uid']['value']) for x in players}

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
                e['value']['Slots']['value']['values'][SlotIndex]['RawData']['value']['instance_id'] = PalGuid
                e['value']['Slots']['value']['values'][SlotIndex]['RawData']['value'][
                    'player_uid'] = "00000000-0000-0000-0000-000000000001"

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

    def GetSoltMaxCount(self, SoltGuid: str):
        if SoltGuid == "00000000-0000-0000-0000-000000000000":
            return 0
        for e in self._CharacterContainerSaveData:
            if (e['key']['ID']['value'] == SoltGuid):
                return len(e['value']['Slots']['value']['values'])

    def GetEmptySlotIndex(self, SoltGuid: str):
        if SoltGuid == "00000000-0000-0000-0000-000000000000":
            return -1
        for e in self._CharacterContainerSaveData:
            if (e['key']['ID']['value'] == SoltGuid):
                Solt = e['value']['Slots']['value']['values']
                for i in range(len(Solt)):
                    if Solt[i]['RawData']['value']['instance_id'] == "00000000-0000-0000-0000-000000000000":
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
        self._inventoryinfo = self._obj['inventoryInfo']['value']

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
PalLearnSet = {}

def LoadPals(lang=None):
    global PalSpecies, PalLearnSet

    if lang is not None and not os.path.exists("%s/resources/data/pals%s.json" % (module_dir, "_" + lang)):
        lang = None

    PalCodeMapping = {}
    with open("%s/resources/data/pals.json" % (module_dir), "r", encoding="utf8") as palfile:
        pals = json.load(palfile)
        PalCodeMapping = {pal['CodeName']: pal['Name'] for pal in pals['values']}
    with open("%s/resources/data/pals%s.json" % (module_dir, "_"+lang if lang is not None else ""), "r", encoding="utf8") as palfile:
        PalSpecies = {}
        PalLearnSet = {}
        for i in json.loads(palfile.read())["values"]:
            # try:
            #     img = Image.open(module_dir + f'/resources/{i["Name"]}.png').resize((240, 240))
            #     with open(module_dir + f'/resources/pals/{i["CodeName"]}.png', 'wb') as f:
            #         img.save(f)
            # except Exception as e:
            #     traceback.print_exception(e)
            h = "Human" in i
            t = "Tower" in i
            p = i["Type"][0]
            s = "None"
            if len(i["Type"]) == 2:
                s = i["Type"][1]
            PalSpecies[i["CodeName"]] = PalObject(i["Name"], i["CodeName"], p, s, h, t, i["Scaling"] if "Scaling" in i else None)
            PalLearnSet[i["CodeName"]] = i["Moveset"]

LoadPals()

PalPassives = {}
PassiveDescriptions = {}
PassiveRating = {}

def LoadPassives(lang=None):
    global PalPassives, PassiveDescriptions, PassiveRating

    PalPassives = {}
    PassiveDescriptions = {}
    PassiveRating = {}

    if lang is not None and not os.path.exists("%s/resources/data/passives%s.json" % (module_dir, "_"+lang)):
        lang = None

    with open("%s/resources/data/passives%s.json" % (module_dir, "_"+lang if lang is not None else ""), "r", encoding="utf8") as passivefile:
        for i in json.loads(passivefile.read())["values"]:
            PalPassives[i["CodeName"]] = i["Name"]
            PassiveDescriptions[i["CodeName"]] = i["Description"]
            PassiveRating[i["CodeName"]] = i["Rating"]
        PalPassives = dict(sorted(PalPassives.items()))

LoadPassives()

PalAttacks = {}
AttackPower = {}
AttackTypes = {}
SkillExclusivity = {}


def LoadAttacks(lang=None):
    global PalAttacks, AttackPower, AttackTypes, SkillExclusivity

    if lang is not None and not os.path.exists("%s/resources/data/attacks%s.json" % (module_dir, "_" + lang)):
        lang = None

    with open("%s/resources/data/attacks%s.json" % (module_dir, "_"+lang if lang is not None else ""), "r", encoding="utf8") as attackfile:
        PalAttacks = {}
        AttackPower = {}
        AttackTypes = {}
        SkillExclusivity = {}

        l = json.loads(attackfile.read())

        debugOutput = l["values"]

        for i in l["values"]:
            PalAttacks[i["CodeName"]] = i["Name"]
            AttackPower[i["CodeName"]] = i["Power"]
            AttackTypes[i["CodeName"]] = i["Type"]
            if "Exclusive" in i:
                SkillExclusivity[i["CodeName"]] = i["Exclusive"]
            else:
                SkillExclusivity[i["CodeName"]] = None

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



##if __name__ == "__main__":
##    PalObject("Mossanda Noct", "Electric", "Dark")
##
##
##    if True:
##        import bs4 as bsoup
##        import urllib.request as ureq
##
##
##
##        with open(module_dir+"/resources/data/pals.json", "r+", encoding="utf8") as palfile:
##            p = json.loads(palfile.read())
##            palfile.seek(0)
##            for pal in p['values']:
##                pal["Moveset"] = {}
##                if not "Human" in pal and not "Tower" in pal:
##                    n = pal["Name"].lower().replace(" ", "-")
##                    headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}
##                    req = ureq.Request(f"http://palworld.gg/pal/{n}", None, headers)
##                    src = ureq.urlopen(req)
##                    soup = bsoup.BeautifulSoup(src, "lxml")
##
##                    con = soup.find_all("div", {"class": "active skills"})
##                    if len(con) > 0:
##                        for item in con[0].find_all("div", {"class": "item"}):
##
##                            name = item.find("div", {"class": "name"}).text
##                            level = item.find("div", {"class": "level"})
##
##                            if not level == None:
##                                level = int(level.text.replace("- Lv ", ""))
##                                pal["Moveset"][name] = level
##            json.dump(p, palfile, indent=4)
##
##
##    if True:
##
##        codes = {}
##        with open("data.txt", "r") as file:
##            for line in file:
##                l = line.replace("\t", " ").replace("\n", "")
##                c, n = l.split(" ", 1)
##                codes[n] = c
##
##        def sortStuff(e):
##            return e["Name"]
##        debugOutput.sort(key=sortStuff)
##
##        for i in debugOutput:
##            if i["Name"] in codes:
##                i["CodeName"] = codes[i["Name"]]
##                codes.pop(i["Name"])
##
##        for i in codes:
##            debugOutput.append({"CodeName": codes[i], "Name": i, "Type": "", "Power": 0})
##        with open(module_dir+"/resources/data/attacks.json", "w", encoding="utf8") as attackfile:
##            json.dump({"values": debugOutput}, attackfile, indent=4)


