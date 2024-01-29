import os, webbrowser, json, time, uuid

import SaveConverter

from PalInfo import *

from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox
from PIL import ImageTk, Image

global palbox
palbox = []
global unknown
unknown = []
global data
global debug
debug = "false"
global editindex
editindex = -1
translations=[]
lang = "English"
SkillTransDesc = {}
global version
version = "0.4.6"

def toggleDebug():
    global debug
    if debug == "false":
        debug = "true"
        frameDebug.pack(fill=BOTH, expand=False)
    else:
        debug = "false"
        frameDebug.pack_forget()


def isPalSelected():
    global palbox
    if len(palbox) == 0:
        return False
    if len(listdisplay.curselection()) == 0:
        return False
    return True

def getSelectedPalInfo():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i]
    print(f"Get Info: {pal.GetNickname()}")     
    print(f"  - Level: {pal.GetLevel() if pal.GetLevel() > 0 else '?'}")    
    print(f"  - Rank: {pal.GetRank()}")    
    print(f"  - Skill 1:  {skills[0].get()}")
    print(f"  - Skill 2:  {skills[1].get()}")
    print(f"  - Skill 3:  {skills[2].get()}")
    print(f"  - Skill 4:  {skills[3].get()}")
    print(f"  - Melee IV:  {pal.GetAttackMelee()}")
    print(f"  - Range IV:  {pal.GetAttackRanged()}")

def getSelectedPalData():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i]
    print(f"Get Data: {pal.GetNickname()}")    
    print(f"{pal._obj}")  

def setpreset(preset):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i] # seems global palbox is not necessary

    match preset:
        case "worker":
            skills[0].set("Artisan")
            skills[1].set("Serious")
            skills[2].set("Lucky")
            skills[3].set("Work Slave")
        case "runner":
            skills[0].set("Swift")
            skills[1].set("Legend")
            skills[2].set("Runner")
            skills[3].set("Nimble")
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
        case "dmg_dragon":
            skills[0].set("Musclehead")
            skills[1].set("Legend")
            skills[2].set("Ferocious")
            skills[3].set("Divine Dragon")
        case "tank":
            skills[0].set("Burly Body")
            skills[1].set("Legend")
            skills[2].set("Masochist")
            skills[3].set("Hard Skin")
        case _:
            print(f"Preset {preset} not found - nothing changed")
            return

    # exp (if level selected)
    if checkboxLevelVar.get() == 1:
        pal.SetLevel(textboxLevelVar.get())
    # rank (if rank selected)
    if checkboxRankVar.get() == 1:
        changerank(optionMenuRankVar.get())
    # attributes (if attributes selected)
    # TODO: change attributes

    refresh(i)

def makeworker():
    setpreset("worker")
def makerunner():
    setpreset("runner")
def makedmgmax():
    setpreset("dmg_max")
def makedmgbalanced():
    setpreset("dmg_balanced")
def makedmgdragon():
    setpreset("dmg_dragon")
def maketank():
    setpreset("tank")

def changerank(configvalue):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i]
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
    pal = palbox[i]
    changerank(ranksvar.get())

def changeskill(num):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i]

    if not TryGetSkillsvar(num) in ["Unknown", "UNKNOWN"]:
        if TryGetSkillsvar(num) in ["None", "NONE"]:
            pal.RemoveSkill(num)
        else:
            pal.SetSkill(num, TryGetSkillsvar(num))

    refresh(i)

def onselect(evt):
    global palbox
    global editindex
    w = evt.widget
    if not isPalSelected():
        return

    if editindex > -1:
        updatestats(editindex)
        
    index = int(w.curselection()[0])
    editindex = index

    pal = palbox[index]
    #palname.config(text=pal.GetName())
    speciesvar.set(TryGetTranslations(pal.GetName()))

    g = pal.GetGender()
    palgender.config(text=TryGetTranslations(g), fg=PalGender.MALE.value if g == "Male ♂" else PalGender.FEMALE.value)

    title.config(text=f"{pal.GetNickname().replace(pal.GetName(), TryGetTranslations(pal.GetName()))}")
    level.config(text=f"Lv. {pal.GetLevel() if pal.GetLevel() > 0 else '?'}")
    portrait.config(image=pal.GetImage())

    ptype.config(text=TryGetTranslations(pal.GetPrimary().GetName()), bg=pal.GetPrimary().GetColour())
    stype.config(text=TryGetTranslations(pal.GetSecondary().GetName()), bg=pal.GetSecondary().GetColour())

    # ⚔🏹
    meleevar.set(pal.GetAttackMelee())
    shotvar.set(pal.GetAttackRanged())
    defvar.set(pal.GetDefence())
    wspvar.set(pal.GetWorkSpeed())

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
        if not s[i] in [s.name for s in PalSkills]:
            skills[i].set(TryGetTranslations("Unknown"))
        else:
            skills[i].set(TryGetTranslations(PalSkills[s[i]].value))
    

