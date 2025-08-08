import json, random, os
import os
VERSION = "1.1"

WEAPONS = {
    "fists": {"min": 1, "max": 2},
    "dagger": {"min": 3, "max": 6},
    "shortsword": {"min": 5, "max": 9},
    "greatsword": {"min": 8, "max": 14},
    "thornbow": {"min": 6, "max": 12},
}
RECIPES = {
    "dagger": {"Iron": 1, "Wood": 1},
    "shortsword": {"Iron": 2, "Wood": 1},
    "greatsword": {"Iron": 3, "Wood": 2, "Crystal": 1},
    "thornbow": {"Wood": 3, "Fang": 2},
}
ENEMIES = [
    {"name": "Slime", "hp": 12, "min": 1, "max": 3, "gold": (5, 9), "xp": 6},
    {"name": "Bandit", "hp": 18, "min": 2, "max": 5, "gold": (8, 14), "xp": 10},
    {"name": "Wolf", "hp": 22, "min": 3, "max": 6, "gold": (10, 16), "xp": 13},
    {"name": "Stone Golem", "hp": 35, "min": 4, "max": 9, "gold": (18, 28), "xp": 20},
]
FOREST_LOOT = ["Wood", "Iron", "Fang", "Crystal", "Herb"]
BAR_MENU = {"small_potion": {"price": 8, "heal": 12},
            "large_potion": {"price": 20, "heal": 30},
            "rest": {"price": 12, "heal": "full"}}
SAVEFILE = "savegame.json"

# Context tips shown automatically per location
HINTS = {
    "town":        "Try: go arena | go bar | go blacksmith | go forest | stats | inv",
    "arena":       "Try: fight | leave | stats | inv | use <potion>",
    "bar":         "Try: buy small_potion | buy large_potion | buy rest | use <potion> | leave",
    "blacksmith":  "Try: recipes | craft <weapon> | leave",
    "forest":      "Try: explore | leave (go town)",
}

class Player:
    def __init__(self, name="Hero"):
        self.name = name
        self.level = 1
        self.xp = 0
        self.gold = 20
        self.hp = 30
        self.max_hp = 30
        self.weapon = "fists"
        self.inv = {"Herb": 0, "Wood": 0, "Iron": 0, "Fang": 0, "Crystal": 0,
                    "small_potion": 0, "large_potion": 0}
        self.location = "town"
        # NEW: cheats & god mode
        self.cheats = False
        self.god = False

    def dmg_roll(self):
        w = WEAPONS[self.weapon]
        return random.randint(w["min"], w["max"])

    def add_xp(self, amount):
        self.xp += amount
        needed = 20 + (self.level - 1) * 15
        leveled = False
        while self.xp >= needed:
            self.xp -= needed
            self.level += 1
            self.max_hp += 5
            self.hp = self.max_hp
            leveled = True
            needed = 20 + (self.level - 1) * 15
        return leveled

    def to_dict(self): return self.__dict__
    @staticmethod
    def from_dict(d): p = Player(); p.__dict__.update(d); return p

def clr(): os.system("cls" if os.name == "nt" else "clear")
def say(t=""): print(t)
def header(t): print("="*50 + f"\n{t}\n" + "="*50)

def save_game(pl):
    with open(SAVEFILE, "w") as f: json.dump(pl.to_dict(), f, indent=2)
    say("Saved.")
def load_game():
    if not os.path.exists(SAVEFILE): say("No save found."); return None
    with open(SAVEFILE) as f: d = json.load(f)
    say("Loaded."); return Player.from_dict(d)

def show_help():
    say("""Commands:
  go town|arena|bar|blacksmith|forest     hint (repeat local tips)
  stats, inv, equip <weapon>              use <small_potion|large_potion>
  craft <weapon>, recipes                 buy <item>, rest
  fight, explore                          save, load, quit
Cheats:
  cheat on/off                            !help  (list cheats)
  !gold <n>   !xp <n>   !level <n>        !heal [n|full]
  !give <Item> <n>                        !equip <weapon> (bypass)
  !tp town|arena|bar|blacksmith|forest    !god (toggle)  !reveal
""")

