import os, webbrowser, json, time, uuid, math

# pyperclip
# docs: https://pypi.org/project/pyperclip/#description
# install: pip install pyperclip
import pyperclip

import SaveConverter
from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.archive import FArchiveReader, FArchiveWriter, UUID
from palworld_save_tools.json_tools import CustomEncoder
from palworld_save_tools.palsav import compress_gvas_to_sav, decompress_sav_to_gvas
from palworld_save_tools.paltypes import PALWORLD_CUSTOM_PROPERTIES, PALWORLD_TYPE_HINTS
import tkinter as tk
import copy

from PalInfo import *

from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def skip_decode(
        reader: FArchiveReader, type_name: str, size: int, path: str
):
    if type_name == "ArrayProperty":
        array_type = reader.fstring()
        value = {
            "skip_type": type_name,
            "array_type": array_type,
            "id": reader.optional_guid(),
            "value": reader.read(size)
        }
    elif type_name == "MapProperty":
        key_type = reader.fstring()
        value_type = reader.fstring()
        _id = reader.optional_guid()
        value = {
            "skip_type": type_name,
            "key_type": key_type,
            "value_type": value_type,
            "id": _id,
            "value": reader.read(size),
        }
    elif type_name == "StructProperty":
        value = {
            "skip_type": type_name,
            "struct_type": reader.fstring(),
            "struct_id": reader.guid(),
            "id": reader.optional_guid(),
            "value": reader.read(size),
        }
    else:
        raise Exception(
            f"Expected ArrayProperty or MapProperty or StructProperty, got {type_name} in {path}"
        )
    return value


