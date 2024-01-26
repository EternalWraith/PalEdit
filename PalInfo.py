from enum import Enum
from PIL import ImageTk, Image

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

    PAL_Sanity_Up_1 = "Positive Thinker"
    PAL_Sanity_Up_2 = "Workaholic"
    PAL_Sanity_Down_1 = "Unstable"
    PAL_Sanity_Down_2 = "Destructive"

    PAL_FullStomach_Up_1 = "Dainty Eater"
    PAL_FullStomach_Up_2 = "Diet Lover"
    PAL_FullStomach_Down_1 = "Glutton"
    PAL_FullStomach_Down_2 = "Bottomless Stomach"
    

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

    PAL_Masochist = "Masochist"
    PAL_Sadist = "Sadist"
    
    Lucky = "Lucky"
    Legend = "Legend"


class PalGender(Enum):
    MALE = "#02A3FE"
    FEMALE = "#EC49A6"

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
    def __init__(self, name, primary, secondary=Elements.NONE):
        self._name = name
        self._img = None
        self._primary = primary
        self._secondary = secondary

    def GetName(self):
        return self._name

    def GetImage(self):
        if self._img == None:
            self._img = ImageTk.PhotoImage(Image.open(f'resources/{self._name}.png').resize((240,240)))
        return self._img

    
    def GetPrimary(self):
        return self._primary

    def GetSecondary(self):
        return self._secondary

