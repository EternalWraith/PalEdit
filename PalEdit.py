import os, webbrowser, json, time, uuid, math, orjson

# pyperclip
# docs: https://pypi.org/project/pyperclip/#description
# install: pip install pyperclip
import pyperclip

import SaveConverter
import tkinter as tk

from PalInfo import *

from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox
from PIL import ImageTk, Image


global palbox
palbox = {}
global players
players = {}

global containers
containers = {}

global unknown
unknown = []

global data
global palguidmanager
palguidmanager : PalGuid = None
global debug
debug = "false"
global editindex
editindex = -1
global version
version = "0.5.3"
global filename
filename = ""


ftsize = 18
badskill = "#DE3C3A"
okayskill = "#DFE8E7"
goodskill = "#FEDE00"


def hex_to_rgb(value):
   value = value.lstrip('#')
   lv = len(value)
   return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_hex(rgb):
   return '%02x%02x%02x' % rgb


def mean_color(color1, color2):
   rgb1 = hex_to_rgb(color1.replace("#", ""))
   rgb2 = hex_to_rgb(color2.replace("#", ""))

   avg = lambda x, y: round((x+y) / 2)

   new_rgb = ()

   for i in range(len(rgb1)):
      new_rgb += (avg(rgb1[i], rgb2[i]),)
       
   return "#"+rgb_to_hex(new_rgb)

def toggleDebug():
    global debug
    if debug == "false":
        debug = "true"
        frameDebug.pack(fill=BOTH, expand=False)
    else:
        debug = "false"
        frameDebug.pack_forget()
    updateWindowSize()



def isPalSelected():
    global palbox
    if current.get() == "":
        return False
    if len(palbox[players[current.get()]]) == 0:
        return False
    if len(listdisplay.curselection()) == 0:
        return False
    return True

def getSelectedPalInfo():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]
    print(f"Get Info: {pal.GetNickname()}")     
    print(f"  - Level: {pal.GetLevel() if pal.GetLevel() > 0 else '?'}")    
    print(f"  - Rank: {pal.GetRank()}")    
    print(f"  - Skill 1:  {skills[0].get()}")
    print(f"  - Skill 2:  {skills[1].get()}")
    print(f"  - Skill 3:  {skills[2].get()}")
    print(f"  - Skill 4:  {skills[3].get()}")
    print(f"  - HP IV:  {pal.GetTalentHP()}")
    print(f"  - Melee IV:  {pal.GetAttackMelee()}")
    print(f"  - Range IV:  {pal.GetAttackRanged()}")

def getSelectedPalData():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]
    # print(f"Get Data: {pal.GetNickname()}")    
    # print(f"{pal._obj}")  
    pyperclip.copy(f"{pal._obj}")
    webbrowser.open('https://jsonformatter.curiousconcept.com/#')

def updateAttacks():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]
    attackops = [PalAttacks[e] for e in PalAttacks]
    
          
    for a in range(0,3):
        if a > len(pal.GetEquippedMoves())-1:
            attacks[a].set("None")
        else:
            attacks[a].set(PalAttacks[pal.GetEquippedMoves()[a]])
    setAttackCols()

def setAttackCols():
    for i in range(0,3):
        if attacks[i].get() == "None":
            attackdrops[i].config(highlightbackground="lightgrey", bg="lightgrey", activebackground="lightgrey")
        else:
            v = attacks[i].get()
            basecol = PalElements[AttackTypes[v]]
            halfcol = mean_color(basecol, "ffffff")
            attackdrops[i].config(highlightbackground=basecol, bg=halfcol, activebackground=halfcol)

def setpreset(preset):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i] # seems global palbox is not necessary

    tid = []
    for v in range(0, 4):
        t = skills[v].trace_add("write", lambda *args, num=v: changeskill(num))
        tid.append(t)
    
    match preset:
        case "base":
            skills[0].set("Artisan")
            skills[1].set("Workaholic")
            skills[2].set("Lucky")
            skills[3].set("Diet Lover")
        case "workspeed":
            skills[0].set("Artisan")
            skills[1].set("Serious")
            skills[2].set("Lucky")
            skills[3].set("Work Slave")
        case "movement":
            skills[0].set("Swift")
            skills[1].set("Legend")
            skills[2].set("Runner")
            skills[3].set("Nimble")
        case "tank":
            skills[0].set("Burly Body")
            skills[1].set("Legend")
            skills[2].set("Masochist")
            skills[3].set("Hard Skin")
        case "dmg_max":
            skills[0].set("Musclehead")
            skills[1].set("Legend")
            skills[2].set("Ferocious")
            skills[3].set("Lucky")
        case "dmg_balanced":
            skills[0].set("Musclehead")
            skills[1].set("Legend")
            skills[2].set("Ferocious")
            skills[3].set("Burly Body")
        case "dmg_mount":
            skills[0].set("Musclehead")
            skills[1].set("Legend")
            skills[2].set("Ferocious")
            skills[3].set("Swift")
        case "dmg_element":
            primary = pal.GetPrimary().lower()
            secondary = pal.GetSecondary().lower()
            if primary == "none":
                messagebox.showerror("Preset: Dmg: Element", "This pal has no elements! Preset skipped")
                return
            skills[0].set("Musclehead")
            skills[1].set("Legend")
            skills[2].set("Ferocious")
            match primary:
                case "neutral":
                    skills[3].set("Celestial Emperor")
                case "dark":
                    skills[3].set("Lord of the Underworld")
                case "dragon":
                    skills[3].set("Divine Dragon")
                case "ice":
                    skills[3].set("Ice Emperor")
                case "fire":
                    skills[3].set("Flame Emperor")
                case "grass":
                    skills[3].set("Spirit Emperor")
                case "ground":
                    skills[3].set("Earth Emperor")
                case "electric":
                    skills[3].set("Lord of Lightning")
                case "water":
                    skills[3].set("Lord of the Sea")
                case _:
                    messagebox.showerror(f"Error: elemental was not found for preset: {primary}-{secondary}")

            # uncecessary msg
            # if not secondary == "none":
            #     messagebox.showerror(f"You pal has a second elemental - its probably better to use Dmg: Max preset")
        case _:
            print(f"Preset {preset} not found - nothing changed")
            return

    for v in range(0, 4):
        skills[v].trace_remove("write", tid[v])
    
    # exp (if level selected)
    if checkboxLevelVar.get() == 1:
        pal.SetLevel(textboxLevelVar.get())
    # rank (if rank selected)
    if checkboxRankVar.get() == 1:
        changerank(optionMenuRankVar.get())
    # attributes (if attributes selected)
    # TODO: change attributes

    refresh(i)

