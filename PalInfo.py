import json

from enum import Enum
from PIL import ImageTk, Image
from EmptyObjectHandler import *


SkillDesc = {
        "Unknown": " does not exist or is not in our database yet",
        "None": "The pal has no skill in this slot",
        
        "Abnormal": "-10% damage received from Neutral attacks",
        "Cheery": "-10% damage received from Dark attacks",
        "Dragonkiller": "-10% damage received from Dragon attacks",
        "Heated Body": "-10% damage received from Ice attacks",
        "Suntan Lover": "-10% damage received from Fire attacks",
        "Botanical Barrier": "-10% damage received from Grass attacks",
        "Earthquake Resistant": "-10% damage received from Ground attacks",
        "Insulated Body": "-10% damage received from Electric attacks",
        "Waterproof": "-10% damage received from Water attacks",

        "Zen Mind": "+10% damage dealt with Neutral attacks",
        "Veil of Darkness": "+10% damage dealt with Dark attacks",
        "Blood of the Dragon": "+10% damage dealt with Dragon attacks",
        "Coldblooded": "+10% damage dealt with Ice attacks",
        "Pyromaniac": "+10% damage dealt with Fire attacks",
        "Fragrant Foliage": "+10% damage dealt with Grass attacks",
        "Power of Gaia": "+10% damage dealt with Ground attacks",
        "Capacitor": "+10% damage dealt with Electric attacks",
        "Hydromaniac": "+10% damage dealt with Water attacks",

        "Celestial Emperor": "+20% damage dealt with Neutral attacks; Paladius' signature ability",
        "Lord of the Underworld": "+20% damage dealt with Dark attacks; Necromus' signature ability",
        "Divine Dragon": "+20% damage dealt with Dragon attacks; Jetragon's signature ability",
        "Ice Emperor": "+20% damage dealt with Ice attacks; Frostallion's signature ability",
        "Flame Emperor": "+20% damage dealt with Fire attacks; Blazamut's signature ability",
        "Spirit Emperor": "+20% damage dealt with Grass attacks; Lyleen's signature ability",
        "Earth Emperor": "+20% damage dealt with Ground attacks; Anubis' signature ability",
        "Lord of Lightning": "+20% damage dealt with Electric attacks; Orserk's signature ability",
        "Lord of the Sea": "+20% damage dealt with Water attacks; Jormuntide's signature ability",

        "Brave": "+10% to Attack stat",
        "Ferocious": "+20% to Attack stat",
        "Coward": "-10% to Attack stat",
        "Pacifist": "-20% to Attack stat",
        
        "Hard Skin": "+10% to Defence stat",
        "Burly Body": "+20% to Defence stat",
        "Downtrodden": "-10% to Defence stat",
        "Brittle": "-20% to Defence stat",

        "Mine Foreman": "+25% to Player mining efficiency",
        "Logging Foreman": "+25% to Player logging efficiency",
        "Vanguard": "+10% to Player attack stat",
        "Motivational Leader": "+25% to Player move speed",
        "Stronghold Strategist": "+10% to Player defence stat",

        "Positive Thinker": "Sanity drops 10% slower",
        "Workaholic": "Sanity drops 15% slower",
        "Unstable": "Sanity drops 10% faster",
        "Destructive": "Sanity drops 15% faster",

        "Dainty Eater": "Hunger drops 10% slower",
        "Diet Lover": "Chance to lose hunger -15%",
        "Glutton": "Hunger drops 10% faster",
        "Bottomless Stomach": "Hunger drops 15% faster",

        "Serious": "+20% work speed",
        "Artisan": "+50% work speed",
        "Clumsy": "-10% work speed",
        "Slacker": "-30% work speed",

        "Nimble": "+10% movement speed",
        "Runner": "+20% movement speed",
        "Swift": "+30% movement speed",

        "Work Slave": "+30% work speed, -30% attack",

        "Hooligan": "+15% attack, -10% work speed",
        "Musclehead": "+30% attack, -50% work speed",

        "Aggressive": "+10% attack, -20% defence",

        "Conceited": "+10% work speed, -20% defence",

        "Masochist": "+15% defence, -15% attack",
        "Sadist": "+15% attack, +15% defence",

        "Lucky": "+15% attack, +15% work speed",
        "Legend": "+20% attack, +20% defence, +15% move speed",
        
        "":""
    }
    