class PalType(Enum):
    NULL = PalObject("#ERROR", Elements.NONE)#
    Anubis = PalObject("Anubis", Elements.EARTH)#
    Baphomet = PalObject("Incineram", Elements.FIRE, Elements.DARK)#
    Baphomet_Dark = PalObject("Incineram Noct", Elements.DARK)#
    Bastet = PalObject("Mau", Elements.DARK)#
    Bastet_Ice = PalObject("Mau Cryst", Elements.ICE)#
    Boar = PalObject("Rushoar", Elements.EARTH)#
    Carbunclo = PalObject("Lifmunk", Elements.LEAF)#
    ColorfulBird = PalObject("Tocotoco", Elements.NORMAL)#
    Deer = PalObject("Eikthyrdeer", Elements.NORMAL)#
    Deer_Ground = PalObject("Eikthyrdeer Terra", Elements.EARTH)#
    DrillGame = PalObject("Digtoise", Elements.EARTH)#
    Eagle = PalObject("Galeclaw", Elements.NORMAL)#
    ElecPanda = PalObject("Grizzbolt", Elements.ELECTRICITY)#
    Ganesha = PalObject("Teafant", Elements.WATER)#
    Garm = PalObject("Direhowl", Elements.NORMAL)#
    Gorilla = PalObject("Gorirat", Elements.NORMAL)#
    Hedgehog = PalObject("Jolthog", Elements.ELECTRICITY)#
    Hedgehog_Ice = PalObject("Jolthog Cryst", Elements.ICE)#
    Kirin = PalObject("Univolt", Elements.ELECTRICITY)#
    Kitsunebi = PalObject("Foxparks", Elements.FIRE)#
    LittleBriarRose = PalObject("Bristla", Elements.LEAF)#
    Mutant = PalObject("Lunaris", Elements.NORMAL)#
    Penguin = PalObject("Pengullet", Elements.WATER, Elements.ICE)#
    RaijinDaughter = PalObject("Dazzi", Elements.ELECTRICITY)#
    SharkKid = PalObject("Gobfin", Elements.WATER)#
    SharkKid_Fire = PalObject("Gobfin Ignis", Elements.FIRE)#
    SheepBall = PalObject("Lamball", Elements.NORMAL)#
    Umihebi = PalObject("Jormuntide", Elements.DRAGON, Elements.WATER)#
    Umihebi_Fire = PalObject("Jormuntide Ignis", Elements.DRAGON, Elements.FIRE)#
    Werewolf = PalObject("Loupmoon", Elements.DARK)#
    WindChimes = PalObject("Hangyu", Elements.EARTH)#
    WindChimes_Ice = PalObject("Hangyu Cryst", Elements.ICE)#
    Suzaku = PalObject("Suzaku", Elements.FIRE)#
    Suzaku_Water = PalObject("Suzaku Aqua", Elements.WATER)#
    FireKirin = PalObject("Pyrin", Elements.FIRE)#
    FireKirin_Dark = PalObject("Pyrin Noct", Elements.FIRE, Elements.DARK)#
    FairyDragon = PalObject("Elphidran", Elements.DRAGON)#
    FairyDragon_Water = PalObject("Elphidran Aqua", Elements.DRAGON, Elements.WATER)#
    SweetsSheep = PalObject("Woolipop", Elements.NORMAL)#
    WhiteTiger = PalObject("Cryolinx", Elements.ICE)#
    Alpaca = PalObject("Melpaca", Elements.NORMAL)#
    Serpent = PalObject("Surfent", Elements.WATER)#
    Serpent_Ground = PalObject("Surfent Terra", Elements.EARTH)#
    DarkCrow = PalObject("Cawgnito", Elements.DARK)#
    BlueDragon = PalObject("Azurobe", Elements.WATER, Elements.DRAGON)#
    PinkCat = PalObject("Cattiva", Elements.NORMAL)#
    NegativeKoala = PalObject("Depresso", Elements.DARK)#
    FengyunDeeper = PalObject("Fenglope", Elements.NORMAL)#
    VolcanicMonster = PalObject("Reptyro", Elements.FIRE, Elements.EARTH)#
    VolcanicMonster_Ice = PalObject("Reptyro Cryst", Elements.ICE, Elements.EARTH)#
    GhostBeast = PalObject("Maraith", Elements.DARK)#
    RobinHood = PalObject("Robinquill", Elements.LEAF)#
    RobinHood_Ground = PalObject("Robinquill Terra", Elements.LEAF, Elements.EARTH)#
    LazyDragon = PalObject("Relaxaurus", Elements.DRAGON, Elements.WATER)#
    LazyDragon_Electric = PalObject("Relaxaurus Lux", Elements.DRAGON, Elements.ELECTRICITY)#
    AmaterasuWolf = PalObject("Kitsun", Elements.FIRE)#
    LizardMan = PalObject("Leezpunk", Elements.DARK)#
    LizardMan_Fire = PalObject("Leezpunk Ignis", Elements.FIRE)#
    BluePlatypus = PalObject("Fuack", Elements.WATER)#
    BirdDragon = PalObject("Vanwyrm", Elements.FIRE, Elements.DARK)#
    BirdDragon_Ice = PalObject("Vanwyrm Cryst", Elements.ICE, Elements.DARK)#
    ChickenPal = PalObject("Chikipi", Elements.NORMAL)#
    FlowerDinosaur = PalObject("Dinossom", Elements.LEAF, Elements.DRAGON)#
    FlowerDinosaur_Electric = PalObject("Dinossom Lux", Elements.ELECTRICITY, Elements.DRAGON)#
    ElecCat = PalObject("Sparkit", Elements.ELECTRICITY)#
    IceHorse = PalObject("Frostallion", Elements.ICE)#
    IceHorse_Dark = PalObject("Frostallion Noct", Elements.DARK)#
    GrassMammoth = PalObject("Mammorest", Elements.LEAF)#
    GrassMammoth_Ice = PalObject("Mammorest Cryst", Elements.ICE)#
    CatVampire = PalObject("Felbat", Elements.DARK)#
    SakuraSaurus = PalObject("Broncherry", Elements.LEAF)#
    SakuraSaurus_Water = PalObject("Broncherry Aqua", Elements.LEAF, Elements.WATER)#
    Horus = PalObject("Faleris", Elements.FIRE)#
    KingBahamut = PalObject("Blazamut", Elements.FIRE)#
    BerryGoat = PalObject("Caprity", Elements.LEAF)#
    IceDeer = PalObject("Reindrix", Elements.ICE)#
    BlackGriffon = PalObject("Shadowbeak", Elements.DARK)#
    WhiteMoth = PalObject("Sibelyx", Elements.ICE)#
    CuteFox = PalObject("Vixy", Elements.NORMAL)#
    FoxMage = PalObject("Wixen", Elements.FIRE)#
    PinkLizard = PalObject("Lovander", Elements.NORMAL)#
    WizardOwl = PalObject("Hoocrates", Elements.DARK)#
    Kelpie = PalObject("Kelpsea", Elements.WATER)#
    Kelpie_Fire = PalObject("Kelpsea Ignis", Elements.FIRE)#
    NegativeOctopus = PalObject("Killamari", Elements.DARK)#
    CowPal = PalObject("Mozzarina", Elements.NORMAL)#
    Yeti = PalObject("Wumpo", Elements.ICE)#
    Yeti_Grass = PalObject("Wumpo Botan", Elements.LEAF)#
    VioletFairy = PalObject("Vaelet", Elements.LEAF)#
    HawkBird = PalObject("Nitewing", Elements.NORMAL)#
    FlowerRabbit = PalObject("Flopie", Elements.LEAF)#
    LilyQueen = PalObject("Lyleen", Elements.LEAF)#
    LilyQueen_Dark = PalObject("Lyleen Noct", Elements.DARK)#
    QueenBee = PalObject("Elizabee", Elements.LEAF)#
    SoldierBee = PalObject("Beegarde", Elements.LEAF)#
    CatBat = PalObject("Tombat", Elements.DARK)#
    GrassPanda = PalObject("Mossanda", Elements.LEAF)#
    GrassPanda_Electric = PalObject("Mossanda Lux", Elements.ELECTRICITY)#
    FlameBuffalo = PalObject("Arsox", Elements.FIRE)#
    ThunderDog = PalObject("Rayhound", Elements.ELECTRICITY)#
    CuteMole = PalObject("Fuddler", Elements.EARTH)#
    BlackMetalDragon = PalObject("Astegon", Elements.DRAGON, Elements.DARK)#
    GrassRabbitMan = PalObject("Verdash", Elements.LEAF)#
    IceFox = PalObject("Foxcicle", Elements.ICE)#
    JetDragon = PalObject("Jetragon", Elements.DRAGON)#
    DreamDemon = PalObject("Daedream", Elements.DARK)#
    Monkey = PalObject("Tanzee", Elements.LEAF)#
    Manticore = PalObject("Blazehowl", Elements.FIRE)#
    Manticore_Dark = PalObject("Blazehowl Noct", Elements.FIRE, Elements.DARK)#
    KingAlpaca = PalObject("Kingpaca", Elements.NORMAL)#
    KingAlpaca_Ice = PalObject("Ice Kingpaca", Elements.ICE)#
    PlantSlime = PalObject("Gumoss", Elements.LEAF, Elements.EARTH)#
    PlantSlime_Flower = PalObject("Gumoss (Special)", Elements.LEAF, Elements.EARTH)#
    MopBaby = PalObject("Swee", Elements.ICE)#
    MopKing = PalObject("Sweepa", Elements.ICE)#
    CatMage = PalObject("Katress", Elements.DARK)#
    PinkRabbit = PalObject("Ribunny", Elements.NORMAL)#
    ThunderBird = PalObject("Beakon", Elements.ELECTRICITY)#
    HerculesBeetle = PalObject("Warsect", Elements.EARTH, Elements.LEAF)#
    SaintCentaur = PalObject("Paladius", Elements.NORMAL)#
    NightFox = PalObject("Nox", Elements.DARK)#
    CaptainPenguin = PalObject("Penking", Elements.WATER, Elements.ICE)#
    WeaselDragon = PalObject("Chillet", Elements.ICE, Elements.DRAGON)#
    SkyDragon = PalObject("Quivern", Elements.DRAGON)#
    HadesBird = PalObject("Helzephyr", Elements.DARK)#
    RedArmorBird = PalObject("Ragnahawk", Elements.FIRE)#
    Ronin = PalObject("Bushi", Elements.FIRE)#
    FlyingManta = PalObject("Celeray", Elements.WATER)#
    BlackCentaur = PalObject("Necromus", Elements.DARK)#
    FlowerDoll = PalObject("Petallia", Elements.LEAF)#
    NaughtyCat = PalObject("Grintale", Elements.NORMAL)#
    CuteButterfly = PalObject("Cinnamoth", Elements.LEAF)#
    DarkScorpion = PalObject("Menasting", Elements.DARK, Elements.EARTH)#
    ThunderDragonMan = PalObject("Orserk", Elements.DRAGON, Elements.ELECTRICITY)#
    WoolFox = PalObject("Cremis", Elements.NORMAL)#
    LazyCatfish = PalObject("Dumud", Elements.EARTH)#
    LavaGirl = PalObject("Flambelle", Elements.FIRE)#
    FlameBambi = PalObject("Rooby", Elements.FIRE)#