def preset_base():
    setpreset("base")
def preset_workspeed():
    setpreset("workspeed")
def preset_movement():
    setpreset("movement")
def preset_tank():
    setpreset("tank")
def preset_dmg_max():
    setpreset("dmg_max")
def preset_dmg_balanced():
    setpreset("dmg_balanced")
def preset_dmg_mount():
    setpreset("dmg_mount")
def preset_dmg_element():
    setpreset("dmg_element")

def changerank(configvalue):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]
    match configvalue:
        case 4:
            pal.SetRank(5)
        case 3:
            pal.SetRank(4)
        case 2:
            pal.SetRank(3)
        case 1:
            pal.SetRank(2)
        case _:
            pal.SetRank(1)
    refresh(i)

def changerankchoice(choice):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]
    changerank(ranksvar.get())

def changeskill(num):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]

    if not skills[num].get() in ["Unknown", "UNKNOWN"]:
        if skills[num].get() in ["None", "NONE"]:
            pal.RemoveSkill(num)
        else:
            
            pal.SetSkill(num, skills[num].get())
    
    refresh(i)

def changeequipmoves(num):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]
    
    if not attacks[num].get() in ["Unknown", "UNKNOWN"]:
        if attacks[num].get() in ["None", "NONE"]:
            pal.RemoveEquipMoves(num)
        else:
            pal.SetEquipMoves(num, attacks[num].get())
    
    refresh(i)

def onselect(evt):
    global palbox
    global editindex
    global debug
    w = evt.widget
    if not isPalSelected():
        return

    if editindex > -1:
        updatestats(editindex)
        
    index = int(w.curselection()[0])
    editindex = index


    pal = palbox[players[current.get()]][index]
    #palname.config(text=pal.GetName())
    speciesvar.set(pal.GetName())

    storageId.config(text=f"StorageID: {pal.storageId}")
    storageSlot.config(text=f"StorageSlot: {pal.storageSlot}")

    g = pal.GetGender()
    palgender.config(text=g, fg=PalGender.MALE.value if g == "Male ♂" else PalGender.FEMALE.value)

    title.config(text=f"{pal.GetNickname()}")
    level.config(text=f"Lv. {pal.GetLevel() if pal.GetLevel() > 0 else '?'}")
    portrait.config(image=pal.GetImage())

    ptype.config(text=pal.GetPrimary(), bg=PalElements[pal.GetPrimary()])
    stype.config(text=pal.GetSecondary(), bg=PalElements[pal.GetSecondary()])

    # ⚔🏹
    #talent_hp_var.set(pal.GetTalentHP())
    phpvar.set(pal.GetTalentHP())
    meleevar.set(pal.GetAttackMelee())
    shotvar.set(pal.GetAttackRanged())
    defvar.set(pal.GetDefence())
    wspvar.set(pal.GetWorkSpeed())

    luckyvar.set(pal.isLucky)
    alphavar.set(pal.isBoss)

    updateAttacks()


    # rank
    match pal.GetRank():
        case 5:
            ranksvar.set(ranks[4])
        case 4:
            ranksvar.set(ranks[3])
        case 3:
            ranksvar.set(ranks[2])
        case 2:
            ranksvar.set(ranks[1])
        case _:
            ranksvar.set(ranks[0])

    s = pal.GetSkills()[:]
    while len(s) < 4:
        s.append("NONE")

    for i in range(0, 4):
        if not s[i] in [p for p in PalPassives]:
            skills[i].set("Unknown")
        else:
            skills[i].set(PalPassives[s[i]])

    setskillcolours()
    

def changetext(num):
    if num == -1:
        skilllabel.config(text="Hover a skill to see it's description")
        return
    
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i] # seems global palbox is not necessary

    global unknown
    if type(num) == str:
        skilllabel.config(text=pal.GetOwner())
        return


    if skills[num].get() == "Unknown":
        skilllabel.config(text=f"{pal.GetSkills()[num]}{PassiveDescriptions['Unknown']}")
        return
    skilllabel.config(text=PassiveDescriptions[skills[num].get()])

    
def loadfile():
    global filename
    skilllabel.config(text="Loading save, please be patient...")

    file = askopenfilename(initialdir=os.path.expanduser('~')+"\AppData\Local\Pal\Saved\SaveGames", filetype=[("Level.sav", "Level.sav")])
    print(f"Opening file {file}")

    if file:
        filename = file
        root.title(f"PalEdit v{version} - {file}")
        skilllabel.config(text="Decompiling save, please be patient...")
        doconvertjson(file, (not debug))
    else:
        messagebox.showerror("Select a file", "Please select a save file.")

def sortPals(e):
    return e.GetName()

def load(file):
    global data
    global palguidmanager

    f = open(file, "r", encoding="utf8")
    data = json.loads(f.read())
    f.close()

    if file.endswith(".pson"):
        paldata = data
    else:
        paldata = data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        palguidmanager = PalGuid(data)
        f = open("current.pson", "w", encoding="utf8")
        json.dump(paldata, f, indent=4)
        f.close()
    loaddata(paldata)