class PalSkills(Enum):
    UNKNOWN = "Unknown"
    NONE = "None"
    
    ElementResist_Normal_1_PAL = "Abnormal"
    ElementResist_Dark_1_PAL = "Cheery"
    ElementResist_Dragon_1_PAL = "Dragonkiller"
    ElementResist_Ice_1_PAL = "Heated Body"
    ElementResist_Fire_1_PAL = "Suntan Lover"
    ElementResist_Leaf_1_PAL = "Botanical Barrier"
    ElementResist_Earth_1_PAL = "Earthquake Resistant"
    ElementResist_Thunder_1_PAL = "Insulated Body"
    ElementResist_Aqua_1_PAL = "Waterproof"

    ElementBoost_Normal_1_PAL = "Zen Mind"
    ElementBoost_Dark_1_PAL = "Veil of Darkness"
    ElementBoost_Dragon_1_PAL = "Blood of the Dragon"
    ElementBoost_Ice_1_PAL = "Coldblooded"
    ElementBoost_Fire_1_PAL = "Pyromaniac"
    ElementBoost_Leaf_1_PAL = "Fragrant Foliage"
    ElementBoost_Earth_1_PAL = "Power of Gaia"
    ElementBoost_Thunder_1_PAL = "Capacitor"
    ElementBoost_Aqua_1_PAL = "Hydromaniac"

    ElementBoost_Normal_2_PAL = "Celestial Emperor"
    ElementBoost_Dark_2_PAL = "Lord of the Underworld"
    ElementBoost_Dragon_2_PAL = "Divine Dragon"
    ElementBoost_Ice_2_PAL = "Ice Emperor"
    ElementBoost_Fire_2_PAL = "Flame Emperor"
    ElementBoost_Leaf_2_PAL = "Spirit Emperor"
    ElementBoost_Earth_2_PAL = "Earth Emperor"
    ElementBoost_Thunder_2_PAL = "Lord of Lightning"
    ElementBoost_Aqua_2_PAL = "Lord of the Sea"

    PAL_ALLAttack_up1 = "Brave"
    PAL_ALLAttack_up2 = "Ferocious"
    PAL_ALLAttack_down1 = "Coward"
    PAL_ALLAttack_down2 = "Pacifist"
    
    Deffence_up1 = "Hard Skin"
    Deffence_up2 = "Burly Body"
    Deffence_down1 = "Downtrodden"
    Deffence_down2 = "Brittle"

    TrainerMining_up1 = "Mine Foreman"
    TrainerLogging_up1 = "Logging Foreman"
    TrainerATK_UP_1 = "Vanguard"
    TrainerWorkSpeed_UP_1 = "Motivational Leader"
    TrainerDEF_UP_1 = "Stronghold Strategist"

    PAL_Sanity_Down_1 = "Positive Thinker"
    PAL_Sanity_Down_2 = "Workaholic"
    PAL_Sanity_Up_1 = "Unstable"
    PAL_Sanity_Up_2 = "Destructive"

    PAL_FullStomach_Down_1 = "Dainty Eater"
    PAL_FullStomach_Down_2 = "Diet Lover"
    PAL_FullStomach_Up_1 = "Glutton"
    PAL_FullStomach_Up_2 = "Bottomless Stomach"
    

    CraftSpeed_up1 = "Serious"
    CraftSpeed_up2 = "Artisan"
    CraftSpeed_down1 = "Clumsy"
    CraftSpeed_down2 = "Slacker"

    MoveSpeed_up_1 = "Nimble"
    MoveSpeed_up_2 = "Runner"
    MoveSpeed_up_3 = "Swift"

    PAL_CorporateSlave = "Work Slave"

    PAL_rude = "Hooligan"
    Noukin = "Musclehead"

    PAL_oraora = "Aggressive"

    PAL_conceited = "Conceited"

    PAL_masochist = "Masochist"
    PAL_sadist = "Sadist"
    
    Rare = "Lucky"
    Legend = "Legend"