class PalEntity:

    def __init__(self, data):
        self._data = data
        self._obj = data['value']['Struct']['Struct']['RawData']['Parsed']['object']['SaveParameter']['value']
        
        typename = self._obj['CharacterID']['value']
        self._type = PalType[typename]
        print(f"Created Entity of type {typename}: {self._type.value}")

        self._gender = "Male ♂" if self._obj['Gender']['value']['value'] == "EPalGenderType::Male" else "Female ♀"

        self._workspeed = self._obj['CraftSpeed']['value']
        self._melee = self._obj['Talent_Melee']['value']
        self._ranged = self._obj['Talent_Shot']['value']
        self._defence = self._obj['Talent_Defense']['value']

        try:
            self._skills = self._obj['PassiveSkillList']['value']['values']
        except:
            self._skills = []

        self._owner = self._obj['OwnerPlayerUId']['value']

    def GetType(self):
        return self._type

    def GetObject(self):
        return self._type.value

    def GetGender(self):
        return self._gender

    def GetWorkSpeed(self):
        return self._workspeed

    def GetAttackMelee(self):
        return self._melee

    def GetAttackRanged(self):
        return self._ranged

    def GetDefence(self):
        return self._defence

    def GetName(self):
        return self.GetObject().GetName()

    def GetImage(self):
        return self.GetObject().GetImage()
    
    def GetPrimary(self):
        return self.GetObject().GetPrimary().value

    def GetSecondary(self):
        return self.GetObject().GetSecondary().value

    def GetSkills(self):
        print(self._skills)
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