def loaddata(paldata):
    global palbox
    global players
    global current
    global containers
    global palguidmanager
    current.set("")
    palbox = {}
    players = palguidmanager.GetPlayerslist()
    for p in players:
        palbox[players[p]] = []
    containers = {}
    nullmoves = []
    for i in paldata:
        try:
            p = PalEntity(i)
            #if not p.owner in palbox:
            #    palbox[p.owner] = []
            #palbox[p.owner].append(p)
            if p.owner in players.values():
                if p.GetPalInstanceGuid() == palguidmanager.GetContainerSave(p.storageId, p.storageSlot):
                    palbox[p.owner].append(p)
                else:#Storage Conflict
                    unknown.append(i)
            else:#Unknow Owner
                unknown.append(i)
            n = p.GetFullName()

            for m in p.GetLearntMoves():
                if not m in nullmoves:
                    if not m in PalAttacks:
                        nullmoves.append(m)

        except Exception as e:

            if str(e) == "This is a player character":
                print("Found Player Character")
                # print(f"\nDebug: Data \n{i}\n\n")
                #o = i['value']['RawData']['value']['object']['SaveParameter']['value']
                #pl = "No Name"
                #if "NickName" in o:
                #    pl = o['NickName']['value']
                #plguid = i['key']['PlayerUId']['value']
                #print(f"{pl} - {plguid}")
                #players[pl] = plguid
            else:
                unknown.append(i)
                print(f"Error occured: {str(e)}")
            # print(f"Debug: Data {i}")

    current.set(next(iter(players)))
    print(f"Defaulted selection to {current.get()}")
    
    updateDisplay()

    print(f"Unknown list contains {len(unknown)} entries")

    #if len(unknown) > 0:
    #    for i in unknown:
    #        paldata.remove(i)

    #for i in unknown:
        #print (i)
    
    print(f"{len(players)} players found:")
    for i in players:
        print(f"{i} = {players[i]}")
    playerdrop['values'] = list(players.keys())
    playerdrop.current(0)
    if False: # change to true to enable testing of containers
        if not file.endswith(".pson"):
            condata = data['properties']['worldSaveData']['value']['CharacterContainerSaveData']['value']
            for c in condata:
                conguid = c["key"]["ID"]["value"]
                if not conguid in containers:
                    containers[conguid] = 0
                else:
                    containers[conguid] += 1

            print(f"{len(containers)} containers were found")
            for c in containers:
                print(f"{c} : {containers[c]}")
    
    nullmoves.sort()    
    for i in nullmoves:
        print(f"{i} was not found in Attack Database")

    refresh()

    changetext(-1)
    jump()
    messagebox.showinfo("Done", "Done loading!")

def jump():
    root.attributes('-topmost', 1)
    root.attributes('-topmost', 0)
    root.focus_force()
    root.bell()

def updateDisplay():
    listdisplay.delete(0,END)
    palbox[players[current.get()]].sort(key=sortPals)

    for p in palbox[players[current.get()]]:
        listdisplay.insert(END, p.GetFullName())

        if p.isBoss:
            listdisplay.itemconfig(END, {'fg': 'red'})
        elif p.isLucky:
            listdisplay.itemconfig(END, {'fg': 'blue'})
    

def savefile():
    global palbox
    global data
    global filename
    skilllabel.config(text="Saving, please be patient... (it can take up to 5 minutes in large files)")
    root.update()
    
    if isPalSelected():
        i = int(listdisplay.curselection()[0])
        refresh(i)

    file = filename.replace('.sav','.sav.json')
    print(file, filename)
    if file:
        print(f"Opening file {file}")

        savejson(file)
        doconvertsave(file)
        

        changetext(-1)
        jump()
        messagebox.showinfo("Done", "Done saving!")

def savepson(filename):
    f = open(filename, "w", encoding="utf8")
    if 'properties' in data:
        json.dump(data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'], f)#, indent=4)
    else:
        json.dump(data, f)#, indent=4)
    f.close()

def savejson(filename):
    #f = open(filename, "r", encoding="utf8")
    #svdata = json.loads(f.read())
    #f.close()

    #if 'properties' in data:
        #svdata['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
    #else:
        #svdata['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = data
    f = open(filename, "wb")
    f.write(orjson.dumps(data))
    f.close()

    changetext(-1)
    
def createGUIDtoClipboard():
    newguid = uuid.uuid4()
    print(newguid)
    pyperclip.copy(f"{newguid}")

def generateguid():
    newguid = uuid.uuid4()
    print(newguid)

def updatestats(e):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][e]
    l = pal.GetLevel()
    #pal.SetTalentHP(talent_hp_var.get())
    h = phpvar.get()
    pal.SetTalentHP(h)
    hv = 500 + (((70*0.5)*l) * (1+ (h / 100)))
    hthstatval.config(text=math.floor(hv))

    a = meleevar.get()
    pal.SetAttackMelee(a)
    pal.SetAttackRanged(shotvar.get())
    av = 100 + (((70*0.75)*l) * (1+ (a / 100)))
    atkstatval.config(text=math.floor(av))

    d = defvar.get()
    pal.SetDefence(d)
    dv = 50 + (((70*0.75)*l) * (1+ (d / 100)))
    defstatval.config(text=math.floor(dv))
    
    pal.SetWorkSpeed(wspvar.get())

def takelevel():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]

    if pal.GetLevel() == 1:
        return
    pal.SetLevel(pal.GetLevel()-1)
    refresh(i)

def givelevel():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]

    if pal.GetLevel() == 50:
        return
    pal.SetLevel(pal.GetLevel()+1)
    refresh(i)

def changespeciestype(evt):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]
    
    pal.SetType(speciesvar.get())
    updateDisplay()
    refresh(palbox[players[current.get()]].index(pal))

def setskillcolours():
    for snum in range(0,4):
        rating = PassiveRating[skills[snum].get()]
        col = goodskill if rating == "Good" else okayskill if rating == "Okay" else badskill

        skilldrops[snum].config(highlightbackground=col, bg=mean_color(col, "ffffff"), activebackground=mean_color(col, "ffffff"))

