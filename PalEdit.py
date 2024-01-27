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

def isPalSelected():
    global palbox
    if len(palbox) == 0:
        return
    if len(listdisplay.curselection()) == 0:
        return
    return 1

def getSelectedPalInfo():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i] # seems global palbox is not necessary

    # print(f"Selected Pal: {pal.GetName() if pal.nickname == "" else pal.nickname}")    
    print(f"Get Info:")    
    print(f"  - Pal: {palname['text']}")    
    print(f"  - Pal: {pal.GetName() if pal._nickname == "" else pal._nickname}")    
    print(f"  - Level: {pal.GetLevel() if pal.GetLevel() > 0 else '?'}")    
    print(f"  - Skill 1:  {skills[0].get()}")
    print(f"  - Skill 2:  {skills[1].get()}")
    print(f"  - Skill 3:  {skills[2].get()}")
    print(f"  - Skill 4:  {skills[3].get()}")

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
    pal = palbox[i] # seems global palbox is not necessary

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
    match ranksvar.get():
        case 4:
            changerank(5)
        case 3:
            changerank(4)
        case 2:
            changerank(3)
        case 1:
            changerank(2)
        case _:
            changerank(1)

def changeskill(num):
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i] # seems global palbox is not necessary

    if not skills[num].get() in ["Unknown", "UNKNOWN"]:
        if skills[num].get() in ["None", "NONE"]:
            pal.RemoveSkill(num)
        else:
            pal.SetSkill(num, skills[num].get())

    refresh(i)

def onselect(evt):
    global palbox
    w = evt.widget
    if (len(w.curselection())== 0):
        return
    
    index = int(w.curselection()[0])

    pal = palbox[index]
    palname.config(text=pal.GetName() if pal._nickname == "" else pal._nickname)

    g = pal.GetGender()
    palgender.config(text=g, fg=PalGender.MALE.value if g == "Male ♂" else PalGender.FEMALE.value)

    title.config(text=f"Data - Lv. {pal.GetLevel() if pal.GetLevel() > 0 else '?'}")
    portrait.config(image=pal.GetImage())

    ptype.config(text=pal.GetPrimary().GetName(), bg=pal.GetPrimary().GetColour())
    stype.config(text=pal.GetSecondary().GetName(), bg=pal.GetSecondary().GetColour())

    palatk.config(text=f"{pal.GetAttackMelee()}⚔/{pal.GetAttackRanged()}🏹")
    paldef.config(text=pal.GetDefence())
    palwsp.config(text=pal.GetWorkSpeed())

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
            skills[i].set("Unknown")
        else:
            skills[i].set(PalSkills[s[i]].value)
    

def changetext(num):
    if num == -1:
        skilllabel.config(text="Hover a skill to see it's description")
        return
    
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i] # seems global palbox is not necessary

    global unknown
    if type(num) == str:
        skilllabel.config(text=pal.GetOwner())
        return


    if skills[num].get() == "Unknown":
        skilllabel.config(text=f"{pal.GetSkills()[num]}{SkillDesc['Unknown']}")
        return
    skilllabel.config(text=SkillDesc[skills[num].get()])

    
def loadfile():
    global palbox
    palbox = []
    listdisplay.delete(0,END)
    skilllabel.config(text="Loading save, please be patient...")

    file = askopenfilename(filetype=[("All files", "*.sav *.sav.json *.pson"),("Palworld Saves", "*.sav *.sav.json"),("Palworld Box", "*.pson")])
    print(f"Opening file {file}")

    if not file.endswith(".pson") and not file.endswith("Level.sav.json"):
        if file.endswith("Level.sav"):
            answer = messagebox.askquestion("Incorrect file", "This save hasn't been decompiled. Would you like to download the decompiler?\n\nCredit for Decompiler goes to 'cheahjs'\nhttps://github.com/cheahjs/palworld-save-tools")
            if answer == "yes":
                webbrowser.open_new("https://github.com/cheahjs/palworld-save-tools")
        else:
            messagebox.showerror("Incorrect file", "This is not the right file. Please select the Level.sav file.")
        changetext(-1)
        return
    load(file)

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
                   
            listdisplay.insert(END, n)

            if p.isBoss:
                listdisplay.itemconfig(END, {'fg': 'red'})
            elif p.isLucky:
                listdisplay.itemconfig(END, {'fg': 'blue'})


        except Exception as e:
            unknown.append(i)
            print(f"Error occured: {str(e)}")        
    print(f"Unknown list contains {len(unknown)} entries")
    #for i in unknown:
        #print (i)
    
    refresh()

    changetext(-1)

def savefile():
    global palbox
    global data
    skilllabel.config(text="Saving, please be patient... (it can take up to 5 minutes in large files)")
    
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