def show_stats(p):
    header("STATS")
    w = WEAPONS[p.weapon]
    say(f"Name: {p.name}  Lv {p.level}  XP {p.xp}")
    say(f"HP: {p.hp}/{p.max_hp}  Gold: {p.gold}  Weapon: {p.weapon} ({w['min']}-{w['max']})")
    say(f"Location: {p.location}  Cheats: {p.cheats}  God: {p.god}")

def show_inv(p):
    header("INVENTORY")
    for k, v in p.inv.items(): say(f"{k}: {v}")

def list_recipes():
    header("RECIPES")
    for w, req in RECIPES.items():
        base = WEAPONS[w]
        cost = ", ".join(f"{k}x{v}" for k, v in req.items())
        say(f"{w}: {base['min']}-{base['max']} dmg  requires: {cost}")

def can_craft(p, weapon):
    need = RECIPES.get(weapon);
    return bool(need) and all(p.inv.get(k,0) >= v for k,v in need.items())
def do_craft(p, weapon):
    if weapon not in RECIPES: say("No such recipe."); return
    if not can_craft(p, weapon): say("You lack materials."); return
    for k,v in RECIPES[weapon].items(): p.inv[k] -= v
    p.weapon = weapon; say(f"Forged a {weapon}! Equipped.")

def bar_buy(p, item):
    if item not in BAR_MENU: say("Not for sale."); return
    price = BAR_MENU[item]["price"]
    if p.gold < price: say("Not enough gold."); return
    p.gold -= price
    if item == "rest":
        p.hp = p.max_hp; say("You rest at the bar. Fully healed.")
    else:
        p.inv[item] += 1; say(f"Bought 1x {item}.")

def use_item(p, item):
    if item not in ("small_potion","large_potion"): say("Only potions can be used."); return
    if p.inv.get(item,0) <= 0: say("You don't have that."); return
    heal = BAR_MENU[item]["heal"]; p.inv[item] -= 1
    before = p.hp; p.hp = p.max_hp if heal=="full" else min(p.max_hp, p.hp + heal)
    say(f"Used {item}. Healed {p.hp - before} HP.")

def explore_forest(p):
    header("FOREST")
    r = random.random()
    if r < 0.55:
        loot = random.choice(FOREST_LOOT)
        amt = 1 if loot=="Crystal" else random.randint(1,2)
        p.inv[loot] = p.inv.get(loot,0)+amt
        gold = random.randint(3,10); p.gold += gold
        say(f"You find {amt}x {loot} and {gold} gold.")
    elif r < 0.8:
        say("A wild creature appears!"); combat(p, scale=0.9)
    else:
        heal = random.randint(4,10); p.hp = min(p.max_hp, p.hp+heal)
        say(f"You find herbs and patch wounds (+{heal} HP).")

def scaled_enemy(scale=1.0):
    e = dict(random.choice(ENEMIES))
    e["hp"] = int(e["hp"]*scale)
    e["min"] = max(1, int(e["min"]*scale))
    e["max"] = max(e["min"]+1, int(e["max"]*scale))
    gmin,gmax = e["gold"]; e["gold"] = (int(gmin*scale), int(gmax*scale))
    e["xp"] = int(e["xp"]*scale + 1); return e