def changetext(num):
    if num == -1:
        skilllabel.config(text=TryGetTranslations("Hover a skill to see it's description"))
        return
    
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i] # seems global palbox is not necessary

    global unknown
    if type(num) == str:
        skilllabel.config(text=pal.GetOwner())
        return

    UnknowDes = "Unknown_Des"
    if(TryGetTranslations("Unknown_Des") == "Unknown_Des"):
        UnknowDes = SkillDesc['Unknown']

    if TryGetSkillsvar(num) == "Unknown":
        skilllabel.config(text=f"{pal.GetSkills()[num]}{UnknowDes}")
        return
    
    if(TryGetTranslations(TryGetSkillsvar(num) + "_Des") == TryGetSkillsvar(num) + "_Des"):
        skilllabel.config(text=SkillDesc[TryGetSkillsvar(num)])
    else:
        skilllabel.config(text=TryGetTranslations(TryGetSkillsvar(num) + "_Des"))
    
def loadfile():
    global palbox
    palbox = []
    skilllabel.config(text="Loading save, please be patient...")

    file = askopenfilename(filetype=[("All files", "*.sav *.sav.json *.pson"),("Palworld Saves", "*.sav *.sav.json"),("Palworld Box", "*.pson")])
    print(f"Opening file {file}")

    if not file.endswith(".pson") and not file.endswith("Level.sav.json"):
        if file.endswith("Level.sav"):
            answer = messagebox.askquestion("Incorrect file", "This save hasn't been decompiled. Would you like to decompile it now?")
            if answer == "yes":
                skilllabel.config(text="Decompiling save, please be patient...")
                doconvertjson(file)
        else:
            messagebox.showerror("Incorrect file", "This is not the right file. Please select the Level.sav file.")
        changetext(-1)
        return
    load(file)

def sortPals(e):
    return e.GetName()

def load(file):
    global data
    global palbox
    palbox = []

    f = open(file, "r", encoding="utf8")
    data = json.loads(f.read())
    f.close()

    if file.endswith(".pson"):
        paldata = data
    else:
        paldata = data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']

        f = open("current.pson", "w", encoding="utf8")
        json.dump(paldata, f, indent=4)
        f.close()


    for i in paldata:
        try:
            p = PalEntity(i)
            palbox.append(p)

            n = p.GetFullName()

        except Exception as e:
            unknown.append(i)
            print(f"Error occured: {str(e)}")
            # print(f"Debug: Data {i}")

    updateDisplay()

    print(f"Unknown list contains {len(unknown)} entries")
    #for i in unknown:
        #print (i)
    
    refresh()

    changetext(-1)

def updateDisplay():
    listdisplay.delete(0,END)
    palbox.sort(key=sortPals)

    for p in palbox:
        listdisplay.insert(END, p.GetFullName().replace(p.GetName(), TryGetTranslations(p.GetName())))

        if p.isBoss:
            listdisplay.itemconfig(END, {'fg': 'red'})
        elif p.isLucky:
            listdisplay.itemconfig(END, {'fg': 'blue'})
    
def savefile():
    global palbox
    global data
    skilllabel.config(text="Saving, please be patient... (it can take up to 5 minutes in large files)")

    if isPalSelected():
        i = int(listdisplay.curselection()[0])
        refresh(i)
    
    file = asksaveasfilename(filetype=[("All files", "*.sav.json *.pson"),("Palworld Saves", "*.sav.json"),("Palworld Box", "*.pson")])
    print(f"Opening file {file}")

    if not file.endswith(".pson") and not file.endswith("Level.sav.json"):
        messagebox.showerror("Incorrect file", "You can only save to an existing Level.sav.json or a new .pson file")

    if file.endswith(".pson"):
        savepson(file)
    else:
        savejson(file)

    changetext(-1)