class PalGender(Enum):
    MALE = "#02A3FE"
    FEMALE = "#EC49A6"
    UNKNOWN = "darkgrey"

class PalElement:
    def __init__(self, name, colour):
        self._name = name
        self._colour = colour

    def GetName(self):
        return self._name

    def GetColour(self):
        return self._colour
    
class Elements(Enum):
    NONE = PalElement("None", "lightgrey")
    NORMAL = PalElement("Neutral", "#D8A796")
    DARK = PalElement("Dark", "#AD0035")
    DRAGON = PalElement("Dragon", "#C22DF9")
    ICE = PalElement("Ice", "#00F2FF")
    FIRE = PalElement("Fire", "#FF4208")
    LEAF = PalElement("Grass", "#83F001")
    EARTH = PalElement("Ground", "#BA5608")
    ELECTRICITY = PalElement("Electric", "#FEED01")
    WATER = PalElement("Water", "#0074FF")

class PalObject:
    def __init__(self, name, primary, secondary=Elements.NONE, human=False, tower=False):
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
            n = self.GetName() if not self._human else "#ERROR"
            self._img = ImageTk.PhotoImage(Image.open(f'resources/{n}.png').resize((240,240)))
        return self._img

    
    def GetPrimary(self):
        return self._primary

    def GetSecondary(self):
        return self._secondary