def skip_encode(
        writer: FArchiveWriter, property_type: str, properties: dict
) -> int:
    if "skip_type" not in properties:
        if properties['custom_type'] in PALWORLD_CUSTOM_PROPERTIES is not None:
            # print("process parent encoder -> ", properties['custom_type'])
            return PALWORLD_CUSTOM_PROPERTIES[properties["custom_type"]][1](
                writer, property_type, properties
            )
        else:
            # Never be run to here
            return writer.property_inner(writer, property_type, properties)
    if property_type == "ArrayProperty":
        del properties["custom_type"]
        del properties["skip_type"]
        writer.fstring(properties["array_type"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    elif property_type == "MapProperty":
        del properties["custom_type"]
        del properties["skip_type"]
        writer.fstring(properties["key_type"])
        writer.fstring(properties["value_type"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    elif property_type == "StructProperty":
        del properties["custom_type"]
        del properties["skip_type"]
        writer.fstring(properties["struct_type"])
        writer.guid(properties["struct_id"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    else:
        raise Exception(
            f"Expected ArrayProperty or MapProperty or StructProperty, got {property_type}"
        )

PALEDIT_PALWORLD_CUSTOM_PROPERTIES = copy.deepcopy(PALWORLD_CUSTOM_PROPERTIES)
PALEDIT_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.MapObjectSaveData"] = (skip_decode, skip_encode)
PALEDIT_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.FoliageGridSaveDataMap"] = (skip_decode, skip_encode)
PALEDIT_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.MapObjectSpawnerInStageSaveData"] = (skip_decode, skip_encode)
PALEDIT_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.DynamicItemSaveData"] = (skip_decode, skip_encode)
PALEDIT_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.CharacterContainerSaveData"] = (skip_decode, skip_encode)
PALEDIT_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.ItemContainerSaveData"] = (skip_decode, skip_encode)
PALEDIT_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.GroupSaveDataMap"] = (skip_decode, skip_encode)

import traceback
class PalEditConfig:
    version = "0.6.1"
    ftsize = 18
    font = "Arial"
    badskill = "#DE3C3A"
    okayskill = "#DFE8E7"
    goodskill = "#FEDE00"

class PalEdit():
    ranks = (0, 1, 2, 3, 4)

    def load_i18n(self, lang=""):
        path = f"{module_dir}/resources/data/ui.json"
        if os.path.exists(f"{module_dir}/resources/data/ui_{lang}.json"):
            path = f"{module_dir}/resources/data/ui_{lang}.json"
        with open(path, "r", encoding="utf-8") as f:
            keys = json.load(f)
            for i18n_k in keys:     # For multi lang didn't translate with original one
                self.i18n[i18n_k] = keys[i18n_k]

        for item in self.i18n_el:
            if item in self.i18n:
                try:
                    if isinstance(self.i18n_el[item], ttk.Combobox):
                        index = self.i18n_el[item].current()
                        self.i18n_el[item]['values'] = self.i18n[item]
                        self.i18n_el[item].current(index)
                    elif isinstance(self.i18n_el[item], tuple):
                        if isinstance(self.i18n_el[item][0], tk.Menu):
                            self.i18n_el[item][0].entryconfigure(self.i18n_el[item][1], label=self.i18n[item])
                        else:
                            print("failed to edit to class ", type(self.i18n_el[item][0]))
                    else:
                        self.i18n_el[item].config(text=self.i18n[item])
                except Exception as e:
                    print("Fail to update i18n for %s" % item)
                    traceback.print_exception(e)
        LoadPals(lang)
        LoadAttacks(lang)
        LoadPassives(lang)
        self.attackops.clear()
        for e in PalInfo.PalAttacks:
            self.attackops.append(PalInfo.PalAttacks[e])
        self.attackops.remove("None")
        self.attackops.sort()
        self.attackops.insert(0, "None")

        op = [PalInfo.PalPassives[e] for e in PalInfo.PalPassives]
        op.pop(0)
        op.pop(0)
        op.sort()
        op.insert(0, "None")

        def atk_upd(menu, atk_id, idx, n):
            menu['menu'].entryconfigure(idx, label=n, command=tk._setit(self.attacks_name[atk_id], n,
                                                                        lambda evt: self.changeattack(atk_id)))

        for atk_id, menu in enumerate(self.attackdrops):
            for idx, n in enumerate(self.attackops):
                atk_upd(menu, atk_id, idx, n)

        def skill_upd(menu, skid, idx, n):
            menu['menu'].entryconfigure(idx, label=n, command=tk._setit(self.skills_name[skid], n, lambda evt:self.changeskill(skid)))

        for skid, menu in enumerate(self.skilldrops):
            for idx, n in enumerate(op):
                skill_upd(menu, skid, idx, n)

        self.updateAttackName()
        self.updateSkillsName()
        species = [PalInfo.PalSpecies[e].GetName() for e in PalInfo.PalSpecies]
        species.sort()
        try:
            for idx, n in enumerate(species):
                self.palname['menu'].entryconfigure(idx, label=n, command=tk._setit(self.speciesvar_name, n, self.changespeciestype))
            if self.speciesvar.get() in PalInfo.PalSpecies:
                self.speciesvar_name.set(PalInfo.PalSpecies[self.speciesvar.get()].GetName())
            else:
                self.speciesvar_name.set(self.speciesvar.get())
        except AttributeError as e:
            pass

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

        pal.CleanseAttacks()
        for a in range(0, 3):
            if a > len(pal.GetEquippedMoves()) - 1:
                self.attacks[a].set("None")
            else:
                self.attacks[a].set(pal.GetEquippedMoves()[a])
        self.setAttackCols()
        self.updateAttackName()

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

    def updateAttackName(self):
        for idx, n in enumerate(self.attacks):
            self.attacks_name[idx].set(PalInfo.PalAttacks[n.get()])

    def setpreset(self, preset):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        tid = []
        for v in range(0, 4):
            t = self.skills_name[v].trace_add("write", lambda *args, num=v: self.changeskill(num))
            tid.append(t)

        match preset:
            case "base":
                self.skills_name[0].set(PalInfo.PalPassives["CraftSpeed_up2"])
                self.skills_name[1].set(PalInfo.PalPassives["PAL_Sanity_Down_2"])
                self.skills_name[2].set(PalInfo.PalPassives["Rare"])
                self.skills_name[3].set(PalInfo.PalPassives["PAL_FullStomach_Down_2"])
            case "workspeed":
                self.skills_name[0].set(PalInfo.PalPassives["CraftSpeed_up2"])
                self.skills_name[1].set(PalInfo.PalPassives["CraftSpeed_up1"])
                self.skills_name[2].set(PalInfo.PalPassives["Rare"])
                self.skills_name[3].set(PalInfo.PalPassives["PAL_CorporateSlave"])
            case "movement":
                self.skills_name[0].set(PalInfo.PalPassives["MoveSpeed_up_3"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["MoveSpeed_up_2"])
                self.skills_name[3].set(PalInfo.PalPassives["MoveSpeed_up_1"])
            case "tank":
                self.skills_name[0].set(PalInfo.PalPassives["Deffence_up2"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["PAL_masochist"])
                self.skills_name[3].set(PalInfo.PalPassives["Deffence_up1"])
            case "dmg_max":
                self.skills_name[0].set(PalInfo.PalPassives["Noukin"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["PAL_ALLAttack_up2"])
                self.skills_name[3].set(PalInfo.PalPassives["Rare"])
            case "dmg_balanced":
                self.skills_name[0].set(PalInfo.PalPassives["Noukin"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["PAL_ALLAttack_up2"])
                self.skills_name[3].set(PalInfo.PalPassives["Deffence_up2"])
            case "dmg_mount":
                self.skills_name[0].set(PalInfo.PalPassives["Noukin"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["PAL_ALLAttack_up2"])
                self.skills_name[3].set(PalInfo.PalPassives["MoveSpeed_up_3"])
            case "dmg_element":
                primary = pal.GetPrimary().lower()
                secondary = pal.GetSecondary().lower()
                if primary == "none":
                    messagebox.showerror("Preset: Dmg: Element", "This pal has no elements! Preset skipped")
                    return
                self.skills_name[0].set(PalInfo.PalPassives["Noukin"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["PAL_ALLAttack_up2"])
                match primary:
                    case "neutral":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Normal_2_PAL"])
                    case "dark":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Dark_2_PAL"])
                    case "dragon":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Dragon_2_PAL"])
                    case "ice":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Ice_2_PAL"])
                    case "fire":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Fire_2_PAL"])
                    case "grass":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Leaf_2_PAL"])
                    case "ground":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Earth_2_PAL"])
                    case "electric":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Thunder_2_PAL"])
                    case "water":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Aqua_2_PAL"])
                    case _:
                        messagebox.showerror(f"Error: elemental was not found for preset: {primary}-{secondary}")

                # uncecessary msg
                # if not secondary == "none":
                #     messagebox.showerror(f"You pal has a second elemental - its probably better to use Dmg: Max preset")
            case _:
                print(f"Preset {preset} not found - nothing changed")
                return

        for v in range(0, 4):
            self.skills_name[v].trace_remove("write", tid[v])

        # exp (if level selected)
        if self.checkboxLevelVar.get() == 1:
            pal.SetLevel(self.textboxLevelVar.get())
        # rank (if rank selected)
        if self.checkboxRankVar.get() == 1:
            self.changerank(self.optionMenuRankVar.get())
        # attributes (if attributes selected)
        # TODO: change attributes

        self.refresh(i)

    def changerank(self, choice):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]
        ranks = {
            4: 5,
            3: 4,
            2: 3,
            1: 2,
        }
        new_rank = ranks.get(choice, 1)
        self.handleMaxHealthUpdates(pal, changes={
            'rank': new_rank
        })
        pal.SetRank(new_rank)
        self.refresh(i)

    def changeskill(self, num):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        index = list(PalInfo.PalPassives.values()).index(self.skills_name[num].get())
        self.skills[num].set(list(PalInfo.PalPassives.keys())[index])
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

        index = list(PalInfo.PalAttacks.values()).index(self.attacks_name[num].get())
        self.attacks[num].set(list(PalInfo.PalAttacks.keys())[index])
        if not self.attacks[num].get() in ["Unknown", "UNKNOWN"]:
            if self.attacks[num].get() in ["None", "NONE"]:
                pal.RemoveAttack(num)
            elif not self.attacks[num].get() in pal._equipMoves:
                pal.SetAttackSkill(num, self.attacks[num].get())

        self.updateAttackName()
        self.refresh(i)

    def onselect(self, evt):
        self.is_onselect = True
        w = evt.widget
        if not self.isPalSelected():
            self.portrait.config(image=self.purplepanda)
            return

        self.updatestats()

        index = int(w.curselection()[0])
        self.editindex = index

        pal = self.palbox[self.players[self.current.get()]][index]
        # palname.config(text=pal.GetName())
        self.speciesvar.set(pal.GetCodeName())
        self.speciesvar_name.set(pal.GetName())

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
        self.ranksvar.set(pal.GetRank() - 1)

        s = pal.GetSkills()[:]
        while len(s) < 4:
            s.append("NONE")

        for i in range(0, 4):
            if not s[i] in [p for p in PalInfo.PalPassives]:
                self.skills[i].set("Unknown")
            else:
                self.skills[i].set(s[i])

        pal.CleanseAttacks()
        self.updateSkillsName()
        self.setskillcolours()
        self.is_onselect = False


    def changetext(self, num):
        if num == -1:
            self.skilllabel.config(text=self.i18n['msg_skill'])
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
        self.skilllabel.config(text=self.i18n['msg_saving'])

        file = askopenfilename(initialdir=os.path.expanduser('~') + "\\AppData\\Local\\Pal\\Saved\\SaveGames",
                               filetypes=[("Level.sav", "Level.sav")])
        print(f"Opening file {file}")

        if file:
            self.filename = file
            self.gui.title(f"PalEdit v{PalEditConfig.version} - {file}")
            self.skilllabel.config(text=self.i18n['msg_decompressing'])
            with open(file, "rb") as f:
                data = f.read()
                raw_gvas, _ = decompress_sav_to_gvas(data)
            self.skilllabel.config(text=self.i18n['msg_loading'])
            gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, PALEDIT_PALWORLD_CUSTOM_PROPERTIES)
            self.loaddata(gvas_file)
            # self.doconvertjson(file, (not self.debug))
        else:
            messagebox.showerror(self.i18n['select_file'], self.i18n['msg_select_save_file'])

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

        messagebox.showinfo("Done", self.i18n['msg_done'])

    def loaddata(self, data):
        print(type(data))
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
                    traceback.print_exception(e)
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

        self.refresh()

    def savefile(self):
        self.skilllabel.config(text=self.i18n['msg_saving_big'])
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
                    gvas_file.write(PALEDIT_PALWORLD_CUSTOM_PROPERTIES), save_type
                )
                self.skilllabel.config(text=self.i18n['msg_writing'])
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


    def handleMaxHealthUpdates(self, pal: PalEntity, changes: dict):
        retval = pal.UpdateMaxHP(changes)
        if retval is not None:
            answer = messagebox.askquestion(
                title="Choose HP Scaling",
                message="""
Note:
- It is rare but some bosses may have different scaling data that I haven't yet added to PalEdit.
- I am using pal's original MaxHealth to derive the Guessed Scaling Value.

Warning:
- Guessed Scaling Value is different from the Non-Boss Scaling:
    - Derived: %s
    - Non-BOSS HP Scaling: %s
- This can be also caused by older version of PalEdit messing up the MaxHealth.
- Don't be worried, leveling up your pals in game can also fix this issue!

Do you want to use %s's DEFAULT Scaling (%s)?
""" % (retval[0], retval[1], pal.GetName(), retval[1]))
            pal.UpdateMaxHP(changes, hp_scaling=retval[1] if answer == 'yes' else retval[0])


    def updatestats(self):
        if not self.isPalSelected():
            return

        if self.editindex < 0:
            return

        pal = self.palbox[self.players[self.current.get()]][self.editindex]
        l = pal.GetLevel()

        if self.phpvar.dirty:
            self.phpvar.dirty = False
            h = self.phpvar.get()
            self.handleMaxHealthUpdates(pal, changes={
                'hp_iv': h
            })
            print(f"{pal.GetFullName()}: TalentHP {pal.GetTalentHP()} -> {h}")
            pal.SetTalentHP(h)
            # hv = 500 + (((70 * 0.5) * l) * (1 + (h / 100)))
            # self.hthstatval.config(text=math.floor(hv))
        if self.meleevar.dirty:
            self.meleevar.dirty = False
            a = self.meleevar.get()
            print(f"{pal.GetFullName()}: AttackMelee {pal.GetAttackMelee()} -> {a}")
            pal.SetAttackMelee(a)
            # av = 100 + (((70 * 0.75) * l) * (1 + (a / 100)))
            # self.atkstatval.config(text=math.floor(av))
        if self.shotvar.dirty:
            self.shotvar.dirty = False
            r = self.shotvar.get()
            print(f"{pal.GetFullName()}: AttackRanged {pal.GetAttackRanged()} -> {r}")
            pal.SetAttackRanged(r)
        if self.defvar.dirty:
            self.defvar.dirty = False
            d = self.defvar.get()
            print(f"{pal.GetFullName()}: Defence {pal.GetDefence()} -> {d}")
            pal.SetDefence(d)
            # dv = 50 + (((70 * 0.75) * l) * (1 + (d / 100)))
            # self.defstatval.config(text=math.floor(dv))
        if self.wspvar.dirty:
            self.wspvar.dirty = False
            w = self.wspvar.get()
            print(f"{pal.GetFullName()}: WorkSpeed {pal.GetWorkSpeed()} -> {w}")
            pal.SetWorkSpeed(w)


    def takelevel(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        if pal.GetLevel() == 1:
            return
        lv = pal.GetLevel() - 1
        self.handleMaxHealthUpdates(pal, changes={
            'level': lv
        })
        pal.SetLevel(lv)
        self.refresh(i)

    def givelevel(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        if pal.GetLevel() == 50:
            return
        lv = pal.GetLevel() + 1
        self.handleMaxHealthUpdates(pal, changes={
            'level': lv
        })
        pal.SetLevel(lv)
        self.refresh(i)

    def changespeciestype(self, evt):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        for item in PalInfo.PalSpecies:
            if PalInfo.PalSpecies[item].GetName() == self.speciesvar_name.get():
                self.speciesvar.set(item)
                break

        pal.SetType(self.speciesvar.get())
        self.handleMaxHealthUpdates(pal, changes={
            'species': self.speciesvar.get()
        })
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

        self.skilllabel.config(text=self.i18n['msg_converting'])

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
            messagebox.showerror(self.i18n['select_file'], self.i18n['msg_select_save_file'])
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
        self.loaddata(self.data)#['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'])

    def dumppals(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.palbox[self.players[self.current.get()]][i]

        pals = {}
        pals['Pals'] = [pal._data] #[pal._data for pal in self.palbox[self.players[self.current.get()]]]
        file = asksaveasfilename(filetypes=[("json files", "*.json")], defaultextension=".json")
        if file:
            with open(file, "wb") as f:
                f.write(json.dumps(pals, indent=4, cls=UUIDEncoder).encode('utf-8'))
        else:
            messagebox.showerror("Select a file", self.i18n['msg_select_file'])

    def doconvertjson(self, file, compress=False):
        SaveConverter.convert_sav_to_json(file, file.replace(".sav", ".sav.json"), True, compress)

        self.load(file.replace(".sav", ".sav.json"))

        self.changetext(-1)
        self.jump()
        # messagebox.showinfo("Done", "Done decompiling!")

    def converttosave(self):
        self.skilllabel.config(text=self.i18n['msg_converting'])

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

    def add_lang_menu(self, langmenu, languages, lang):
        langmenu.add_command(label=languages[lang], command=lambda: self.load_i18n(lang))

    def build_menu(self):
        self.menu = tk.Menu(self.gui)
        tools = self.menu
        self.gui.config(menu=tools)

        global filemenu
        filemenu = tk.Menu(tools, tearoff=0)
        filemenu.add_command(label=self.i18n['menu_load_save'], command=self.loadfile)
        self.i18n_el['menu_load_save'] = (filemenu, 0)
        filemenu.add_command(label=self.i18n['menu_save'], command=self.savefile)
        self.i18n_el['menu_save'] = (filemenu, 1)

        tools.add_cascade(label="File", menu=filemenu, underline=0)

        toolmenu = tk.Menu(tools, tearoff=0)
        toolmenu.add_command(label="Debug", command=self.toggleDebug)
        toolmenu.add_command(label="Generate GUID", command=self.generateguid)

        tools.add_cascade(label="Tools", menu=toolmenu, underline=0)

        langmenu = tk.Menu(tools, tearoff=0)
        with open(f"{module_dir}/resources/data/ui-lang.json", "r", encoding="utf-8") as f:
            languages = json.load(f)
            for lang in languages:
                self.add_lang_menu(langmenu, languages, lang)

        tools.add_cascade(label="Language", menu=langmenu, underline=0)

        # convmenu = Menu(tools, tearoff=0)
        # convmenu.add_command(label="Convert Save to Json", command=converttojson)
        # convmenu.add_command(label="Convert Json to Save", command=converttosave)

        # tools.add_cascade(label="Converter", menu=convmenu, underline=0)

    def updateSkillsName(self):
        for idx, n in enumerate(self.skills):
            self.skills_name[idx].set(PalInfo.PalPassives[n.get()])

    def __init__(self):
        global EmptyObjectHandler, PalInfo
        import EmptyObjectHandler
        import PalInfo

        self.i18n = {}
        self.i18n_el = {}
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
        self.is_onselect = False


        self.attacks = []
        self.attacks_name = []
        self.attackops = []
        self.attackdrops = []
        self.skilldrops = []
        self.skills = []
        self.skills_name = []
        self.load_i18n()

        self.purplepanda = tk.PhotoImage(master=self.gui, file=f'{module_dir}/resources/MossandaIcon.png')
        self.gui.iconphoto(True, self.purplepanda)

        root = self.gui

        self.current = tk.StringVar()
        self.current.set("")

        scrollview = tk.Frame(root)
        scrollview.pack(side=tk.constants.LEFT, fill=tk.constants.Y)

        self.build_menu()
        playerframe = tk.Frame(scrollview)
        playerframe.pack(fill=tk.constants.X)
        playerlbl = tk.Label(playerframe, text=self.i18n['player_lbl'])
        self.i18n_el['player_lbl'] = playerlbl
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
        atkLabel = tk.Label(atkskill, bg="darkgrey", width=12, text=self.i18n['atk_lbl'],
                            font=(PalEditConfig.font, PalEditConfig.ftsize),
                            justify="center")
        self.i18n_el['atk_lbl'] = atkLabel
        atkLabel.pack(fill=tk.constants.X)

        self.attacks = [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        self.attacks_name = [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        self.attacks[0].set("EPalWazaID::Unique_GrassPanda_Electric_ElectricPunch")
        self.attacks[1].set("EPalWazaID::ThreeThunder")
        self.attacks[2].set("EPalWazaID::DarkLaser")
        self.updateAttackName()

        equipFrame = tk.Frame(atkskill, borderwidth=2, relief="raised")
        equipFrame.pack(fill=tk.constants.X)

        self.attackdrops = [
            tk.OptionMenu(equipFrame, self.attacks_name[0], *self.attackops, command=lambda evt: self.changeattack(0)),
            tk.OptionMenu(equipFrame, self.attacks_name[1], *self.attackops, command=lambda evt: self.changeattack(1)),
            tk.OptionMenu(equipFrame, self.attacks_name[2], *self.attackops, command=lambda evt: self.changeattack(2))
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

        statLabel = tk.Label(stats, bg="darkgrey", width=12, text=self.i18n['stat_lbl'],
                             font=(PalEditConfig.font, PalEditConfig.ftsize), justify="center")
        statLabel.pack(fill=tk.constants.X)
        self.i18n_el['stat_lbl'] = statLabel

        statlbls = tk.Frame(stats, width=6, bg="darkgrey")
        statlbls.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.X)

        hthstatlbl = tk.Label(statlbls, bg="darkgrey", text=self.i18n['health_lbl'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                              justify="center")
        self.i18n_el['health_lbl'] = hthstatlbl
        hthstatlbl.pack()
        atkstatlbl = tk.Label(statlbls, bg="darkgrey", text=self.i18n['attack_lbl'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                              justify="center")
        self.i18n_el['attack_lbl'] = atkstatlbl
        atkstatlbl.pack()
        defstatlbl = tk.Label(statlbls, bg="darkgrey", text=self.i18n['defence_lbl'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                              justify="center")
        self.i18n_el['defence_lbl'] = atkstatlbl
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

        disclaim = tk.Label(atkskill, bg="darkgrey", text=self.i18n['msg_disclaim'],
                            font=(PalEditConfig.font, PalEditConfig.ftsize // 2))
        self.i18n_el['msg_disclaim'] = disclaim
        # disclaim.pack(fill=tk.constants.X)

        # Individual Info
        infoview = tk.Frame(root, relief="groove", borderwidth=2, width=480, height=480)
        infoview.pack(side=tk.constants.RIGHT, fill=tk.constants.BOTH, expand=True)

        dataview = tk.Frame(infoview)
        dataview.pack(side=tk.constants.TOP, fill=tk.constants.BOTH)

        resourceview = tk.Frame(dataview)
        resourceview.pack(side=tk.constants.LEFT, fill=tk.constants.BOTH, expand=True)

        self.portrait = tk.Label(resourceview, image=self.purplepanda, relief="sunken", borderwidth=2)
        self.portrait.pack()

        typeframe = tk.Frame(resourceview)
        typeframe.pack(expand=True, fill=tk.constants.X)
        self.ptype = tk.Label(typeframe, text=self.i18n['electric_lbl'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                              bg=PalInfo.PalElements["Electric"], width=6)
        self.i18n_el['electric_lbl'] = self.ptype
        self.ptype.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.X)
        self.stype = tk.Label(typeframe, text=self.i18n['dark_lbl'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                              bg=PalInfo.PalElements["Dark"], width=6)
        self.i18n_el['dark_lbl'] = self.stype
        self.stype.pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.X)

        formframe = tk.Frame(resourceview)
        formframe.pack(expand=True, fill=tk.constants.X)
        self.luckyvar = tk.IntVar()
        self.alphavar = tk.IntVar()
        luckybox = tk.Checkbutton(formframe, text=self.i18n['lucky_lbl'], variable=self.luckyvar, onvalue='1', offvalue='0',
                                  command=self.togglelucky)
        self.i18n_el['lucky_lbl'] = luckybox
        luckybox.pack(side=tk.constants.LEFT, expand=True)
        alphabox = tk.Checkbutton(formframe, text=self.i18n['alpha_lbl'], variable=self.alphavar, onvalue='1', offvalue='0',
                                  command=self.togglealpha)
        self.i18n_el['alpha_lbl'] = alphabox
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

        name = tk.Label(labelview, text=self.i18n['name_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize), bg="lightgrey")
        name.pack(expand=True, fill=tk.constants.X)
        self.i18n_el['name_prop'] = name
        gender = tk.Label(labelview, text=self.i18n['gender_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize), bg="lightgrey",
                          width=6, pady=6)
        self.i18n_el['gender_prop'] = gender
        gender.pack(expand=True, fill=tk.constants.X)
        attack = tk.Label(labelview, text=self.i18n['attack_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize), bg="lightgrey",
                          width=8)
        self.i18n_el['attack_prop'] = attack
        attack.pack(expand=True, fill=tk.constants.X)
        defence = tk.Label(labelview, text=self.i18n['defence_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                           bg="lightgrey", width=8)
        self.i18n_el['defence_prop'] = defence
        defence.pack(expand=True, fill=tk.constants.X)
        workspeed = tk.Label(labelview, text=self.i18n['workspeed_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                             bg="lightgrey", width=12)
        self.i18n_el['workspeed_prop'] = workspeed
        workspeed.pack(expand=True, fill=tk.constants.X)
        hp = tk.Label(labelview, text=self.i18n['hp_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize), bg="lightgrey",
                      width=10)
        self.i18n_el['hp_prop'] = hp
        hp.pack(expand=True, fill=tk.constants.X)
        rankspeed = tk.Label(labelview, text=self.i18n['rank_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize), bg="lightgrey")
        self.i18n_el['rank_prop'] = rankspeed
        rankspeed.pack(expand=True, fill=tk.constants.X)

        editview = tk.Frame(deckview)
        editview.pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.BOTH)

        species = [PalInfo.PalSpecies[e].GetName() for e in PalInfo.PalSpecies]
        species.sort()
        self.speciesvar = tk.StringVar()
        self.speciesvar_name = tk.StringVar()
        self.speciesvar_name.set("PalEdit")
        self.palname = tk.OptionMenu(editview, self.speciesvar_name, *species, command=self.changespeciestype)
        self.palname.config(font=(PalEditConfig.font, PalEditConfig.ftsize), padx=0, pady=0, borderwidth=1, width=5,
                       direction='right')
        self.palname.pack(expand=True, fill=tk.constants.X)

        genderframe = tk.Frame(editview, pady=0)
        genderframe.pack()
        self.palgender = tk.Label(genderframe, text="Unknown", font=(PalEditConfig.font, PalEditConfig.ftsize),
                                  fg=PalInfo.PalGender.UNKNOWN.value, width=10)
        self.palgender.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.X)
        swapbtn = tk.Button(genderframe, text="↺", borderwidth=1, font=(PalEditConfig.font, PalEditConfig.ftsize - 2),
                            command=self.swapgender)
        swapbtn.pack(side=tk.constants.RIGHT)

        def validate_and_mark_dirty(var, entry: tk.Entry):
            if self.is_onselect:
                return
            if entry.focus_get() != entry:
                return
            try:
                int(var.get())
            except TclError as e:
                var.dirty = False
                return

            clamp(var)
            var.dirty = True

        def clamp(var):
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

        def try_update(var, event=None):
            if not var.dirty:
                return
            if self.editindex < 0:
                return
            self.updatestats()


        valreg = root.register(ivvalidate)

        attackframe = tk.Frame(editview, width=6)
        attackframe.pack(fill=tk.constants.X)

        self.meleevar = tk.IntVar()
        self.meleevar.dirty = False
        self.meleevar.set(100)
##        meleeicon = tk.Label(attackframe, text="⚔", font=(PalEditConfig.font, PalEditConfig.ftsize))
##        meleeicon.pack(side=tk.constants.LEFT)
##        palmelee = tk.Entry(attackframe, textvariable=self.meleevar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
##        palmelee.config(justify="center", validate="all", validatecommand=(valreg, '%P'), state="disabled")
##        palmelee.bind("<FocusOut>", lambda event, var=self.meleevar: try_update(var))
##        palmelee.pack(side=tk.constants.LEFT)
##        self.meleevar.trace_add("write", lambda name, index, mode, sv=self.meleevar, entry=palmelee: validate_and_mark_dirty(sv, entry))


        self.shotvar = tk.IntVar()
        self.shotvar.dirty = False
        self.shotvar.set(100)
        #shoticon = tk.Label(attackframe, text="🏹", font=(PalEditConfig.font, PalEditConfig.ftsize))
        #shoticon.pack(side=tk.constants.RIGHT)
        palshot = tk.Entry(attackframe, textvariable=self.shotvar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        palshot.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palshot.bind("<FocusOut>", lambda event, var=self.shotvar: try_update(var))
        palshot.pack(fill=X)#side=tk.constants.RIGHT)
        self.shotvar.trace_add("write", lambda name, index, mode, sv=self.shotvar, entry=palshot: validate_and_mark_dirty(sv, entry))


        self.defvar = tk.IntVar()
        self.defvar.dirty = False
        self.defvar.set(100)
        paldef = tk.Entry(editview, textvariable=self.defvar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        paldef.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        paldef.bind("<FocusOut>", lambda event, var=self.defvar: try_update(var))
        paldef.pack(expand=True, fill=tk.constants.X)
        self.defvar.trace_add("write", lambda name, index, mode, sv=self.defvar, entry=paldef: validate_and_mark_dirty(sv, entry))


        self.wspvar = tk.IntVar()
        self.wspvar.dirty = False
        self.wspvar.set(70)
        palwsp = tk.Entry(editview, textvariable=self.wspvar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        palwsp.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palwsp.bind("<FocusOut>", lambda event, var=self.wspvar: try_update(var))
        palwsp.pack(expand=True, fill=tk.constants.X)
        self.wspvar.trace_add("write", lambda name, index, mode, sv=self.wspvar, entry=palwsp: validate_and_mark_dirty(sv, entry))


        def talent_hp_changed(*args):
            if not self.isPalSelected():
                return
            i = int(listdisplay.curselection()[0])
            pal = palbox[self.players[self.current.get()]][i]
            if talent_hp_var.get() == 0:
                talent_hp_var.set(1)
            # change value of pal

        self.phpvar = tk.IntVar()
        self.phpvar.dirty = False
        self.phpvar.set(50)
        palhps = tk.Entry(editview, textvariable=self.phpvar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        palhps.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palhps.bind("<FocusOut>", lambda event, var=self.phpvar: try_update(var))
        palhps.pack(expand=True, fill=tk.constants.X)
        self.phpvar.trace_add("write", lambda name, index, mode, sv=self.phpvar, entry=palhps: validate_and_mark_dirty(sv, entry))


        """
        talent_hp_var = IntVar(value=50)
        talent_hp_var.trace_add("write", lambda name, index, mode, sv=talent_hp_var: talent_hp_changed(clamp(sv)))
        # hpslider = Scale(editview, from_=0, to=100, tickinterval=50, orient='horizontal', variable=talent_hp_var)
        hpslider = Scale(editview, from_=0, to=100, orient='horizontal', variable=talent_hp_var)
        hpslider.config(width=9)
        hpslider.pack(pady=(0,10), expand=True, fill=tk.constants.X, anchor="center")
        """

        self.ranksvar = tk.IntVar()
        palrank = tk.OptionMenu(editview, self.ranksvar, *PalEdit.ranks, command=self.changerank)
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
        self.skills_name = [tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()]
        # for i in range(0, 4):
        # skills[i].set("Unknown")
        # skills[i].trace("w", lambda *args, num=i: changeskill(num))
        self.skills[0].set("Legend")
        self.skills[1].set("PAL_Sanity_Down_2")
        self.skills[2].set("PAL_ALLAttack_up2")
        self.skills[3].set("Rare")
        self.updateSkillsName()

        op = [PalInfo.PalPassives[e] for e in PalInfo.PalPassives]
        op.pop(0)
        op.pop(0)
        op.sort()
        op.insert(0, "None")
        self.skilldrops = [
            tk.OptionMenu(topview, self.skills_name[0], *op, command=lambda evt: self.changeskill(0)),
            tk.OptionMenu(topview, self.skills_name[1], *op, command=lambda evt: self.changeskill(1)),
            tk.OptionMenu(botview, self.skills_name[2], *op, command=lambda evt: self.changeskill(2)),
            tk.OptionMenu(botview, self.skills_name[3], *op, command=lambda evt: self.changeskill(3))
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
        presetTitle = tk.Label(framePresetsTitle, text=self.i18n['preset_lbl'], anchor='w', bg="darkgrey",
                               font=(PalEditConfig.font, PalEditConfig.ftsize), width=6,
                               height=1)
        presetTitle.pack(fill=tk.constants.BOTH)
        self.i18n_el['preset_lbl'] = presetTitle

        framePresetsButtons = tk.Frame(framePresets, relief="groove", borderwidth=4)
        framePresetsButtons.pack(fill=tk.constants.BOTH, expand=True)

        framePresetsButtons1 = tk.Frame(framePresetsButtons)
        framePresetsButtons1.pack(fill=tk.constants.BOTH, expand=True)
        preset_title1 = tk.Label(framePresetsButtons1, text=self.i18n['preset_title1'], anchor='e', bg="darkgrey",
                                 font=(PalEditConfig.font, 13),
                                 width=9)
        preset_title1.pack(side=tk.constants.LEFT, fill=tk.constants.X)
        self.i18n_el['preset_title1'] = preset_title1
        preset_button = tk.Button(framePresetsButtons1, text=self.i18n['preset_base'], command=lambda: self.setpreset("base"))
        self.i18n_el['preset_base'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons1, text=self.i18n['preset_speed_worker'],
                                  command=lambda: self.setpreset("workspeed"))
        self.i18n_el['preset_speed_worker'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons1, text=self.i18n['preset_speed_runner'], command=lambda: self.setpreset("movement"))
        self.i18n_el['preset_speed_runner'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons1, text=self.i18n['preset_tank'], command=lambda: self.setpreset("tank"))
        self.i18n_el['preset_tank'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)

        framePresetsButtons2 = tk.Frame(framePresetsButtons)
        framePresetsButtons2.pack(fill=tk.constants.BOTH, expand=True)
        preset_title2 = tk.Label(framePresetsButtons2, text=self.i18n['preset_title2'], anchor='e', bg="darkgrey",
                                 font=(PalEditConfig.font, 13),
                                 width=9)
        preset_title2.pack(side=tk.constants.LEFT, fill=tk.constants.X)
        self.i18n_el['preset_title2'] = preset_title2
        preset_button = tk.Button(framePresetsButtons2, text=self.i18n['preset_max'], command=lambda: self.setpreset("dmg_max"))
        self.i18n_el['preset_max'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons2, text=self.i18n['preset_balance'], command=lambda: self.setpreset("dmg_balanced"))
        self.i18n_el['preset_balance'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons2, text=self.i18n['preset_mount'], command=lambda: self.setpreset("dmg_mount"))
        self.i18n_el['preset_mount'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons2, text=self.i18n['preset_element'], command=lambda: self.setpreset("dmg_element"))
        self.i18n_el['preset_element'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)

        # PRESETS OPTIONS
        framePresetsExtras = tk.Frame(framePresets, relief="groove", borderwidth=4)
        framePresetsExtras.pack(fill=tk.constants.BOTH, expand=True)

        framePresetsLevel = tk.Frame(framePresetsExtras)
        framePresetsLevel.pack(fill=tk.constants.BOTH, expand=True)
        presetTitleLevel = tk.Label(framePresetsLevel, text=self.i18n['preset_title_level'], anchor='center', bg="lightgrey",
                                    font=(PalEditConfig.font, 13),
                                    width=20, height=1)
        presetTitleLevel.pack(side=tk.constants.LEFT, expand=False, fill=tk.constants.Y)
        self.i18n_el['preset_title_level'] = presetTitleLevel
        self.checkboxLevelVar = tk.IntVar()
        checkboxLevel = tk.Checkbutton(framePresetsLevel, text=self.i18n['preset_chg_lvl'], variable=self.checkboxLevelVar,
                                       onvalue='1',
                                       offvalue='0')
        checkboxLevel.pack(side=tk.constants.LEFT, expand=False, fill=tk.constants.BOTH)
        self.i18n_el['preset_chg_lvl'] = checkboxLevel
        self.textboxLevelVar = tk.IntVar(value=1)
        textboxLevel = tk.Entry(framePresetsLevel, textvariable=self.textboxLevelVar, justify='center', width=10)
        textboxLevel.config(font=(PalEditConfig.font, 10), width=10)
        textboxLevel.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.Y)

        framePresetsRank = tk.Frame(framePresetsExtras)
        framePresetsRank.pack(fill=tk.constants.BOTH, expand=True)
        presetTitleRank = tk.Label(framePresetsRank, text=self.i18n['preset_title_rank'], anchor='center', bg="lightgrey",
                                   font=(PalEditConfig.font, 13),
                                   width=20, height=1)
        presetTitleRank.pack(side=tk.constants.LEFT, expand=False, fill=tk.constants.Y)
        self.i18n_el['preset_title_rank'] = presetTitleRank
        self.checkboxRankVar = tk.IntVar()
        checkboxRank = tk.Checkbutton(framePresetsRank, text=self.i18n['preset_change_rank'], variable=self.checkboxRankVar,
                                      onvalue='1',
                                      offvalue='0')
        checkboxRank.pack(side=tk.constants.LEFT, expand=False, fill=tk.constants.BOTH)
        self.i18n_el['preset_change_rank'] = checkboxRank
        self.optionMenuRankVar = tk.IntVar(value=1)
        self.optionMenuRank = tk.OptionMenu(framePresetsRank, self.optionMenuRankVar, *PalEdit.ranks)
        self.optionMenuRankVar.set(PalEdit.ranks[0])
        self.optionMenuRank.config(font=(PalEditConfig.font, 10), width=5, justify='center')
        self.optionMenuRank.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.Y)

        framePresetsAttributes = tk.Frame(framePresetsExtras)
        framePresetsAttributes.pack(fill=tk.constants.BOTH, expand=False)
        presetTitleAttributes = tk.Label(framePresetsAttributes, text=self.i18n['preset_set_attr'], anchor='center',
                                         bg="lightgrey",
                                         font=(PalEditConfig.font, 13), width=20, height=1)
        presetTitleAttributes.pack(side=tk.constants.LEFT,
                                                                                                 expand=False,
                                                                                                 fill=tk.constants.Y)
        self.i18n_el['preset_set_attr'] = presetTitleAttributes
        self.checkboxAttributesVar = tk.IntVar()
        checkboxAttributes = tk.Checkbutton(framePresetsAttributes, text=self.i18n['preset_change_attr'],
                                            variable=self.checkboxAttributesVar, onvalue='1', offvalue='0')
        checkboxAttributes.pack(
            side=tk.constants.LEFT,
            expand=False,
            fill=tk.constants.BOTH)
        self.i18n_el['preset_change_attr'] = checkboxAttributes
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

        cloneLabel = tk.Label(atkskill, bg="darkgrey", width=12, text=self.i18n['clone_lbl'],
                            font=(PalEditConfig.font, PalEditConfig.ftsize),
                            justify="center")
        self.i18n_el['clone_lbl'] = cloneLabel
        cloneLabel.pack(fill=tk.constants.X)
        palframe = Frame(atkskill)
        palframe.pack(fill=X)
        button = Button(palframe, text="Add Pal", command=self.spawnpal)
        button.config(font=(PalEditConfig.font, 12))
        button.pack(side=LEFT, expand=True, fill=BOTH)
        button = Button(palframe, text="Dump Pal", command=self.dumppals)
        button.config(font=(PalEditConfig.font, 12))
        button.pack(side=LEFT, expand=True, fill=BOTH)

        # FOOTER
        frameFooter = tk.Frame(infoview, relief="flat")
        frameFooter.pack(fill=tk.constants.BOTH, expand=False)
        self.skilllabel = tk.Label(frameFooter, text=self.i18n['msg_skill'])
        self.skilllabel.pack()
        self.i18n_el['msg_skill'] = self.skilllabel

        # root.resizable(width=False, height=True)
        root.geometry("")  # auto window size
        self.updateWindowSize("true")

        def save_before_close():
            self.updatestats()
            root.destroy()
        root.protocol("WM_DELETE_WINDOW", save_before_close)

    def mainloop(self):
        self.gui.mainloop()


    def cleanup_pal_selection(self):
        # workaround so onselect no longer tries to get pals using pal[newplayer][oldindex]
        self.editindex = -1


    def changeplayer(self, evt):
        self.cleanup_pal_selection()
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
    global pal
    pal = PalEdit()
    pal.gui.mainloop()

if __name__ == "__main__":
    main()
