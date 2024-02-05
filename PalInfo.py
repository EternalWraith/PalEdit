import json
import os
from enum import Enum
from PIL import ImageTk, Image
from EmptyObjectHandler import *
import uuid

module_dir = os.path.dirname(os.path.abspath(__file__))

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
    def __init__(self, name, primary, secondary="None", human=False, tower=False):
        self._name = name
        self._img = None
        self._primary = primary
        self._secondary = secondary
        self._human = human
        self._tower = tower

    def GetName(self):
        return self._name

    def IsTower(self):
        return self._tower

    def GetImage(self):
        if self._img == None:
            n = self.GetName() if not self._human else "Human"
            self._img = ImageTk.PhotoImage(Image.open(module_dir+f'/resources/{n}.png').resize((240,240)))
        return self._img

    def GetPrimary(self):
        return self._primary

    def GetSecondary(self):
        return self._secondary

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
            self._obj["IsRarePal"] = EmptyRarePalObject.copy()
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
            self._obj['Talent_HP'] = EmptyMeleeObject.copy()
            self._talent_hp = 0 # we set 0, so if its not changed it should be removed by the game again.
        self._talent_hp = self._obj['Talent_HP']['value']

        if not "Talent_Melee" in self._obj:
            self._obj['Talent_Melee'] = EmptyMeleeObject.copy()
        self._melee = self._obj['Talent_Melee']['value']

        if not "Talent_Shot" in self._obj:
            self._obj['Talent_Shot'] = EmptyShotObject.copy()
        self._ranged = self._obj['Talent_Shot']['value']

        if not "Talent_Defense" in self._obj:
            self._obj['Talent_Defense'] = EmptyDefenceObject.copy()
        self._defence = self._obj['Talent_Defense']['value']

        if not "Rank" in self._obj:
            self._obj['Rank'] = EmptyRankObject.copy()
        self._rank = self._obj['Rank']['value']

        # Fix broken ranks
        if self.GetRank() < 1 or self.GetRank() > 5:
            self.SetRank(1)

        if not "PassiveSkillList" in self._obj:
            self._obj['PassiveSkillList'] = EmptySkillObject.copy()
        self._skills = self._obj['PassiveSkillList']['value']['values']
        self.CleanseSkills()

        if not "Level" in self._obj:
            self._obj['Level'] = EmptyLevelObject.copy()
        self._level = self._obj['Level']['value']

        if not "Exp" in self._obj:
            self._obj['Exp'] = EmptyExpObject.copy()
        # We don't store Exp yet

        self._nickname = ""
        if "NickName" in self._obj:
            self._nickname = self._obj['NickName']['value']

        self.isTower = self._type.IsTower()

        self._storedLocation = self._obj['SlotID']
        self.storageId = self._storedLocation["value"]["ContainerId"]["value"]["ID"]["value"]
        self.storageSlot = self._storedLocation["value"]["SlotIndex"]["value"]

        if not "MasteredWaza" in self._obj:
            self._obj["MasteredWaza"] = EmptyMovesObject.copy()
        
        for i in self._obj["MasteredWaza"]["value"]["values"]:
            if not matches(typename, i) or PalAttacks[i] in PalLearnSet[self._type.GetName()]:
                self._obj["MasteredWaza"]["value"]["values"].remove(i)
        for i in self._obj["EquipWaza"]["value"]["values"]:
            if not matches(typename, i):
                self._obj["EquipWaza"]["value"]["values"].remove(i)
                
        self._learntMoves = self._obj["MasteredWaza"]["value"]["values"]
        self._equipMoves = self._obj["EquipWaza"]["value"]["values"]
        self._learntBackup = self._learntMoves[:]

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
        
    def GetType(self):
        return self._type

    def SetType(self, value):
        f = find(value)
        self._obj['CharacterID']['value'] = ("BOSS_" if (self.isBoss or self.isLucky) else "") + f
        self._type = PalSpecies[f]
        self.SetLevelMoves()

    def GetObject(self):
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
        if slot > len(self._skills)-1:
            self._skills.append(find(skill))
        else:
            self._skills[slot] = find(skill)

    def SetAttackSkill(self, slot, attack):
        if slot > len(self._equipMoves)-1:
            self._equipMoves.append(find(attack))
        else:
            self._equipMoves[slot] = find(attack)
        self.SetLevelMoves()

    def GetOwner(self):
        return self.owner

    def GetLevel(self):
        return self._level

    def SetLevel(self, value):
        # We need this check until we fix adding missing nodes
        if "Level" in self._obj and "Exp" in self._obj:
            self._obj['Level']['value'] = self._level = value
            self._obj['Exp']['value'] = xpthresholds[value-1]
            self.SetLevelMoves()
        else:
            print(f"[ERROR:] Failed to update level for: '{self.GetName()}'")

    def SetLevelMoves(self):
        value = self._level
        self._obj["MasteredWaza"]["value"]["values"] = self._learntMoves = self._learntBackup[:]
        for i in PalLearnSet[self._type.GetName()]:
            if value >= PalLearnSet[self._type.GetName()][i]:
                if not find(i) in self._obj["MasteredWaza"]["value"]["values"]:
                    self._obj["MasteredWaza"]["value"]["values"].append(find(i))
            elif find(i) in self._obj["MasteredWaza"]["value"]["values"]:
                self._obj["MasteredWaza"]["value"]["values"].remove(find(i))

        for i in self._equipMoves:
            if not matches(find(self._type.GetName()), i):
                self._equipMoves.remove(i)
                self._obj["EquipWaza"]["value"]["values"] = self._equipMoves
            elif not i in self._obj["MasteredWaza"]["value"]["values"]:
                self._obj["MasteredWaza"]["value"]["values"].append(i)
                
        self._learntMoves = self._obj["MasteredWaza"]["value"]["values"]
        print("------")
        for i in self._learntMoves:
            print(i)


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
        self.SetLevelMoves()

    def GetNickname(self):
        return self.GetName() if self._nickname == "" else self._nickname

    def GetFullName(self):
        return self.GetObject().GetName() + (" 💀" if self.isBoss else "") + (" ♖" if self.isTower else "" ) + (" ✨" if self.isLucky else "") + (f" - '{self._nickname}'" if not self._nickname == "" else "")
    
    def SetLucky(self, v=True):
        self._obj["IsRarePal"]['value'] = self.isLucky = v
        self.SetType(self._type.GetName())
        if v:
            if self.isBoss:
                self.isBoss = False
                
    def SetBoss(self, v=True):
        self.isBoss = v
        self.SetType(self._type.GetName())
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