class PalType(Enum):
    # Thank you to @DMVoidKitten
    
    # Normal Pal List
    Alpaca = PalObject("Melpaca", Elements.NORMAL)#
    AmaterasuWolf = PalObject("Kitsun", Elements.FIRE)#
    Anubis = PalObject("Anubis", Elements.EARTH)#
    Baphomet = PalObject("Incineram", Elements.FIRE, Elements.DARK)#
    Baphomet_Dark = PalObject("Incineram Noct", Elements.DARK)#
    Bastet = PalObject("Mau", Elements.DARK)#
    Bastet_Ice = PalObject("Mau Cryst", Elements.ICE)#
    BerryGoat = PalObject("Caprity", Elements.LEAF)#
    BirdDragon = PalObject("Vanwyrm", Elements.FIRE, Elements.DARK)#
    BirdDragon_Ice = PalObject("Vanwyrm Cryst", Elements.ICE, Elements.DARK)#
    BlackCentaur = PalObject("Necromus", Elements.DARK)#
    BlackGriffon = PalObject("Shadowbeak", Elements.DARK)#
    BlackMetalDragon = PalObject("Astegon", Elements.DRAGON, Elements.DARK)#
    BlueDragon = PalObject("Azurobe", Elements.WATER, Elements.DRAGON)#
    BluePlatypus = PalObject("Fuack", Elements.WATER)#
    Boar = PalObject("Rushoar", Elements.EARTH)#
    CaptainPenguin = PalObject("Penking", Elements.WATER, Elements.ICE)#
    Carbunclo = PalObject("Lifmunk", Elements.LEAF)#
    CatBat = PalObject("Tombat", Elements.DARK)#
    CatMage = PalObject("Katress", Elements.DARK)#
    CatVampire = PalObject("Felbat", Elements.DARK)#
    ChickenPal = PalObject("Chikipi", Elements.NORMAL)#
    ColorfulBird = PalObject("Tocotoco", Elements.NORMAL)#
    CowPal = PalObject("Mozzarina", Elements.NORMAL)#
    CuteButterfly = PalObject("Cinnamoth", Elements.LEAF)#
    CuteFox = PalObject("Vixy", Elements.NORMAL)#
    CuteMole = PalObject("Fuddler", Elements.EARTH)#
    DarkCrow = PalObject("Cawgnito", Elements.DARK)#
    DarkScorpion = PalObject("Menasting", Elements.DARK, Elements.EARTH)#
    Deer = PalObject("Eikthyrdeer", Elements.NORMAL)#
    Deer_Ground = PalObject("Eikthyrdeer Terra", Elements.EARTH)#
    DreamDemon = PalObject("Daedream", Elements.DARK)#
    DrillGame = PalObject("Digtoise", Elements.EARTH)#
    Eagle = PalObject("Galeclaw", Elements.NORMAL)#
    ElecCat = PalObject("Sparkit", Elements.ELECTRICITY)#
    ElecPanda = PalObject("Grizzbolt", Elements.ELECTRICITY)#
    FairyDragon = PalObject("Elphidran", Elements.DRAGON)#
    FairyDragon_Water = PalObject("Elphidran Aqua", Elements.DRAGON, Elements.WATER)#
    FengyunDeeper = PalObject("Fenglope", Elements.NORMAL)#
    FireKirin = PalObject("Pyrin", Elements.FIRE)#
    FireKirin_Dark = PalObject("Pyrin Noct", Elements.FIRE, Elements.DARK)#
    FlameBambi = PalObject("Rooby", Elements.FIRE)#
    FlameBuffalo = PalObject("Arsox", Elements.FIRE)#
    FlowerDinosaur = PalObject("Dinossom", Elements.LEAF, Elements.DRAGON)#
    FlowerDinosaur_Electric = PalObject("Dinossom Lux", Elements.ELECTRICITY, Elements.DRAGON)#
    FlowerDoll = PalObject("Petallia", Elements.LEAF)#
    FlowerRabbit = PalObject("Flopie", Elements.LEAF)#
    FlyingManta = PalObject("Celaray", Elements.WATER)#
    FoxMage = PalObject("Wixen", Elements.FIRE)#
    Ganesha = PalObject("Teafant", Elements.WATER)#
    Garm = PalObject("Direhowl", Elements.NORMAL)#
    GhostBeast = PalObject("Maraith", Elements.DARK)#
    Gorilla = PalObject("Gorirat", Elements.NORMAL)#
    GrassMammoth = PalObject("Mammorest", Elements.LEAF)#
    GrassMammoth_Ice = PalObject("Mammorest Cryst", Elements.ICE)#
    GrassPanda = PalObject("Mossanda", Elements.LEAF)#
    GrassPanda_Electric = PalObject("Mossanda Lux", Elements.ELECTRICITY)#
    GrassRabbitMan = PalObject("Verdash", Elements.LEAF)#
    HadesBird = PalObject("Helzephyr", Elements.DARK)#
    HawkBird = PalObject("Nitewing", Elements.NORMAL)#
    Hedgehog = PalObject("Jolthog", Elements.ELECTRICITY)#
    Hedgehog_Ice = PalObject("Jolthog Cryst", Elements.ICE)#
    HerculesBeetle = PalObject("Warsect", Elements.EARTH, Elements.LEAF)#
    Horus = PalObject("Faleris", Elements.FIRE)#
    IceDeer = PalObject("Reindrix", Elements.ICE)#
    IceFox = PalObject("Foxcicle", Elements.ICE)#
    IceHorse = PalObject("Frostallion", Elements.ICE)#
    IceHorse_Dark = PalObject("Frostallion Noct", Elements.DARK)#
    JetDragon = PalObject("Jetragon", Elements.DRAGON)#
    Kelpie = PalObject("Kelpsea", Elements.WATER)#
    Kelpie_Fire = PalObject("Kelpsea Ignis", Elements.FIRE)#
    KingAlpaca = PalObject("Kingpaca", Elements.NORMAL)#
    KingAlpaca_Ice = PalObject("Ice Kingpaca", Elements.ICE)#
    KingBahamut = PalObject("Blazamut", Elements.FIRE)#
    Kirin = PalObject("Univolt", Elements.ELECTRICITY)#
    Kitsunebi = PalObject("Foxparks", Elements.FIRE)#
    LavaGirl = PalObject("Flambelle", Elements.FIRE)#
    LazyCatfish = PalObject("Dumud", Elements.EARTH)#
    LazyDragon = PalObject("Relaxaurus", Elements.DRAGON, Elements.WATER)#
    LazyDragon_Electric = PalObject("Relaxaurus Lux", Elements.DRAGON, Elements.ELECTRICITY)#
    LilyQueen = PalObject("Lyleen", Elements.LEAF)#
    LilyQueen_Dark = PalObject("Lyleen Noct", Elements.DARK)#
    LittleBriarRose = PalObject("Bristla", Elements.LEAF)#
    LizardMan = PalObject("Leezpunk", Elements.DARK)#
    LizardMan_Fire = PalObject("Leezpunk Ignis", Elements.FIRE)#
    Manticore = PalObject("Blazehowl", Elements.FIRE)#
    Manticore_Dark = PalObject("Blazehowl Noct", Elements.FIRE, Elements.DARK)#
    Monkey = PalObject("Tanzee", Elements.LEAF)#
    MopBaby = PalObject("Swee", Elements.ICE)#
    MopKing = PalObject("Sweepa", Elements.ICE)#
    Mutant = PalObject("Lunaris", Elements.NORMAL)#
    NaughtyCat = PalObject("Grintale", Elements.NORMAL)#
    NegativeKoala = PalObject("Depresso", Elements.DARK)#
    NegativeOctopus = PalObject("Killamari", Elements.DARK)#
    NightFox = PalObject("Nox", Elements.DARK)#
    Penguin = PalObject("Pengullet", Elements.WATER, Elements.ICE)#
    PinkCat = PalObject("Cattiva", Elements.NORMAL)#
    PinkLizard = PalObject("Lovander", Elements.NORMAL)#
    PinkRabbit = PalObject("Ribbuny", Elements.NORMAL)#
    PlantSlime = PalObject("Gumoss", Elements.LEAF, Elements.EARTH)#
    QueenBee = PalObject("Elizabee", Elements.LEAF)#
    RaijinDaughter = PalObject("Dazzi", Elements.ELECTRICITY)#
    RedArmorBird = PalObject("Ragnahawk", Elements.FIRE)#
    RobinHood = PalObject("Robinquill", Elements.LEAF)#
    RobinHood_Ground = PalObject("Robinquill Terra", Elements.LEAF, Elements.EARTH)#
    Ronin = PalObject("Bushi", Elements.FIRE)#
    SaintCentaur = PalObject("Paladius", Elements.NORMAL)#
    SakuraSaurus = PalObject("Broncherry", Elements.LEAF)#
    SakuraSaurus_Water = PalObject("Broncherry Aqua", Elements.LEAF, Elements.WATER)#
    Serpent = PalObject("Surfent", Elements.WATER)#
    Serpent_Ground = PalObject("Surfent Terra", Elements.EARTH)#
    SharkKid = PalObject("Gobfin", Elements.WATER)#
    SharkKid_Fire = PalObject("Gobfin Ignis", Elements.FIRE)#
    Sheepball = PalObject("Lamball", Elements.NORMAL)#
    SkyDragon = PalObject("Quivern", Elements.DRAGON)#
    SoldierBee = PalObject("Beegarde", Elements.LEAF)#
    Suzaku = PalObject("Suzaku", Elements.FIRE)#
    Suzaku_Water = PalObject("Suzaku Aqua", Elements.WATER)#
    SweetsSheep = PalObject("Woolipop", Elements.NORMAL)#
    ThunderBird = PalObject("Beakon", Elements.ELECTRICITY)#
    ThunderDog = PalObject("Rayhound", Elements.ELECTRICITY)#
    ThunderDragonMan = PalObject("Orserk", Elements.DRAGON, Elements.ELECTRICITY)#
    Umihebi = PalObject("Jormuntide", Elements.DRAGON, Elements.WATER)#
    Umihebi_Fire = PalObject("Jormuntide Ignis", Elements.DRAGON, Elements.FIRE)#
    VioletFairy = PalObject("Vaelet", Elements.LEAF)#
    VolcanicMonster = PalObject("Reptyro", Elements.FIRE, Elements.EARTH)#
    VolcanicMonster_Ice = PalObject("Reptyro Cryst", Elements.ICE, Elements.EARTH)#
    WeaselDragon = PalObject("Chillet", Elements.ICE, Elements.DRAGON)#
    Werewolf = PalObject("Loupmoon", Elements.DARK)#
    WhiteMoth = PalObject("Sibelyx", Elements.ICE)#
    WhiteTiger = PalObject("Cryolinx", Elements.ICE)#
    WindChimes = PalObject("Hangyu", Elements.EARTH)#
    WindChimes_Ice = PalObject("Hangyu Cryst", Elements.ICE)#
    WizardOwl = PalObject("Hoocrates", Elements.DARK)#
    WoolFox = PalObject("Cremis", Elements.NORMAL)#
    Yeti = PalObject("Wumpo", Elements.ICE)#
    Yeti_Grass = PalObject("Wumpo Botan", Elements.LEAF)#

    # Tower Bosses
    GYM_ThunderDragonMan = PalObject("Axel & Orserk", Elements.DRAGON, Elements.ELECTRICITY, tower=True)#
    GYM_LilyQueen = PalObject("Lily & Lyleen", Elements.LEAF, tower=True)#
    GYM_Horus = PalObject("Marus & Faleris", Elements.FIRE, tower=True)#
    GYM_BlackGriffon = PalObject("Victor & Shadowbeak", Elements.DARK, tower=True)#
    GYM_ElecPanda = PalObject("Zoe & Grizzbolt", Elements.ELECTRICITY, tower=True)#

    # Human Entities (Not yet finished)
    Male_DarkTrader01 = PalObject("Black Marketeer", Elements.NONE, human=True)#
    FireCult_FlameThrower = PalObject("Brothers of the Eternal Pyre Martyr", Elements.NONE, human=True)#
    Male_Soldier01 = PalObject("Burly Merc", Elements.NONE, human=True)#
    Female_Soldier01 = PalObject("Expedition Survivor", Elements.NONE, human=True)#
    Believer_CrossBow = PalObject("Free Pal Alliance Devout", Elements.NONE, human=True)#
    Male_Scientist01_LaserRifle = PalObject("PAL Genetic Research Unit Executioner", Elements.NONE, human=True)#
    PalDealer = PalObject("Pal Merchant", Elements.NONE, human=True)#
    Police_Handgun = PalObject("PIDF Guard", Elements.NONE, human=True)#
    Hunter_Bat = PalObject("Syndicate Thug (Bat)", Elements.NONE, human=True)#
    Hunter_FlameThrower = PalObject("Syndicate Cleaner", Elements.NONE, human=True)#
    Hunter_Fat_GatlingGun = PalObject("Syndicate Crusher", Elements.NONE, human=True)#
    Hunter_RocketLauncher = PalObject("Syndicate Elite", Elements.NONE, human=True)#
    Hunter_Grenade = PalObject("Syndicate Grenadier", Elements.NONE, human=True)#
    Hunter_Rifle = PalObject("Syndicate Gunner", Elements.NONE, human=True)#
    Hunter_Shotgun = PalObject("Syndicate Hunter", Elements.NONE, human=True)#
    Hunter_Handgun = PalObject("Syndicate Thug (Handgun)", Elements.NONE, human=True)#
    SalesPerson = PalObject("Wandering Merchant", Elements.NONE, human=True)#

    @classmethod
    def find(self, value):
        for i in PalType:
            if i.value.GetName() == value:
                return i