def savepson(filename):
    f = open(filename, "w", encoding="utf8")
    if 'properties' in data:
        json.dump(data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'], f, indent=4)
    else:
        json.dump(data, f, indent=4)
    f.close()

def savejson(filename):
    f = open(filename, "r", encoding="utf8")
    svdata = json.loads(f.read())
    f.close()

    if 'properties' in data:
        svdata['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
    else:
        svdata['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = data

    f = open(filename, "w", encoding="utf8")
    json.dump(svdata, f)
    f.close()

    changetext(-1)

def generateguid():
    print(uuid.uuid4())

def updatestats(e):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[e]

    pal.SetAttackMelee(meleevar.get())
    pal.SetAttackRanged(shotvar.get())
    pal.SetDefence(defvar.get())
    pal.SetWorkSpeed(wspvar.get())

def takelevel():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i]

    if pal.GetLevel() == 1:
        return
    pal.SetLevel(pal.GetLevel()-1)
    refresh(i)

def givelevel():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i]

    if pal.GetLevel() == 50:
        return
    pal.SetLevel(pal.GetLevel()+1)
    refresh(i)

def changespeciestype(evt):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i]
    
    pal.SetType(TryGetSpeciesvar())
    updateDisplay()
    refresh(palbox.index(pal))

def refresh(num=0):
    listdisplay.select_set(num)
    listdisplay.event_generate("<<ListboxSelect>>")

def converttojson():

    skilllabel.config(text="Converting... this may take a while.")
    
    file = askopenfilename(filetype=[("All files", "*.sav")])
    print(f"Opening file {file}")

    doconvertjson(file)

def doconvertjson(file, compress=False):
    SaveConverter.convert_sav_to_json(file, file.replace(".sav", ".sav.json"), compress)

    load(file.replace(".sav", ".sav.json"))

    changetext(-1)

def converttosave():
    skilllabel.config(text="Converting... this may take a while.")
    
    file = askopenfilename(filetype=[("All files", "*.sav.json")])
    print(f"Opening file {file}")

    doconvertsave(file)


def doconvertsave(file):
    SaveConverter.convert_json_to_sav(file, file.replace(".sav.json", ".sav"))

    changetext(-1)

def swapgender():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i]

    pal.SwapGender()
    refresh(i)

def LoadTranslationsFile():
    global translations
    if(os.path.exists('translations.json')):
        with open('translations.json', 'r',encoding='utf-8') as f:
            translations = json.load(f)
        return True
    else:
        return False

def SaveTranslationsFile():
    global translations
    with open('translations.json', 'w+', encoding='utf-8') as f:
        json.dump(translations, f,indent=1,ensure_ascii=False)

def TryGetTranslations(tag):
    global translations
    global lang
    if(len(translations) == 0):
        if(not(LoadTranslationsFile())):
            return tag
    try:
        return translations[lang][tag]
    except:
        return tag
    
def TryGetSpeciesvar():
    if(len(SkillTransDesc) > 0):
        try:
            return SkillTransDesc[speciesvar.get()]
        except:
            return speciesvar.get()
    return speciesvar.get()

def TryGetSkillsvar(i):
    if(len(SkillTransDesc) > 0):
        try:
            return SkillTransDesc[skills[i].get()]
        except:
            return skills[i].get()
    return skills[i].get()