def refresh(num=0):
    setskillcolours()
    setAttackCols()
    
    listdisplay.select_set(num)
    listdisplay.event_generate("<<ListboxSelect>>")

def converttojson():

    skilllabel.config(text="Converting... this may take a while.")
    
    file = askopenfilename(filetype=[("All files", "*.sav")])
    print(f"Opening file {file}")

    doconvertjson(file)

def doconvertjson(file, compress=False):
    SaveConverter.convert_sav_to_json(file, file.replace(".sav", ".sav.json"), True, compress)

    load(file.replace(".sav", ".sav.json"))

    changetext(-1)
    jump()
    #messagebox.showinfo("Done", "Done decompiling!")

def converttosave():
    skilllabel.config(text="Converting... this may take a while.")
    
    file = askopenfilename(filetype=[("All files", "*.sav.json")])
    print(f"Opening file {file}")

    doconvertsave(file)

def spawnpal():
    global filename
    global palguidmanager
    global data
    if not isPalSelected() or palguidmanager is None:
        return

    playermanager = PalPlayerManager(filename, palguidmanager.GetPlayerslist().values())
    playerguid = players[current.get()]
    player = playermanager.TryGetPlayerEntity(playerguid)
    if player is None:
        return
    #SaveConverter.convert_obj_to_sav(player.dump(), playersav + ".bak", True)

    file = askopenfilename(filetype=[("json files", "*.json")])
    if file == '':
        messagebox.showerror("Select a file", "Please select a save file.")
        return

    f = open(file, "r", encoding="utf8")
    spawnpaldata = json.loads(f.read())
    f.close()

    slotguid = player.GetPalStorageGuid()
    groupguid = palguidmanager.GetGroupGuid(playerguid)
    if any(guid == None for guid in [slotguid, groupguid]):
        return
    for p in spawnpaldata['Pals']:
        newguid = str(uuid.uuid4())
        pal = PalEntity(p)
        i = palguidmanager.GetEmptySlotIndex(slotguid)
        if i == -1:
            print("Player Pal Storage is full!")
            return
        pal.InitializationPal(newguid, playerguid, groupguid, slotguid)
        palguidmanager.AddGroupSaveData(groupguid, newguid)
        palguidmanager.SetContainerSave(slotguid, i, newguid)
        data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'].append(pal._data)
        print(f"Add Pal at slot {i} : {slotguid}")
    loaddata(data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'])

def dumppals():
    if not isPalSelected():
        return
    pals = {}
    pals['Pals'] = [pal._data for pal in palbox[players[current.get()]]]
    file = asksaveasfilename(filetype=[("json files", "*.json")], defaultextension = ".json")
    if file:
        with open(file, "wb") as f:
            f.write(orjson.dumps(pals, option= orjson.OPT_INDENT_2))
    else:
        messagebox.showerror("Select a file", "Please select a save file.")
    

def doconvertsave(file):
    SaveConverter.convert_json_to_sav(file, file.replace(".sav.json", ".sav"), True)

    changetext(-1)
    jump()
    #messagebox.showinfo("Done", "Done compiling!")

def swapgender():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]

    pal.SwapGender()
    refresh(i)

def replaceitem(i, pal):
    listdisplay.delete(i)
    listdisplay.insert(i, pal.GetFullName())

    if pal.isBoss:
        listdisplay.itemconfig(i, {'fg': 'red'})
    elif pal.isLucky:
        listdisplay.itemconfig(i, {'fg': 'blue'})

def togglelucky():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]

    if luckyvar.get() == 1 and alphavar.get() == 1:
        alphavar.set(0)

    pal.SetLucky(True if luckyvar.get() == 1 else False)
    replaceitem(i, pal)
    refresh(i)

def togglealpha():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]

    if luckyvar.get() == 1 and alphavar.get() == 1:
        luckyvar.set(0)

    pal.SetBoss(True if alphavar.get() == 1 else False)
    replaceitem(i, pal)
    refresh(i)

root = Tk()
purplepanda = ImageTk.PhotoImage(Image.open(f'resources/MossandaIcon.png').resize((240,240)))
root.iconphoto(True, purplepanda)
root.title(f"PalEdit v{version}")

global current
current = StringVar()
current.set("")

tools = Menu(root)
root.config(menu=tools)

filemenu = Menu(tools, tearoff=0)
filemenu.add_command(label="Load PalWorld Save", command=loadfile)
filemenu.add_command(label="Save Changes To File", command=savefile)

tools.add_cascade(label="File", menu=filemenu, underline=0)

toolmenu = Menu(tools, tearoff=0)
toolmenu.add_command(label="Debug", command=toggleDebug)
# toolmenu.add_command(label="Generate GUID", command=generateguid)

tools.add_cascade(label="Tools", menu=toolmenu, underline=0)

#convmenu = Menu(tools, tearoff=0)
#convmenu.add_command(label="Convert Save to Json", command=converttojson)
#convmenu.add_command(label="Convert Json to Save", command=converttosave)

#tools.add_cascade(label="Converter", menu=convmenu, underline=0)

scrollview = Frame(root)
scrollview.pack(side=LEFT, fill=Y)

def changeplayer(evt):
    print(current.get())
    print(len(palbox[players[current.get()]]))
    updateDisplay()

playerframe = Frame(scrollview)
playerframe.pack(fill=X)
playerlbl = Label(playerframe, text="Player:")
playerlbl.config(justify='center')
playerlbl.pack(side=LEFT, fill=X, expand=True)
playerdrop = ttk.Combobox(playerframe, textvariable=current)
playerdrop.pack(side=RIGHT, fill=X)
playerdrop.bind("<<ComboboxSelected>>", changeplayer)

scrollbar = Scrollbar(scrollview)
scrollbar.pack(side=LEFT, fill=Y)
listdisplay = Listbox(scrollview, width=30, yscrollcommand=scrollbar.set, exportselection=0)
listdisplay.pack(side=LEFT, fill=BOTH)
listdisplay.bind("<<ListboxSelect>>", onselect)
scrollbar.config(command=listdisplay.yview)