def changeivs():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i] # seems global palbox is not necessary
    
    def change():
        global palbox
        if len(palbox) == 0:
            return
        
        pal.SetAttackMelee(mval.get())
        pal.SetAttackRanged(rval.get())

        refresh(i)

        win.destroy()

    win = Toplevel(root)

    mval = IntVar()
    rval = IntVar()
    mval.set(pal.GetAttackMelee())
    rval.set(pal.GetAttackRanged())

    fr = Frame(win)
    fr.pack()
    melee = Entry(fr, textvariable=mval)
    melee.pack(side=LEFT)
    ranged = Entry(fr, textvariable=rval)
    ranged.pack(side=RIGHT)
    update = Button(win, text="OK", command=change)
    update.pack()

    win.mainloop()


def changelevel():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i] # seems global palbox is not necessary
    
    def change():
        global palbox
        if len(palbox) == 0:
            return

        pal.SetLevel(value.get())

        refresh(i)

        win.destroy()

    win = Toplevel(root)

    value = IntVar()
    value.set(pal.GetLevel())
    
    entry = Entry(win, textvariable=value)
    entry.pack()
    update = Button(win, text="OK", command=change)
    update.pack()

    win.mainloop()

def changespecies():
    if not isPalSelected():
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i] # seems global palbox is not necessary
    
    def change():
        global palbox
        if len(palbox) == 0:
            return

        pal.SetType(value.get())

        refresh(i)
        n = pal.GetFullName()
        listdisplay.delete(i)
        listdisplay.insert(i, n)

        if pal.isBoss:
            listdisplay.itemconfig(i, {'fg': 'red'})
        elif pal.isLucky:
            listdisplay.itemconfig(i, {'fg': 'blue'})

        win.destroy()

    win = Toplevel(root)

    value = StringVar()
    value.set(pal.GetName())

    op = [e.value.GetName() for e in PalType]
    ops = OptionMenu(win, value, *op)
    ops.pack()
    
    update = Button(win, text="OK", command=change)
    update.pack()

    win.mainloop()

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


root = Tk()
root.iconphoto(True, PalType.GrassPanda.value.GetImage())
root.title("PalEdit v0.31")
root.geometry("") # auto window size
root.minsize("800", "500") # minwidth for better view
root.resizable(width=False, height=False)

tools = Menu(root)
root.config(menu=tools)

filemenu = Menu(tools, tearoff=0)
filemenu.add_command(label="Load Save", command=loadfile)
filemenu.add_command(label="Save Changes", command=savefile)

tools.add_cascade(label="File", menu=filemenu, underline=0)

toolmenu = Menu(tools, tearoff=0)
toolmenu.add_command(label="Generate GUID", command=generateguid)
toolmenu.add_command(label="Change IVs", command=changeivs)
toolmenu.add_command(label="Change Level", command=changelevel)
toolmenu.add_command(label="Change Species", command=changespecies)

tools.add_cascade(label="Tools", menu=toolmenu, underline=0)

convmenu = Menu(tools, tearoff=0)
convmenu.add_command(label="Convert Save to Json", command=converttojson)
convmenu.add_command(label="Convert Json to Save", command=converttosave)

tools.add_cascade(label="Converter", menu=convmenu, underline=0)


scrollbar = Scrollbar(root)
scrollbar.pack(side=LEFT, fill=Y)
listdisplay = Listbox(root, width=30, yscrollcommand=scrollbar.set, exportselection=0)
listdisplay.pack(side=LEFT, fill=BOTH)
listdisplay.bind("<<ListboxSelect>>", onselect)
scrollbar.config(command=listdisplay.yview)

infoview = Frame(root, relief="groove", borderwidth=2, width=480, height=480)
infoview.pack(side=RIGHT, fill=BOTH, expand=True)

dataview = Frame(infoview, relief="raised")
dataview.pack(side=TOP, fill=BOTH)

portrait = Label(dataview, image=PalType.GrassPanda.value.GetImage(), relief="sunken")
portrait.pack(side=LEFT)

deckview = Frame(dataview, width=320, relief="sunken", borderwidth=2)
deckview.pack(side=RIGHT, fill=BOTH, expand=True)

title = Label(deckview, text="Data - Lv. 0", bg="darkgrey", font=("Arial", 24))
title.bind("<Enter>", lambda evt, num="owner": changetext(num))
title.bind("<Leave>", lambda evt, num=-1: changetext(num))
title.pack(fill=X)

ftsize = 18

typeview = Frame(deckview)
typeview.pack(fill=X)
ptype = Label(typeview, text="Grass", font=("Arial", ftsize), bg=Elements.LEAF.value.GetColour(), width=6)
ptype.pack(side=LEFT, expand=True, fill=X)
stype = Label(typeview, text="None", font=("Arial", ftsize), bg=Elements.NONE.value.GetColour(), width=6)
stype.pack(side=RIGHT, expand=True, fill=X)

nameview = Frame(deckview)
nameview.pack(fill=X)
name = Label(nameview, text="Name", font=("Arial", ftsize), bg="lightgrey", width=6)
name.pack(side=LEFT, expand=True, fill=X)
palname = Label(nameview, text="Mossanda", font=("Arial", ftsize), width=6)
palname.pack(side=RIGHT, expand=True, fill=X)