def translateedit(t):
    global lang
    if(lang == t):
        return
    lang = t
    tools.entryconfig(1, label=TryGetTranslations("File"))
    tools.entryconfig(2, label=TryGetTranslations("Tools"))
    tools.entryconfig(3, label=TryGetTranslations("Converter"))
    tools.entryconfig(4, label=TryGetTranslations("Translate"))
    filemenu.entryconfig(0, label=TryGetTranslations("Load Save"))
    filemenu.entryconfig(1, label=TryGetTranslations("Save Changes"))
    toolmenu.entryconfig(0, label=TryGetTranslations("Generate GUID"))
    toolmenu.entryconfig(1, label=TryGetTranslations("Debug"))
    convmenu.entryconfig(0, label=TryGetTranslations("Convert Save to Json"))
    convmenu.entryconfig(1, label=TryGetTranslations("Convert Json to Save"))
    name.config(text = TryGetTranslations("Species"))
    gender.config(text = TryGetTranslations("Gender"))
    attack.config(text = TryGetTranslations("Attack"))
    defence.config(text = TryGetTranslations("Defence"))
    workspeed.config(text = TryGetTranslations("Workspeed"))
    rankspeed.config(text = TryGetTranslations("Rank"))


    framePresetsButtons1.winfo_children()[0]['text']= TryGetTranslations("Worker")
    framePresetsButtons1.winfo_children()[1]['text']= TryGetTranslations("Preset_Runner")
    framePresetsButtons1.winfo_children()[2]['text']= TryGetTranslations("Tank")

    framePresetsButtons2.winfo_children()[0]['text']= TryGetTranslations("DMG: Max")
    framePresetsButtons2.winfo_children()[1]['text']= TryGetTranslations("DMG: Balanced")
    framePresetsButtons2.winfo_children()[2]['text']= TryGetTranslations("DMG: Dragon")

    framePresetsTitle.winfo_children()[0].config(text = TryGetTranslations("Presets:"))

    framePresetsLevel.winfo_children()[0].config(text = TryGetTranslations("Set Level:"))
    framePresetsLevel.winfo_children()[1].config(text = TryGetTranslations("Preset changes level"))

    framePresetsRank.winfo_children()[0].config(text = TryGetTranslations("Set Rank:"))
    framePresetsRank.winfo_children()[1].config(text = TryGetTranslations("Preset changes rank"))

    framePresetsAttributes.winfo_children()[0].config(text = TryGetTranslations("Set Attributes:"))
    framePresetsAttributes.winfo_children()[1].config(text = TryGetTranslations("Preset changes attributes"))

    global SkillTransDesc
    global species
    global palname
    global editview


    species = []
    for e in PalType:
        species.append(TryGetTranslations(e.value.GetName()))
        SkillTransDesc[TryGetTranslations(e.value.GetName())] = e.value.GetName()
    species.sort()

    palname.destroy()
    palname = OptionMenu(editview, speciesvar, *species, command=changespeciestype)
    palname.config(font=("Arial", ftsize), padx=0, pady=0, borderwidth=1, width=5, direction='right')
    palname.pack(before=editview.pack_slaves()[0],expand=True, fill=X)

    global skilldrops
    global op
    global topview
    global skills
    global botview
    for e in skilldrops:
        e.destroy()
    op = []
    for e in PalSkills:
        op.append(TryGetTranslations(e.value))
        SkillTransDesc[TryGetTranslations(e.value)] = e.value
    op.sort()
    op.pop(0)

    skills[0].set(TryGetTranslations(TryGetSkillsvar(0)))
    skills[1].set(TryGetTranslations(TryGetSkillsvar(1)))
    skills[2].set(TryGetTranslations(TryGetSkillsvar(2)))
    skills[3].set(TryGetTranslations(TryGetSkillsvar(3)))

    skilldrops = [
        OptionMenu(topview, skills[0], *op),
        OptionMenu(topview, skills[1], *op),
        OptionMenu(botview, skills[2], *op),
        OptionMenu(botview, skills[3], *op)
        ]

    skilldrops[0].pack(side=LEFT, expand=True, fill=BOTH)
    skilldrops[0].config(font=("Arial", ftsize), width=6, direction="right")
    skilldrops[1].pack(side=RIGHT, expand=True, fill=BOTH)
    skilldrops[1].config(font=("Arial", ftsize), width=6, direction="right")
    skilldrops[2].pack(side=LEFT, expand=True, fill=BOTH)
    skilldrops[2].config(font=("Arial", ftsize), width=6, direction="right")
    skilldrops[3].pack(side=RIGHT, expand=True, fill=BOTH)
    skilldrops[3].config(font=("Arial", ftsize), width=6, direction="right")

    skilldrops[0].bind("<Enter>", lambda evt, num=0: changetext(num))
    skilldrops[1].bind("<Enter>", lambda evt, num=1: changetext(num))
    skilldrops[2].bind("<Enter>", lambda evt, num=2: changetext(num))
    skilldrops[3].bind("<Enter>", lambda evt, num=3: changetext(num))
    skilldrops[0].bind("<Leave>", lambda evt, num=-1: changetext(num))
    skilldrops[1].bind("<Leave>", lambda evt, num=-1: changetext(num))
    skilldrops[2].bind("<Leave>", lambda evt, num=-1: changetext(num))
    skilldrops[3].bind("<Leave>", lambda evt, num=-1: changetext(num))

    updateDisplay()
    