# Attack Skills
atkskill = Frame(root, width=120, relief="groove", borderwidth=2)
atkskill.pack(side=RIGHT, fill=Y)
atkLabel = Label(atkskill, bg="darkgrey", width=12, text="Equipped", font=("Arial", ftsize), justify="center")
atkLabel.pack(fill=X)

attacks = [StringVar(), StringVar(), StringVar()]
attacks[0].set("Blast Punch")
attacks[1].set("Tri-Lightning")
attacks[2].set("Dark Laser")

equipFrame = Frame(atkskill, borderwidth=2, relief="raised")
equipFrame.pack(fill=X)

attackops = [PalAttacks[e] for e in PalAttacks]
attackops.remove("None")
attackops.sort()
attackops.insert(0,"None")
attackdrops = [
    OptionMenu(equipFrame, attacks[0], *attackops, command=lambda evt: changeequipmoves(0)),
    OptionMenu(equipFrame, attacks[1], *attackops, command=lambda evt: changeequipmoves(1)),
    OptionMenu(equipFrame, attacks[2], *attackops, command=lambda evt: changeequipmoves(2))
    ]

attackdrops[0].pack(fill=X)
attackdrops[0].config(font=("Arial", ftsize), width=12, direction="right")
attackdrops[1].pack(fill=X)
attackdrops[1].config(font=("Arial", ftsize), width=12, direction="right")
attackdrops[2].pack(fill=X)
attackdrops[2].config(font=("Arial", ftsize), width=12, direction="right")

attackdrops[0].config(highlightbackground=PalElements["Electric"], bg=mean_color(PalElements["Electric"], "ffffff"), activebackground=mean_color(PalElements["Electric"], "ffffff"))
attackdrops[1].config(highlightbackground=PalElements["Electric"], bg=mean_color(PalElements["Electric"], "ffffff"), activebackground=mean_color(PalElements["Electric"], "ffffff"))
attackdrops[2].config(highlightbackground=PalElements["Dark"], bg=mean_color(PalElements["Dark"], "ffffff"), activebackground=mean_color(PalElements["Dark"], "ffffff"))

stats = Frame(atkskill)
#stats.pack(fill=X)

statLabel = Label(stats, bg="darkgrey", width=12, text="Stats", font=("Arial", ftsize), justify="center")
statLabel.pack(fill=X)


statlbls = Frame(stats, width=6, bg="darkgrey")
statlbls.pack(side=LEFT, expand=True, fill=X)

hthstatlbl = Label(statlbls, bg="darkgrey", text="Health", font=("Arial", ftsize), justify="center")
hthstatlbl.pack()
atkstatlbl = Label(statlbls, bg="darkgrey", text="Attack", font=("Arial", ftsize), justify="center")
atkstatlbl.pack()
defstatlbl = Label(statlbls, bg="darkgrey", text="Defence", font=("Arial", ftsize), justify="center")
defstatlbl.pack()


statvals = Frame(stats, width=6)
statvals.pack(side=RIGHT, expand=True, fill=X)

hthstatval = Label(statvals, bg="lightgrey", text="500", font=("Arial", ftsize), justify="center")
hthstatval.pack(fill=X)
atkstatval = Label(statvals, text="100", font=("Arial", ftsize), justify="center")
atkstatval.pack(fill=X)
defstatval = Label(statvals, bg="lightgrey", text="50", font=("Arial", ftsize), justify="center")
defstatval.pack(fill=X)

