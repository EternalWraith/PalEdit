import os, webbrowser, json, time, uuid

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

def changeskill(num):
    global palbox
    if len(palbox) == 0:
        return

    if not skills[num].get() in ["Unknown", "UNKNOWN"]:
        pal = palbox[int(listdisplay.curselection()[0])]
        pal.SetSkill(num, skills[num].get())

def onselect(evt):
    global palbox
    w = evt.widget
    if (len(w.curselection())== 0):
        return
    
    index = int(w.curselection()[0])

    pal = palbox[index]
    palname.config(text=pal.GetName())

    g = pal.GetGender()
    palgender.config(text=g, fg=PalGender.MALE.value if g == "Male ♂" else PalGender.FEMALE.value)

    title.config(text=f"Data - Lv. {pal.GetLevel()}")
    portrait.config(image=pal.GetImage())

    ptype.config(text=pal.GetPrimary().GetName(), bg=pal.GetPrimary().GetColour())
    stype.config(text=pal.GetSecondary().GetName(), bg=pal.GetSecondary().GetColour())

    palatk.config(text=f"{pal.GetAttackMelee()}⚔/{pal.GetAttackRanged()}🏹")
    paldef.config(text=pal.GetDefence())
    palwsp.config(text=pal.GetWorkSpeed())

    s = pal.GetSkills()[:]
    while len(s) < 4:
        s.append("NONE")

    for i in range(0, 4):
        if not s[i] in [s.name for s in PalSkills]:
            skills[i].set("Unknown")
        else:
            skills[i].set(PalSkills[s[i]].value)
    

def changetext(num):
    global palbox
    global unknown
    if len(palbox) == 0:
        return

    pal = palbox[int(listdisplay.curselection()[0])]

    if type(num) == str:
        skilllabel.config(text=pal.GetOwner())
        return

    if num == -1:
        skilllabel.config(text="Hover a skill to see it's description")
        return
    if skills[num].get() == "Unknown":
        skilllabel.config(text=f"{pal.GetSkills()[num]}{SkillDesc['Unknown']}")
        return
    skilllabel.config(text=SkillDesc[skills[num].get()])

    
def loadfile():
    global palbox
    global data
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

    f = open(file, "r", encoding="utf8")
    data = json.loads(f.read())
    f.close()

    if file.endswith(".pson"):
        paldata = data
        print(paldata)
        print(len(paldata))
    else:
        paldata = data['root']['properties']['worldSaveData']['Struct']['value']['Struct']['CharacterSaveParameterMap']['Map']['value']

        f = open("current.pson", "w", encoding="utf8")
        json.dump(paldata, f, indent=4)
        f.close()

    for i in paldata:
        try:
            p = PalEntity(i)
            palbox.append(p)
            listdisplay.insert(END, p.GetObject().GetName())
        except Exception as e:
            unknown.append(i)
            print(f"Error occured: {e}")        
    print(f"Unknown list contains {len(unknown)} entries")
    #for i in unknown:
        #print (i)
    listdisplay.select_set(0)
    listdisplay.event_generate("<<ListboxSelect>>")

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
    if 'root' in data:
        json.dump(data['root']['properties']['worldSaveData']['Struct']['value']['Struct']['CharacterSaveParameterMap']['Map']['value'], f, indent=4)
    else:
        json.dump(data, f, indent=4)
    f.close()

def savejson(filename):
    f = open(filename, "r", encoding="utf8")
    svdata = json.loads(f.read())
    f.close()

    if 'root' in data:
        svdata['root']['properties']['worldSaveData']['Struct']['value']['Struct']['CharacterSaveParameterMap']['Map']['value'] = data['root']['properties']['worldSaveData']['Struct']['value']['Struct']['CharacterSaveParameterMap']['Map']['value']
    else:
        svdata['root']['properties']['worldSaveData']['Struct']['value']['Struct']['CharacterSaveParameterMap']['Map']['value'] = data

    f = open(filename, "w", encoding="utf8")
    json.dump(svdata, f)
    f.close()

    changetext(-1)

def generateguid():
    print(uuid.uuid4())

def changeivs():
    if len(listdisplay.curselection()) == 0:
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i]
    
    def change():
        global palbox
        if len(palbox) == 0:
            return
        
        pal.SetAttackMelee(mval.get())
        pal.SetAttackRanged(rval.get())

        listdisplay.select_set(i)
        listdisplay.event_generate("<<ListboxSelect>>")

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
    if len(listdisplay.curselection()) == 0:
        return
    i = int(listdisplay.curselection()[0])
    pal = palbox[i]
    
    def change():
        global palbox
        if len(palbox) == 0:
            return

        pal.SetLevel(value.get())

        listdisplay.select_set(i)
        listdisplay.event_generate("<<ListboxSelect>>")

        win.destroy()

    win = Toplevel(root)

    value = IntVar()
    value.set(pal.GetLevel())
    
    entry = Entry(win, textvariable=value)
    entry.pack()
    update = Button(win, text="OK", command=change)
    update.pack()

    win.mainloop()

root = Tk()
root.iconphoto(True, PalType.GrassPanda.value.GetImage())
root.title("PalEdit v0.1")
root.geometry("640x400")
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

tools.add_cascade(label="Tools", menu=toolmenu, underline=0)


scrollbar = Scrollbar(root)
scrollbar.pack(side=LEFT, fill=Y)
listdisplay = Listbox(root, yscrollcommand=scrollbar.set)
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

skilllabel = Label(skillview, text="Hover a skill to see it's description")
skilllabel.pack()

skilldrops[0].bind("<Enter>", lambda evt, num=0: changetext(num))
skilldrops[1].bind("<Enter>", lambda evt, num=1: changetext(num))
skilldrops[2].bind("<Enter>", lambda evt, num=2: changetext(num))
skilldrops[3].bind("<Enter>", lambda evt, num=3: changetext(num))
skilldrops[0].bind("<Leave>", lambda evt, num=-1: changetext(num))
skilldrops[1].bind("<Leave>", lambda evt, num=-1: changetext(num))
skilldrops[2].bind("<Leave>", lambda evt, num=-1: changetext(num))
skilldrops[3].bind("<Leave>", lambda evt, num=-1: changetext(num))

root.mainloop()