def combat(p, scale=1.0):
    e = scaled_enemy(scale)
    header(f"ARENA FIGHT: {e['name']}  HP {e['hp']}")
    while e["hp"]>0 and p.hp>0:
        say(f"\nYour HP {p.hp}/{p.max_hp}   |   {e['name']} HP {e['hp']}")
        cmd = input("Action [attack/use <potion>/run]: ").strip().lower()
        if cmd.startswith("use "): use_item(p, cmd.split(" ",1)[1]); continue
        if cmd=="run":
            if random.random()<0.5: say("You break away!"); return
            else: say("Couldn't escape!")
        # player
        pdmg = p.dmg_roll()
        if random.random()<0.1: pdmg=int(pdmg*1.5); say("Critical hit!")
        e["hp"] -= pdmg; say(f"You hit {e['name']} for {pdmg}.")
        if e["hp"]<=0: break
        # enemy (skip if god)
        if not p.god:
            edmg = random.randint(e["min"], e["max"])
            if random.random()<0.08: edmg=int(edmg*1.5); say(f"{e['name']} crits!")
            p.hp -= edmg; say(f"{e['name']} hits you for {edmg}.")
    if p.hp<=0:
        say("\nYou fall... but wake at the bar. Some gold is gone.")
        loss = min(p.gold,10); p.gold -= loss
        p.hp = max(1, p.max_hp//2); p.location="bar"; return
    g = random.randint(*e["gold"]); p.gold += g
    leveled = p.add_xp(e["xp"])
    say(f"\nVictory! +{g} gold, +{e['xp']} XP.")
    if leveled: say(f"*** Level up → Lv {p.level}! Max HP {p.max_hp}. ***")

def arena(p):
    header("ARENA"); say(HINTS["arena"])
    while True:
        cmd = input("> ").strip().lower()
        if cmd=="leave": return
        if cmd=="fight":
            scale = 1.0 + (p.level-1)*0.15; combat(p, scale); say("\n(Arena ready for another fight.)")
        else: say("Commands: fight, leave")

def bar(p):
    header("BAR"); say(HINTS["bar"])
    while True:
        cmd = input("> ").strip().lower()
        if cmd=="leave": return
        if cmd.startswith("buy "): bar_buy(p, cmd.split(" ",1)[1])
        elif cmd.startswith("use "): use_item(p, cmd.split(" ",1)[1])
        elif cmd=="rest": bar_buy(p,"rest")
        else: say("Try: buy small_potion | buy large_potion | buy rest | use <potion> | leave")

def blacksmith(p):
    header("BLACKSMITH"); say(HINTS["blacksmith"]); list_recipes()
    while True:
        cmd = input("> ").strip().lower()
        if cmd=="leave": return
        if cmd.startswith("craft "): do_craft(p, cmd.split(" ",1)[1])
        else: say("Try: craft dagger | craft shortsword | craft greatsword | craft thornbow | leave")

def show_place_hint(p):
    say(f"[{p.location.upper()}] {HINTS.get(p.location, '')}")

# ---------- CHEATS ----------
def cheats_help():
    say("""Cheats (prefix !). Enable with: cheat on
  !gold <n>      add gold
  !xp <n>        add XP
  !level <n>     set level (heals to full)
  !heal [n|full] heal HP
  !give <Item> <n>  (Wood/Iron/Fang/Crystal/small_potion/large_potion/Herb)
  !equip <weapon>   (bypass recipes)
  !tp town|arena|bar|blacksmith|forest
  !god          toggle invulnerability
  !reveal       quick stats+inv
""")

def handle_cheat(p, cmd):
    if cmd == "!help": cheats_help(); return
    if not p.cheats: say("Cheats are off. Use: cheat on"); return
    parts = cmd.split()
    if parts[0] == "!gold" and len(parts)==2:
        p.gold += int(parts[1]); say(f"+{int(parts[1])} gold")
    elif parts[0] == "!xp" and len(parts)==2:
        leveled = p.add_xp(int(parts[1])); say(f"+{int(parts[1])} XP")
        if leveled: say(f"Level up → Lv {p.level}")
    elif parts[0] == "!level" and len(parts)==2:
        p.level = max(1, int(parts[1])); p.max_hp = 25 + 5*p.level; p.hp = p.max_hp
        say(f"Level set to {p.level}. HP {p.hp}/{p.max_hp}")
    elif parts[0] == "!heal":
        if len(parts)==1 or parts[1]=="full": p.hp = p.max_hp; say("Healed to full.")
        else: p.hp = min(p.max_hp, p.hp + int(parts[1])); say(f"Healed {parts[1]}.")
    elif parts[0] == "!give" and len(parts)==3:
        item, n = parts[1].capitalize() if parts[1].islower() else parts[1], int(parts[2])
        p.inv[item] = p.inv.get(item,0)+n; say(f"Gave {n}x {item}.")
    elif parts[0] == "!equip" and len(parts)==2:
        w = parts[1]
        if w in WEAPONS: p.weapon = w; say(f"Equipped {w}.")
        else: say("Unknown weapon.")
    elif parts[0] == "!tp" and len(parts)==2:
        dest = parts[1]
        if dest in ("town","arena","bar","blacksmith","forest"):
            p.location = dest; show_place_hint(p)
        else: say("Bad destination.")
    elif parts[0] == "!god":
        p.god = not p.god; say(f"God mode: {p.god}")
    elif parts[0] == "!reveal":
        show_stats(p); show_inv(p)
    else:
        say("Bad cheat. !help for list.")

# ---------- LOOP ----------
def game_loop(p):
    clr()
    say(f"Open Adventure v{VERSION} — type 'hint' for local tips. 'cheat on' to enable cheats.")
    prev_loc = None
    while True:
        if p.location != prev_loc:
            show_place_hint(p); prev_loc = p.location
        cmd = input(f"[{p.location}] > ").strip().lower()

        # Cheats toggles/commands
        if cmd == "cheat on": p.cheats = True; say("Cheats enabled. Use !help"); continue
        if cmd == "cheat off": p.cheats = False; say("Cheats disabled."); continue
        if cmd.startswith("!"): handle_cheat(p, cmd); continue

        # Convenience
        if cmd == "hint": show_place_hint(p); continue
        if cmd == "help": show_help(); continue
        if cmd == "stats": show_stats(p); continue
        if cmd == "inv": show_inv(p); continue
        if cmd.startswith("equip "):
            w = cmd.split(" ",1)[1]
            if w in WEAPONS: p.weapon = w; say(f"Equipped {w}.")
            else: say("Unknown weapon."); continue
        if cmd == "recipes": list_recipes(); continue
        if cmd.startswith("craft "): do_craft(p, cmd.split(" ",1)[1]); continue
        if cmd.startswith("use "): use_item(p, cmd.split(" ",1)[1]); continue
        if cmd == "save": save_game(p); continue
        if cmd == "load":
            x = load_game();
            if x: p = x; prev_loc=None; continue
        if cmd == "quit": say("Bye!"); return

        # Travel / actions
        if cmd.startswith("go "):
            dest = cmd.split(" ",1)[1]
            if dest not in ("town","arena","bar","blacksmith","forest"):
                say("You can go: town, arena, bar, blacksmith, forest."); continue
            p.location = dest
            if dest=="arena": arena(p)
            elif dest=="bar": bar(p)
            elif dest=="blacksmith": blacksmith(p)
            elif dest=="forest": explore_forest(p)
            else: say("Back in town.")
            continue

        if cmd == "fight":
            if p.location!="arena": say("Go to the arena first: go arena")
            else: arena(p)
            continue

        if cmd == "explore":
            if p.location!="forest": say("Go to the forest first: go forest")
            else: explore_forest(p)
            continue

        if cmd == "rest":
            if p.location!="bar": say("You can rest at the bar: go bar")
            else: bar_buy(p,"rest")
            continue

        if cmd.startswith("buy "):
            if p.location!="bar": say("You can buy at the bar: go bar")
            else: bar_buy(p, cmd.split(" ",1)[1])
            continue

        say("Unknown command. Type 'hint' for local tips or 'help'.")

if __name__ == "__main__":
    name = input("Name your hero: ").strip() or "Hero"
    player = Player(name=name)
    try:
        game_loop(player)
    except KeyboardInterrupt:
        say("\n(Interrupted)")


        def clr():
            if os.getenv("TERM"):
                os.system("cls" if os.name == "nt" else "clear")