disclaim = Label(atkskill, bg="darkgrey", text="The values above do not include passive skills", font=("Arial", ftsize//2))
#disclaim.pack(fill=X)

# Individual Info
infoview = Frame(root, relief="groove", borderwidth=2, width=480, height=480)
infoview.pack(side=RIGHT, fill=BOTH, expand=True)

dataview = Frame(infoview)
dataview.pack(side=TOP, fill=BOTH)

resourceview = Frame(dataview)
resourceview.pack(side=LEFT, fill=BOTH, expand=True)

portrait = Label(resourceview, image=purplepanda, relief="sunken", borderwidth=2)
portrait.pack()

typeframe = Frame(resourceview)
typeframe.pack(expand=True, fill=X)
ptype = Label(typeframe, text="Electric", font=("Arial", ftsize), bg=PalElements["Electric"], width=6)
ptype.pack(side=LEFT, expand=True, fill=X)
stype = Label(typeframe, text="Dark", font=("Arial", ftsize), bg=PalElements["Dark"], width=6)
stype.pack(side=RIGHT, expand=True, fill=X)

formframe = Frame(resourceview)
formframe.pack(expand=True, fill=X)
luckyvar = IntVar()
alphavar = IntVar()
luckybox = Checkbutton(formframe, text='Lucky', variable=luckyvar, onvalue='1', offvalue='0', command=togglelucky)
luckybox.pack(side=LEFT, expand=True)
alphabox = Checkbutton(formframe, text='Alpha', variable=alphavar, onvalue='1', offvalue='0', command=togglealpha)
alphabox.pack(side=RIGHT, expand=True)

deckview = Frame(dataview, width=320, relief="sunken", borderwidth=2, pady=0)
deckview.pack(side=RIGHT, fill=BOTH, expand=True)

title = Label(deckview, text=f"PalEdit", bg="darkgrey", font=("Arial", 24), width=17)
title.pack(expand=True, fill=BOTH)

headerframe = Frame(deckview, padx=0, pady=0, bg="darkgrey")
headerframe.pack(fill=X)
headerframe.grid_rowconfigure(0, weight=1)
headerframe.grid_columnconfigure((0,2), uniform="equal")
headerframe.grid_columnconfigure(1, weight=1)

level = Label(headerframe, text=f"v{version}", bg="darkgrey", font=("Arial", 24), width=17)
level.bind("<Enter>", lambda evt, num="owner": changetext(num))
level.bind("<Leave>", lambda evt, num=-1: changetext(num))
level.grid(row=0, column=1, sticky="nsew")

minlvlbtn = Button(headerframe, text="➖", borderwidth=1, font=("Arial", ftsize-2), command=takelevel, bg="darkgrey")
minlvlbtn.grid(row=0, column=0, sticky="nsew")

addlvlbtn = Button(headerframe, text="➕", borderwidth=1, font=("Arial", ftsize-2), command=givelevel, bg="darkgrey")
addlvlbtn.grid(row=0, column=2, sticky="nsew")


labelview = Frame(deckview, bg="lightgrey", pady=0, padx=16)
labelview.pack(side=LEFT, expand=True, fill=BOTH)

name = Label(labelview, text="Species", font=("Arial", ftsize), bg="lightgrey")
name.pack(expand=True, fill=X)
gender = Label(labelview, text="Gender", font=("Arial", ftsize), bg="lightgrey", width=6, pady=6)
gender.pack(expand=True, fill=X)
attack = Label(labelview, text="Attack IV%", font=("Arial", ftsize), bg="lightgrey", width=8)
attack.pack(expand=True, fill=X)
defence = Label(labelview, text="Defence IV%", font=("Arial", ftsize), bg="lightgrey", width=8)
defence.pack(expand=True, fill=X)
workspeed = Label(labelview, text="Workspeed IV%", font=("Arial", ftsize), bg="lightgrey", width=12)
workspeed.pack(expand=True, fill=X)
hp = Label(labelview, text="HP IV%", font=("Arial", ftsize), bg="lightgrey", width=10)
hp.pack(expand=True, fill=X)
rankspeed = Label(labelview, text="Rank", font=("Arial", ftsize), bg="lightgrey")
rankspeed.pack(expand=True, fill=X)

editview = Frame(deckview)
editview.pack(side=RIGHT, expand=True, fill=BOTH)

species = [PalSpecies[e].GetName() for e in PalSpecies]
species.sort()
speciesvar = StringVar()
speciesvar.set("PalEdit")
palname = OptionMenu(editview, speciesvar, *species, command=changespeciestype)
palname.config(font=("Arial", ftsize), padx=0, pady=0, borderwidth=1, width=5, direction='right')
palname.pack(expand=True, fill=X)

genderframe = Frame(editview, pady=0)
genderframe.pack()
palgender = Label(genderframe, text="Unknown", font=("Arial", ftsize), fg=PalGender.UNKNOWN.value, width=10)
palgender.pack(side=LEFT, expand=True, fill=X)
swapbtn = Button(genderframe, text="↺", borderwidth=1, font=("Arial", ftsize-2), command=swapgender)
swapbtn.pack(side=RIGHT)

def clamp(var):
    try:
        int(var.get())
    except TclError as e:
        return

    if var.get() > 100:
        var.set(100)
        return

    if var.get() < 0:
        var.set(0)
        return

def ivvalidate(p):
    if len(p) > 3:
        return False
    
    if p.isdigit() or p == "":
        return True

    return False

def fillifempty(var):
    try:
        int(var.get())
    except TclError as e:
        var.set(0)

valreg = root.register(ivvalidate)

attackframe = Frame(editview, width=6)
attackframe.pack(fill=X)
meleevar = IntVar()
shotvar = IntVar()
meleevar.trace("w", lambda name, index, mode, sv=meleevar: clamp(sv))
shotvar.trace("w", lambda name, index, mode, sv=shotvar: clamp(sv))
meleevar.set(100)
shotvar.set(0)
meleeicon = Label(attackframe, text="⚔", font=("Arial", ftsize))
meleeicon.pack(side=LEFT)
shoticon = Label(attackframe, text="🏹", font=("Arial", ftsize))
shoticon.pack(side=RIGHT)
palmelee = Entry(attackframe, textvariable=meleevar, font=("Arial", ftsize), width=6)
palmelee.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
palmelee.bind("<FocusOut>", lambda evt, sv=meleevar: fillifempty(sv))
palmelee.pack(side=LEFT)
palshot = Entry(attackframe, textvariable=shotvar, font=("Arial", ftsize), width=6)
palshot.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
palshot.bind("<FocusOut>", lambda evt, sv=shotvar: fillifempty(sv))
palshot.pack(side=RIGHT)


defvar = IntVar()
defvar.trace("w", lambda name, index, mode, sv=defvar: clamp(sv))
defvar.set(100)
paldef = Entry(editview, textvariable=defvar, font=("Arial", ftsize), width=6)
paldef.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
paldef.bind("<FocusOut>", lambda evt, sv=defvar: fillifempty(sv))
paldef.pack(expand=True, fill=X)

wspvar = IntVar()
wspvar.trace("w", lambda name, index, mode, sv=wspvar: clamp(sv))
wspvar.set(70)
palwsp = Entry(editview, textvariable=wspvar, font=("Arial", ftsize), width=6)
palwsp.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
palwsp.bind("<FocusOut>", lambda evt, sv=wspvar: fillifempty(sv))
palwsp.pack(expand=True, fill=X)

def talent_hp_changed(*args):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[players[current.get()]][i]
    if talent_hp_var.get() == 0:
        talent_hp_var.set(1)
    # change value of pal

phpvar = IntVar()
phpvar.trace("w", lambda name, index, mode, sv=phpvar: clamp(sv))
phpvar.set(50)
palhps = Entry(editview, textvariable=phpvar, font=("Arial", ftsize), width=6)
palhps.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
palhps.bind("<FocusOut>", lambda evt, sv=phpvar: fillifempty(sv))
palhps.pack(expand=True, fill=X)

"""
talent_hp_var = IntVar(value=50)
talent_hp_var.trace_add("write", lambda name, index, mode, sv=talent_hp_var: talent_hp_changed(clamp(sv)))
# hpslider = Scale(editview, from_=0, to=100, tickinterval=50, orient='horizontal', variable=talent_hp_var)
hpslider = Scale(editview, from_=0, to=100, orient='horizontal', variable=talent_hp_var)
hpslider.config(width=9)
hpslider.pack(pady=(0,10), expand=True, fill=X, anchor="center")
"""

ranks = ('0', '1', '2', '3', '4')
ranksvar = IntVar()
palrank = OptionMenu(editview, ranksvar, *ranks, command=changerankchoice)
palrank.config(font=("Arial", ftsize),  justify='center', padx=0, pady=0, borderwidth=1, width=5)
ranksvar.set(ranks[4])
palrank.pack(expand=True, fill=X)

# PASSIVE ABILITIES
skillview = Frame(infoview, relief="sunken", borderwidth=2)
skillview.pack(fill=BOTH, expand=True)

topview = Frame(skillview)
topview.pack(fill=BOTH, expand=True)
botview = Frame(skillview)
botview.pack(fill=BOTH, expand=True)

skills = [StringVar(), StringVar(), StringVar(), StringVar()]
#for i in range(0, 4):
    #skills[i].set("Unknown")
    #skills[i].trace("w", lambda *args, num=i: changeskill(num))
skills[0].set("Legend")
skills[1].set("Workaholic")
skills[2].set("Ferocious")
skills[3].set("Lucky")

op = [PalPassives[e] for e in PalPassives]
op.pop(0)
op.pop(0)
op.sort()
op.insert(0, "None")
skilldrops = [
    OptionMenu(topview, skills[0], *op, command=lambda evt: changeskill(0)),
    OptionMenu(topview, skills[1], *op, command=lambda evt: changeskill(1)),
    OptionMenu(botview, skills[2], *op, command=lambda evt: changeskill(2)),
    OptionMenu(botview, skills[3], *op, command=lambda evt: changeskill(3))
    ]

skilldrops[0].pack(side=LEFT, expand=True, fill=BOTH)
skilldrops[0].config(font=("Arial", ftsize), width=6, direction="right")
skilldrops[1].pack(side=RIGHT, expand=True, fill=BOTH)
skilldrops[1].config(font=("Arial", ftsize), width=6, direction="right")
skilldrops[2].pack(side=LEFT, expand=True, fill=BOTH)
skilldrops[2].config(font=("Arial", ftsize), width=6, direction="right")
skilldrops[3].pack(side=RIGHT, expand=True, fill=BOTH)
skilldrops[3].config(font=("Arial", ftsize), width=6, direction="right")

skilldrops[0].config(highlightbackground=goodskill, bg=mean_color(goodskill, "ffffff"), activebackground=mean_color(goodskill, "ffffff"))
skilldrops[1].config(highlightbackground=goodskill, bg=mean_color(goodskill, "ffffff"), activebackground=mean_color(goodskill, "ffffff"))
skilldrops[2].config(highlightbackground=goodskill, bg=mean_color(goodskill, "ffffff"), activebackground=mean_color(goodskill, "ffffff"))
skilldrops[3].config(highlightbackground=goodskill, bg=mean_color(goodskill, "ffffff"), activebackground=mean_color(goodskill, "ffffff"))

skilldrops[0].bind("<Enter>", lambda evt, num=0: changetext(num))
skilldrops[1].bind("<Enter>", lambda evt, num=1: changetext(num))
skilldrops[2].bind("<Enter>", lambda evt, num=2: changetext(num))
skilldrops[3].bind("<Enter>", lambda evt, num=3: changetext(num))
skilldrops[0].bind("<Leave>", lambda evt, num=-1: changetext(num))
skilldrops[1].bind("<Leave>", lambda evt, num=-1: changetext(num))
skilldrops[2].bind("<Leave>", lambda evt, num=-1: changetext(num))
skilldrops[3].bind("<Leave>", lambda evt, num=-1: changetext(num))

# PRESETS
framePresets = Frame(infoview, relief="groove", borderwidth=0)
framePresets.pack(fill=BOTH, expand=True)

framePresetsTitle = Frame(framePresets)
framePresetsTitle.pack(fill=BOTH)
presetTitle = Label(framePresetsTitle, text='Presets:', anchor='w', bg="darkgrey", font=("Arial", ftsize), width=6, height=1).pack(fill=BOTH)

framePresetsButtons = Frame(framePresets, relief="groove", borderwidth=4)
framePresetsButtons.pack(fill=BOTH, expand=True)

framePresetsButtons1 = Frame(framePresetsButtons)
framePresetsButtons1.pack(fill=BOTH, expand=True)
preset_title1 = Label(framePresetsButtons1, text='Utility:', anchor='e', bg="darkgrey", font=("Arial", 13), width=9).pack(side=LEFT, fill=X)
preset_button = Button(framePresetsButtons1, text="Base", command=preset_base)
preset_button.config(font=("Arial", 12))
preset_button.pack(side=LEFT, expand=True, fill=BOTH)
preset_button = Button(framePresetsButtons1, text="Speed Worker", command=preset_workspeed)
preset_button.config(font=("Arial", 12))
preset_button.pack(side=LEFT, expand=True, fill=BOTH)
preset_button = Button(framePresetsButtons1, text="Speed Runner", command=preset_movement)
preset_button.config(font=("Arial", 12))
preset_button.pack(side=LEFT, expand=True, fill=BOTH)
preset_button = Button(framePresetsButtons1, text="Tank", command=preset_tank)
preset_button.config(font=("Arial", 12))
preset_button.pack(side=LEFT, expand=True, fill=BOTH)

framePresetsButtons2 = Frame(framePresetsButtons)
framePresetsButtons2.pack(fill=BOTH, expand=True)
preset_title2 = Label(framePresetsButtons2, text='Damage:', anchor='e', bg="darkgrey", font=("Arial", 13), width=9).pack(side=LEFT, fill=X)
preset_button = Button(framePresetsButtons2, text="Max", command=preset_dmg_max)
preset_button.config(font=("Arial", 12))
preset_button.pack(side=LEFT, expand=True, fill=BOTH)
preset_button = Button(framePresetsButtons2, text="Balanced", command=preset_dmg_balanced)
preset_button.config(font=("Arial", 12))
preset_button.pack(side=LEFT, expand=True, fill=BOTH)
preset_button = Button(framePresetsButtons2, text="Mount", command=preset_dmg_mount)
preset_button.config(font=("Arial", 12))
preset_button.pack(side=LEFT, expand=True, fill=BOTH)
preset_button = Button(framePresetsButtons2, text="Element", command=preset_dmg_element)
preset_button.config(font=("Arial", 12))
preset_button.pack(side=LEFT, expand=True, fill=BOTH)

# PRESETS OPTIONS
framePresetsExtras = Frame(framePresets, relief="groove", borderwidth=4)
framePresetsExtras.pack(fill=BOTH, expand=True)

framePresetsLevel = Frame(framePresetsExtras)
framePresetsLevel.pack(fill=BOTH, expand=True)
presetTitleLevel = Label(framePresetsLevel, text='Set Level:', anchor='center', bg="lightgrey", font=("Arial", 13), width=20, height=1).pack(side=LEFT, expand=False, fill=Y)
checkboxLevelVar = IntVar()
checkboxLevel = Checkbutton(framePresetsLevel, text='Preset changes level', variable=checkboxLevelVar, onvalue='1', offvalue='0').pack(side=LEFT,expand=False, fill=BOTH)
textboxLevelVar = IntVar(value=1)
textboxLevel = Entry(framePresetsLevel, textvariable=textboxLevelVar, justify='center', width=10)
textboxLevel.config(font=("Arial", 10), width=10)
textboxLevel.pack(side=LEFT,expand=True, fill=Y)

framePresetsRank = Frame(framePresetsExtras)
framePresetsRank.pack(fill=BOTH, expand=True)
presetTitleRank = Label(framePresetsRank, text='Set Rank:', anchor='center', bg="lightgrey", font=("Arial", 13), width=20, height=1).pack(side=LEFT, expand=False, fill=Y)
checkboxRankVar = IntVar()
checkboxRank = Checkbutton(framePresetsRank, text='Preset changes rank', variable=checkboxRankVar, onvalue='1', offvalue='0').pack(side=LEFT,expand=False, fill=BOTH)
optionMenuRankVar = IntVar(value=1)
ranks = ('0', '1', '2', '3', '4')
optionMenuRank = OptionMenu(framePresetsRank, optionMenuRankVar, *ranks)
optionMenuRankVar.set(ranks[0])
optionMenuRank.config(font=("Arial", 10), width=5, justify='center')
optionMenuRank.pack(side=LEFT, expand=True, fill=Y)

framePresetsAttributes = Frame(framePresetsExtras)
framePresetsAttributes.pack(fill=BOTH, expand=False)
presetTitleAttributes = Label(framePresetsAttributes, text='Set Attributes:', anchor='center', bg="lightgrey", font=("Arial", 13), width=20, height=1).pack(side=LEFT, expand=False, fill=Y)
checkboxAttributesVar = IntVar()
checkboxAttributes = Checkbutton(framePresetsAttributes, text='Preset changes attributes', variable=checkboxAttributesVar, onvalue='1', offvalue='0').pack(side=LEFT,expand=False, fill=BOTH)
presetTitleAttributesTodo = Label(framePresetsAttributes, text='Not Yet', font=("Arial", 10), width=10, justify='center').pack(side=LEFT, expand=True, fill=Y)

# DEBUG
frameDebug = Frame(infoview, relief="flat")
frameDebug.pack()
frameDebug.pack_forget()
debugTitle = Label(frameDebug, text='Debug:', anchor='w', bg="darkgrey", font=("Arial", ftsize), width=6, height=1)
debugTitle.pack(fill=BOTH)
storageId = Label(frameDebug, text='StorageID: NULL', anchor='w', bg="darkgrey", font=("Arial", ftsize), width=6, height=1)
storageId.pack(fill=BOTH)
storageSlot = Label(frameDebug, text='StorageSlot: NULL', anchor='w', bg="darkgrey", font=("Arial", ftsize), width=6, height=1)
storageSlot.pack(fill=BOTH)
button = Button(frameDebug, text="Get Info", command=getSelectedPalInfo)
button.config(font=("Arial", 12))
button.pack(side=LEFT, expand=True, fill=BOTH)
button = Button(frameDebug, text="Copy Pal Data", command=getSelectedPalData)
button.config(font=("Arial", 12))
button.pack(side=LEFT, expand=True, fill=BOTH)
button = Button(frameDebug, text="Generate & Copy GUID", command=createGUIDtoClipboard)
button.config(font=("Arial", 12))
button.pack(side=LEFT, expand=True, fill=BOTH)
button = Button(frameDebug, text="Add Pal", command=spawnpal)
button.config(font=("Arial", 12))
button.pack(side=LEFT, expand=True, fill=BOTH)
button = Button(frameDebug, text="Dump Pal", command=dumppals)
button.config(font=("Arial", 12))
button.pack(side=LEFT, expand=True, fill=BOTH)
# FOOTER
frameFooter = Frame(infoview, relief="flat")
frameFooter.pack(fill=BOTH, expand=False)
skilllabel = Label(frameFooter, text="Hover a skill to see it's description")
skilllabel.pack()



# center & window size
def updateWindowSize(doCenter=""):
    root.update()
    window_height = root.winfo_reqheight()
    window_width = root.winfo_reqwidth()
    root.minsize(window_width, window_height) # minwidth for better view
    if doCenter:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2) - (window_height/2))
        root.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
    else:
        root.geometry("{}x{}".format(window_width, window_height))


# root.resizable(width=False, height=True)
root.geometry("") # auto window size
updateWindowSize("true")
root.mainloop()