root = Tk()
purplepanda = ImageTk.PhotoImage(Image.open(f'resources/MossandaIcon.png').resize((240,240)))
root.iconphoto(True, purplepanda)
root.title(f"PalEdit v{version}")
root.geometry("") # auto window size
root.minsize("800", "500") # minwidth for better view
#root.resizable(width=False, height=False)

tools = Menu(root)
root.config(menu=tools)

filemenu = Menu(tools, tearoff=0)
filemenu.add_command(label="Load Save", command=loadfile)
filemenu.add_command(label="Save Changes", command=savefile)

tools.add_cascade(label="File", menu=filemenu, underline=0)

toolmenu = Menu(tools, tearoff=0)
toolmenu.add_command(label="Generate GUID", command=generateguid)
toolmenu.add_command(label="Debug", command=toggleDebug)

tools.add_cascade(label="Tools", menu=toolmenu, underline=0)

convmenu = Menu(tools, tearoff=0)
convmenu.add_command(label="Convert Save to Json", command=converttojson)
convmenu.add_command(label="Convert Json to Save", command=converttosave)

tools.add_cascade(label="Converter", menu=convmenu, underline=0)

if(LoadTranslationsFile()):
    translatemenu = Menu(tools, tearoff=0)
    for language in translations:
        translatemenu.add_command(label=language, command=(lambda lang=language: translateedit(lang)))
    tools.add_cascade(label="Translate", menu=translatemenu, underline=0)


scrollbar = Scrollbar(root)
scrollbar.pack(side=LEFT, fill=Y)
listdisplay = Listbox(root, width=30, yscrollcommand=scrollbar.set, exportselection=0)
listdisplay.pack(side=LEFT, fill=BOTH)
listdisplay.bind("<<ListboxSelect>>", onselect)
scrollbar.config(command=listdisplay.yview)

infoview = Frame(root, relief="groove", borderwidth=2, width=480, height=480)
infoview.pack(side=RIGHT, fill=BOTH, expand=True)

dataview = Frame(infoview)
dataview.pack(side=TOP, fill=BOTH)

resourceview = Frame(dataview)
resourceview.pack(side=LEFT, fill=BOTH, expand=True)

portrait = Label(resourceview, image=purplepanda, relief="sunken", borderwidth=2)
portrait.pack()

ftsize = 18

typeframe = Frame(resourceview)
typeframe.pack(expand=True, fill=X)
ptype = Label(typeframe, text="Electric", font=("Arial", ftsize), bg=Elements.ELECTRICITY.value.GetColour(), width=6)
ptype.pack(side=LEFT, expand=True, fill=X)
stype = Label(typeframe, text="Dark", font=("Arial", ftsize), bg=Elements.DARK.value.GetColour(), width=6)
stype.pack(side=RIGHT, expand=True, fill=X)

deckview = Frame(dataview, width=320, relief="sunken", borderwidth=2, pady=0)
deckview.pack(side=RIGHT, fill=BOTH, expand=True)

title = Label(deckview, text=f"PalEdit", bg="darkgrey", font=("Arial", 24), width=17)
title.pack(expand=True, fill=X)

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
gender = Label(labelview, text="Gender", font=("Arial", ftsize), bg="lightgrey", width=6)
gender.pack(expand=True, fill=X)
attack = Label(labelview, text="Attack", font=("Arial", ftsize), bg="lightgrey", width=6)
attack.pack(expand=True, fill=X)
defence = Label(labelview, text="Defence", font=("Arial", ftsize), bg="lightgrey", width=6)
defence.pack(expand=True, fill=X)
workspeed = Label(labelview, text="Workspeed", font=("Arial", ftsize), bg="lightgrey", width=10)
workspeed.pack(expand=True, fill=X)
rankspeed = Label(labelview, text="Rank", font=("Arial", ftsize), bg="lightgrey")
rankspeed.pack(expand=True, fill=X)