def matches(pal, move):
    if SkillExclusivity[move] == None:
        return True
    elif pal in SkillExclusivity[move]:
        return True
    return False
    """
    print(pal, move)
    if move.startswith("EPalWazaID::Unique_"):
        o = move.split("_")
        n = o[1]
        if len(o) > 3:
            t = o.pop(1)
            v = o.pop(1)
            n = f"{t}_{v}"
        if not pal == n and n != "Frostallion":
            return False
    return True
    """
                    

with open(module_dir+"/resources/data/elements.json", "r", encoding="utf8") as elementfile:
    PalElements = {}
    for i in json.loads(elementfile.read())["values"]:
        PalElements[i['Name']] = i['Color']

with open(module_dir+"/resources/data/pals.json", "r", encoding="utf8") as palfile:
    PalSpecies = {}
    PalLearnSet = {}
    for i in json.loads(palfile.read())["values"]:
        h = "Human" in i
        t = "Tower" in i
        p = i["Type"][0]
        s = "None"
        if len(i["Type"]) == 2:
            s = i["Type"][1]
        PalSpecies[i["CodeName"]] = PalObject(i["Name"], p, s, h, t)
        PalLearnSet[i["Name"]] = i["Moveset"]

with open(module_dir+"/resources/data/passives.json", "r", encoding="utf8") as passivefile:
    PalPassives = {}
    PassiveDescriptions = {}
    PassiveRating = {}
    for i in json.loads(passivefile.read())["values"]:
        PalPassives[i["CodeName"]] = i["Name"]
        PassiveDescriptions[i["Name"]] = i["Description"]
        PassiveRating[i["Name"]] = i["Rating"]
    PalPassives = dict(sorted(PalPassives.items()))

with open(module_dir+"/resources/data/attacks.json", "r", encoding="utf8") as attackfile:
    PalAttacks = {}
    AttackPower = {}
    AttackTypes = {}
    SkillExclusivity = {}

    l = json.loads(attackfile.read())

    debugOutput = l["values"]
    
    for i in l["values"]:
        PalAttacks[i["CodeName"]] = i["Name"]
        AttackPower[i["Name"]] = i["Power"]
        AttackTypes[i["Name"]] = i["Type"]
        if "Exclusive" in i:
            SkillExclusivity[i["CodeName"]] = i["Exclusive"]
        else:
            SkillExclusivity[i["CodeName"]] = None

    PalAttacks = dict(sorted(PalAttacks.items()))

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
    PalObject("Mossanda Noct", "Electric", "Dark")


    if True:
        import bs4 as bsoup
        import urllib.request as ureq

        
        
        with open(module_dir+"/resources/data/pals.json", "r+", encoding="utf8") as palfile:
            p = json.loads(palfile.read())
            palfile.seek(0)
            for pal in p['values']:
                pal["Moveset"] = {}
                if not "Human" in pal and not "Tower" in pal:
                    n = pal["Name"].lower().replace(" ", "-")
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}
                    req = ureq.Request(f"http://palworld.gg/pal/{n}", None, headers)
                    src = ureq.urlopen(req)
                    soup = bsoup.BeautifulSoup(src, "lxml")

                    con = soup.find_all("div", {"class": "active skills"})
                    if len(con) > 0:
                        for item in con[0].find_all("div", {"class": "item"}):
                            
                            name = item.find("div", {"class": "name"}).text
                            level = item.find("div", {"class": "level"})

                            if not level == None:
                                level = int(level.text.replace("- Lv ", ""))
                                pal["Moveset"][name] = level
            json.dump(p, palfile, indent=4)
            

    if True:

        codes = {}
        with open("data.txt", "r") as file:
            for line in file:
                l = line.replace("\t", " ").replace("\n", "")
                c, n = l.split(" ", 1)
                codes[n] = c

        def sortStuff(e):
            return e["Name"]
        debugOutput.sort(key=sortStuff)

        for i in debugOutput:
            if i["Name"] in codes:
                i["CodeName"] = codes[i["Name"]]
                codes.pop(i["Name"])

        for i in codes:
            debugOutput.append({"CodeName": codes[i], "Name": i, "Type": "", "Power": 0})
        with open(module_dir+"/resources/data/attacks.json", "w", encoding="utf8") as attackfile:
            json.dump({"values": debugOutput}, attackfile, indent=4)
    
        
