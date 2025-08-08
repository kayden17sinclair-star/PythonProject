import random

adjectives = ["Flaming", "Shadow", "Thunderous", "Frozen", "Venomous", "Holy", "Cursed", "Ancient", "Bloodthirsty", "Phantom"]
weapons = ["Sword", "Axe", "Bow", "Dagger", "Hammer", "Staff", "Lance", "Crossbow", "Whip", "Mace"]
effects = ["of Doom", "of Eternal Night", "of Light", "of the Fallen", "of Whispers", "of Destruction", "of the Phoenix", "of Shadows"]

def generate_weapon():
    return f"{random.choice(adjectives)} {random.choice(weapons)} {random.choice(effects)}"

if __name__ == "__main__":
    print("Welcome to the Fantasy Weapon Generator!")
    for _ in range(5):
        print(" -", generate_weapon())
