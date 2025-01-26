import os, webbrowser, json, time, uuid, math, zipfile

import pyperclip

import palworld_pal_edit.SaveConverter


from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.archive import FArchiveReader, FArchiveWriter, UUID
from palworld_save_tools.json_tools import CustomEncoder
from palworld_save_tools.palsav import compress_gvas_to_sav, decompress_sav_to_gvas
from palworld_save_tools.paltypes import PALWORLD_CUSTOM_PROPERTIES, PALWORLD_TYPE_HINTS
import tkinter as tk
import copy

import palworld_pal_edit.PalInfo as PalInfo
from palworld_pal_edit.PalEditLogger import *

from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox

from datetime import datetime

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
#PALEDIT_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.CharacterContainerSaveData"] = (skip_decode, skip_encode)
PALEDIT_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.ItemContainerSaveData"] = (skip_decode, skip_encode)
#PALEDIT_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.GroupSaveDataMap"] = (skip_decode, skip_encode)

import traceback


class PalEditConfig:
    version = "0.11.5"
    ftsize = 18
    font = "Microsoft YaHei"
    skill_col = ["#DE3C3A", "#DE3C3A", "#DE3C3A", "#000000", "#DFE8E7", "#DFE8E7", "#FEDE00", "#68FFD8"]
    levelcap = 60


