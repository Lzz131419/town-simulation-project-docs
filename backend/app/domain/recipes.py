"""Production and consumption rules; shared with the action catalog."""

RECIPES = {
    "harvest_veg": {"inputs": {}, "outputs": {"vegetable": 3}},
    "gather_honey": {"inputs": {}, "outputs": {"honey": 2}},
    "harvest_flax": {"inputs": {}, "outputs": {"flax": 3}},
    "weave": {"inputs": {"flax": 2}, "outputs": {"cloth": 1}},
    "assemble": {"inputs": {"wood": 3, "cloth": 1}, "outputs": {"furniture": 1}},
    "cook": {"inputs": {"vegetable": 2, "wood": 1}, "outputs": {"soup": 2}},
    "farm": {"inputs": {}, "outputs": {"grain": 3}},
    "craft": {"inputs": {}, "outputs": {"wood": 2}},
    "bake": {"inputs": {"grain": 2}, "outputs": {"bread": 3}},
    "gather": {"inputs": {}, "outputs": {"fruit": 2}},
    "fish": {"inputs": {}, "outputs": {"fish": 1}},
    "chop": {"inputs": {}, "outputs": {"wood": 3}},
    "mine": {"inputs": {}, "outputs": {"ore": 2}},
    "forage": {"inputs": {}, "outputs": {"herb": 2}},
    "grill": {"inputs": {"fish": 1, "wood": 1}, "outputs": {"meal": 1}},
    "forge": {"inputs": {"ore": 2, "wood": 2}, "outputs": {"tool": 1}},
}
CONSUMABLES = {
    "eat_soup": {"inputs": {"soup": 1}, "hunger_relief": 30, "energy_gain": 6},
    "honey_tea": {"inputs": {"honey": 1, "herb": 1}, "hunger_relief": 10, "energy_gain": 24},
    "eat": {"inputs": {"bread": 1}, "hunger_relief": 35, "energy_gain": 0},
    "eat_fruit": {"inputs": {"fruit": 1}, "hunger_relief": 20, "energy_gain": 0},
    "eat_meal": {"inputs": {"meal": 1}, "hunger_relief": 45, "energy_gain": 8},
    "brew": {"inputs": {"herb": 2}, "hunger_relief": 0, "energy_gain": 18},
    "picnic": {"inputs": {"fruit": 2}, "hunger_relief": 30, "energy_gain": 12},
}
# One tool is used up for one enhanced outdoor work action.
TOOL_BONUS = {"chop": {"wood": 2}, "mine": {"ore": 2}}