genderview = Frame(deckview)
genderview.pack(fill=X)
gender = Label(genderview, text="Gender", font=("Arial", ftsize), bg="lightgrey", width=6)
gender.pack(side=LEFT, expand=True, fill=X)
palgender = Label(genderview, text="Male ♂", font=("Arial", ftsize), fg=PalGender.MALE.value, width=6)
palgender.pack(side=RIGHT, expand=True, fill=X)

attackview = Frame(deckview)
attackview.pack(fill=X)
attack = Label(attackview, text="Attack", font=("Arial", ftsize), bg="lightgrey", width=6)
attack.pack(side=LEFT, expand=True, fill=X)
palatk = Label(attackview, text="0", font=("Arial", ftsize), width=6)
palatk.pack(side=RIGHT, expand=True, fill=X)

defenceview = Frame(deckview)
defenceview.pack(fill=X)
defence = Label(defenceview, text="Defence", font=("Arial", ftsize), bg="lightgrey", width=6)
defence.pack(side=LEFT, expand=True, fill=X)
paldef = Label(defenceview, text="0", font=("Arial", ftsize), width=6)
paldef.pack(side=RIGHT, expand=True, fill=X)

workview = Frame(deckview)
workview.pack(fill=X)
workspeed = Label(workview, text="Workspeed", font=("Arial", ftsize), bg="lightgrey", width=6)
workspeed.pack(side=LEFT, expand=True, fill=X)
palwsp = Label(workview, text="0", font=("Arial", ftsize), width=6)
palwsp.pack(side=RIGHT, expand=True, fill=X)

rankview = Frame(deckview)
rankview.pack(side=LEFT, expand=True, fill=X)
rankspeed = Label(rankview, text="Rank", font=("Arial", ftsize), bg="lightgrey", width=6)
rankspeed.pack(side=LEFT, expand=True, fill=X)
ranks = ('0', '1', '2', '3', '4')
ranksvar = IntVar()
# palwsp = Label(rankview, text="0", font=("Arial", ftsize), width=6)
# palwsp.pack(side=RIGHT, expand=True, fill=X)
palrank = OptionMenu(deckview, ranksvar, *ranks, command=changerankchoice)
palrank. config(font=("Arial", 11),  justify='center', width=6)
ranksvar.set(ranks[0])
palrank.pack(side=RIGHT, expand=True, fill=X)


# rank = Label(rankview, text="Rank", font=("Arial", ftsize), bg="lightgrey", width=6)
# rank.pack(side=LEFT, expand=True, fill=X)
# ranks = ('0', '1', '2', '3', '4')
# ranksvar = IntVar()
# palrank = OptionMenu(rankview, ranksvar, *ranks, command=changerank)
# ranksvar.trace("w", lambda *args: changerank(ranksvar))
# ranksvar.set(ranks[0])
# palrank.pack(side=RIGHT, expand=True, fill=X)

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

op = [e.value for e in PalSkills]
op.pop(0)
skilldrops = [
    OptionMenu(topview, skills[0], *op),
    OptionMenu(topview, skills[1], *op),
    OptionMenu(botview, skills[2], *op),
    OptionMenu(botview, skills[3], *op)
    ]

skilldrops[0].pack(side=LEFT, expand=True, fill=BOTH)
skilldrops[0].config(font=("Arial", ftsize), width=6)
skilldrops[1].pack(side=RIGHT, expand=True, fill=BOTH)
skilldrops[1].config(font=("Arial", ftsize), width=6)
skilldrops[2].pack(side=LEFT, expand=True, fill=BOTH)
skilldrops[2].config(font=("Arial", ftsize), width=6)
skilldrops[3].pack(side=RIGHT, expand=True, fill=BOTH)
skilldrops[3].config(font=("Arial", ftsize), width=6)

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
# debug
makeworkerBtn = Button(framePresetsButtons1, text="Get Info", command=getSelectedPalInfo)
makeworkerBtn.config(font=("Arial", 12))
makeworkerBtn.pack(side=LEFT, expand=True, fill=BOTH)
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
framePresetsAttributes.pack(fill=BOTH, expand=True)
presetTitleAttributes = Label(framePresetsAttributes, text='Set Attributes:', anchor='center', bg="lightgrey", font=("Arial", 13), width=20, height=1).pack(side=LEFT, expand=False, fill=Y)
checkboxAttributesVar = IntVar()
checkboxAttributes = Checkbutton(framePresetsAttributes, text='Preset changes attributes', variable=checkboxAttributesVar, onvalue='1', offvalue='0').pack(side=LEFT,expand=False, fill=BOTH)
presetTitleAttributesTodo = Label(framePresetsAttributes, text='Not Yet', font=("Arial", 10), width=10, justify='center').pack(side=LEFT, expand=True, fill=Y)

# FOOTER
frameFooter = Frame(infoview, relief="flat")
frameFooter.pack(fill=BOTH, expand=False)
skilllabel = Label(frameFooter, text="Hover a skill to see it's description")
skilllabel.pack()



root.mainloop()
