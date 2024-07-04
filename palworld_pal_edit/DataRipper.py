import json

elements = {
    "Electricity":"Electric",
    "Water":"Water",
    "Fire":"Fire",
    "Dark":"Dark",
    "Dragon":"Dragon",
    "Normal":"Neutral",
    "Earth":"Ground",
    "Ice":"Ice",
    "Leaf":"Grass"
    }

with open("RIP.json", "r") as file:
    ripped = json.loads(file.read())

with open("resources/data/pals.json", "r") as file:
    mine = json.loads(file.read())

for i in mine["values"]:
    n = i["CodeName"]
    if n in ripped[0]["Rows"]:
        p = ripped[0]["Rows"][n]
        i['Scaling'] = {
            "HP": p["HP"],
            "PHY": p["MeleeAttack"],
            "MAG": p["ShotAttack"],
            "DEF": p["Defense"]
            }

with open("resources/data/pals.json", "w") as file:
    file.write(json.dumps(mine, indent=4, ensure_ascii=False))


with open("MoveRIP.json", "r") as file:
    ripmoves = json.loads(file.read())

reform = {}
for i in ripmoves[0]["Rows"]:
    o = ripmoves[0]["Rows"][i]
    n = o["WazaType"]
    t = o["Category"].split("::")[-1]
    p = o["Power"]
    e = elements[o["Element"].split("::")[-1]]
    reform[n] = {
        "t":t,"p":p,"e":e
        }

with open("resources/data/attacks.json", "r") as file:
    mine = json.loads(file.read())

with open("resources/data/en-GB/attacks.json", "r") as file:
    lang = json.loads(file.read())

for i in mine:
    if i in ['','None','Unknown']:
        mine[i]["Category"] = "Null"
        continue
    if i not in reform:
        print(i, "not found")
        continue
    mine[i]["Category"] = reform[i]["t"]
    mine[i]["Type"] = reform[i]["e"]
    mine[i]["Power"] = reform[i]["p"]
    reform.pop(i)
    if i not in lang:
        lang[i] = i.split("::")[-1].split("_")[-1]

for i in reform:
    mine[i] = {
        "Type": reform[i]["e"],
        "Power": reform[i]["p"],
        "Category": reform[i]["t"]
    }
    if i not in lang:
        lang[i] = i.split("::")[-1].split("_")[-1]

with open("resources/data/attacks.json", "w") as file:
    file.write(json.dumps(mine, indent=4, ensure_ascii=False))

with open("resources/data/en-GB/attacks.json", "w") as file:
    file.write(json.dumps(lang, indent=4, ensure_ascii=False))