editview = Frame(deckview)
editview.pack(side=RIGHT, expand=True, fill=BOTH)

species = [e.value.GetName() for e in PalType]
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
for i in range(0, 4):
    skills[i].set("Unknown")
    skills[i].trace("w", lambda *args, num=i: changeskill(num))
skills[0].set("Legend")
skills[1].set("Workaholic")
skills[2].set("Ferocious")
skills[3].set("Lucky")

op = [e.value for e in PalSkills]
op.pop(0)
op.pop(1)
op.sort()
op.insert(0, "None")
skilldrops = [
    OptionMenu(topview, skills[0], *op),
    OptionMenu(topview, skills[1], *op),
    OptionMenu(botview, skills[2], *op),
    OptionMenu(botview, skills[3], *op)
    ]

skilldrops[0].pack(side=LEFT, expand=True, fill=BOTH)
skilldrops[0].config(font=("Arial", ftsize), width=6, direction="right")
skilldrops[1].pack(side=RIGHT, expand=True, fill=BOTH)
skilldrops[1].config(font=("Arial", ftsize), width=6, direction="right")
skilldrops[2].pack(side=LEFT, expand=True, fill=BOTH)
skilldrops[2].config(font=("Arial", ftsize), width=6, direction="right")
skilldrops[3].pack(side=RIGHT, expand=True, fill=BOTH)
skilldrops[3].config(font=("Arial", ftsize), width=6, direction="right")

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
makeworkerBtn = Button(framePresetsButtons1, text="Worker", command=makeworker)
makeworkerBtn.config(font=("Arial", 12))
makeworkerBtn.pack(side=LEFT, expand=True, fill=BOTH)
makeworkerBtn = Button(framePresetsButtons1, text="Runner", command=makerunner)
makeworkerBtn.config(font=("Arial", 12))
makeworkerBtn.pack(side=LEFT, expand=True, fill=BOTH)
makeworkerBtn = Button(framePresetsButtons1, text="Tank", command=maketank)
makeworkerBtn.config(font=("Arial", 12))
makeworkerBtn.pack(side=LEFT, expand=True, fill=BOTH)

framePresetsButtons2 = Frame(framePresetsButtons)
framePresetsButtons2.pack(fill=BOTH, expand=True)
makeworkerBtn = Button(framePresetsButtons2, text="DMG: Max", command=makedmgmax)
makeworkerBtn.config(font=("Arial", 12))
makeworkerBtn.pack(side=LEFT, expand=True, fill=BOTH)
makeworkerBtn = Button(framePresetsButtons2, text="DMG: Balanced", command=makedmgbalanced)
makeworkerBtn.config(font=("Arial", 12))
makeworkerBtn.pack(side=LEFT, expand=True, fill=BOTH)
makeworkerBtn = Button(framePresetsButtons2, text="DMG: Dragon", command=makedmgdragon)
makeworkerBtn.config(font=("Arial", 12))
makeworkerBtn.pack(side=LEFT, expand=True, fill=BOTH)

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
presetTitle = Label(frameDebug, text='Debug:', anchor='w', bg="darkgrey", font=("Arial", ftsize), width=6, height=1).pack(fill=BOTH)
button = Button(frameDebug, text="Get Info", command=getSelectedPalInfo)
button.config(font=("Arial", 12))
button.pack(side=LEFT, expand=True, fill=BOTH)
button = Button(frameDebug, text="Get Data", command=getSelectedPalData)
button.config(font=("Arial", 12))
button.pack(side=LEFT, expand=True, fill=BOTH)

# FOOTER
frameFooter = Frame(infoview, relief="flat")
frameFooter.pack(fill=BOTH, expand=False)
skilllabel = Label(frameFooter, text="Hover a skill to see it's description")
skilllabel.pack()


root.mainloop()
