import os, webbrowser, json, time, uuid, math

# pyperclip
# docs: https://pypi.org/project/pyperclip/#description
# install: pip install pyperclip
import pyperclip

import SaveConverter
from lib.gvas import GvasFile
from lib.archive import FArchiveReader, FArchiveWriter
from lib.json_tools import CustomEncoder
from lib.palsav import compress_gvas_to_sav, decompress_sav_to_gvas
from lib.paltypes import PALWORLD_CUSTOM_PROPERTIES, PALWORLD_TYPE_HINTS
import tkinter as tk
import copy

from PalInfo import *

from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox
from PIL import ImageTk, Image

class PalEditConfig:
    version = "0.5.4"
    ftsize = 18
    font = "Arial"
    badskill = "#DE3C3A"
    okayskill = "#DFE8E7"
    goodskill = "#FEDE00"

class PalEdit():
    ranks = ('0', '1', '2', '3', '4')

    @staticmethod
    def hex_to_rgb(value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    @staticmethod
    def rgb_to_hex(rgb):
        return '%02x%02x%02x' % rgb

    @staticmethod
    def mean_color(color1, color2):
        rgb1 = PalEdit.hex_to_rgb(color1.replace("#", ""))
        rgb2 = PalEdit.hex_to_rgb(color2.replace("#", ""))

        avg = lambda x, y: round((x + y) / 2)

        new_rgb = ()

        for i in range(len(rgb1)):
            new_rgb += (avg(rgb1[i], rgb2[i]),)

        return "#" + PalEdit.rgb_to_hex(new_rgb)

    def toggleDebug(self):
        if self.debug == "false":
            self.debug = "true"
            self.frameDebug.pack(fill=tk.constants.BOTH, expand=False)
        else:
            self.debug = "false"
            self.frameDebug.pack_forget()
        self.updateWindowSize()

    def isPalSelected(self):
        if self.current.get() == "":
            return False
        if len(self.palbox[self.players[self.current.get()]]) == 0:
            return False
        if len(self.listdisplay.curselection()) == 0:
            return False
        return True

    def getSelectedPalInfo(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]
        print(f"Get Info: {pal.GetNickname()}")
        print(f"  - Level: {pal.GetLevel() if pal.GetLevel() > 0 else '?'}")
        print(f"  - Rank: {pal.GetRank()}")
        print(f"  - Skill 1:  {self.skills[0].get()}")
        print(f"  - Skill 2:  {self.skills[1].get()}")
        print(f"  - Skill 3:  {self.skills[2].get()}")
        print(f"  - Skill 4:  {self.skills[3].get()}")
        print(f"  - HP IV:  {pal.GetTalentHP()}")
        print(f"  - Melee IV:  {pal.GetAttackMelee()}")
        print(f"  - Range IV:  {pal.GetAttackRanged()}")

    def getSelectedPalData(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]
        # print(f"Get Data: {pal.GetNickname()}")    
        # print(f"{pal._obj}")  
        pyperclip.copy(f"{pal._obj}")
        webbrowser.open('https://jsonformatter.curiousconcept.com/#')

    def updateAttacks(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]
        self.attackops = [PalInfo.PalAttacks[e] for e in PalInfo.PalAttacks]

        for a in range(0, 3):
            if a > len(pal.GetEquippedMoves()) - 1:
                self.attacks[a].set("None")
            else:
                self.attacks[a].set(PalInfo.PalAttacks[pal.GetEquippedMoves()[a]])
        self.setAttackCols()

    def setAttackCols(self):
        for i in range(0, 3):
            if self.attacks[i].get() == "None":
                self.attackdrops[i].config(highlightbackground="lightgrey", bg="lightgrey",
                                           activebackground="lightgrey")
            else:
                v = self.attacks[i].get()
                basecol = PalInfo.PalElements[PalInfo.AttackTypes[v]]
                halfcol = PalEdit.mean_color(basecol, "ffffff")
                self.attackdrops[i].config(highlightbackground=basecol, bg=halfcol, activebackground=halfcol)

    def setpreset(self, preset):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        tid = []
        for v in range(0, 4):
            t = self.skills[v].trace_add("write", lambda *args, num=v: self.changeskill(num))
            tid.append(t)

        match preset:
            case "base":
                self.skills[0].set("Artisan")
                self.skills[1].set("Workaholic")
                self.skills[2].set("Lucky")
                self.skills[3].set("Diet Lover")
            case "workspeed":
                self.skills[0].set("Artisan")
                self.skills[1].set("Serious")
                self.skills[2].set("Lucky")
                self.skills[3].set("Work Slave")
            case "movement":
                self.skills[0].set("Swift")
                self.skills[1].set("Legend")
                self.skills[2].set("Runner")
                self.skills[3].set("Nimble")
            case "tank":
                self.skills[0].set("Burly Body")
                self.skills[1].set("Legend")
                self.skills[2].set("Masochist")
                self.skills[3].set("Hard Skin")
            case "dmg_max":
                self.skills[0].set("Musclehead")
                self.skills[1].set("Legend")
                self.skills[2].set("Ferocious")
                self.skills[3].set("Lucky")
            case "dmg_balanced":
                self.skills[0].set("Musclehead")
                self.skills[1].set("Legend")
                self.skills[2].set("Ferocious")
                self.skills[3].set("Burly Body")
            case "dmg_mount":
                self.skills[0].set("Musclehead")
                self.skills[1].set("Legend")
                self.skills[2].set("Ferocious")
                self.skills[3].set("Swift")
            case "dmg_element":
                primary = pal.GetPrimary().lower()
                secondary = pal.GetSecondary().lower()
                if primary == "none":
                    messagebox.showerror("Preset: Dmg: Element", "This pal has no elements! Preset skipped")
                    return
                self.skills[0].set("Musclehead")
                self.skills[1].set("Legend")
                self.skills[2].set("Ferocious")
                match primary:
                    case "neutral":
                        self.skills[3].set("Celestial Emperor")
                    case "dark":
                        self.skills[3].set("Lord of the Underworld")
                    case "dragon":
                        self.skills[3].set("Divine Dragon")
                    case "ice":
                        self.skills[3].set("Ice Emperor")
                    case "fire":
                        self.skills[3].set("Flame Emperor")
                    case "grass":
                        self.skills[3].set("Spirit Emperor")
                    case "ground":
                        self.skills[3].set("Earth Emperor")
                    case "electric":
                        self.skills[3].set("Lord of Lightning")
                    case "water":
                        self.skills[3].set("Lord of the Sea")
                    case _:
                        messagebox.showerror(f"Error: elemental was not found for preset: {primary}-{secondary}")

                # uncecessary msg
                # if not secondary == "none":
                #     messagebox.showerror(f"You pal has a second elemental - its probably better to use Dmg: Max preset")
            case _:
                print(f"Preset {preset} not found - nothing changed")
                return

        for v in range(0, 4):
            self.skills[v].trace_remove("write", tid[v])

        # exp (if level selected)
        if self.checkboxLevelVar.get() == 1:
            pal.SetLevel(self.textboxLevelVar.get())
        # rank (if rank selected)
        if self.checkboxRankVar.get() == 1:
            self.changerank(self.optionMenuRankVar.get())
        # attributes (if attributes selected)
        # TODO: change attributes

        self.refresh(i)

    def changerank(self, configvalue):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]
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
        self.refresh(i)

    def changerankchoice(self, choice):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]
        self.changerank(self.ranksvar.get())

    def changeskill(self, num):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        if not self.skills[num].get() in ["Unknown", "UNKNOWN"]:
            if self.skills[num].get() in ["None", "NONE"]:
                pal.RemoveSkill(num)
            else:

                pal.SetSkill(num, self.skills[num].get())

        self.refresh(i)

    def changeattack(self, num):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        if not self.attacks[num].get() in ["Unknown", "UNKNOWN"]:
            if self.attacks[num].get() in ["None", "NONE"]:
                pal.RemoveAttack(num)
            else:
                pal.SetAttackSkill(num, self.attacks[num].get())

        self.refresh(i)

    def onselect(self, evt):
        w = evt.widget
        if not self.isPalSelected():
            return

        if self.editindex > -1:
            self.updatestats(self.editindex)

        index = int(w.curselection()[0])
        self.editindex = index

        pal = self.palbox[self.players[self.current.get()]][index]
        # palname.config(text=pal.GetName())
        self.speciesvar.set(pal.GetName())

        self.storageId.config(text=f"StorageID: {pal.storageId}")
        self.storageSlot.config(text=f"StorageSlot: {pal.storageSlot}")

        g = pal.GetGender()
        self.palgender.config(text=g,
                              fg=PalInfo.PalGender.MALE.value if g == "Male ♂" else PalInfo.PalGender.FEMALE.value)

        self.title.config(text=f"{pal.GetNickname()}")
        self.level.config(text=f"Lv. {pal.GetLevel() if pal.GetLevel() > 0 else '?'}")
        self.portrait.config(image=pal.GetImage())

        self.ptype.config(text=pal.GetPrimary(), bg=PalInfo.PalElements[pal.GetPrimary()])
        self.stype.config(text=pal.GetSecondary(), bg=PalInfo.PalElements[pal.GetSecondary()])

        # ⚔🏹
        # talent_hp_var.set(pal.GetTalentHP())
        self.phpvar.set(pal.GetTalentHP())
        self.meleevar.set(pal.GetAttackMelee())
        self.shotvar.set(pal.GetAttackRanged())
        self.defvar.set(pal.GetDefence())
        self.wspvar.set(pal.GetWorkSpeed())

        self.luckyvar.set(pal.isLucky)
        self.alphavar.set(pal.isBoss)

        self.updateAttacks()

        # rank
        match pal.GetRank():
            case 5:
                self.ranksvar.set(PalEdit.ranks[4])
            case 4:
                self.ranksvar.set(PalEdit.ranks[3])
            case 3:
                self.ranksvar.set(PalEdit.ranks[2])
            case 2:
                self.ranksvar.set(PalEdit.ranks[1])
            case _:
                self.ranksvar.set(PalEdit.ranks[0])

        s = pal.GetSkills()[:]
        while len(s) < 4:
            s.append("NONE")

        for i in range(0, 4):
            if not s[i] in [p for p in PalInfo.PalPassives]:
                self.skills[i].set("Unknown")
            else:
                self.skills[i].set(PalInfo.PalPassives[s[i]])

        self.setskillcolours()

    def changetext(self, num):
        if num == -1:
            self.skilllabel.config(text="Hover a skill to see it's description")
            return

        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        if type(num) == str:
            self.skilllabel.config(text=pal.GetOwner())
            return

        if self.skills[num].get() == "Unknown":
            self.skilllabel.config(text=f"{pal.GetSkills()[num]}{PalInfo.PassiveDescriptions['Unknown']}")
            return
        self.skilllabel.config(text=PalInfo.PassiveDescriptions[self.skills[num].get()])

    def loadfile(self):
        self.skilllabel.config(text="Loading save, please be patient...")

        file = askopenfilename(initialdir=os.path.expanduser('~') + "\\AppData\\Local\\Pal\\Saved\\SaveGames",
                               filetypes=[("Level.sav", "Level.sav")])
        print(f"Opening file {file}")

        if file:
            self.filename = file
            self.gui.title(f"PalEdit v{PalEditConfig.version} - {file}")
            self.skilllabel.config(text="Decompressing save, please be patient...")
            with open(file, "rb") as f:
                data = f.read()
                raw_gvas, _ = decompress_sav_to_gvas(data)
            self.skilllabel.config(text=f"Loading GVAS file, please be patient...")
            gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)
            self.loaddata(gvas_file)
            # self.doconvertjson(file, (not self.debug))
        else:
            messagebox.showerror("Select a file", "Please select a save file.")

    def load(self, file):
        self.current.set("")
        self.palbox = {}
        self.players = {}
        
        f = open(file, "r", encoding="utf8")
        data = json.loads(f.read())
        f.close()

        if file.endswith(".pson"):
            self.loadpal(paldata)
        else:
            self.loaddata(data)
            # paldata = self.data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
            # f = open("current.pson", "w", encoding="utf8")
            # json.dump(paldata, f, indent=4)
            # f.close()
        
        messagebox.showinfo("Done", "Done loading!")
    
    def loaddata(self, data):
        self.data = data
        if isinstance(data, GvasFile):
            self.data = {
                'gvas_file': data,
                'properties': data.properties
            }
        paldata = self.data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        self.palguidmanager = PalGuid(self.data)
        self.loadpal(paldata)
        
    def loadpal(self, paldata):
        self.palbox = {}
        self.players = {}
        self.players = self.palguidmanager.GetPlayerslist()
        print(self.players)
        for p in self.players:
            self.palbox[self.players[p]] = []
        self.containers = {}
        nullmoves = []
        for i in paldata:
            try:
                p = PalInfo.PalEntity(i)
                if not str(p.owner) in self.palbox:
                    self.palbox[str(p.owner)] = []
                self.palbox[str(p.owner)].append(p)

                n = p.GetFullName()

                for m in p.GetLearntMoves():
                    if not m in nullmoves:
                        if not m in PalInfo.PalAttacks:
                            nullmoves.append(m)
            except Exception as e:
                if str(e) == "This is a player character":
                    print("Found Player Character")
                    # print(f"\nDebug: Data \n{i}\n\n")
                    # o = i['value']['RawData']['value']['object']['SaveParameter']['value']
                    # pl = "No Name"
                    # if "NickName" in o:
                    #     pl = o['NickName']['value']
                    # plguid = i['key']['PlayerUId']['value']
                    # print(f"{pl} - {plguid}")
                    # self.players[pl] = plguid
                else:
                    self.unknown.append(i)
                    print(f"Error occured: {str(e)}")
                # print(f"Debug: Data {i}")

        self.current.set(next(iter(self.players)))
        print(f"Defaulted selection to {self.current.get()}")

        self.updateDisplay()

        print(f"Unknown list contains {len(self.unknown)} entries")
        # for i in unknown:
        # print (i)

        print(f"{len(self.players)} players found:")
        for i in self.players:
            print(f"{i} = {self.players[i]}")
        self.playerdrop['values'] = list(self.players.keys())
        self.playerdrop.current(0)

        if False:  # change to true to enable testing of containers
            if not file.endswith(".pson"):
                condata = self.data['properties']['worldSaveData']['value']['CharacterContainerSaveData']['value']
                for c in condata:
                    conguid = c["key"]["ID"]["value"]
                    if not conguid in self.containers:
                        self.containers[conguid] = 0
                    else:
                        self.containers[conguid] += 1

                print(f"{len(self.containers)} containers were found")
                for c in self.containers:
                    print(f"{c} : {self.containers[c]}")

        nullmoves.sort()
        for i in nullmoves:
            print(f"{i} was not found in Attack Database")
        
        self.refresh()

        self.changetext(-1)
        self.jump()

    def jump(self):
        self.gui.attributes('-topmost', 1)
        self.gui.attributes('-topmost', 0)
        self.gui.focus_force()
        self.gui.bell()

    def updateDisplay(self):
        self.listdisplay.delete(0, tk.constants.END)
        self.palbox[self.players[self.current.get()]].sort(key=lambda e: e.GetName())

        for p in self.palbox[self.players[self.current.get()]]:
            self.listdisplay.insert(tk.constants.END, p.GetFullName())

            if p.isBoss:
                self.listdisplay.itemconfig(tk.constants.END, {'fg': 'red'})
            elif p.isLucky:
                self.listdisplay.itemconfig(tk.constants.END, {'fg': 'blue'})

    def savefile(self):
        self.skilllabel.config(text="Saving, please be patient... (it can take up to 5 minutes in large files)")
        self.gui.update()

        if self.isPalSelected():
            i = int(self.listdisplay.curselection()[0])
            self.refresh(i)

        file = self.filename
        print(file, self.filename)
        if file:
            print(f"Opening file {file}")
            
            if 'gvas_file' in self.data:
                gvas_file = self.data['gvas_file']
                if (
                        "Pal.PalWorldSaveGame" in gvas_file.header.save_game_class_name
                        or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name
                ):
                    save_type = 0x32
                else:
                    save_type = 0x31
                sav_file = compress_gvas_to_sav(
                    gvas_file.write(PALWORLD_CUSTOM_PROPERTIES), save_type
                )
                self.skilllabel.config(text="Writing SAV file...")
                with open(file, "wb") as f:
                    f.write(sav_file)
                self.data = None
                self.current.set("")
                self.palbox = {}
                self.players = {}
                self.listdisplay.delete(0, tk.constants.END)
            else:
                self.savejson(file)
                self.doconvertsave(file)

            self.changetext(-1)
            self.jump()
            messagebox.showinfo("Done", "Done saving!")

    def savepson(self, filename):
        f = open(filename, "w", encoding="utf8")
        if 'properties' in self.data:
            json.dump(self.data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'],
                      f)  # , indent=4)
        else:
            json.dump(self.data, f)  # , indent=4)
        f.close()

    def savejson(self, filename):
        # f = open(filename, "r", encoding="utf8")
        # svdata = json.loads(f.read())
        # f.close()

        # if 'properties' in data:
        # svdata['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        # else:
        # svdata['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = data

        f = open(filename, "w", encoding="utf8")
        if 'gvas_file' in self.data:
            json.dump(self.data['gvas_file'].dump(), f, cls=CustomEncoder)
        else:
            json.dump(self.data, f)  # svdata, f)
        f.close()

        self.changetext(-1)

    def createGUIDtoClipboard(self):
        newguid = uuid.uuid4()
        print(newguid)
        pyperclip.copy(f"{newguid}")

    def generateguid(self):
        newguid = uuid.uuid4()
        print(newguid)

    def updatestats(self, e):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][e]
        l = pal.GetLevel()
        # pal.SetTalentHP(talent_hp_var.get())
        h = self.phpvar.get()
        pal.SetTalentHP(h)
        hv = 500 + (((70 * 0.5) * l) * (1 + (h / 100)))
        self.hthstatval.config(text=math.floor(hv))

        a = self.meleevar.get()
        pal.SetAttackMelee(a)
        pal.SetAttackRanged(self.shotvar.get())
        av = 100 + (((70 * 0.75) * l) * (1 + (a / 100)))
        self.atkstatval.config(text=math.floor(av))

        d = self.defvar.get()
        pal.SetDefence(d)
        dv = 50 + (((70 * 0.75) * l) * (1 + (d / 100)))
        self.defstatval.config(text=math.floor(dv))

        pal.SetWorkSpeed(self.wspvar.get())

    def takelevel(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        if pal.GetLevel() == 1:
            return
        pal.SetLevel(pal.GetLevel() - 1)
        self.refresh(i)

    def givelevel(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        if pal.GetLevel() == 50:
            return
        pal.SetLevel(pal.GetLevel() + 1)
        self.refresh(i)

    def changespeciestype(self, evt):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        pal.SetType(self.speciesvar.get())
        self.updateDisplay()
        self.refresh(self.palbox[self.players[self.current.get()]].index(pal))

    def setskillcolours(self):
        for snum in range(0, 4):
            rating = PalInfo.PassiveRating[self.skills[snum].get()]
            col = PalEditConfig.goodskill if rating == "Good" else PalEditConfig.okayskill if rating == "Okay" else PalEditConfig.badskill

            self.skilldrops[snum].config(highlightbackground=col, bg=PalEdit.mean_color(col, "ffffff"),
                                         activebackground=PalEdit.mean_color(col, "ffffff"))

    def refresh(self, num=0):
        self.setskillcolours()
        self.setAttackCols()

        self.listdisplay.select_set(num)
        self.listdisplay.event_generate("<<ListboxSelect>>")

    def converttojson(self):

        self.skilllabel.config(text="Converting... this may take a while.")

        file = askopenfilename(filetypes=[("All files", "*.sav")])
        print(f"Opening file {file}")

        self.doconvertjson(file)

    def spawnpal(self):
        if not self.isPalSelected() or self.palguidmanager is None:
            return
        playerguid = self.players[self.current.get()]
        playersav = os.path.dirname(self.filename) + f"/players/{playerguid.replace('-', '')}.sav"
        if not os.path.exists(playersav):
            print("Cannot Load Player Save!")
            return
        player = PalPlayerEntity(SaveConverter.convert_sav_to_obj(playersav))
        SaveConverter.convert_obj_to_sav(player.dump(), playersav + ".bak", True)

        file = askopenfilename(filetypes=[("json files", "*.json")])
        if file == '':
            messagebox.showerror("Select a file", "Please select a save file.")
            return

        f = open(file, "r", encoding="utf8")
        spawnpaldata = json.loads(f.read())
        f.close()

        slotguid = str(player.GetPalStorageGuid())
        groupguid = self.palguidmanager.GetGroupGuid(playerguid)
        if any(guid == None for guid in [slotguid, groupguid]):
            return
        for p in spawnpaldata['Pals']:
            newguid = str(uuid.uuid4())
            pal = PalEntity(p)
            i = self.palguidmanager.GetEmptySlotIndex(slotguid)
            if i == -1:
                print("Player Pal Storage is full!")
                return
            pal.InitializationPal(newguid, playerguid, groupguid, slotguid)
            self.palguidmanager.AddGroupSaveData(groupguid, newguid)
            self.palguidmanager.SetContainerSave(slotguid, i, newguid)
            self.data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'].append(pal._data)
            print(f"Add Pal at slot {i} : {slotguid}")
        self.loaddata(self.data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'])

    def dumppals(self):
        if not self.isPalSelected():
            return
        pals = {}
        pals['Pals'] = [pal._data for pal in self.palbox[self.players[self.current.get()]]]
        file = asksaveasfilename(filetypes=[("json files", "*.json")], defaultextension=".json")
        if file:
            with open(file, "wb") as f:
                f.write(json.dumps(pals, indent=4).encode('utf-8'))
        else:
            messagebox.showerror("Select a file", "Please select a save file.")

    def doconvertjson(self, file, compress=False):
        SaveConverter.convert_sav_to_json(file, file.replace(".sav", ".sav.json"), True, compress)

        self.load(file.replace(".sav", ".sav.json"))

        self.changetext(-1)
        self.jump()
        # messagebox.showinfo("Done", "Done decompiling!")

    def converttosave(self):
        self.skilllabel.config(text="Converting... this may take a while.")

        file = askopenfilename(filetypes=[("All files", "*.sav.json")])
        print(f"Opening file {file}")

        self.doconvertsave(file)

    def doconvertsave(self, file):
        SaveConverter.convert_json_to_sav(file, file.replace(".sav.json", ".sav"), True)

        self.changetext(-1)
        self.jump()
        # messagebox.showinfo("Done", "Done compiling!")

    def swapgender(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        pal.SwapGender()
        self.refresh(i)

    def replaceitem(self, i, pal):
        self.listdisplay.delete(i)
        self.listdisplay.insert(i, pal.GetFullName())

        if pal.isBoss:
            self.listdisplay.itemconfig(i, {'fg': 'red'})
        elif pal.isLucky:
            self.listdisplay.itemconfig(i, {'fg': 'blue'})

    def togglelucky(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        if self.luckyvar.get() == 1 and self.alphavar.get() == 1:
            self.alphavar.set(0)

        pal.SetLucky(True if self.luckyvar.get() == 1 else False)
        self.replaceitem(i, pal)
        self.refresh(i)

    def togglealpha(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        if self.luckyvar.get() == 1 and self.alphavar.get() == 1:
            self.luckyvar.set(0)

        pal.SetBoss(True if self.alphavar.get() == 1 else False)
        self.replaceitem(i, pal)
        self.refresh(i)

    def createWindow(self):
        root = tk.Tk()
        root.title(f"PalEdit v{PalEditConfig.version}")
        return root

    def build_menu(self):
        self.menu = tk.Menu(self.gui)
        tools = self.menu
        self.gui.config(menu=tools)

        filemenu = tk.Menu(tools, tearoff=0)
        filemenu.add_command(label="Load PalWorld Save", command=self.loadfile)
        filemenu.add_command(label="Save Changes To File", command=self.savefile)

        tools.add_cascade(label="File", menu=filemenu, underline=0)

        toolmenu = tk.Menu(tools, tearoff=0)
        toolmenu.add_command(label="Debug", command=self.toggleDebug)
        toolmenu.add_command(label="Generate GUID", command=self.generateguid)

        tools.add_cascade(label="Tools", menu=toolmenu, underline=0)

        # convmenu = Menu(tools, tearoff=0)
        # convmenu.add_command(label="Convert Save to Json", command=converttojson)
        # convmenu.add_command(label="Convert Json to Save", command=converttosave)

        # tools.add_cascade(label="Converter", menu=convmenu, underline=0)

    def __init__(self):
        global EmptyObjectHandler, PalInfo
        import EmptyObjectHandler
        import PalInfo

        self.data = None
        self.palbox = {}
        self.players = {}
        self.containers = {}
        self.unknown = []
        self.debug = "false"
        self.editindex = -1
        self.filename = ""
        self.gui = self.createWindow()
        self.palguidmanager: PalGuid = None

        purplepanda = ImageTk.PhotoImage(
            Image.open(f'{module_dir}/../PalEdit/resources/MossandaIcon.png').resize((240, 240)))
        self.gui.iconphoto(True, purplepanda)

        root = self.gui

        self.current = tk.StringVar()
        self.current.set("")

        scrollview = tk.Frame(root)
        scrollview.pack(side=tk.constants.LEFT, fill=tk.constants.Y)

        self.build_menu()
        playerframe = tk.Frame(scrollview)
        playerframe.pack(fill=tk.constants.X)
        playerlbl = tk.Label(playerframe, text="Player:")
        playerlbl.config(justify='center')
        playerlbl.pack(side=tk.constants.LEFT, fill=tk.constants.X, expand=True)
        self.playerdrop = ttk.Combobox(playerframe, textvariable=self.current)
        self.playerdrop.pack(side=tk.constants.RIGHT, fill=tk.constants.X)
        self.playerdrop.bind("<<ComboboxSelected>>", self.changeplayer)

        scrollbar = tk.Scrollbar(scrollview)
        scrollbar.pack(side=tk.constants.LEFT, fill=tk.constants.Y)
        self.listdisplay = tk.Listbox(scrollview, width=30, yscrollcommand=scrollbar.set, exportselection=0)
        self.listdisplay.pack(side=tk.constants.LEFT, fill=tk.constants.BOTH)
        self.listdisplay.bind("<<ListboxSelect>>", self.onselect)
        scrollbar.config(command=self.listdisplay.yview)

        # Attack Skills
        atkskill = tk.Frame(root, width=120, relief="groove", borderwidth=2)
        atkskill.pack(side=tk.constants.RIGHT, fill=tk.constants.Y)
        atkLabel = tk.Label(atkskill, bg="darkgrey", width=12, text="Equipped",
                            font=(PalEditConfig.font, PalEditConfig.ftsize),
                            justify="center")
        atkLabel.pack(fill=tk.constants.X)

        self.attacks = [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        self.attacks[0].set("Blast Punch")
        self.attacks[1].set("Tri-Lightning")
        self.attacks[2].set("Dark Laser")

        equipFrame = tk.Frame(atkskill, borderwidth=2, relief="raised")
        equipFrame.pack(fill=tk.constants.X)

        self.attackops = [PalInfo.PalAttacks[e] for e in PalInfo.PalAttacks]
        self.attackops.remove("None")
        self.attackops.sort()
        self.attackops.insert(0, "None")
        self.attackdrops = [
            tk.OptionMenu(equipFrame, self.attacks[0], *self.attackops, command=lambda evt: self.changeattack(0)),
            tk.OptionMenu(equipFrame, self.attacks[1], *self.attackops, command=lambda evt: self.changeattack(1)),
            tk.OptionMenu(equipFrame, self.attacks[2], *self.attackops, command=lambda evt: self.changeattack(2))
        ]

        self.attackdrops[0].pack(fill=tk.constants.X)
        self.attackdrops[0].config(font=(PalEditConfig.font, PalEditConfig.ftsize), width=12, direction="right")
        self.attackdrops[1].pack(fill=tk.constants.X)
        self.attackdrops[1].config(font=(PalEditConfig.font, PalEditConfig.ftsize), width=12, direction="right")
        self.attackdrops[2].pack(fill=tk.constants.X)
        self.attackdrops[2].config(font=(PalEditConfig.font, PalEditConfig.ftsize), width=12, direction="right")

        self.attackdrops[0].config(highlightbackground=PalInfo.PalElements["Electric"],
                                   bg=PalEdit.mean_color(PalInfo.PalElements["Electric"], "ffffff"),
                                   activebackground=PalEdit.mean_color(PalInfo.PalElements["Electric"], "ffffff"))
        self.attackdrops[1].config(highlightbackground=PalInfo.PalElements["Electric"],
                                   bg=PalEdit.mean_color(PalInfo.PalElements["Electric"], "ffffff"),
                                   activebackground=PalEdit.mean_color(PalInfo.PalElements["Electric"], "ffffff"))
        self.attackdrops[2].config(highlightbackground=PalInfo.PalElements["Dark"],
                                   bg=PalEdit.mean_color(PalInfo.PalElements["Dark"], "ffffff"),
                                   activebackground=PalEdit.mean_color(PalInfo.PalElements["Dark"], "ffffff"))

        stats = tk.Frame(atkskill)
        # stats.pack(fill=tk.constants.X)

        statLabel = tk.Label(stats, bg="darkgrey", width=12, text="Stats",
                             font=(PalEditConfig.font, PalEditConfig.ftsize), justify="center")
        statLabel.pack(fill=tk.constants.X)

        statlbls = tk.Frame(stats, width=6, bg="darkgrey")
        statlbls.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.X)

        hthstatlbl = tk.Label(statlbls, bg="darkgrey", text="Health", font=(PalEditConfig.font, PalEditConfig.ftsize),
                              justify="center")
        hthstatlbl.pack()
        atkstatlbl = tk.Label(statlbls, bg="darkgrey", text="Attack", font=(PalEditConfig.font, PalEditConfig.ftsize),
                              justify="center")
        atkstatlbl.pack()
        defstatlbl = tk.Label(statlbls, bg="darkgrey", text="Defence", font=(PalEditConfig.font, PalEditConfig.ftsize),
                              justify="center")
        defstatlbl.pack()

        statvals = tk.Frame(stats, width=6)
        statvals.pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.X)

        self.hthstatval = tk.Label(statvals, bg="lightgrey", text="500",
                                   font=(PalEditConfig.font, PalEditConfig.ftsize),
                                   justify="center")
        self.hthstatval.pack(fill=tk.constants.X)
        self.atkstatval = tk.Label(statvals, text="100", font=(PalEditConfig.font, PalEditConfig.ftsize),
                                   justify="center")
        self.atkstatval.pack(fill=tk.constants.X)
        self.defstatval = tk.Label(statvals, bg="lightgrey", text="50", font=(PalEditConfig.font, PalEditConfig.ftsize),
                                   justify="center")
        self.defstatval.pack(fill=tk.constants.X)

        disclaim = tk.Label(atkskill, bg="darkgrey", text="The values above do not include passive skills",
                            font=(PalEditConfig.font, PalEditConfig.ftsize // 2))
        # disclaim.pack(fill=tk.constants.X)

        # Individual Info
        infoview = tk.Frame(root, relief="groove", borderwidth=2, width=480, height=480)
        infoview.pack(side=tk.constants.RIGHT, fill=tk.constants.BOTH, expand=True)

        dataview = tk.Frame(infoview)
        dataview.pack(side=tk.constants.TOP, fill=tk.constants.BOTH)

        resourceview = tk.Frame(dataview)
        resourceview.pack(side=tk.constants.LEFT, fill=tk.constants.BOTH, expand=True)

        self.portrait = tk.Label(resourceview, image=purplepanda, relief="sunken", borderwidth=2)
        self.portrait.pack()

        typeframe = tk.Frame(resourceview)
        typeframe.pack(expand=True, fill=tk.constants.X)
        self.ptype = tk.Label(typeframe, text="Electric", font=(PalEditConfig.font, PalEditConfig.ftsize),
                              bg=PalInfo.PalElements["Electric"], width=6)
        self.ptype.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.X)
        self.stype = tk.Label(typeframe, text="Dark", font=(PalEditConfig.font, PalEditConfig.ftsize),
                              bg=PalInfo.PalElements["Dark"], width=6)
        self.stype.pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.X)

        formframe = tk.Frame(resourceview)
        formframe.pack(expand=True, fill=tk.constants.X)
        self.luckyvar = tk.IntVar()
        self.alphavar = tk.IntVar()
        luckybox = tk.Checkbutton(formframe, text='Lucky', variable=self.luckyvar, onvalue='1', offvalue='0',
                                  command=self.togglelucky)
        luckybox.pack(side=tk.constants.LEFT, expand=True)
        alphabox = tk.Checkbutton(formframe, text='Alpha', variable=self.alphavar, onvalue='1', offvalue='0',
                                  command=self.togglealpha)
        alphabox.pack(side=tk.constants.RIGHT, expand=True)

        deckview = tk.Frame(dataview, width=320, relief="sunken", borderwidth=2, pady=0)
        deckview.pack(side=tk.constants.RIGHT, fill=tk.constants.BOTH, expand=True)

        self.title = tk.Label(deckview, text=f"PalEdit", bg="darkgrey", font=(PalEditConfig.font, 24), width=17)
        self.title.pack(expand=True, fill=tk.constants.BOTH)

        headerframe = tk.Frame(deckview, padx=0, pady=0, bg="darkgrey")
        headerframe.pack(fill=tk.constants.X)
        headerframe.grid_rowconfigure(0, weight=1)
        headerframe.grid_columnconfigure((0, 2), uniform="equal")
        headerframe.grid_columnconfigure(1, weight=1)

        self.level = tk.Label(headerframe, text=f"v{PalEditConfig.version}", bg="darkgrey",
                              font=(PalEditConfig.font, 24),
                              width=17)
        self.level.bind("<Enter>", lambda evt, num="owner": self.changetext(num))
        self.level.bind("<Leave>", lambda evt, num=-1: self.changetext(num))
        self.level.grid(row=0, column=1, sticky="nsew")

        minlvlbtn = tk.Button(headerframe, text="➖", borderwidth=1, font=(PalEditConfig.font, PalEditConfig.ftsize - 2),
                              command=self.takelevel,
                              bg="darkgrey")
        minlvlbtn.grid(row=0, column=0, sticky="nsew")

        addlvlbtn = tk.Button(headerframe, text="➕", borderwidth=1, font=(PalEditConfig.font, PalEditConfig.ftsize - 2),
                              command=self.givelevel,
                              bg="darkgrey")
        addlvlbtn.grid(row=0, column=2, sticky="nsew")

        labelview = tk.Frame(deckview, bg="lightgrey", pady=0, padx=16)
        labelview.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)

        name = tk.Label(labelview, text="Species", font=(PalEditConfig.font, PalEditConfig.ftsize), bg="lightgrey")
        name.pack(expand=True, fill=tk.constants.X)
        gender = tk.Label(labelview, text="Gender", font=(PalEditConfig.font, PalEditConfig.ftsize), bg="lightgrey",
                          width=6, pady=6)
        gender.pack(expand=True, fill=tk.constants.X)
        attack = tk.Label(labelview, text="Attack IV%", font=(PalEditConfig.font, PalEditConfig.ftsize), bg="lightgrey",
                          width=8)
        attack.pack(expand=True, fill=tk.constants.X)
        defence = tk.Label(labelview, text="Defence IV%", font=(PalEditConfig.font, PalEditConfig.ftsize),
                           bg="lightgrey", width=8)
        defence.pack(expand=True, fill=tk.constants.X)
        workspeed = tk.Label(labelview, text="Workspeed IV%", font=(PalEditConfig.font, PalEditConfig.ftsize),
                             bg="lightgrey", width=12)
        workspeed.pack(expand=True, fill=tk.constants.X)
        hp = tk.Label(labelview, text="HP IV%", font=(PalEditConfig.font, PalEditConfig.ftsize), bg="lightgrey",
                      width=10)
        hp.pack(expand=True, fill=tk.constants.X)
        rankspeed = tk.Label(labelview, text="Rank", font=(PalEditConfig.font, PalEditConfig.ftsize), bg="lightgrey")
        rankspeed.pack(expand=True, fill=tk.constants.X)

        editview = tk.Frame(deckview)
        editview.pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.BOTH)

        species = [PalInfo.PalSpecies[e].GetName() for e in PalInfo.PalSpecies]
        species.sort()
        self.speciesvar = tk.StringVar()
        self.speciesvar.set("PalEdit")
        palname = tk.OptionMenu(editview, self.speciesvar, *species, command=self.changespeciestype)
        palname.config(font=(PalEditConfig.font, PalEditConfig.ftsize), padx=0, pady=0, borderwidth=1, width=5,
                       direction='right')
        palname.pack(expand=True, fill=tk.constants.X)

        genderframe = tk.Frame(editview, pady=0)
        genderframe.pack()
        self.palgender = tk.Label(genderframe, text="Unknown", font=(PalEditConfig.font, PalEditConfig.ftsize),
                                  fg=PalInfo.PalGender.UNKNOWN.value, width=10)
        self.palgender.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.X)
        swapbtn = tk.Button(genderframe, text="↺", borderwidth=1, font=(PalEditConfig.font, PalEditConfig.ftsize - 2),
                            command=self.swapgender)
        swapbtn.pack(side=tk.constants.RIGHT)

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

        attackframe = tk.Frame(editview, width=6)
        attackframe.pack(fill=tk.constants.X)
        self.meleevar = tk.IntVar()
        self.shotvar = tk.IntVar()
        self.meleevar.trace("w", lambda name, index, mode, sv=self.meleevar: clamp(sv))
        self.shotvar.trace("w", lambda name, index, mode, sv=self.shotvar: clamp(sv))
        self.meleevar.set(100)
        self.shotvar.set(0)
        meleeicon = tk.Label(attackframe, text="⚔", font=(PalEditConfig.font, PalEditConfig.ftsize))
        meleeicon.pack(side=tk.constants.LEFT)
        shoticon = tk.Label(attackframe, text="🏹", font=(PalEditConfig.font, PalEditConfig.ftsize))
        shoticon.pack(side=tk.constants.RIGHT)
        palmelee = tk.Entry(attackframe, textvariable=self.meleevar, font=(PalEditConfig.font, PalEditConfig.ftsize),
                            width=6)
        palmelee.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palmelee.bind("<FocusOut>", lambda evt, sv=self.meleevar: fillifempty(sv))
        palmelee.pack(side=tk.constants.LEFT)
        palshot = tk.Entry(attackframe, textvariable=self.shotvar, font=(PalEditConfig.font, PalEditConfig.ftsize),
                           width=6)
        palshot.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palshot.bind("<FocusOut>", lambda evt, sv=self.shotvar: fillifempty(sv))
        palshot.pack(side=tk.constants.RIGHT)

        self.defvar = tk.IntVar()
        self.defvar.trace("w", lambda name, index, mode, sv=self.defvar: clamp(sv))
        self.defvar.set(100)
        paldef = tk.Entry(editview, textvariable=self.defvar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        paldef.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        paldef.bind("<FocusOut>", lambda evt, sv=self.defvar: fillifempty(sv))
        paldef.pack(expand=True, fill=tk.constants.X)

        self.wspvar = tk.IntVar()
        self.wspvar.trace("w", lambda name, index, mode, sv=self.wspvar: clamp(sv))
        self.wspvar.set(70)
        palwsp = tk.Entry(editview, textvariable=self.wspvar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        palwsp.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palwsp.bind("<FocusOut>", lambda evt, sv=self.wspvar: fillifempty(sv))
        palwsp.pack(expand=True, fill=tk.constants.X)

        def talent_hp_changed(*args):
            if not self.isPalSelected():
                return
            i = int(listdisplay.curselection()[0])
            pal = palbox[self.players[self.current.get()]][i]
            if talent_hp_var.get() == 0:
                talent_hp_var.set(1)
            # change value of pal

        self.phpvar = tk.IntVar()
        self.phpvar.trace("w", lambda name, index, mode, sv=self.phpvar: clamp(sv))
        self.phpvar.set(50)
        palhps = tk.Entry(editview, textvariable=self.phpvar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        palhps.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palhps.bind("<FocusOut>", lambda evt, sv=self.phpvar: fillifempty(sv))
        palhps.pack(expand=True, fill=tk.constants.X)

        """
        talent_hp_var = IntVar(value=50)
        talent_hp_var.trace_add("write", lambda name, index, mode, sv=talent_hp_var: talent_hp_changed(clamp(sv)))
        # hpslider = Scale(editview, from_=0, to=100, tickinterval=50, orient='horizontal', variable=talent_hp_var)
        hpslider = Scale(editview, from_=0, to=100, orient='horizontal', variable=talent_hp_var)
        hpslider.config(width=9)
        hpslider.pack(pady=(0,10), expand=True, fill=tk.constants.X, anchor="center")
        """

        self.ranksvar = tk.IntVar()
        palrank = tk.OptionMenu(editview, self.ranksvar, *PalEdit.ranks, command=self.changerankchoice)
        palrank.config(font=(PalEditConfig.font, PalEditConfig.ftsize), justify='center', padx=0, pady=0, borderwidth=1,
                       width=5)
        self.ranksvar.set(PalEdit.ranks[4])
        palrank.pack(expand=True, fill=tk.constants.X)

        # PASSIVE ABILITIES
        skillview = tk.Frame(infoview, relief="sunken", borderwidth=2)
        skillview.pack(fill=tk.constants.BOTH, expand=True)

        topview = tk.Frame(skillview)
        topview.pack(fill=tk.constants.BOTH, expand=True)
        botview = tk.Frame(skillview)
        botview.pack(fill=tk.constants.BOTH, expand=True)

        self.skills = [tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()]
        # for i in range(0, 4):
        # skills[i].set("Unknown")
        # skills[i].trace("w", lambda *args, num=i: changeskill(num))
        self.skills[0].set("Legend")
        self.skills[1].set("Workaholic")
        self.skills[2].set("Ferocious")
        self.skills[3].set("Lucky")

        op = [PalInfo.PalPassives[e] for e in PalInfo.PalPassives]
        op.pop(0)
        op.pop(0)
        op.sort()
        op.insert(0, "None")
        self.skilldrops = [
            tk.OptionMenu(topview, self.skills[0], *op, command=lambda evt: self.changeskill(0)),
            tk.OptionMenu(topview, self.skills[1], *op, command=lambda evt: self.changeskill(1)),
            tk.OptionMenu(botview, self.skills[2], *op, command=lambda evt: self.changeskill(2)),
            tk.OptionMenu(botview, self.skills[3], *op, command=lambda evt: self.changeskill(3))
        ]

        self.skilldrops[0].pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        self.skilldrops[0].config(font=(PalEditConfig.font, PalEditConfig.ftsize), width=6, direction="right")
        self.skilldrops[1].pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.BOTH)
        self.skilldrops[1].config(font=(PalEditConfig.font, PalEditConfig.ftsize), width=6, direction="right")
        self.skilldrops[2].pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        self.skilldrops[2].config(font=(PalEditConfig.font, PalEditConfig.ftsize), width=6, direction="right")
        self.skilldrops[3].pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.BOTH)
        self.skilldrops[3].config(font=(PalEditConfig.font, PalEditConfig.ftsize), width=6, direction="right")

        self.skilldrops[0].config(highlightbackground=PalEditConfig.goodskill,
                                  bg=PalEdit.mean_color(PalEditConfig.goodskill, "ffffff"),
                                  activebackground=PalEdit.mean_color(PalEditConfig.goodskill, "ffffff"))
        self.skilldrops[1].config(highlightbackground=PalEditConfig.goodskill,
                                  bg=PalEdit.mean_color(PalEditConfig.goodskill, "ffffff"),
                                  activebackground=PalEdit.mean_color(PalEditConfig.goodskill, "ffffff"))
        self.skilldrops[2].config(highlightbackground=PalEditConfig.goodskill,
                                  bg=PalEdit.mean_color(PalEditConfig.goodskill, "ffffff"),
                                  activebackground=PalEdit.mean_color(PalEditConfig.goodskill, "ffffff"))
        self.skilldrops[3].config(highlightbackground=PalEditConfig.goodskill,
                                  bg=PalEdit.mean_color(PalEditConfig.goodskill, "ffffff"),
                                  activebackground=PalEdit.mean_color(PalEditConfig.goodskill, "ffffff"))

        self.skilldrops[0].bind("<Enter>", lambda evt, num=0: self.changetext(num))
        self.skilldrops[1].bind("<Enter>", lambda evt, num=1: self.changetext(num))
        self.skilldrops[2].bind("<Enter>", lambda evt, num=2: self.changetext(num))
        self.skilldrops[3].bind("<Enter>", lambda evt, num=3: self.changetext(num))
        self.skilldrops[0].bind("<Leave>", lambda evt, num=-1: self.changetext(num))
        self.skilldrops[1].bind("<Leave>", lambda evt, num=-1: self.changetext(num))
        self.skilldrops[2].bind("<Leave>", lambda evt, num=-1: self.changetext(num))
        self.skilldrops[3].bind("<Leave>", lambda evt, num=-1: self.changetext(num))

        # PRESETS
        framePresets = tk.Frame(infoview, relief="groove", borderwidth=0)
        framePresets.pack(fill=tk.constants.BOTH, expand=True)

        framePresetsTitle = tk.Frame(framePresets)
        framePresetsTitle.pack(fill=tk.constants.BOTH)
        presetTitle = tk.Label(framePresetsTitle, text='Presets:', anchor='w', bg="darkgrey",
                               font=(PalEditConfig.font, PalEditConfig.ftsize), width=6,
                               height=1).pack(fill=tk.constants.BOTH)

        framePresetsButtons = tk.Frame(framePresets, relief="groove", borderwidth=4)
        framePresetsButtons.pack(fill=tk.constants.BOTH, expand=True)

        framePresetsButtons1 = tk.Frame(framePresetsButtons)
        framePresetsButtons1.pack(fill=tk.constants.BOTH, expand=True)
        preset_title1 = tk.Label(framePresetsButtons1, text='Utility:', anchor='e', bg="darkgrey",
                                 font=(PalEditConfig.font, 13),
                                 width=9).pack(side=tk.constants.LEFT, fill=tk.constants.X)
        preset_button = tk.Button(framePresetsButtons1, text="Base", command=lambda: self.setpreset("base"))
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons1, text="Speed Worker",
                                  command=lambda: self.setpreset("workspeed"))
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons1, text="Speed Runner", command=lambda: self.setpreset("movement"))
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons1, text="Tank", command=lambda: self.setpreset("tank"))
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)

        framePresetsButtons2 = tk.Frame(framePresetsButtons)
        framePresetsButtons2.pack(fill=tk.constants.BOTH, expand=True)
        preset_title2 = tk.Label(framePresetsButtons2, text='Damage:', anchor='e', bg="darkgrey",
                                 font=(PalEditConfig.font, 13),
                                 width=9).pack(side=tk.constants.LEFT, fill=tk.constants.X)
        preset_button = tk.Button(framePresetsButtons2, text="Max", command=lambda: self.setpreset("dmg_max"))
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons2, text="Balanced", command=lambda: self.setpreset("dmg_balanced"))
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons2, text="Mount", command=lambda: self.setpreset("dmg_mount"))
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons2, text="Element", command=lambda: self.setpreset("dmg_element"))
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)

        # PRESETS OPTIONS
        framePresetsExtras = tk.Frame(framePresets, relief="groove", borderwidth=4)
        framePresetsExtras.pack(fill=tk.constants.BOTH, expand=True)

        framePresetsLevel = tk.Frame(framePresetsExtras)
        framePresetsLevel.pack(fill=tk.constants.BOTH, expand=True)
        presetTitleLevel = tk.Label(framePresetsLevel, text='Set Level:', anchor='center', bg="lightgrey",
                                    font=(PalEditConfig.font, 13),
                                    width=20, height=1).pack(side=tk.constants.LEFT, expand=False, fill=tk.constants.Y)
        self.checkboxLevelVar = tk.IntVar()
        checkboxLevel = tk.Checkbutton(framePresetsLevel, text='Preset changes level', variable=self.checkboxLevelVar,
                                       onvalue='1',
                                       offvalue='0').pack(side=tk.constants.LEFT, expand=False, fill=tk.constants.BOTH)
        self.textboxLevelVar = tk.IntVar(value=1)
        textboxLevel = tk.Entry(framePresetsLevel, textvariable=self.textboxLevelVar, justify='center', width=10)
        textboxLevel.config(font=(PalEditConfig.font, 10), width=10)
        textboxLevel.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.Y)

        framePresetsRank = tk.Frame(framePresetsExtras)
        framePresetsRank.pack(fill=tk.constants.BOTH, expand=True)
        presetTitleRank = tk.Label(framePresetsRank, text='Set Rank:', anchor='center', bg="lightgrey",
                                   font=(PalEditConfig.font, 13),
                                   width=20, height=1).pack(side=tk.constants.LEFT, expand=False, fill=tk.constants.Y)
        self.checkboxRankVar = tk.IntVar()
        checkboxRank = tk.Checkbutton(framePresetsRank, text='Preset changes rank', variable=self.checkboxRankVar,
                                      onvalue='1',
                                      offvalue='0').pack(side=tk.constants.LEFT, expand=False, fill=tk.constants.BOTH)
        self.optionMenuRankVar = tk.IntVar(value=1)
        self.optionMenuRank = tk.OptionMenu(framePresetsRank, self.optionMenuRankVar, *PalEdit.ranks)
        self.optionMenuRankVar.set(PalEdit.ranks[0])
        self.optionMenuRank.config(font=(PalEditConfig.font, 10), width=5, justify='center')
        self.optionMenuRank.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.Y)

        framePresetsAttributes = tk.Frame(framePresetsExtras)
        framePresetsAttributes.pack(fill=tk.constants.BOTH, expand=False)
        presetTitleAttributes = tk.Label(framePresetsAttributes, text='Set Attributes:', anchor='center',
                                         bg="lightgrey",
                                         font=(PalEditConfig.font, 13), width=20, height=1).pack(side=tk.constants.LEFT,
                                                                                                 expand=False,
                                                                                                 fill=tk.constants.Y)
        self.checkboxAttributesVar = tk.IntVar()
        checkboxAttributes = tk.Checkbutton(framePresetsAttributes, text='Preset changes attributes',
                                            variable=self.checkboxAttributesVar, onvalue='1', offvalue='0').pack(
            side=tk.constants.LEFT,
            expand=False,
            fill=tk.constants.BOTH)
        presetTitleAttributesTodo = tk.Label(framePresetsAttributes, text='Not Yet', font=(PalEditConfig.font, 10),
                                             width=10,
                                             justify='center').pack(side=tk.constants.LEFT, expand=True,
                                                                    fill=tk.constants.Y)

        # DEBUG
        frameDebug = self.frameDebug = tk.Frame(infoview, relief="flat")
        frameDebug.pack()
        frameDebug.pack_forget()
        debugTitle = tk.Label(frameDebug, text='Debug:', anchor='w', bg="darkgrey",
                              font=(PalEditConfig.font, PalEditConfig.ftsize), width=6, height=1)
        debugTitle.pack(fill=tk.constants.BOTH)
        self.storageId = tk.Label(frameDebug, text='StorageID: NULL', anchor='w', bg="darkgrey",
                                  font=(PalEditConfig.font, PalEditConfig.ftsize), width=6,
                                  height=1)
        self.storageId.pack(fill=tk.constants.BOTH)
        self.storageSlot = tk.Label(frameDebug, text='StorageSlot: NULL', anchor='w', bg="darkgrey",
                                    font=(PalEditConfig.font, PalEditConfig.ftsize), width=6,
                                    height=1)
        self.storageSlot.pack(fill=tk.constants.BOTH)
        button = tk.Button(frameDebug, text="Get Info", command=self.getSelectedPalInfo)
        button.config(font=(PalEditConfig.font, 12))
        button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        button = tk.Button(frameDebug, text="Copy Pal Data", command=self.getSelectedPalData)
        button.config(font=(PalEditConfig.font, 12))
        button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        button = tk.Button(frameDebug, text="Generate & Copy GUID", command=self.createGUIDtoClipboard)
        button.config(font=(PalEditConfig.font, 12))
        button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        button = Button(frameDebug, text="Add Pal", command=self.spawnpal)
        button.config(font=(PalEditConfig.font, 12))
        button.pack(side=LEFT, expand=True, fill=BOTH)
        button = Button(frameDebug, text="Dump Pal", command=self.dumppals)
        button.config(font=(PalEditConfig.font, 12))
        button.pack(side=LEFT, expand=True, fill=BOTH)

        # FOOTER
        frameFooter = tk.Frame(infoview, relief="flat")
        frameFooter.pack(fill=tk.constants.BOTH, expand=False)
        self.skilllabel = tk.Label(frameFooter, text="Hover a skill to see it's description")
        self.skilllabel.pack()

        # root.resizable(width=False, height=True)
        root.geometry("")  # auto window size
        self.updateWindowSize("true")
    
    def mainloop(self):
        self.gui.mainloop()

    def changeplayer(self, evt):
        print(self.current.get())
        self.updateDisplay()

    # center & window size
    def updateWindowSize(self, doCenter=""):
        root = self.gui
        root.update()
        window_height = root.winfo_reqheight()
        window_width = root.winfo_reqwidth()
        root.minsize(window_width, window_height)  # minwidth for better view
        if doCenter:
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            x_cordinate = int((screen_width / 2) - (window_width / 2))
            y_cordinate = int((screen_height / 2) - (window_height / 2))
            root.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
        else:
            root.geometry("{}x{}".format(window_width, window_height))

def main():
    pal = PalEdit()
    pal.gui.mainloop()

if __name__ == "__main__":
    main()