class PalEdit():
    ranks = (0, 1, 2, 3, 4)
    debug_listPassivesSeen = set()

    def load_i18n(self, lang=""):
        path = f"{PalInfo.module_dir}/resources/data/en-GB/ui.json"
        if os.path.exists(f"{PalInfo.module_dir}/resources/data/{lang}/ui.json"):
            path = f"{PalInfo.module_dir}/resources/data/{lang}/ui.json"
        with open(path, "r", encoding="utf-8") as f:
            keys = json.load(f)
            for i18n_k in keys:  # For multi lang didn't translate with original one
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
        PalInfo.LoadPals(lang)
        PalInfo.LoadAttacks(lang)
        PalInfo.LoadPassives(lang)
        self.attackops = []
        for e in PalInfo.PalAttacks:
            self.attackops.append(PalInfo.PalAttacks[e])
        if "None" in self.attackops:
            self.attackops.remove("None")
        self.attackops.sort()
        self.attackops.insert(0, "None")

        # Skip the first load. And handle the situation where the user switches language before loading save.
        if hasattr(self, "listdisplay") and self.current.get() != "": 
            self.updateDisplay()
        
        self.updateSkillMenu()
        self.updateAttackName()
        self.updateSkillsName()
        species = [PalInfo.PalSpecies[e].GetName() for e in PalInfo.PalSpecies]
        species.sort()
        try:
            self.palname.config(values=species)
            #for idx, n in enumerate(species):
                #self.palname['menu'].entryconfigure(idx, label=n,
                                                    #command=tk._setit(self.speciesvar_name, n, self.changespeciestype))
            if self.speciesvar.get() in PalInfo.PalSpecies:
                self.speciesvar_name.set(PalInfo.PalSpecies[self.speciesvar.get()].GetName())
            else:
                self.speciesvar_name.set(self.speciesvar.get())
        except AttributeError as e:
            pass

    def updateSkillMenu(self):
        if not self.isPalSelected():
            return

        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        available_ops = pal.GetAvailableSkills()
        available_ops.insert(0, "None")
        print(available_ops)

        def atk_upd(menu, atk_id, label, codename):
            menu['menu'].add_command(label=label, command=tk._setit(self.attacks[atk_id], codename,
                                                                    lambda evt: self.changeattack(atk_id)))

        for atk_id, menu in enumerate(self.attackdrops):
            while menu['menu'].index("end") is not None:
                menu['menu'].delete(0)
            for idx, codename in enumerate(available_ops):
                atk_upd(menu, atk_id, PalInfo.PalAttacks[codename], codename)

        op = [PalInfo.PalPassives[e] for e in PalInfo.PalPassives]
        if "None" in op:
            op.remove("None")
        if "Unknown" in op:
            op.remove("Unknown")
        op.sort()
        op.insert(0, "None")

        def skill_upd(menu, skid, idx, n):
            menu['menu'].entryconfigure(idx, label=n, command=tk._setit(self.skills_name[skid], n,
                                                                        lambda evt: self.changeskill(skid)))

        for skid, menu in enumerate(self.skilldrops):
            for idx, n in enumerate(op):
                skill_upd(menu, skid, idx, n)

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
        if len(self.FilteredPals()) == 0:
            return False
        if len(self.listdisplay.curselection()) == 0:
            return False
        return True

    def getSelectedPalInfo(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]
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
        pal = self.FilteredPals()[i]
        # print(f"Get Data: {pal.GetNickname()}")
        # print(f"{pal._obj}")
        pyperclip.copy(f"{pal._obj}")
        webbrowser.open('https://jsonformatter.curiousconcept.com/#')

    def updateAttacks(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]
        self.attackops = [PalInfo.PalAttacks[e] for e in PalInfo.PalAttacks].sort()

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
        pal = self.FilteredPals()[i]

        tid = []
        for v in range(0, 4):
            t = self.skills_name[v].trace_add("write", lambda *args, num=v: self.changeskill(num))
            tid.append(t)

        match preset:
            case "base":
                self.skills_name[0].set(PalInfo.PalPassives["CraftSpeed_up3"])
                self.skills_name[1].set(PalInfo.PalPassives["PAL_Sanity_Down_3"])
                self.skills_name[2].set(PalInfo.PalPassives["CraftSpeed_up2"])
                self.skills_name[3].set(PalInfo.PalPassives["PAL_FullStomach_Down_3"])
            case "workspeed":
                self.skills_name[0].set(PalInfo.PalPassives["CraftSpeed_up3"])
                self.skills_name[1].set(PalInfo.PalPassives["CraftSpeed_up2"])
                self.skills_name[2].set(PalInfo.PalPassives["CraftSpeed_up1"])
                self.skills_name[3].set(PalInfo.PalPassives["PAL_CorporateSlave"])
            case "movement":
                self.skills_name[0].set(PalInfo.PalPassives["MoveSpeed_up_3"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["MoveSpeed_up_2"])
                self.skills_name[3].set(PalInfo.PalPassives["MoveSpeed_up_1"])
            case "tank":
                self.skills_name[0].set(PalInfo.PalPassives["Deffence_up3"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["Deffence_up2"])
                self.skills_name[3].set(PalInfo.PalPassives["PAL_masochist"])
            case "dmg_max":
                self.skills_name[0].set(PalInfo.PalPassives["PAL_ALLAttack_up3"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["PAL_ALLAttack_up2"])
                self.skills_name[3].set(PalInfo.PalPassives["Noukin"])
            case "dmg_balanced":
                self.skills_name[0].set(PalInfo.PalPassives["PAL_ALLAttack_up3"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["PAL_ALLAttack_up2"])
                self.skills_name[3].set(PalInfo.PalPassives["Deffence_up2"])
            case "dmg_mount":
                self.skills_name[0].set(PalInfo.PalPassives["Stamina_Up_3"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["PAL_ALLAttack_up3"])
                self.skills_name[3].set(PalInfo.PalPassives["MoveSpeed_up_3"])
            case "dmg_element":
                primary = pal.GetPrimary().lower()
                secondary = pal.GetSecondary().lower()
                if primary == "none":
                    messagebox.showerror("Preset: Dmg: Element", "This pal has no elements! Preset skipped")
                    return
                self.skills_name[0].set(PalInfo.PalPassives["PAL_ALLAttack_up3"])
                self.skills_name[1].set(PalInfo.PalPassives["Legend"])
                self.skills_name[2].set(PalInfo.PalPassives["PAL_ALLAttack_up2"])
                match primary:
                    case "normal":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Normal_2_PAL"])
                    case "dark":
                        self.skills_name[3].set(PalInfo.PalPassives["Witch"])
                    case "dragon":
                        self.skills_name[3].set(PalInfo.PalPassives["Invader"])
                    case "ice":
                        self.skills_name[3].set(PalInfo.PalPassives["Witch"])
                    case "fire":
                        self.skills_name[3].set(PalInfo.PalPassives["EternalFlame"])
                    case "leaf":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Leaf_2_PAL"])
                    case "earth":
                        self.skills_name[3].set(PalInfo.PalPassives["ElementBoost_Earth_2_PAL"])
                    case "electricity":
                        self.skills_name[3].set(PalInfo.PalPassives["EternalFlame"])
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
        pal = self.FilteredPals()[i]
        ranks = {
            4: 5,
            3: 4,
            2: 3,
            1: 2,
        }
        new_rank = ranks.get(choice, 1)
        pal.SetRank(new_rank)
        self.handleMaxHealthUpdates(pal)
        self.refresh(i)

    def changeskill(self, num):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

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
        pal = self.FilteredPals()[i]

        pal.PurgeAttack(num)
        # index = list(PalInfo.PalAttacks.values()).index(self.attacks_name[num].get())
        # self.attacks[num].set(list(PalInfo.PalAttacks.keys())[index])
        if not self.attacks[num].get() in ["Unknown", "UNKNOWN"]:
            if self.attacks[num].get() in ["None", "NONE"]:
                pal.RemoveAttack(num)
            elif not self.attacks[num].get() in pal._equipMoves:
                pal.SetAttackSkill(num, self.attacks[num].get())

        self.updateAttacks()
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

        pal = self.FilteredPals()[index]

        # All Entities
        self.speciesvar.set(pal.GetCodeName())
        self.speciesvar_name.set(PalInfo.PalSpecies[self.speciesvar.get()].GetName())

        self.debugTitle.config(text=f"Debug: {pal.GetPalInstanceGuid()}")
        self.storageId.config(text=f"StorageID: {pal.GetSlotGuid()}")
        self.storageSlot.config(text=f"StorageSlot: {pal.GetSlotIndex()}")

        self.portrait.config(image=pal.GetImage())

        # palname.config(text=pal.GetName())

        g = pal.GetGender()
        self.palgender.config(text=g,
                              fg=PalInfo.PalGender.MALE.value if g == "Male ♂" else PalInfo.PalGender.FEMALE.value)

        self.title.config(text=f"{pal.GetNickname()}")
        self.level.config(text=f"Lv. {pal.GetLevel() if pal.GetLevel() > 0 else '?'}")

        self.fruitOptions['values'] = [PalInfo.PalAttacks[aval] for aval in pal.GetAvailableSkills()]

        p = 0
        self.learntMoves.delete(0, tk.constants.END)
        for i in pal._learntMoves:
            an = PalInfo.PalAttacks[i]
            

            if i in PalInfo.AttackCats:
                ct = PalInfo.AttackCats[i]
                match ct:
                    case "Melee":
                        an += '⚔'
                    case "Shot":
                        an += '🏹'
            if i in pal._equipMoves:
                self.learntMoves.insert(0, an)
                self.learntMoves.itemconfig(0, {'bg': 'lightgrey'})
                p += 1
            elif i in PalInfo.PalLearnSet[pal.GetCodeName()]:
                if PalInfo.PalLearnSet[pal.GetCodeName()][i] <= pal.GetLevel():
                    if not i in pal._equipMoves:
                        self.learntMoves.insert(p, an)
                        self.learntMoves.itemconfig(p, {'bg': 'darkgrey'})
            else:
                self.learntMoves.insert(tk.constants.END, an)

        
        
        self.ptype.config(text=self.i18n[f'{pal.GetPrimary().lower()}_lbl'], bg=PalInfo.PalElements[pal.GetPrimary()])
        self.stype.config(text=self.i18n[f'{pal.GetSecondary().lower()}_lbl'], bg=PalInfo.PalElements[pal.GetSecondary()])

        # ⚔🏹
        # talent_hp_var.set(pal.GetTalentHP())
        self.phpvar.set(pal.GetTalentHP())
        self.meleevar.set(pal.GetAttackMelee())
        self.shotvar.set(pal.GetAttackRanged())
        self.defvar.set(pal.GetDefence())
        #self.wspvar.set(pal.GetWorkSpeed())

        self.luckyvar.set(pal.isLucky)
        self.alphavar.set(pal.isBoss)

        self.updateSkillMenu()
        self.updateAttacks()

        if not pal.IsHuman():
            
            pt = pal.GetType()


            for i in suitabilities:
                pp = pal.GetSuit(i)
                sp = pt._suits[i]
                tp = pp + sp
                self.suits[f"{i}_var"].set(tp)
                c = "#55FF55" if tp > sp else "#D3D3D3"
                self.suits[f"{i}_label"].config(state=(tk.NORMAL if sp > 0 else tk.DISABLED), from_=sp, bg=c)
                #self.suits[f"{i}_label"].config(text=tp, bg=c)

            calc = pal.CalculateIngameStats()
            self.hthstatval.config(text=calc["HP"])
            self.matkstatval.config(text=calc["PHY"])
            self.satkstatval.config(text=calc["MAG"])
            self.defstatval.config(text=calc["DEF"])
        else:
            
            for i in suitabilities:
                self.suits[f"{i}_var"].set(0)
                self.suits[f"{i}_label"].config(state=tk.DISABLED, bg="#D3D3D3")

            self.hthstatval.config(text="n/a")
            self.matkstatval.config(text="n/a")
            self.satkstatval.config(text="n/a")
            self.defstatval.config(text="n/a")

        if pal.IsHuman() or pal.IsTower():
            self.alphabox.config(state=tk.DISABLED)
            self.luckybox.config(state=tk.DISABLED)

            self.luckyvar.set(0)
            self.alphavar.set(0)

            pal.SetLucky(False)
            pal.SetBoss(False)
        else:
            self.alphabox.config(state=tk.NORMAL)
            self.luckybox.config(state=tk.NORMAL)

        # rank
        self.ranksvar.set(pal.GetRank() - 1)
        self.hpsoulvar.set(pal.GetRankHP())
        self.atsoulvar.set(pal.GetRankAttack())
        self.dfsoulvar.set(pal.GetRankDefence())
        self.wssoulvar.set(pal.GetRankWorkSpeed())

        s = pal.GetSkills()[:]
        while len(s) < 4:
            s.append("NONE")

        for i in range(0, 4):
            if not s[i] in [p for p in PalInfo.PalPassives]:
                self.skills[i].set("UNKNOWN")
                self.debug_listPassivesSeen.add(s[i])
                print(self.debug_listPassivesSeen)
            else:
                self.skills[i].set(s[i])

        pal.CleanseAttacks()
        self.updateSkillsName()
        self.setskillcolours()
        self.is_onselect = False

    def setsuits(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        pt = pal.GetType()

        for i in suitabilities:

            pp = self.suits[f"{i}_var"].get() #pal.GetSuit(suit)
            sp = pt._suits[i]
            pp = pp - sp
            tp = pp + sp
            c = "#55FF55" if tp > sp else "#D3D3D3"
            self.suits[f"{i}_label"].config(bg=c)

            pal.SetSuit(i, pp)

            

    def changetext(self, num):
        if num == -1:
            self.skilllabel.config(text=self.i18n['msg_skill'])
            return

        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

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
        logger.info(f"Opening file {file}")

        if file:
            self.filename = file
            self.gui.title(f"PalEdit v{PalEditConfig.version} - {file}")
            self.skilllabel.config(text=self.i18n['msg_decompressing'])
            with open(file, "rb") as f:
                data = f.read()
                raw_gvas, _ = decompress_sav_to_gvas(data)
            self.skilllabel.config(text=self.i18n['msg_loading'])
            
            try:
                gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, PALEDIT_PALWORLD_CUSTOM_PROPERTIES)
                self.loaddata(gvas_file)
            except Exception as e:
                self.logerror(str(e))           
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
        self.palguidmanager = PalInfo.PalGuid(self.data)
        self.loadpal(paldata)

    def loadpal(self, paldata):
        logger.Space()
        self.palbox = []
        self.players = {}
        self.players = self.palguidmanager.GetPlayerslist()
        print(self.players)
        for p in self.players:
            playerguid = self.players[p]
            playersav = os.path.dirname(self.filename) + f"/Players/{str(playerguid).upper().replace('-', '')}.sav"
            self.players[p] = PalInfo.PalPlayerEntity(palworld_pal_edit.SaveConverter.convert_sav_to_obj(playersav))
        self.containers = {}
        nullmoves = []

        self.unknown = []
        erroredpals = []
        for i in paldata:
            try:
                p = PalInfo.PalEntity(i)
                self.palbox.append(p)

                n = p.GetFullName()

                for m in p.GetLearntMoves():
                    if not m in nullmoves:
                        if not m in PalInfo.PalAttacks:
                            nullmoves.append(m)
            except Exception as e:
                if str(e) == "This is a player character":
                    logger.debug(f"Found Player Character")
                    # print(f"\nDebug: Data \n{i}\n\n")
                    # o = i['value']['RawData']['value']['object']['SaveParameter']['value']
                    # pl = "No Name"
                    # if "NickName" in o:
                    #     pl = o['NickName']['value']
                    # plguid = i['key']['PlayerUId']['value']
                    # print(f"{pl} - {plguid}")
                    # self.players[pl] = plguid
                else:
                    self.unknown.append(str(e))
                    try:
                        erroredpals.append(i)
                    except:
                        erroredpals.append(None)
                    logger.error(f"Error occured on {i['key']['InstanceId']['value']}", exc_info=True)
                    # print(f"Error occured on {i['key']['InstanceId']['value']}: {e.__class__.__name__}: {str(e)}")
                    # traceback.print_exception(e)
                    print()
                # print(f"Debug: Data {i}")

        self.current.set(next(iter(self.players)))
        logger.info(f"Defaulted selection to {self.current.get()}")

        self.updateDisplay()

        logger.Space()
        logger.info(f"NOTE: Unknown list is a list of pals that could not be loaded")
        logger.warning(f"Unknown list contains {len(self.unknown)} entries")
        for i in range(0, len(self.unknown)):
            logger.warning("  %s" % str(self.unknown[i]))
            with open(f"pals/error_{i}.json", "wb") as errorfile:
                errorfile.write(json.dumps(erroredpals[i], indent=4, cls=UUIDEncoder).encode('utf-8'))
            

        logger.Space()
        logger.debug(f"{len(self.players)} players found:")
        for i in self.players:
            logger.debug(f"{i} = {self.players[i]}")
        self.playerdrop['values'] = list(self.players.keys())
        self.playerdrop.current(0)
        logger.Space()

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
        self.enable_menus()


    def jump(self):
        self.gui.attributes('-topmost', 1)
        self.gui.attributes('-topmost', 0)
        self.gui.focus_force()
        self.gui.bell()

    def updateDisplay(self):
        self.listdisplay.delete(0, tk.constants.END)
        currentguid = self.players[self.current.get()].GetPlayerGuid()

        self.playerguid.config(text=currentguid)
        
        print("Filter", self.FilteredPals())
        pals = self.FilteredPals()

        for p in pals:
            self.listdisplay.insert(tk.constants.END, p.GetFullName())

            if p.isBoss:
                self.listdisplay.itemconfig(tk.constants.END, {'fg': 'red'})
            elif p.isLucky:
                self.listdisplay.itemconfig(tk.constants.END, {'fg': 'blue'})

        self.refresh()

    def logerror(self, msg):
        logger.WriteLog(msg)
        messagebox.showinfo("Error", "There was an error! Your save may have issues or the tool is unable to process it. Upload your log.txt file to the support channel in our discord and ask for help.")

    def savefile(self):
        self.skilllabel.config(text=self.i18n['msg_saving_big'])
        self.gui.update()

        if self.isPalSelected():
            i = int(self.listdisplay.curselection()[0])
            self.refresh(i)

        file = self.filename
        # print(file, self.filename)
        if file:
            logger.info(f"Opening file {file}")
            try:
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
            except Exception as e:
                self.logerror(str(e))

            self.changetext(-1)
            self.jump()
            messagebox.showinfo("Done", "Done saving!")
            self.resetTitle()
            self.disable_menus()


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

    def handleMaxHealthUpdates(self, pal: PalInfo.PalEntity):#, changes: dict):
        if not pal.IsTower() and not pal.IsHuman():
            pal.UpdateMaxHP()

    def OLD_handleMaxHealthUpdates(self, pal: PalInfo.PalEntity, changes: dict):
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

    def FilteredPals(self):
        def GetMyPals(item):
            player = self.players[self.current.get()]

            if item.owner == player.GetTravelPalInventoryGuid():
                return True
            if item.owner == player.GetPalStorageGuid():
                return True
            return False

        filtered = filter(GetMyPals, self.palbox)
        filterlist = list(filtered)

        filterlist.sort(key=lambda e: e.GetName())
        
        return filterlist

    def updatestats(self):
        if not self.isPalSelected():
            return

        if self.editindex < 0:
            return


        pal = self.FilteredPals()[self.editindex]
        l = pal.GetLevel()

        if self.phpvar.dirty:
            self.phpvar.dirty = False
            h = self.phpvar.get()
            pal.SetTalentHP(h)
            self.handleMaxHealthUpdates(pal)
            print(f"{pal.GetFullName()}: TalentHP {pal.GetTalentHP()} -> {h}")
            
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

        if not pal.IsTower() and not pal.IsHuman():
            calc = pal.CalculateIngameStats()
            self.hthstatval.config(text=calc["HP"])
            self.matkstatval.config(text=calc["PHY"])
            self.satkstatval.config(text=calc["MAG"])
            self.defstatval.config(text=calc["DEF"])


    def takelevel(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        if pal.GetLevel() == 1:
            return
        lv = pal.GetLevel() - 1
        pal.SetLevel(lv)
        self.handleMaxHealthUpdates(pal)
        self.refresh(i)

    def givelevel(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        if pal.GetLevel() == PalEditConfig.levelcap:
            return
        lv = pal.GetLevel() + 1
        pal.SetLevel(lv)
        self.handleMaxHealthUpdates(pal)
        self.refresh(i)

    def changespeciestype(self, evt):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        for item in PalInfo.PalSpecies:
            if PalInfo.PalSpecies[item].GetName() == self.speciesvar_name.get():
                self.speciesvar.set(item)
                break

        pal.SetType(self.speciesvar.get())
        self.handleMaxHealthUpdates(pal)
        self.updateDisplay()
        self.refresh(self.FilteredPals().index(pal))

    def setskillcolours(self):
        for snum in range(0, 4):
            rating = PalInfo.PassiveRating[self.skills[snum].get()]
            col = PalEditConfig.skill_col[int(rating)+3]

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
        logger.info(f"Opening file {file}")

        self.doconvertjson(file)

    def spawnpal(self):
        print(self.palguidmanager)
        if not self.isPalSelected() or self.palguidmanager is None:
            return

        
        
        playerguid = self.players[self.current.get()].GetPlayerGuid()
        playersav = os.path.dirname(self.filename) + f"/Players/{str(playerguid).upper().replace('-', '')}.sav"
        if not os.path.exists(playersav):
            print("Cannot Load Player Save!")
            return
        player = PalInfo.PalPlayerEntity(palworld_pal_edit.SaveConverter.convert_sav_to_obj(playersav))
        palworld_pal_edit.SaveConverter.convert_obj_to_sav(player.dump(), playersav + ".bak", True)

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
            pal = PalInfo.PalEntity(p)
            i = self.palguidmanager.GetEmptySlotIndex(slotguid)
            if i == -1:
                print("Player Pal Storage is full!")
                return

            owneruid = "00000000-0000-0000-0000-000000000000"
            if pal.GetOwner() != owneruid:
                owneruid = playerguid
            
            pal.InitializationPal(newguid, playerguid, groupguid, slotguid, owneruid)
            pal.SetSoltIndex(i)
            self.palguidmanager.AddGroupSaveData(groupguid, newguid)
            self.palguidmanager.SetContainerSave(slotguid, i, newguid)
            self.data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'].append(pal._data)
            print(f"Add Pal at slot {i} : {slotguid}")
        self.loaddata(self.data)  # ['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'])

    def dumppals(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        pals = {}
        pals['Pals'] = [pal._data]  # [pal._data for pal in self.FilteredPals()]
        file = asksaveasfilename(filetypes=[("json files", "*.json")], defaultextension=".json")
        if file:
            with open(file, "wb") as f:
                f.write(json.dumps(pals, indent=4, cls=UUIDEncoder).encode('utf-8'))
        else:
            messagebox.showerror("Select a file", self.i18n['msg_select_file'])

    def clonepal(self):
        if not self.isPalSelected() or self.palguidmanager is None:
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        owneruid = "00000000-0000-0000-0000-000000000000"
 

        with open("temp.json", "wb") as f:
            f.write(json.dumps(pal._data, indent=4, cls=UUIDEncoder).encode('utf-8'))

        f = open("temp.json", "r", encoding="utf8")
        spawnpaldata = json.loads(f.read())
        f.close()

        playerguid = self.players[self.current.get()].GetPlayerGuid()
        playersav = os.path.dirname(self.filename) + f"/Players/{str(playerguid).upper().replace('-', '')}.sav"
        if not os.path.exists(playersav):
            print("Cannot Load Player Save!")
            return
        player = PalInfo.PalPlayerEntity(palworld_pal_edit.SaveConverter.convert_sav_to_obj(playersav))
        palworld_pal_edit.SaveConverter.convert_obj_to_sav(player.dump(), playersav + ".bak", True)

        slotguid = str(player.GetPalStorageGuid())
        groupguid = self.palguidmanager.GetGroupGuid(playerguid)
        if any(guid == None for guid in [slotguid, groupguid]):
            return

        newguid = str(uuid.uuid4())
        pal = PalInfo.PalEntity(spawnpaldata)
        i = self.palguidmanager.GetEmptySlotIndex(slotguid)
        if i == -1:
            print("Player Pal Storage is full!")
            return
        print(playerguid)

        if pal.GetOwner() != owneruid:
            owneruid = playerguid
        
        pal.InitializationPal(newguid, playerguid, groupguid, slotguid, owneruid)
        pal.SetSoltIndex(i)
        self.palguidmanager.AddGroupSaveData(groupguid, newguid)
        self.palguidmanager.SetContainerSave(slotguid, i, newguid)
        self.data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'].append(pal._data)
        print(f"Add Pal at slot {i} : {slotguid}")
        self.loaddata(self.data)

        os.remove("temp.json")

    def deletepal(self):
        if not self.isPalSelected() or self.palguidmanager is None:
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        s = pal.GetSlotIndex()

        playerguid = self.players[self.current.get()].GetPlayerGuid()
        playersav = os.path.dirname(self.filename) + f"/Players/{str(playerguid).upper().replace('-', '')}.sav"
        if not os.path.exists(playersav):
            print("Cannot Load Player Save!")
            return
        player = PalInfo.PalPlayerEntity(palworld_pal_edit.SaveConverter.convert_sav_to_obj(playersav))
        palworld_pal_edit.SaveConverter.convert_obj_to_sav(player.dump(), playersav + ".bak", True)

        slotguid = str(player.GetPalStorageGuid())
        palguid = pal.GetPalInstanceGuid()

        groupguid = self.palguidmanager.GetGroupGuid(playerguid)
        if any(guid == None for guid in [slotguid, groupguid]):
            return

        self.palguidmanager.RemovePal(slotguid, s, "0")
        self.palguidmanager.RemoveGroupSaveData(groupguid, palguid)
        self.data['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value'].remove(pal._data)
        
        self.loaddata(self.data)

        
        
    def doconvertjson(self, file, compress=False):
        SaveConverter.convert_sav_to_json(file, file.replace(".sav", ".sav.json"), True, compress)

        self.load(file.replace(".sav", ".sav.json"))

        self.changetext(-1)
        self.jump()
        # messagebox.showinfo("Done", "Done decompiling!")

    def converttosave(self):
        self.skilllabel.config(text=self.i18n['msg_converting'])

        file = askopenfilename(filetypes=[("All files", "*.sav.json")])
        logger.info(f"Opening file {file}")

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
        pal = self.FilteredPals()[i]

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
        pal = self.FilteredPals()[i]

        if self.luckyvar.get() == 1 and self.alphavar.get() == 1:
            self.alphavar.set(0)

        pal.SetLucky(True if self.luckyvar.get() == 1 else False)
        self.replaceitem(i, pal)
        self.refresh(i)

    def togglealpha(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        if self.luckyvar.get() == 1 and self.alphavar.get() == 1:
            self.luckyvar.set(0)

        pal.SetBoss(True if self.alphavar.get() == 1 else False)
        self.replaceitem(i, pal)
        self.refresh(i)

    def stripMove(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        m = self.learntMoves.curselection()

        if len(m) > 0:
            m = self.learntMoves.get(int(m[0])).replace("⚔","").replace("🏹","")
            pal.StripAttack(PalInfo.find(m))
            self.refresh(i)

    def appendMove(self):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]

        pal.FruitAttack(PalInfo.find(self.fruitPicker.get()))
        self.refresh(i)

    def createWindow(self):
        root = tk.Tk()
        return root

    def resetTitle(self):
        self.gui.title(f"PalEdit v{PalEditConfig.version}")

    def add_lang_menu(self, langmenu, lang):
        if lang in ["pals", "attacks"]: return
        with open(f"{PalInfo.module_dir}/resources/data/{lang}/ui.json", "r", encoding="utf-8") as f:
            content = json.load(f)
            l = content["language"]
        langmenu.add_command(label=l, command=lambda: self.load_i18n(lang))

    def disable_menus(self):
        filemenu.entryconfig(self.i18n['menu_save'], state="disabled")
        filemenu.entryconfig(self.i18n['menu_export'], state="disabled")
        filemenu.entryconfig(self.i18n['menu_import'], state="disabled")

    def enable_menus(self):
        filemenu.entryconfig(self.i18n['menu_save'], state="normal")
        filemenu.entryconfig(self.i18n['menu_export'], state="normal")
        filemenu.entryconfig(self.i18n['menu_import'], state="normal")

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

        filemenu.add_separator()        
        filemenu.add_command(label=self.i18n['menu_export'], command=self.dumppals)
        self.i18n_el['menu_export'] = (filemenu, 3)
        filemenu.add_command(label=self.i18n['menu_import'], command=self.spawnpal)
        self.i18n_el['menu_import'] = (filemenu, 4)

        self.disable_menus()

        tools.add_cascade(label="File", menu=filemenu, underline=0)

        toolmenu = tk.Menu(tools, tearoff=0)
        toolmenu.add_command(label="Debug", command=self.toggleDebug)
        toolmenu.add_command(label="Generate GUID", command=self.generateguid)

        tools.add_cascade(label="Tools", menu=toolmenu, underline=0)

        langmenu = tk.Menu(tools, tearoff=0)
        langops = next(os.walk(f"{PalInfo.module_dir}/resources/data"))
        langops = [x for x in langops[1]]
        #with open(f"{PalInfo.module_dir}/resources/data/ui-lang.json", "r", encoding="utf-8") as f:
            #languages = json.load(f)
            #for lang in languages:
                #self.add_lang_menu(langmenu, languages, lang)

        for lang in langops:
            self.add_lang_menu(langmenu, lang)


        def installlang():
            file = askopenfilename(filetypes=[("Zip files", "*.zip")])
            if file:
                with zipfile.ZipFile(file, "r") as z:
                    name = file.split("/")[-1].replace(".zip","")
                    z.extractall(f"{PalInfo.module_dir}/resources/data/{name}")
                    langmenu.delete(langmenu.index("end")-1, langmenu.index("end"))
                    self.add_lang_menu(langmenu, name)
                    dlclangs()

        def dlclangs():
            langmenu.add_separator()
            langmenu.add_command(label="Install language...", command=installlang)
        dlclangs()

        tools.add_cascade(label="Language", menu=langmenu, underline=0)

        # convmenu = Menu(tools, tearoff=0)
        # convmenu.add_command(label="Convert Save to Json", command=converttojson)
        # convmenu.add_command(label="Convert Json to Save", command=converttosave)

        # tools.add_cascade(label="Converter", menu=convmenu, underline=0)



# for i in paldata:
#             try:
#                 p = PalInfo.PalEntity(i)
#                 if not str(p.owner) in self.palbox:
#                     self.palbox[str(p.owner)] = []
#                 self.palbox[str(p.owner)].append(p)

#                 n = p.GetFullName()

#                 for m in p.GetLearntMoves():
#                     if not m in nullmoves:
#                         if not m in PalInfo.PalAttacks:
#                             nullmoves.append(m)
#             except Exception as e:
#                 if str(e) == "This is a player character":
#                     logger.debug(f"Found Player Character")
#                     # print(f"\nDebug: Data \n{i}\n\n")
#                     # o = i['value']['RawData']['value']['object']['SaveParameter']['value']
#                     # pl = "No Name"
#                     # if "NickName" in o:
#                     #     pl = o['NickName']['value']
#                     # plguid = i['key']['PlayerUId']['value']
#                     # print(f"{pl} - {plguid}")
#                     # self.players[pl] = plguid
#                 else:
#                     self.unknown.append(str(e))
#                     try:
#                         erroredpals.append(i)
#                     except:
#                         erroredpals.append(None)
#                     logger.error(f"Error occured on {i['key']['InstanceId']['value']}", exc_info=True)
#                     # print(f"Error occured on {i['key']['InstanceId']['value']}: {e.__class__.__name__}: {str(e)}")
#                     # traceback.print_exception(e)
#                     print()
#                 # print(f"Debug: Data {i}")



    def updateSkillsName(self):
        for idx, n in enumerate(self.skills):
            try:
                self.skills_name[idx].set(PalInfo.PalPassives[n.get()])
            except Exception as e:
                print(type(n))
                # self.unknown.append(str(e))
                # logger.error(f"Error occured on {i['key']['InstanceId']['value']}", exc_info=True)
                #     # print(f"Error occured on {i['key']['InstanceId']['value']}: {e.__class__.__name__}: {str(e)}")
                #     # traceback.print_exception(e)
                # print()


    def changesoul(self, field):
        if not self.isPalSelected():
            return
        i = int(self.listdisplay.curselection()[0])
        pal = self.FilteredPals()[i]
            
        match field:
            case "HP":
                v = self.hpsoulvar.get()
                self.hpsoulval.config(text=f"+{v*3}%")
                pal.SetRankHP(v)
            case "AT":
                v = self.atsoulvar.get()
                self.atsoulval.config(text=f"+{v*3}%")
                pal.SetRankAttack(v)
            case "DF":
                v = self.dfsoulvar.get()
                self.dfsoulval.config(text=f"+{v*3}%")
                pal.SetRankDefence(v)
            case "WS":
                v = self.wssoulvar.get()
                self.wssoulval.config(text=f"+{v*3}%")
                pal.SetRankWorkSpeed(v)
            case _:
                return

    def __init__(self):
        global EmptyObjectHandler, PalInfo, PalEditLogger
        import palworld_pal_edit.EmptyObjectHandler
        import palworld_pal_edit.PalInfo as PalInfo
        import palworld_pal_edit.PalEditLogger as PalEditLogger

        global logger
        logger = PalEditLogger.Logger()
        PalInfo.RecieveLogger(logger)

        t = datetime.today().strftime('%H:%M:%S')
        d = datetime.today().strftime('%d/%m/%Y')
        logger.info(f"App opened at {t} on {d}")

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
        self.resetTitle()
        self.palguidmanager: PalGuid = None
        self.is_onselect = False

        self.suits = {}
        self.suiticons = {}

        global suitabilities
        suitabilities = {
            "EmitFlame": "kindling",
            "Watering": "watering",
            "Seeding": "planting",
            "GenerateElectricity": "generating",
            "Handcraft": "handiwork",
            "Collection": "gathering",
            "Deforest": "deforesting",
            "Mining": "mining",
            "OilExtraction": "extracting",
            "ProductMedicine": "production",
            "Cool": "cooling",
            "Transport": "transporting",
            "MonsterFarm": "farming"
        }
        for i in suitabilities:
            n = suitabilities[i]
            self.suiticons[i] = [tk.PhotoImage(master=self.gui,
                                              file=f'{PalInfo.module_dir}/resources/icons/no_{n}.png'),
                                 tk.PhotoImage(master=self.gui,
                                              file=f'{PalInfo.module_dir}/resources/icons/{n}.png')]

        self.attacks = []
        self.attacks_name = []
        self.attackops = []
        self.attackdrops = []
        self.skilldrops = []
        self.skills = []
        self.skills_name = []

        self.current = tk.StringVar()
        self.current.set("")

        self.load_i18n()

        self.purplepanda = tk.PhotoImage(master=self.gui, file=f'{PalInfo.module_dir}/resources/MossandaIcon.png')
        self.gui.iconphoto(True, self.purplepanda)

        root = self.gui

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

        self.playerguid = tk.Label(scrollview, text="-")
        self.playerguid.config(font=(PalEditConfig.font, 7))
        self.playerguid.pack()

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

        self.attackdrops[0].config(highlightbackground=PalInfo.PalElements["Electricity"],
                                   bg=PalEdit.mean_color(PalInfo.PalElements["Electricity"], "ffffff"),
                                   activebackground=PalEdit.mean_color(PalInfo.PalElements["Electricity"], "ffffff"))
        self.attackdrops[1].config(highlightbackground=PalInfo.PalElements["Electricity"],
                                   bg=PalEdit.mean_color(PalInfo.PalElements["Electricity"], "ffffff"),
                                   activebackground=PalEdit.mean_color(PalInfo.PalElements["Electricity"], "ffffff"))
        self.attackdrops[2].config(highlightbackground=PalInfo.PalElements["Dark"],
                                   bg=PalEdit.mean_color(PalInfo.PalElements["Dark"], "ffffff"),
                                   activebackground=PalEdit.mean_color(PalInfo.PalElements["Dark"], "ffffff"))

        learntWaza = tk.Frame(atkskill)
        learntWaza.pack(fill=tk.constants.BOTH)

        wazaDisplay = tk.Frame(learntWaza)
        wazaDisplay.pack(side=tk.constants.LEFT, fill=tk.constants.BOTH, expand=True)
        wazaButtons = tk.Frame(learntWaza, width=20)
        wazaButtons.pack(side=tk.constants.RIGHT, fill=tk.constants.BOTH)

        wazaScroll = tk.Frame(wazaDisplay)
        wazaScroll.pack(expand=True, fill=tk.constants.X)
        scrollbar = tk.Scrollbar(wazaScroll)
        scrollbar.pack(side=tk.constants.LEFT, fill=tk.constants.Y)
        self.learntMoves = tk.Listbox(wazaScroll, width=30, yscrollcommand=scrollbar.set, exportselection=0)
        self.learntMoves.pack(side=tk.constants.LEFT, fill=tk.constants.X, expand=True)

        removeMove = tk.Button(wazaButtons, fg="red", text="🗑", borderwidth=1,
                               font=(PalEditConfig.font, PalEditConfig.ftsize - 2),
                               command=self.stripMove,
                               bg="darkgrey")
        removeMove.pack(fill=tk.constants.BOTH, expand=True)

        # self.listdisplay.bind("<<ListboxSelect>>", self.onselect)
        scrollbar.config(command=self.learntMoves.yview)

        # ➕
        self.fruitPicker = StringVar()
        self.fruitOptions = ttk.Combobox(wazaDisplay, textvariable=self.fruitPicker)
        self.fruitOptions.pack(fill=tk.constants.BOTH)
        addMove = tk.Button(wazaButtons, text="➕", borderwidth=1, font=(PalEditConfig.font, PalEditConfig.ftsize - 10),
                            command=self.appendMove,
                            bg="darkgrey")
        addMove.pack(side=tk.constants.RIGHT, fill=tk.constants.BOTH, expand=True)

        # Individual Info
        infoview = tk.Frame(root, relief="groove", borderwidth=2, width=480, height=480, bg="darkgrey")
        infoview.pack(side=tk.constants.RIGHT, fill=tk.constants.BOTH, expand=True)

        dataview = tk.Frame(infoview)
        dataview.pack(side=tk.constants.TOP, fill=tk.constants.BOTH)

        resourceview = tk.Frame(dataview)
        resourceview.pack(side=tk.constants.LEFT, fill=tk.constants.BOTH, expand=True)

        self.portrait = tk.Label(resourceview, image=self.purplepanda, relief="sunken", borderwidth=2)
        self.portrait.pack(pady=0)

        typeframe = tk.Frame(resourceview)
        typeframe.pack(expand=True, fill=tk.constants.X)
        self.ptype = tk.Label(typeframe, text=self.i18n['electricity_lbl'],
                              font=(PalEditConfig.font, PalEditConfig.ftsize),
                              bg=PalInfo.PalElements["Electricity"], width=6)
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
        self.luckybox = tk.Checkbutton(formframe, text=self.i18n['lucky_lbl'], variable=self.luckyvar, onvalue='1',
                                  offvalue='0',
                                  command=self.togglelucky)
        self.i18n_el['lucky_lbl'] = self.luckybox
        self.luckybox.pack(side=tk.constants.LEFT, expand=True)
        self.alphabox = tk.Checkbutton(formframe, text=self.i18n['alpha_lbl'], variable=self.alphavar, onvalue='1',
                                  offvalue='0',
                                  command=self.togglealpha)
        self.i18n_el['alpha_lbl'] = self.alphabox
        self.alphabox.pack(side=tk.constants.RIGHT, expand=True)

        button = Button(resourceview, text=self.i18n['btn_clone_pal'], command=self.clonepal)
        button.config(font=(PalEditConfig.font, 12))
        button.pack(expand=True, fill=BOTH)
        self.i18n_el['btn_clone_pal'] = button

        button = Button(resourceview, text=self.i18n['btn_delete_pal'], command=self.deletepal)
        button.config(font=(PalEditConfig.font, 12))
        button.pack(expand=True, fill=BOTH)
        self.i18n_el['btn_delete_pal'] = button
        

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

        baseinfoview = tk.Frame(deckview)
        baseinfoview.pack(fill=tk.constants.BOTH)
        labelview = tk.Frame(baseinfoview, bg="lightgrey", pady=0, padx=16)
        labelview.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)

        name = tk.Label(labelview, text=self.i18n['name_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                        bg="lightgrey")
        name.pack(expand=True, fill=tk.constants.X)
        self.i18n_el['name_prop'] = name
        gender = tk.Label(labelview, text=self.i18n['gender_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                          bg="lightgrey",
                          width=6, pady=6)
        self.i18n_el['gender_prop'] = gender
        gender.pack(expand=True, fill=tk.constants.X)
        rankspeed = tk.Label(labelview, text=self.i18n['rank_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                             bg="lightgrey")
        self.i18n_el['rank_prop'] = rankspeed
        rankspeed.pack(expand=True, fill=tk.constants.X)
        workspeed = tk.Label(labelview, text=self.i18n['workspeed_prop'],
                             font=(PalEditConfig.font, PalEditConfig.ftsize),
                             bg="lightgrey", width=12)
        self.i18n_el['workspeed_prop'] = workspeed
        workspeed.pack(expand=True, fill=tk.constants.X)


        statview = tk.Frame(deckview, relief="raised", borderwidth=2, bg="darkgrey")
        statview.pack(fill=tk.constants.X)
        statinfoview = tk.Frame(statview)
        statinfoview.pack(fill=tk.constants.X, side=tk.constants.LEFT, expand=True)
        statlabelview = tk.Frame(statinfoview)
        statlabelview.pack(fill=tk.constants.X, side=tk.constants.LEFT, expand=True)

        hp = tk.Label(statlabelview, text=self.i18n['hp_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                      bg="darkgrey",
                      width=10)
        self.i18n_el['hp_prop'] = hp
        hp.pack(expand=True, fill=tk.constants.X)
        mattack = tk.Label(statlabelview, text=self.i18n['mattack_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                          bg="darkgrey",
                          width=8)
        self.i18n_el['mattack_prop'] = mattack
        mattack.pack(expand=True, fill=tk.constants.X)
        sattack = tk.Label(statlabelview, text=self.i18n['sattack_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                          bg="darkgrey",
                          width=8)
        self.i18n_el['sattack_prop'] = sattack
        sattack.pack(expand=True, fill=tk.constants.X)
        
        defence = tk.Label(statlabelview, text=self.i18n['defence_prop'], font=(PalEditConfig.font, PalEditConfig.ftsize),
                           bg="darkgrey", width=8)
        self.i18n_el['defence_prop'] = defence
        defence.pack(expand=True, fill=tk.constants.X)
        


        statvals = tk.Frame(statinfoview, width=6)
        statvals.pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.X)

        self.hthstatval = tk.Label(statvals, bg="darkgrey", text="500",
                                   font=(PalEditConfig.font, PalEditConfig.ftsize),
                                   justify="center")
        self.hthstatval.pack(fill=tk.constants.X)
        self.matkstatval = tk.Label(statvals, bg="darkgrey", text="100", font=(PalEditConfig.font, PalEditConfig.ftsize),
                                   justify="center")
        self.matkstatval.pack(fill=tk.constants.X)
        self.satkstatval = tk.Label(statvals, bg="darkgrey", text="100", font=(PalEditConfig.font, PalEditConfig.ftsize),
                                   justify="center")
        self.satkstatval.pack(fill=tk.constants.X)
        self.defstatval = tk.Label(statvals, bg="darkgrey", text="50", font=(PalEditConfig.font, PalEditConfig.ftsize),
                                   justify="center")
        self.defstatval.pack(fill=tk.constants.X)

        disclaim = tk.Label(deckview, relief="raised", borderwidth=2, bg="darkgrey", text=self.i18n['msg_disclaim'],
                            font=(PalEditConfig.font, PalEditConfig.ftsize // 2))
        self.i18n_el['msg_disclaim'] = disclaim
        disclaim.pack(fill=tk.constants.X)

        editview = tk.Frame(baseinfoview)
        editview.pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.BOTH)

        species = [PalInfo.PalSpecies[e].GetName() for e in PalInfo.PalSpecies]
        species.sort()
        self.speciesvar = tk.StringVar()
        self.speciesvar_name = tk.StringVar()
        self.speciesvar_name.set("PalEdit")
        self.palname = ttk.Combobox(editview, textvariable=self.speciesvar_name, values=species)
        #self.palname = tk.OptionMenu(editview, self.speciesvar_name, *species, command=self.changespeciestype)
        self.palname.bind("<<ComboboxSelected>>", self.changespeciestype)
        self.palname.config(font=(PalEditConfig.font, PalEditConfig.ftsize),
                            #padx=0,
                            #pady=0,
                            #borderwidth=1,
                            width=5,
                            #direction='right'
                            )
        self.palname.pack(expand=True, fill=tk.constants.X)

        genderframe = tk.Frame(editview, pady=0)
        genderframe.pack()
        self.palgender = tk.Label(genderframe, text="Unknown", font=(PalEditConfig.font, PalEditConfig.ftsize),
                                  fg=PalInfo.PalGender.UNKNOWN.value, width=10)
        self.palgender.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.X)
        swapbtn = tk.Button(genderframe, text="↺", borderwidth=1, font=(PalEditConfig.font, PalEditConfig.ftsize - 2),
                            command=self.swapgender)
        swapbtn.pack(side=tk.constants.RIGHT)

        self.ranksvar = tk.IntVar()
        palrank = tk.OptionMenu(editview, self.ranksvar, *PalEdit.ranks, command=self.changerank)
        palrank.config(font=(PalEditConfig.font, PalEditConfig.ftsize), justify='center', padx=0, pady=0, borderwidth=1,
                       width=5)
        self.ranksvar.set(PalEdit.ranks[4])
        palrank.pack(expand=True, fill=tk.constants.X)

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

        self.wspvar = tk.IntVar()
        self.wspvar.dirty = False
        self.wspvar.set(70)
        palwsp = tk.Entry(editview, textvariable=self.wspvar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        palwsp.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palwsp.bind("<FocusOut>", lambda event, var=self.wspvar: try_update(var))
        palwsp.pack(expand=True, fill=tk.constants.X)
        self.wspvar.trace_add("write",
                              lambda name, index, mode, sv=self.wspvar, entry=palwsp: validate_and_mark_dirty(sv,
                                                                                                              entry))

        stateditview = tk.Frame(statview, bg="darkgrey")
        stateditview.pack(fill=tk.constants.X, side=tk.constants.RIGHT, expand=True)

##        def talent_hp_changed(*args):
##            if not self.isPalSelected():
##                return
##            i = int(listdisplay.curselection()[0])
##            pal = palbox[self.players[self.current.get()].GetPlayerGuid()][i]
##            if talent_hp_var.get() == 0:
##                talent_hp_var.set(1)
            # change value of pal

        self.phpvar = tk.IntVar()
        self.phpvar.dirty = False
        self.phpvar.set(50)
        palhps = tk.Entry(stateditview, textvariable=self.phpvar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        palhps.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palhps.bind("<FocusOut>", lambda event, var=self.phpvar: try_update(var))
        palhps.pack(expand=True, fill=tk.constants.X, pady=1)
        self.phpvar.trace_add("write",
                              lambda name, index, mode, sv=self.phpvar, entry=palhps: validate_and_mark_dirty(sv,
                                                                                                              entry))
        
        meleeframe = tk.Frame(stateditview, width=6, bg="darkgrey")
        meleeframe.pack(fill=tk.constants.X)
        
        self.meleevar = tk.IntVar()
        self.meleevar.dirty = False
        self.meleevar.set(100)
        meleeicon = tk.Label(meleeframe, width=2, text="⚔", font=(PalEditConfig.font, PalEditConfig.ftsize))
        meleeicon.pack(side=tk.constants.LEFT)
        palmelee = tk.Entry(meleeframe, textvariable=self.meleevar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        palmelee.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palmelee.bind("<FocusOut>", lambda event, var=self.meleevar: try_update(var))
        palmelee.pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.X, pady=1)
        self.meleevar.trace_add("write", lambda name, index, mode, sv=self.meleevar, entry=palmelee: validate_and_mark_dirty(sv, entry))


        shotframe = tk.Frame(stateditview, width=6, bg="darkgrey")
        shotframe.pack(fill=tk.constants.X)
        
        self.shotvar = tk.IntVar()
        self.shotvar.dirty = False
        self.shotvar.set(100)
        shoticon = tk.Label(shotframe, width=2, text="🏹", font=(PalEditConfig.font, PalEditConfig.ftsize))
        shoticon.pack(side=tk.constants.LEFT)
        palshot = tk.Entry(shotframe, textvariable=self.shotvar, font=(PalEditConfig.font, PalEditConfig.ftsize),
                           width=6)
        palshot.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        palshot.bind("<FocusOut>", lambda event, var=self.shotvar: try_update(var))
        palshot.pack(side=tk.constants.RIGHT, expand=True, fill=tk.constants.X, pady=1)
        self.shotvar.trace_add("write",
                               lambda name, index, mode, sv=self.shotvar, entry=palshot: validate_and_mark_dirty(sv,
                                                                                                                 entry))

        self.defvar = tk.IntVar()
        self.defvar.dirty = False
        self.defvar.set(100)
        paldef = tk.Entry(stateditview, textvariable=self.defvar, font=(PalEditConfig.font, PalEditConfig.ftsize), width=6)
        paldef.config(justify="center", validate="all", validatecommand=(valreg, '%P'))
        paldef.bind("<FocusOut>", lambda event, var=self.defvar: try_update(var))
        paldef.pack(expand=True, fill=tk.constants.X, pady=1)
        self.defvar.trace_add("write",
                              lambda name, index, mode, sv=self.defvar, entry=paldef: validate_and_mark_dirty(sv,
                                                                                                              entry))        

        """
        talent_hp_var = IntVar(value=50)
        talent_hp_var.trace_add("write", lambda name, index, mode, sv=talent_hp_var: talent_hp_changed(clamp(sv)))
        # hpslider = Scale(editview, from_=0, to=100, tickinterval=50, orient='horizontal', variable=talent_hp_var)
        hpslider = Scale(editview, from_=0, to=100, orient='horizontal', variable=talent_hp_var)
        hpslider.config(width=9)
        hpslider.pack(pady=(0,10), expand=True, fill=tk.constants.X, anchor="center")
        """


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
        op.remove("None")
        op.sort()
        op.insert(0, "None")
        op.remove("Unknown")
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

        gr = 0
        self.skilldrops[0].config(highlightbackground=PalEditConfig.skill_col[gr],
                                  bg=PalEdit.mean_color(PalEditConfig.skill_col[gr], "ffffff"),
                                  activebackground=PalEdit.mean_color(PalEditConfig.skill_col[gr], "ffffff"))
        self.skilldrops[1].config(highlightbackground=PalEditConfig.skill_col[gr],
                                  bg=PalEdit.mean_color(PalEditConfig.skill_col[gr], "ffffff"),
                                  activebackground=PalEdit.mean_color(PalEditConfig.skill_col[gr], "ffffff"))
        self.skilldrops[2].config(highlightbackground=PalEditConfig.skill_col[gr],
                                  bg=PalEdit.mean_color(PalEditConfig.skill_col[gr], "ffffff"),
                                  activebackground=PalEdit.mean_color(PalEditConfig.skill_col[gr], "ffffff"))
        self.skilldrops[3].config(highlightbackground=PalEditConfig.skill_col[gr],
                                  bg=PalEdit.mean_color(PalEditConfig.skill_col[gr], "ffffff"),
                                  activebackground=PalEdit.mean_color(PalEditConfig.skill_col[gr], "ffffff"))
        self.setskillcolours()

        self.skilldrops[0].bind("<Enter>", lambda evt, num=0: self.changetext(num))
        self.skilldrops[1].bind("<Enter>", lambda evt, num=1: self.changetext(num))
        self.skilldrops[2].bind("<Enter>", lambda evt, num=2: self.changetext(num))
        self.skilldrops[3].bind("<Enter>", lambda evt, num=3: self.changetext(num))
        self.skilldrops[0].bind("<Leave>", lambda evt, num=-1: self.changetext(num))
        self.skilldrops[1].bind("<Leave>", lambda evt, num=-1: self.changetext(num))
        self.skilldrops[2].bind("<Leave>", lambda evt, num=-1: self.changetext(num))
        self.skilldrops[3].bind("<Leave>", lambda evt, num=-1: self.changetext(num))

        # FOOTER
        frameFooter = tk.Frame(infoview, relief="flat")
        frameFooter.pack(fill=tk.constants.BOTH, expand=False)
        self.skilllabel = tk.Label(frameFooter, text=self.i18n['msg_skill'])
        self.skilllabel.pack()
        self.i18n_el['msg_skill'] = self.skilllabel


        # SUITABILITIES
        suitbox = tk.Frame(infoview)
        suitbox.pack()
        suiticonbox = tk.Frame(suitbox)
        suiticonbox.pack(expand=True, fill=tk.constants.X, anchor=tk.constants.CENTER)
        
        for i in suitabilities:
            throwawaybox = tk.Frame(suiticonbox)
            throwawaybox.pack(side=tk.constants.LEFT, anchor=tk.constants.CENTER)
            
            self.suits[i] = tk.Label(throwawaybox, image=self.suiticons[i][1], bg="lightgrey", relief="groove", borderwidth=1)
            self.suits[i].pack()

            v = f"{i}_var"
            self.suits[v] = tk.IntVar()
            #self.suits[v].trace(

            s = f"{i}_label"
            self.suits[s] = tk.Spinbox(throwawaybox, width=1, text="0",
                                       from_=0, to=5, bg="lightgrey", relief="groove",
                                       borderwidth=1, textvariable=self.suits[v],
                                       font=(PalEditConfig.font, PalEditConfig.ftsize),
                                       command=self.setsuits)
            self.suits[s].pack(fill=tk.constants.X, expand=True)
        
        # PRESETS
        framePresets = tk.Frame(infoview, relief="raised", borderwidth=2)
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
        preset_button = tk.Button(framePresetsButtons1, text=self.i18n['preset_base'],
                                  command=lambda: self.setpreset("base"))
        self.i18n_el['preset_base'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons1, text=self.i18n['preset_speed_worker'],
                                  command=lambda: self.setpreset("workspeed"))
        self.i18n_el['preset_speed_worker'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons1, text=self.i18n['preset_speed_runner'],
                                  command=lambda: self.setpreset("movement"))
        self.i18n_el['preset_speed_runner'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons1, text=self.i18n['preset_tank'],
                                  command=lambda: self.setpreset("tank"))
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
        preset_button = tk.Button(framePresetsButtons2, text=self.i18n['preset_max'],
                                  command=lambda: self.setpreset("dmg_max"))
        self.i18n_el['preset_max'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons2, text=self.i18n['preset_balance'],
                                  command=lambda: self.setpreset("dmg_balanced"))
        self.i18n_el['preset_balance'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons2, text=self.i18n['preset_mount'],
                                  command=lambda: self.setpreset("dmg_mount"))
        self.i18n_el['preset_mount'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)
        preset_button = tk.Button(framePresetsButtons2, text=self.i18n['preset_element'],
                                  command=lambda: self.setpreset("dmg_element"))
        self.i18n_el['preset_element'] = preset_button
        preset_button.config(font=(PalEditConfig.font, 12))
        preset_button.pack(side=tk.constants.LEFT, expand=True, fill=tk.constants.BOTH)

        # PRESETS OPTIONS
        framePresetsExtras = tk.Frame(framePresets, relief="groove", borderwidth=4)
        #framePresetsExtras.pack(fill=tk.constants.BOTH, expand=True)

        framePresetsLevel = tk.Frame(framePresetsExtras)
        framePresetsLevel.pack(fill=tk.constants.BOTH, expand=True)
        presetTitleLevel = tk.Label(framePresetsLevel, text=self.i18n['preset_title_level'], anchor='center',
                                    bg="lightgrey",
                                    font=(PalEditConfig.font, 13),
                                    width=20, height=1)
        presetTitleLevel.pack(side=tk.constants.LEFT, expand=False, fill=tk.constants.Y)
        self.i18n_el['preset_title_level'] = presetTitleLevel
        self.checkboxLevelVar = tk.IntVar()
        checkboxLevel = tk.Checkbutton(framePresetsLevel, text=self.i18n['preset_chg_lvl'],
                                       variable=self.checkboxLevelVar,
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
        presetTitleRank = tk.Label(framePresetsRank, text=self.i18n['preset_title_rank'], anchor='center',
                                   bg="lightgrey",
                                   font=(PalEditConfig.font, 13),
                                   width=20, height=1)
        presetTitleRank.pack(side=tk.constants.LEFT, expand=False, fill=tk.constants.Y)
        self.i18n_el['preset_title_rank'] = presetTitleRank
        self.checkboxRankVar = tk.IntVar()
        checkboxRank = tk.Checkbutton(framePresetsRank, text=self.i18n['preset_change_rank'],
                                      variable=self.checkboxRankVar,
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

        # SOUL STATUE STUFF ⚪⚫
        soulview = tk.Frame(atkskill, relief="groove", borderwidth=2)
        soulview.pack(fill=tk.constants.X)
        soullbl = tk.Label(soulview, text=self.i18n["soul_tooltip"], bg="darkgrey", font=(PalEditConfig.font, PalEditConfig.ftsize))
        soullbl.pack(expand=True, fill=tk.constants.X, pady=0)
        self.i18n_el["soul_tooltip"] = soullbl

        self.hpsoulvar = tk.IntVar()
        self.hpsoulvar.set(10)
        self.hpsoulvar.trace_add("write", lambda *args: self.changesoul("HP"))
        self.atsoulvar = tk.IntVar()
        self.atsoulvar.set(5)
        self.atsoulvar.trace_add("write", lambda *args: self.changesoul("AT"))
        self.dfsoulvar = tk.IntVar()
        self.dfsoulvar.set(7)
        self.dfsoulvar.trace_add("write", lambda *args: self.changesoul("DF"))
        self.wssoulvar = tk.IntVar()
        self.wssoulvar.set(0)
        self.wssoulvar.trace_add("write", lambda *args: self.changesoul("WS"))

        hpsoul = tk.Frame(soulview)
        hpsoul.pack(fill=tk.constants.X)
        hpsoultag = tk.Label(hpsoul, width=10, text=self.i18n["health_soul_lbl"], bg="darkgrey", font=(PalEditConfig.font, PalEditConfig.ftsize))
        hpsoultag.pack(side=tk.constants.LEFT, fill=tk.constants.X, expand=True)
        self.i18n_el["health_soul_lbl"] = hpsoultag
        self.hpsoulval = tk.Label(hpsoul, width=6, text="+30%", font=(PalEditConfig.font, PalEditConfig.ftsize-4))
        self.hpsoulval.pack(side=tk.constants.RIGHT)
        hpsoulbar = tk.Scale(hpsoul, showvalue=False, variable=self.hpsoulvar, from_=0, to=20, orient=HORIZONTAL)
        hpsoulbar.pack(side=tk.constants.RIGHT)

        atsoul = tk.Frame(soulview)
        atsoul.pack(fill=tk.constants.X)
        atsoultag = tk.Label(atsoul, width=10, text=self.i18n["attack_soul_lbl"], bg="darkgrey", font=(PalEditConfig.font, PalEditConfig.ftsize))
        atsoultag.pack(side=tk.constants.LEFT, fill=tk.constants.X, expand=True)
        self.i18n_el["attack_soul_lbl"] = atsoultag
        self.atsoulval = tk.Label(atsoul, width=6, text="+15%", font=(PalEditConfig.font, PalEditConfig.ftsize-4))
        self.atsoulval.pack(side=tk.constants.RIGHT)
        atsoulbar = tk.Scale(atsoul, showvalue=False, variable=self.atsoulvar, from_=0, to=20, orient=HORIZONTAL)
        atsoulbar.pack(side=tk.constants.RIGHT)

        dfsoul = tk.Frame(soulview)
        dfsoul.pack(fill=tk.constants.X)
        dfsoultag = tk.Label(dfsoul, width=10, text=self.i18n["defence_soul_lbl"], bg="darkgrey", font=(PalEditConfig.font, PalEditConfig.ftsize))
        dfsoultag.pack(side=tk.constants.LEFT, fill=tk.constants.X, expand=True)
        self.i18n_el["defence_soul_lbl"] = dfsoultag
        self.dfsoulval = tk.Label(dfsoul, width=6, text="+21%", font=(PalEditConfig.font, PalEditConfig.ftsize-4))
        self.dfsoulval.pack(side=tk.constants.RIGHT)
        dfsoulbar = tk.Scale(dfsoul, showvalue=False, variable=self.dfsoulvar, from_=0, to=20, orient=HORIZONTAL)
        dfsoulbar.pack(side=tk.constants.RIGHT)

        wssoul = tk.Frame(soulview)
        wssoul.pack(fill=tk.constants.X)
        wssoultag = tk.Label(wssoul, width=10, text=self.i18n["working_soul_lbl"], bg="darkgrey", font=(PalEditConfig.font, PalEditConfig.ftsize))
        wssoultag.pack(side=tk.constants.LEFT, fill=tk.constants.X, expand=True)
        self.i18n_el["working_soul_lbl"] = wssoultag
        self.wssoulval = tk.Label(wssoul, width=6, text="+0%", font=(PalEditConfig.font, PalEditConfig.ftsize-4))
        self.wssoulval.pack(side=tk.constants.RIGHT)
        wssoulbar = tk.Scale(wssoul, showvalue=False, variable=self.wssoulvar, from_=0, to=20, orient=HORIZONTAL)
        wssoulbar.pack(side=tk.constants.RIGHT)
        
        # DEBUG
        frameDebug = self.frameDebug = tk.Frame(infoview, relief="flat")
        frameDebug.pack()
        frameDebug.pack_forget()
        self.debugTitle = tk.Label(frameDebug, text='Debug:', anchor='w', bg="darkgrey",
                              font=(PalEditConfig.font, PalEditConfig.ftsize), width=6, height=1)
        self.debugTitle.pack(fill=tk.constants.BOTH)
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
        #cloneLabel.pack(fill=tk.constants.X)
        palframe = Frame(atkskill)
        palframe.pack(fill=X)
        button = Button(palframe, text=self.i18n['btn_add_pal'], command=self.spawnpal)
        button.config(font=(PalEditConfig.font, 12))
        #button.pack(side=LEFT, expand=True, fill=BOTH)
        self.i18n_el['btn_add_pal'] = button
        button = Button(palframe, text=self.i18n['btn_dump_pal'], command=self.dumppals)
        button.config(font=(PalEditConfig.font, 12))
        #button.pack(side=LEFT, expand=True, fill=BOTH)
        self.i18n_el['btn_dump_pal'] = button

        warning = tk.Frame(atkskill, relief="groove", borderwidth=2)
        warning.pack(fill=tk.constants.BOTH)

        warnhdr = tk.Label(warning, width=10, text="WARNING!", bg="darkgrey", font=(PalEditConfig.font, PalEditConfig.ftsize+2))
        warnhdr.pack(fill=tk.constants.BOTH)

        warnstr = "Players who have not logged in for a while can break your save. If you cannot get them to join to upgrade their save data then remove them using Prune or remove their player data from the 'Players' folder while on the title screen then load the save."

        warnlabel = tk.Label(warning, wrap=300, width=10, text=warnstr, bg="darkgrey", font=(PalEditConfig.font, PalEditConfig.ftsize-6))
        warnlabel.pack(fill=tk.constants.BOTH)
        

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
    logger.Close()


if __name__ == "__main__":
    sys.path.append('..')
    print(sys.path)
    main()