class PalEntity:

    def __init__(self, data):
        self._data = data
        self._obj = data['value']['RawData']['value']['object']['SaveParameter']['value']

        if "IsPlayer" in self._obj:
            raise Exception("This is a player character")

        self.isLucky = ("IsRarePal" in self._obj)
        
        typename = self._obj['CharacterID']['value']
        self.isBoss = False
        
        if typename[:5].lower() == "boss_":
            typename = typename.replace("BOSS_", "")
            
            self.isBoss = True if not self.isLucky else False

        if typename.lower() == "sheepball":
            typename = "Sheepball"
            # Strangely, Boss and Lucky Lamballs have camelcasing
            # Regular ones... don't
        
        self._type = PalType[typename]
        print(f"Created Entity of type {typename}: {self._type.value}")

        if "Gender" in self._obj:
            if self._obj['Gender']['value']['value'] == "EPalGenderType::Male":
                self._gender = "Male ♂"
            else:
                self._gender = "Female ♀"
        else:
            self._gender = "Unknown"

        self._workspeed = self._obj['CraftSpeed']['value']

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
            

        if not "PassiveSkillList" in self._obj:
            self._obj['PassiveSkillList'] = EmptySkillObject.copy()
        self._skills = self._obj['PassiveSkillList']['value']['values']
        self.CleanseSkills()

        self._owner = self._obj['OwnerPlayerUId']['value']

        if not "Level" in self._obj:
            self._obj['Level'] = EmptyLevelObject.copy()
        self._level = self._obj['Level']['value']

        if not "Exp" in self._obj:
            self._obj['Exp'] = EmptyExpObject.copy()
        # We don't store Exp yet

        self._nickname = ""
        if "NickName" in self._obj:
            self._nickname = self._obj['NickName']['value']

        self.isTower = self._type.value.IsTower()

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
        self._obj['CharacterID']['value'] = PalType.find(value).name
        self._type = PalType.find(value)

    def GetObject(self):
        return self._type.value

    def GetGender(self):
        return self._gender

    def GetWorkSpeed(self):
        return self._workspeed

    def SetWorkSpeed(self, value):
        self._obj['CraftSpeed']['value'] = self._workspeed = value

    def SetAttack(self, mval, rval):
        self._obj['Talent_Melee']['value'] = self._melee = mval
        self._obj['Talent_Shot']['value'] = self._ranged = rval

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
        return self.GetObject().GetPrimary().value

    def GetSecondary(self):
        return self.GetObject().GetSecondary().value

    def GetSkills(self):
        self.CleanseSkills()
        return self._skills

    def SkillCount(self):
        return len(self._skills)

    def SetSkill(self, slot, skill):
        if slot > len(self._skills)-1:
            self._skills.append(PalSkills(skill).name)
        else:
            self._skills[slot] = PalSkills(skill).name

    def GetOwner(self):
        return self._owner

    def GetLevel(self):
        return self._level

    def SetLevel(self, value):
        # We need this check until we fix adding missing nodes
        if "Level" in self._obj and "Exp" in self._obj:
            self._obj['Level']['value'] = self._level = value
            self._obj['Exp']['value'] = 0
        else:
            print(f"[ERROR:] Failed to update level for: '{self.GetName()}'")

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

    def GetNickname(self):
        return self.GetName() if self._nickname == "" else self._nickname

    def GetFullName(self):
        return self.GetObject().GetName() + (" 💀" if self.isBoss else "") + (" ♖" if self.isTower else "" ) + (" ✨" if self.isLucky else "") + (f" - '{self._nickname}'" if not self._nickname == "" else "")

if __name__ == "__main__":
    import os

    print(len(PalType))
    
    print(PalType.GrassPanda)
    print(PalType.GrassPanda.name)
    print(PalType.GrassPanda.value)

    for i in PalType:
        if not os.path.exists(f"resources/{i.value.GetName()}.png"):
            f = open(f"resources/{i.value.GetName()}.png", "w")
            f.write("0")
            f.close()
