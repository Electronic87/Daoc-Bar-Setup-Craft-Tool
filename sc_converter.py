#!/usr/bin/env python3
"""Convert DAoC spellcraft gem reports between Zenk text and DAoC Tools .forge."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET


SLOT_KEYS = [
    "head",
    "torso",
    "arms",
    "hands",
    "legs",
    "feet",
    "neck",
    "cloak",
    "jewel",
    "belt",
    "lwrist",
    "rwrist",
    "lring",
    "rring",
    "mythical",
    "mainhand",
    "offhand",
    "twohanded",
    "ranged",
]

SLOT_TITLES = {
    "head": "Helmet",
    "torso": "Torso",
    "arms": "Arms",
    "hands": "Hands",
    "legs": "Legs",
    "feet": "Feet",
    "neck": "Neck",
    "cloak": "Cloak",
    "jewel": "Jewel",
    "belt": "Waist",
    "lwrist": "L. Wrist",
    "rwrist": "R. Wrist",
    "lring": "L. Ring",
    "rring": "R. Ring",
    "mythical": "Mythical",
    "mainhand": "Right Hand",
    "offhand": "Left Hand",
    "twohanded": "Two Handed",
    "ranged": "Ranged",
}

SLOT_ALIASES = {
    "head": "head",
    "helm": "head",
    "helmet": "head",
    "torso": "torso",
    "chest": "torso",
    "body": "torso",
    "arms": "arms",
    "sleeves": "arms",
    "hands": "hands",
    "hand": "hands",
    "gloves": "hands",
    "legs": "legs",
    "leggings": "legs",
    "feet": "feet",
    "boots": "feet",
    "neck": "neck",
    "necklace": "neck",
    "cloak": "cloak",
    "jewel": "jewel",
    "jewelry": "jewel",
    "gem": "jewel",
    "belt": "belt",
    "waist": "belt",
    "lwrist": "lwrist",
    "l wrist": "lwrist",
    "left wrist": "lwrist",
    "left bracer": "lwrist",
    "rwrist": "rwrist",
    "r wrist": "rwrist",
    "right wrist": "rwrist",
    "right bracer": "rwrist",
    "lring": "lring",
    "l ring": "lring",
    "left ring": "lring",
    "rring": "rring",
    "r ring": "rring",
    "right ring": "rring",
    "mythical": "mythical",
    "myth": "mythical",
    "mainhand": "mainhand",
    "main hand": "mainhand",
    "right hand": "mainhand",
    "r hand": "mainhand",
    "weapon": "mainhand",
    "offhand": "offhand",
    "off hand": "offhand",
    "left hand": "offhand",
    "l hand": "offhand",
    "shield": "offhand",
    "twohanded": "twohanded",
    "two handed": "twohanded",
    "two hand": "twohanded",
    "2h": "twohanded",
    "ranged": "ranged",
    "bow": "ranged",
    "instrument": "ranged",
}

ALBION_CLASS_NAMES = {
    "Armsman",
    "Cabalist",
    "Cleric",
    "Friar",
    "Heretic",
    "Infiltrator",
    "Mercenary",
    "Minstrel",
    "Necromancer",
    "Paladin",
    "Reaver",
    "Scout",
    "Sorcerer",
    "Theurgist",
    "Wizard",
}
DEFAULT_ZENK_CLASS = "Minstrel"

REALM_ID_BY_NAME = {
    "Albion": "68ed9771-239c-4b7a-8d83-28d05c437277",
    "Midgard": "1a2a5a33-978a-4f76-bb83-b378ffceb008",
    "Hibernia": "d886a40c-c6ec-43ac-af35-18e5e5f2cc81",
}

REALM_SUFFIX_BY_NAME = {
    "albion": "alb",
    "midgard": "mid",
    "hibernia": "hib",
}

REALM_NAME_BY_SUFFIX = {
    "alb": "Albion",
    "mid": "Midgard",
    "hib": "Hibernia",
}

TIER_BY_NAME = {
    "raw": 1,
    "uncut": 2,
    "rough": 3,
    "flawed": 4,
    "imperfect": 5,
    "polished": 6,
    "faceted": 7,
    "precious": 8,
    "flawless": 9,
    "perfect": 10,
}
TIER_NAMES = {value: key.title() for key, value in TIER_BY_NAME.items()}

STAT_VALUE = {1: 1, 2: 4, 3: 7, 4: 10, 5: 13, 6: 16, 7: 19, 8: 22, 9: 25, 10: 28}
HITS_VALUE = {1: 4, 2: 12, 3: 20, 4: 28, 5: 36, 6: 44, 7: 52, 8: 60, 9: 68, 10: 76}
RESIST_VALUE = {1: 1, 2: 2, 3: 3, 4: 5, 5: 7, 6: 9, 7: 11, 8: 13, 9: 15, 10: 17}
POWER_VALUE = RESIST_VALUE
FOCUS_VALUE = {tier: tier * 5 for tier in range(1, 11)}
SKILL_VALUE = {tier: tier for tier in range(1, 11)}

STAT_IMBUE = {1: 0.5, 2: 1, 3: 2, 4: 3, 5: 4.5, 6: 5.5, 7: 7, 8: 7.5, 9: 9, 10: 9.5}
HITS_IMBUE = {1: 0.5, 2: 2, 3: 3, 4: 4, 5: 5, 6: 5.5, 7: 6.5, 8: 7.5, 9: 8.5, 10: 9.5}
RESIST_IMBUE = {1: 0.5, 2: 1, 3: 2, 4: 4, 5: 6, 6: 8, 7: 10, 8: 12, 9: 14, 10: 16}
POWER_IMBUE = RESIST_IMBUE
SKILL_IMBUE = {1: 0.5, 2: 3, 3: 5, 4: 7, 5: 10, 6: 13, 7: 16, 8: 19, 9: 22, 10: 25}
FOCUS_IMBUE = SKILL_IMBUE

STAT_BY_ADJECTIVE = {
    "fiery": "strength",
    "earthen": "constitution",
    "vapor": "dexterity",
    "airy": "quickness",
    "dusty": "intelligence",
    "watery": "piety",
    "icy": "charisma",
    "heated": "empathy",
}

RESIST_BY_ADJECTIVE = {
    "fiery": "crush",
    "watery": "slash",
    "airy": "thrust",
    "dusty": "body",
    "icy": "cold",
    "light": "energy",
    "heated": "heat",
    "earthen": "matter",
    "vapor": "spirit",
}

SKILL_BY_GEM_FAMILY = {
    "airy battle jewel": "stealth_alb",
    "airy battle sigil": "stealth_alb",
    "airy evocation sigil": "wind_magic",
    "airy fervor sigil": "enhancements",
    "airy war sigil": "longbow",
    "ashen fervor sigil": "death_servant",
    "brilliant sigil": "all_focus_alb",
    "cinder war sigil": "mauler_staff_alb",
    "clout fervor sigil": "power_strike_alb",
    "dusty battle jewel": "envenom_alb",
    "dusty battle sigil": "envenom_alb",
    "dusty evocation sigil": "matter_magic",
    "dusty war sigil": "thrusting",
    "earthen battle jewel": "staff_alb",
    "earthen battle sigil": "staff_alb",
    "earthen evocation sigil": "earth_magic",
    "earthen fervor sigil": "chants",
    "earthen war sigil": "polearm",
    "fiery battle jewel": "shield_alb",
    "fiery battle sigil": "shield_alb",
    "fiery evocation sigil": "fire_magic",
    "fiery fervor sigil": "smite",
    "fiery war sigil": "crushing",
    "finesse fervor sigil": "all_magic_alb",
    "finesse war sigil": "all_melee_alb",
    "glacier war sigil": "fist_wraps_alb",
    "heated battle jewel": "critical_strike_alb",
    "heated battle sigil": "critical_strike_alb",
    "heated evocation sigil": "body_magic",
    "heated war sigil": "two_handed",
    "icy evocation sigil": "cold_magic",
    "icy war sigil": "dual_wield",
    "magnetic fervor sigil": "magnetism_alb",
    "molten magma war sigil": "flexible",
    "radiant fervor sigil": "aura_manipulation_alb",
    "salt crusted fervor sigil": "painworking",
    "salt encrusted fervor sigil": "painworking",
    "steaming fervor sigil": "soulrending",
    "vacuous fervor sigil": "deathsight",
    "vapor battle jewel": "parry_alb",
    "vapor battle sigil": "parry_alb",
    "vapor evocation sigil": "spirit_magic",
    "vapor fervor sigil": "instruments",
    "vapor war sigil": "crossbow",
    "watery evocation sigil": "mind_magic",
    "watery fervor sigil": "rejuvenation",
    "watery war sigil": "slashing",
}

SKILL_GEM_FAMILY_BY_TYPE = {value: key for key, value in SKILL_BY_GEM_FAMILY.items()}
SKILL_GEM_FAMILY_BY_TYPE.update(
    {
        "all_focus_hib": "brilliant stone",
        "all_focus_mid": "brilliant rune",
        "all_magic_hib": "finesse nature spell stone",
        "all_magic_mid": "finesse primal rune",
        "all_melee_hib": "finesse war spell stone",
        "all_melee_mid": "finesse war rune",
        "arboreal_path": "steaming nature spell stone",
        "augmentation": "airy primal rune",
        "aura_manipulation_hib": "radiant nature spell stone",
        "aura_manipulation_mid": "radiant primal rune",
        "axe": "dusty war rune",
        "battlesongs": "vapor primal rune",
        "beastcraft": "earthen primal rune",
        "blades": "watery war spell stone",
        "blunt": "fiery war spell stone",
        "bonedancing": "ashen primal rune",
        "celtic_dual": "icy war spell stone",
        "celtic_spear": "earthen war spell stone",
        "composite_bow": "airy war rune",
        "creeping_path": "oozing nature spell stone",
        "critical_strike_hib": "heated battle stone",
        "critical_strike_mid": "heated battle rune",
        "darkness": "icy primal rune",
        "enchantments": "vapor arcane spell stone",
        "envenom_hib": "dusty battle stone",
        "envenom_mid": "dusty battle rune",
        "fist_wraps_hib": "glacier war spell stone",
        "fist_wraps_mid": "glacier war rune",
        "hammer": "fiery war rune",
        "hand_to_hand": "light war rune",
        "large_weapons": "heated war spell stone",
        "left_axe": "icy war rune",
        "light_magic": "fiery arcane spell stone",
        "magnetism_hib": "magnetic nature spell stone",
        "magnetism_mid": "magnetic primal rune",
        "mana_magic": "watery arcane spell stone",
        "mauler_staff_hib": "cinder war spell stone",
        "mauler_staff_mid": "cinder war rune",
        "mending": "watery primal rune",
        "mentalism": "earthen arcane spell stone",
        "music": "vapor nature spell stone",
        "nature": "earthen nature spell stone",
        "nurture": "fiery nature spell stone",
        "odins_will": "dusty primal rune",
        "pacification": "earthen primal rune",
        "parry_hib": "vapor battle stone",
        "parry_mid": "vapor battle rune",
        "piercing": "dusty war spell stone",
        "power_strike_hib": "clout nature spell stone",
        "power_strike_mid": "clout primal rune",
        "recurved_bow": "airy war spell stone",
        "regrowth": "watery nature spell stone",
        "runecarving": "fiery primal rune",
        "scythe": "light war spell stone",
        "shield_hib": "fiery battle stone",
        "shield_mid": "fiery battle rune",
        "spear": "heated war rune",
        "staff_hib": "earthen battle stone",
        "staff_mid": "earthen battle rune",
        "stealth_hib": "airy battle stone",
        "stealth_mid": "airy battle rune",
        "stormcalling": "fiery primal rune",
        "subterranean": "fiery primal rune",
        "summoning": "vapor primal rune",
        "suppression": "heated primal rune",
        "sword": "watery war rune",
        "thrown_weapons": "airy war rune",
        "valor": "airy nature spell stone",
        "verdant_path": "mineral encrusted nature spell stone",
        "void_magic": "icy arcane spell stone",
    }
)
for type_key, family in SKILL_GEM_FAMILY_BY_TYPE.items():
    SKILL_BY_GEM_FAMILY.setdefault(family, type_key)

BONUS_CODE_BY_TYPE = {
    "strength": 1,
    "dexterity": 2,
    "constitution": 3,
    "quickness": 4,
    "intelligence": 5,
    "piety": 6,
    "charisma": 7,
    "empathy": 8,
    "power": 9,
    "hits": 10,
    "body": 11,
    "cold": 12,
    "crush": 13,
    "energy": 14,
    "heat": 15,
    "matter": 16,
    "slash": 17,
    "spirit": 18,
    "thrust": 19,
    "two_handed": 20,
    "body_magic": 21,
    "chants": 22,
    "critical_strike_alb": 23,
    "crossbow": 24,
    "crushing": 25,
    "death_servant": 26,
    "deathsight": 27,
    "dual_wield": 28,
    "earth_magic": 29,
    "enhancements": 30,
    "envenom_alb": 31,
    "fire_magic": 32,
    "flexible": 33,
    "cold_magic": 34,
    "instruments": 35,
    "longbow": 36,
    "matter_magic": 37,
    "mind_magic": 38,
    "painworking": 39,
    "parry_alb": 40,
    "polearm": 41,
    "rejuvenation": 42,
    "shield_alb": 43,
    "slashing": 44,
    "smite": 45,
    "soulrending": 46,
    "spirit_magic": 47,
    "staff_alb": 48,
    "stealth_alb": 49,
    "thrusting": 50,
    "wind_magic": 51,
    "fist_wraps_alb": 100,
    "mauler_staff_alb": 101,
    "aura_manipulation_alb": 102,
    "magnetism_alb": 103,
    "power_strike_alb": 104,
    "all_focus_alb": 131,
    "acuity": 156,
    "all_melee_alb": 200,
    "all_magic_alb": 201,
    "shadow_mastery": 100,
    "all_dual_wield": 167,
}
BONUS_CODE_BY_TYPE.update(
    {
        "all_focus_hib": 131,
        "all_focus_mid": 131,
        "all_magic_hib": 203,
        "all_magic_mid": 205,
        "all_melee_hib": 202,
        "all_melee_mid": 204,
        "arboreal_path": 89,
        "augmentation": 58,
        "aura_manipulation_hib": 102,
        "aura_manipulation_mid": 102,
        "axe": 54,
        "battlesongs": 69,
        "beastcraft": 64,
        "blades": 72,
        "blunt": 73,
        "bonedancing": 86,
        "celtic_dual": 81,
        "celtic_spear": 82,
        "composite_bow": 68,
        "creeping_path": 88,
        "critical_strike_hib": 23,
        "critical_strike_mid": 23,
        "darkness": 60,
        "enchantments": 70,
        "envenom_hib": 31,
        "envenom_mid": 31,
        "fist_wraps_hib": 100,
        "fist_wraps_mid": 100,
        "hammer": 53,
        "hand_to_hand": 92,
        "large_weapons": 75,
        "left_axe": 55,
        "light_magic": 65,
        "magnetism_hib": 103,
        "magnetism_mid": 103,
        "mana_magic": 67,
        "mauler_staff_hib": 101,
        "mauler_staff_mid": 101,
        "mending": 57,
        "mentalism": 76,
        "music": 80,
        "nature": 79,
        "nurture": 78,
        "odins_will": 105,
        "pacification": 94,
        "parry_hib": 40,
        "parry_mid": 40,
        "piercing": 74,
        "power_strike_hib": 104,
        "power_strike_mid": 104,
        "recurved_bow": 83,
        "regrowth": 77,
        "runecarving": 62,
        "scythe": 90,
        "shield_hib": 43,
        "shield_mid": 43,
        "spear": 56,
        "staff_hib": 48,
        "staff_mid": 48,
        "stealth_hib": 49,
        "stealth_mid": 49,
        "stormcalling": 63,
        "subterranean": 85,
        "summoning": 98,
        "suppression": 61,
        "sword": 52,
        "thrown_weapons": 91,
        "valor": 84,
        "verdant_path": 87,
        "void_magic": 66,
    }
)

DISPLAY_BY_TYPE = {
    "strength": "Strength",
    "dexterity": "Dexterity",
    "constitution": "Constitution",
    "quickness": "Quickness",
    "intelligence": "Intelligence",
    "piety": "Piety",
    "charisma": "Charisma",
    "empathy": "Empathy",
    "acuity": "Acuity",
    "hits": "Hit Points",
    "power": "Power",
    "all_focus_alb": "All Focus",
    "body": "Body",
    "cold": "Cold",
    "crush": "Crush",
    "energy": "Energy",
    "heat": "Heat",
    "matter": "Matter",
    "slash": "Slash",
    "spirit": "Spirit",
    "thrust": "Thrust",
    "all_magic_alb": "All Magic",
    "all_melee_alb": "All Melee",
    "aura_manipulation_alb": "Aura Manipulation",
    "body_magic": "Body Magic",
    "chants": "Chants",
    "cold_magic": "Cold Magic",
    "critical_strike_alb": "Critical Strike",
    "crossbow": "Crossbow",
    "crushing": "Crushing",
    "death_servant": "Death Servant",
    "deathsight": "Deathsight",
    "dual_wield": "Dual Wield",
    "earth_magic": "Earth Magic",
    "enhancements": "Enhancements",
    "envenom_alb": "Envenom",
    "fire_magic": "Fire Magic",
    "fist_wraps_alb": "Fist Wraps",
    "flexible": "Flexible",
    "instruments": "Instruments",
    "longbow": "Longbow",
    "magnetism_alb": "Magnetism",
    "matter_magic": "Matter Magic",
    "mauler_staff_alb": "Mauler Staff",
    "mind_magic": "Mind Magic",
    "painworking": "Painworking",
    "parry_alb": "Parry",
    "polearm": "Polearm",
    "power_strike_alb": "Power Strike",
    "rejuvenation": "Rejuvenation",
    "shield_alb": "Shield",
    "slashing": "Slashing",
    "smite": "Smite",
    "soulrending": "Soulrending",
    "spirit_magic": "Spirit Magic",
    "staff_alb": "Staff",
    "stealth_alb": "Stealth",
    "thrusting": "Thrusting",
    "two_handed": "Two Handed",
    "wind_magic": "Wind Magic",
    "all_melee_skills": "All Melee Skills",
    "all_dual_wield": "All Dual Wield",
    "shadow_mastery": "Shadow Mastery",
}
DISPLAY_BY_TYPE.update(
    {
        "all_focus_hib": "All Focus",
        "all_focus_mid": "All Focus",
        "all_magic_hib": "All Magic",
        "all_magic_mid": "All Magic",
        "all_melee_hib": "All Melee",
        "all_melee_mid": "All Melee",
        "arboreal_path": "Arboreal Path",
        "augmentation": "Augmentation",
        "aura_manipulation_hib": "Aura Manipulation",
        "aura_manipulation_mid": "Aura Manipulation",
        "axe": "Axe",
        "battlesongs": "Battlesongs",
        "beastcraft": "Beastcraft",
        "blades": "Blades",
        "blunt": "Blunt",
        "bonedancing": "Bonedancing",
        "celtic_dual": "Celtic Dual",
        "celtic_spear": "Celtic Spear",
        "composite_bow": "Composite Bow",
        "creeping_path": "Creeping Path",
        "critical_strike_hib": "Critical Strike",
        "critical_strike_mid": "Critical Strike",
        "darkness": "Darkness",
        "enchantments": "Enchantments",
        "envenom_hib": "Envenom",
        "envenom_mid": "Envenom",
        "fist_wraps_hib": "Fist Wraps",
        "fist_wraps_mid": "Fist Wraps",
        "hammer": "Hammer",
        "hand_to_hand": "Hand to Hand",
        "large_weapons": "Large Weapons",
        "left_axe": "Left Axe",
        "light_magic": "Light Magic",
        "magnetism_hib": "Magnetism",
        "magnetism_mid": "Magnetism",
        "mana_magic": "Mana Magic",
        "mauler_staff_hib": "Mauler Staff",
        "mauler_staff_mid": "Mauler Staff",
        "mending": "Mending",
        "mentalism": "Mentalism",
        "music": "Music",
        "nature": "Nature",
        "nurture": "Nurture",
        "odins_will": "Odin's Will",
        "pacification": "Pacification",
        "parry_hib": "Parry",
        "parry_mid": "Parry",
        "piercing": "Piercing",
        "power_strike_hib": "Power Strike",
        "power_strike_mid": "Power Strike",
        "recurved_bow": "Recurved Bow",
        "regrowth": "Regrowth",
        "runecarving": "Runecarving",
        "scythe": "Scythe",
        "shield_hib": "Shield",
        "shield_mid": "Shield",
        "spear": "Spear",
        "staff_hib": "Staff",
        "staff_mid": "Staff",
        "stealth_hib": "Stealth",
        "stealth_mid": "Stealth",
        "stormcalling": "Stormcalling",
        "subterranean": "Subterranean",
        "summoning": "Summoning",
        "suppression": "Suppression",
        "sword": "Sword",
        "thrown_weapons": "Thrown Weapons",
        "valor": "Valor",
        "verdant_path": "Verdant Path",
        "void_magic": "Void Magic",
    }
)

ZENK_DISPLAY_BY_TYPE = {
    "all_magic_alb": "All Magic Skills",
    "all_melee_alb": "All Melee Skills",
    "crushing": "Crush",
    "enhancements": "Enhancement",
    "polearm": "Polearms",
    "slashing": "Slash",
    "thrusting": "Thrust",
}
ZENK_DISPLAY_BY_TYPE.update(
    {
        "all_magic_hib": "All Magic Skills",
        "all_magic_mid": "All Magic Skills",
        "all_melee_hib": "All Melee Skills",
        "all_melee_mid": "All Melee Skills",
        "bone_army": "Bone Army",
        "bonedancing": "Bonedancing",
        "large_weapons": "Large Weaponry",
        "recurved_bow": "Recurve Bow",
    }
)

REALM_SKILL_TYPES = {
    "albion": {
        "all_magic_alb",
        "all_melee_alb",
        "aura_manipulation_alb",
        "body_magic",
        "chants",
        "cold_magic",
        "critical_strike_alb",
        "crossbow",
        "crushing",
        "death_servant",
        "deathsight",
        "dual_wield",
        "earth_magic",
        "enhancements",
        "envenom_alb",
        "fire_magic",
        "fist_wraps_alb",
        "flexible",
        "instruments",
        "longbow",
        "magnetism_alb",
        "matter_magic",
        "mauler_staff_alb",
        "mind_magic",
        "painworking",
        "parry_alb",
        "polearm",
        "power_strike_alb",
        "rejuvenation",
        "shield_alb",
        "slashing",
        "smite",
        "soulrending",
        "spirit_magic",
        "staff_alb",
        "stealth_alb",
        "thrusting",
        "two_handed",
        "wind_magic",
    },
    "midgard": {
        "all_magic_mid",
        "all_melee_mid",
        "augmentation",
        "aura_manipulation_mid",
        "axe",
        "battlesongs",
        "beastcraft",
        "bonedancing",
        "composite_bow",
        "critical_strike_mid",
        "darkness",
        "envenom_mid",
        "fist_wraps_mid",
        "hammer",
        "hand_to_hand",
        "left_axe",
        "magnetism_mid",
        "mauler_staff_mid",
        "mending",
        "odins_will",
        "pacification",
        "parry_mid",
        "power_strike_mid",
        "runecarving",
        "shield_mid",
        "spear",
        "staff_mid",
        "stealth_mid",
        "stormcalling",
        "subterranean",
        "summoning",
        "suppression",
        "sword",
        "thrown_weapons",
    },
    "hibernia": {
        "all_magic_hib",
        "all_melee_hib",
        "arboreal_path",
        "aura_manipulation_hib",
        "blades",
        "blunt",
        "celtic_dual",
        "celtic_spear",
        "creeping_path",
        "critical_strike_hib",
        "enchantments",
        "envenom_hib",
        "fist_wraps_hib",
        "large_weapons",
        "light_magic",
        "magnetism_hib",
        "mana_magic",
        "mauler_staff_hib",
        "mentalism",
        "music",
        "nature",
        "nurture",
        "parry_hib",
        "piercing",
        "power_strike_hib",
        "recurved_bow",
        "regrowth",
        "scythe",
        "shield_hib",
        "staff_hib",
        "stealth_hib",
        "valor",
        "verdant_path",
        "void_magic",
    },
}

ZENK_CONFIG_CANDIDATES = [
    Path(r"F:\SteamLibrary\steamapps\common\ZenkCraft\ZenkcraftRemastered\ZenkcraftRemastered_Data\Eden-ZenkServerConfig.zsc"),
    Path(r"D:\Software\Steam\steamapps\common\ZenkCraft\ZenkcraftRemastered\ZenkcraftRemastered_Data\Eden-ZenkServerConfig.zsc"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\ZenkCraft\ZenkcraftRemastered\ZenkcraftRemastered_Data\Eden-ZenkServerConfig.zsc"),
    Path(r"C:\Program Files\Steam\steamapps\common\ZenkCraft\ZenkcraftRemastered\ZenkcraftRemastered_Data\Eden-ZenkServerConfig.zsc"),
]

MANUAL_GEM_BASE_ID_BY_TYPE = {
    # Zenk's Eden config currently has a placeholder for Albion Crossbow, but
    # the surrounding Albion war-sigil sequence makes this base ID clear.
    "crossbow": 130580,
}

ICON_BY_FIRST_WORD = {
    "blood": 150,
    "fiery": 150,
    "heated": 150,
    "mystic": 150,
    "mystical": 150,
    "earthen": 152,
    "watery": 155,
    "icy": 156,
    "vapor": 156,
    "light": 157,
    "dusty": 158,
}

FALLBACK_GEM_BASE_ID_BY_TYPE = {
    "strength": 130000,
    "constitution": 130020,
    "dexterity": 130040,
    "quickness": 130060,
    "piety": 130080,
    "empathy": 130100,
    "intelligence": 130120,
    "charisma": 130140,
    "matter": 130160,
    "cold": 130180,
    "heat": 130200,
    "energy": 130220,
    "thrust": 130240,
    "spirit": 130260,
    "body": 130280,
    "crush": 130300,
    "slash": 130320,
    "parry_alb": 130340,
    "shield_alb": 130360,
    "staff_alb": 130380,
    "stealth_alb": 130400,
    "envenom_alb": 130420,
    "critical_strike_alb": 130440,
    "slashing": 130460,
    "crushing": 130480,
    "thrusting": 130500,
    "two_handed": 130520,
    "polearm": 130540,
    "longbow": 130560,
    "crossbow": 130580,
    "all_melee_alb": 130600,
    "dual_wield": 130620,
    "all_magic_alb": 130640,
    "smite": 130660,
    "enhancements": 130680,
    "rejuvenation": 130700,
    "chants": 130720,
    "instruments": 130740,
    "earth_magic": 130760,
    "cold_magic": 130780,
    "fire_magic": 130800,
    "wind_magic": 130820,
    "body_magic": 130840,
    "matter_magic": 130860,
    "spirit_magic": 130880,
    "mind_magic": 130900,
    "hits": 130920,
    "power": 130940,
    "flexible": 131120,
    "deathsight": 131140,
    "painworking": 131160,
    "death_servant": 131180,
    "soulrending": 131200,
}

REALM_FALLBACK_GEM_BASE_ID_BY_TYPE = {
    "midgard": {
        "hits": 130860,
        "power": 130880,
        "all_melee_mid": 130600,
        "all_magic_mid": 130640,
        "augmentation": 130800,
        "axe": 130500,
        "battlesongs": 130660,
        "beastcraft": 130620,
        "bonedancing": 130960,
        "composite_bow": 130540,
        "critical_strike_mid": 130440,
        "darkness": 130700,
        "envenom_mid": 130420,
        "hammer": 130480,
        "hand_to_hand": 130940,
        "left_axe": 130580,
        "mending": 130780,
        "pacification": 130820,
        "parry_mid": 130340,
        "runecarving": 130740,
        "shield_mid": 130360,
        "spear": 130520,
        "stealth_mid": 130400,
        "stormcalling": 130680,
        "subterranean": 130820,
        "summoning": 130760,
        "suppression": 130720,
        "sword": 130460,
        "thrown_weapons": 130560,
    },
    "hibernia": {
        "hits": 130840,
        "power": 130860,
        "all_melee_hib": 130620,
        "all_magic_hib": 130660,
        "arboreal_path": 131000,
        "blades": 130460,
        "blunt": 130480,
        "celtic_dual": 130560,
        "celtic_spear": 130540,
        "creeping_path": 131020,
        "critical_strike_hib": 130440,
        "enchantments": 130780,
        "envenom_hib": 130420,
        "large_weapons": 130520,
        "light_magic": 130740,
        "mana_magic": 130760,
        "mentalism": 130820,
        "music": 130700,
        "nature": 130680,
        "nurture": 130620,
        "parry_hib": 130340,
        "piercing": 130500,
        "recurved_bow": 130580,
        "regrowth": 130660,
        "scythe": 130020,
        "shield_hib": 130360,
        "stealth_hib": 130400,
        "valor": 130720,
        "verdant_path": 131040,
        "void_magic": 130800,
    },
}


def default_eden_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return base / "Electronic Arts" / "Dark Age of Camelot" / "eden"


def find_default_eden_ini(eden_dir: Path | None = None) -> Path | None:
    eden_dir = eden_dir or default_eden_dir()
    if not eden_dir.exists():
        return None
    ini_files = [
        path
        for path in eden_dir.glob("*.ini")
        if path.is_file()
        and "backup" not in path.name.lower()
        and "back_up" not in path.name.lower()
        and "copy" not in path.stem.lower()
    ]
    if not ini_files:
        return None
    return max(ini_files, key=lambda path: path.stat().st_mtime)


DEFAULT_SETTINGS = {
    "last_input_path": "",
    "last_input_dir": "",
    "last_chat_log_path": "",
    "input_source": "paste",
    "last_eden_dir": str(default_eden_dir()),
    "last_ini_path": str(find_default_eden_ini() or ""),
    "last_export_dir": "",
    "last_action": "forge",
    "realm": "Albion",
    "quickbar": 1,
    "page": 3,
    "slot": 1,
    "include_item_separators": True,
    "open_output_location": False,
}

def default_settings_path() -> Path:
    if getattr(sys, "frozen", False):
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home()
        return base / "Daoc Craft tool" / "settings.json"
    return Path(__file__).with_name("sc_craft_tool_settings.json")


SETTINGS_PATH = default_settings_path()


@dataclass
class WarningBag:
    messages: list[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        if message not in self.messages:
            self.messages.append(message)


BLOCKING_WARNING_PREFIXES = (
    "Skipped possible gem",
    "Could not identify gem text",
)


def blocking_warnings(warnings: WarningBag) -> list[str]:
    return [
        message
        for message in warnings.messages
        if message.startswith(BLOCKING_WARNING_PREFIXES)
    ]


@dataclass
class Gem:
    name: str
    tier: int
    category: str
    type: str
    display: str
    value: int
    imbue: float
    bonus_code: int | None = None

    @property
    def forge_gem_name(self) -> str:
        name = self.name
        if self.category == "power":
            name = name.replace("Mystical Essence Jewel", "Mystic Essence Jewel")
        return name.replace("Battle Jewel", "Battle Sigil").replace(
            "Salt Encrusted Fervor Sigil", "Salt Crusted Fervor Sigil"
        )

    @property
    def zenk_gem_name(self) -> str:
        tier_name, rest = split_tier_from_name(self.name)
        rest = (
            rest.replace("Mystic Essence Jewel", "Mystical Essence Jewel")
            .replace("Battle Sigil", "Battle Jewel")
            .replace("Salt Crusted Fervor Sigil", "Salt Encrusted Fervor Sigil")
        )
        return f"({tier_name}) {rest}"

    @property
    def forge_bonus_type(self) -> str:
        if self.category == "hits":
            return "Hits"
        if self.category == "focus":
            return "Focus"
        return self.category.title()

    @property
    def forge_stat(self) -> str:
        if self.category == "hits":
            return "Hits"
        if self.category == "resist":
            return f"{self.display} Resist"
        if self.category == "focus":
            return f"{self.display} Focus"
        return self.display

    @property
    def zenk_group(self) -> str:
        if self.category == "hits":
            return "Stat"
        if self.category == "power":
            return "Power"
        if self.category == "focus":
            return "Focus"
        return self.category.title()

    @property
    def zenk_display(self) -> str:
        if self.category == "hits":
            return "Hit Points"
        return ZENK_DISPLAY_BY_TYPE.get(self.type, self.display)

    @property
    def zenk_suffix(self) -> str:
        return "%" if self.category == "resist" else ""

    @property
    def utility(self) -> float:
        if self.category == "stat":
            return self.value * 2 / 3
        if self.category == "hits":
            return self.value / 4
        if self.category == "resist":
            return self.value * 2
        if self.category == "skill":
            return self.value * 5
        if self.category == "power":
            return self.value
        return 0


@dataclass
class Item:
    slot: str
    gems: list[Gem] = field(default_factory=list)
    quality: int = 99
    current_imbue: float | None = None

    @property
    def title(self) -> str:
        return SLOT_TITLES.get(self.slot, title_from_type(self.slot))

    @property
    def computed_imbue(self) -> float:
        if not self.gems:
            return 0
        values = [gem.imbue for gem in self.gems]
        return sum(values) + max(values)

    @property
    def imbue(self) -> float:
        return self.current_imbue if self.current_imbue is not None else self.computed_imbue

    @property
    def utility(self) -> float:
        return sum(gem.utility for gem in self.gems)


@dataclass
class BarSetupResult:
    ini_path: Path
    backup_path: Path
    quickbar_section: str
    start_hotkey: int
    hotkey_count: int
    macro_count: int
    backup_cleanup_count: int = 0


def load_settings(path: Path = SETTINGS_PATH) -> dict:
    settings = dict(DEFAULT_SETTINGS)
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            loaded = {}
        if isinstance(loaded, dict):
            settings.update(loaded)
    return settings


def save_settings(settings: dict, path: Path = SETTINGS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def find_zenk_config(explicit_path: str | None = None) -> Path | None:
    candidates = [Path(explicit_path)] if explicit_path else []
    candidates.extend(ZENK_CONFIG_CANDIDATES)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def canonical_realm(realm: str | None) -> str:
    cleaned = clean_key(realm or "Albion")
    if cleaned in REALM_SUFFIX_BY_NAME:
        return REALM_NAME_BY_SUFFIX[REALM_SUFFIX_BY_NAME[cleaned]]
    for name in REALM_ID_BY_NAME:
        if clean_key(name).startswith(cleaned):
            return name
    return "Albion"


def realm_suffix(realm: str | None) -> str:
    return REALM_SUFFIX_BY_NAME[clean_key(canonical_realm(realm))]


def zenk_skill_type(skill_name: str, realm: str = "Albion") -> str:
    return type_from_display(skill_name, realm)


def load_gem_base_ids(realm: str = "Albion", zenk_config: str | None = None) -> dict[str, int]:
    realm = canonical_realm(realm)
    ids = dict(FALLBACK_GEM_BASE_ID_BY_TYPE)
    ids.update(REALM_FALLBACK_GEM_BASE_ID_BY_TYPE.get(clean_key(realm), {}))
    ids.update(MANUAL_GEM_BASE_ID_BY_TYPE)
    config_path = find_zenk_config(zenk_config)
    if not config_path:
        return ids

    root = ET.parse(config_path).getroot()
    for node in root.findall("./statConfig/stats/StatInfo"):
        if (node.findtext("realm") or "").lower() != realm.lower():
            continue
        gem_id = parse_optional_int(node.findtext("gemId"))
        if gem_id is not None:
            ids[type_from_display(node.findtext("statName") or "")] = gem_id

    hit_points = root.find("./hpPowerConfig/hitPoints")
    if hit_points is not None:
        gem_id = parse_optional_int(hit_points.findtext(f"gemId_{realm[:3].title()}"))
        if gem_id is not None:
            ids["hits"] = gem_id

    power = root.find("./hpPowerConfig/power")
    if power is not None:
        gem_id = parse_optional_int(power.findtext(f"gemId_{realm[:3].title()}"))
        if gem_id is not None:
            ids["power"] = gem_id

    for node in root.findall("./resistConfig/resists/ResistInfo"):
        if (node.findtext("realm") or "").lower() != realm.lower():
            continue
        gem_id = parse_optional_int(node.findtext("gemId"))
        if gem_id is not None:
            ids[type_from_display(node.findtext("resistName") or "")] = gem_id

    for node in root.findall("./skillConfig/skills/SkillInfo"):
        if (node.findtext("realm") or "").lower() != realm.lower():
            continue
        gem_id = parse_optional_int(node.findtext("gemId"))
        if gem_id is None or gem_id == 123456:
            continue
        ids[zenk_skill_type(node.findtext("skillName") or "", realm)] = gem_id

    ids.update(MANUAL_GEM_BASE_ID_BY_TYPE)
    return ids


def parse_optional_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def clean_key(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def title_from_type(value: str) -> str:
    return DISPLAY_BY_TYPE.get(value, value.replace("_", " ").title())


def type_from_display(value: str, realm: str = "Albion") -> str:
    original_cleaned = clean_key(value)
    suffix = realm_suffix(realm)
    aliases = {
        "all magic skills": f"all_magic_{suffix}",
        "all magic": f"all_magic_{suffix}",
        "all melee skills": f"all_melee_{suffix}",
        "all melee weapon skills": f"all_melee_{suffix}",
        "all melee": f"all_melee_{suffix}",
        "all focus focus": f"all_focus_{suffix}",
        "all focus": f"all_focus_{suffix}",
        "crush": "crushing",
        "slash": "slashing",
        "thrust": "thrusting",
        "enhancement": "enhancements",
        "polearms": "polearm",
        "critical strike": f"critical_strike_{suffix}",
        "envenom": f"envenom_{suffix}",
        "fist wraps": f"fist_wraps_{suffix}",
        "magnetism": f"magnetism_{suffix}",
        "mauler staff": f"mauler_staff_{suffix}",
        "power strike": f"power_strike_{suffix}",
        "staff": f"staff_{suffix}",
        "stealth": f"stealth_{suffix}",
        "shield": f"shield_{suffix}",
        "parry": f"parry_{suffix}",
    }
    realm_aliases = {
        "albion": {
            "enhancement": "enhancements",
            "thrust": "thrusting",
            "slash": "slashing",
            "crush": "crushing",
        },
        "midgard": {
            "augmentation": "augmentation",
            "aura manipulation": "aura_manipulation_mid",
            "axe": "axe",
            "battlesongs": "battlesongs",
            "beastcraft": "beastcraft",
            "bone army": "bonedancing",
            "bonedancing": "bonedancing",
            "composite bow": "composite_bow",
            "darkness": "darkness",
            "hammer": "hammer",
            "hand to hand": "hand_to_hand",
            "left axe": "left_axe",
            "mending": "mending",
            "odins will": "odins_will",
            "pacification": "pacification",
            "runecarving": "runecarving",
            "spear": "spear",
            "stormcalling": "stormcalling",
            "subterranean": "subterranean",
            "summoning": "summoning",
            "suppression": "suppression",
            "sword": "sword",
            "thrown weapon": "thrown_weapons",
            "thrown weapons": "thrown_weapons",
        },
        "hibernia": {
            "arboreal path": "arboreal_path",
            "aura manipulation": "aura_manipulation_hib",
            "blades": "blades",
            "blunt": "blunt",
            "celtic dual": "celtic_dual",
            "celtic spear": "celtic_spear",
            "creeping": "creeping_path",
            "creeping path": "creeping_path",
            "enchantments": "enchantments",
            "large weaponry": "large_weapons",
            "large weapons": "large_weapons",
            "light": "light_magic",
            "light magic": "light_magic",
            "mana": "mana_magic",
            "mana magic": "mana_magic",
            "mentalism": "mentalism",
            "music": "music",
            "nature": "nature",
            "nurture": "nurture",
            "piercing": "piercing",
            "recurve bow": "recurved_bow",
            "recurved bow": "recurved_bow",
            "regrowth": "regrowth",
            "scythe": "scythe",
            "valor": "valor",
            "verdant": "verdant_path",
            "verdant path": "verdant_path",
            "void": "void_magic",
            "void magic": "void_magic",
        },
    }
    aliases.update(realm_aliases.get(clean_key(canonical_realm(realm)), {}))
    if original_cleaned in aliases:
        return aliases[original_cleaned]
    value = re.sub(r"\bresist\b", "", value, flags=re.I)
    value = re.sub(r"\bcap\b", "", value, flags=re.I)
    value = re.sub(r"\bfocus\b", "", value, flags=re.I)
    value = value.strip()
    if clean_key(value) in {"hit points", "hits", "h p", "hp"}:
        return "hits"
    cleaned = clean_key(value)
    if cleaned in aliases:
        return aliases[cleaned]
    for type_key, display in DISPLAY_BY_TYPE.items():
        if clean_key(display) == cleaned:
            return type_key
    return cleaned.replace(" ", "_")


def slot_from_label(label: str) -> str | None:
    cleaned = clean_key(label)
    return SLOT_ALIASES.get(cleaned)


def normalize_tier_word(value: str) -> str:
    return value.strip().strip("()[]").lower()


def canonical_gem_name(name: str) -> str:
    name = name.strip().strip("[]")
    match = re.match(r"^\(?([A-Za-z]+)\)?\s+(.+)$", name)
    if not match:
        return name
    tier_word = normalize_tier_word(match.group(1))
    if tier_word not in TIER_BY_NAME:
        return name
    return f"{TIER_NAMES[TIER_BY_NAME[tier_word]]} {match.group(2).strip()}"


def split_tier_from_name(name: str) -> tuple[str, str]:
    canonical = canonical_gem_name(name)
    match = re.match(r"^([A-Za-z]+)\s+(.+)$", canonical)
    if not match:
        raise ValueError(f"Could not read gem tier from {name!r}")
    tier_word = normalize_tier_word(match.group(1))
    if tier_word not in TIER_BY_NAME:
        raise ValueError(f"Unknown gem tier in {name!r}")
    return TIER_NAMES[TIER_BY_NAME[tier_word]], match.group(2).strip()


def category_from_effect(effect_group: str, effect_display: str) -> str:
    group = clean_key(effect_group)
    display = clean_key(effect_display)
    if group in {"h p", "hp", "hits"} or display in {"hit points", "hits"}:
        return "hits"
    if group == "power" or display == "power":
        return "power"
    if group == "focus" or display.endswith("focus"):
        return "focus"
    if group == "resist":
        return "resist"
    if group == "skill":
        return "skill"
    return "stat"


def infer_from_gem_name(name: str) -> tuple[int, str, str]:
    tier_name, rest = split_tier_from_name(name)
    tier = TIER_BY_NAME[tier_name.lower()]
    lower_rest = rest.lower()
    parts = lower_rest.split()
    adjective = parts[0] if parts else ""

    if lower_rest == "blood essence jewel":
        return tier, "hits", "hits"
    if lower_rest in {"mystic essence jewel", "mystical essence jewel"}:
        return tier, "power", "power"
    if lower_rest == "brilliant sigil":
        return tier, "focus", "all_focus_alb"
    if lower_rest == "brilliant rune":
        return tier, "focus", "all_focus_mid"
    if lower_rest == "brilliant stone":
        return tier, "focus", "all_focus_hib"
    if lower_rest.endswith("essence jewel") and adjective in STAT_BY_ADJECTIVE:
        return tier, "stat", STAT_BY_ADJECTIVE[adjective]
    if lower_rest.endswith("shielding jewel") and adjective in RESIST_BY_ADJECTIVE:
        return tier, "resist", RESIST_BY_ADJECTIVE[adjective]
    if lower_rest in SKILL_BY_GEM_FAMILY:
        return tier, "skill", SKILL_BY_GEM_FAMILY[lower_rest]

    raise ValueError(f"Unknown gem family for {name!r}")


def value_for(category: str, tier: int) -> int:
    if category == "stat":
        return STAT_VALUE[tier]
    if category == "hits":
        return HITS_VALUE[tier]
    if category == "resist":
        return RESIST_VALUE[tier]
    if category == "power":
        return POWER_VALUE[tier]
    if category == "focus":
        return FOCUS_VALUE[tier]
    if category == "skill":
        return SKILL_VALUE[tier]
    raise ValueError(f"Unknown category {category!r}")


def imbue_for(category: str, tier: int) -> float:
    if category == "stat":
        return STAT_IMBUE[tier]
    if category == "hits":
        return HITS_IMBUE[tier]
    if category == "resist":
        return RESIST_IMBUE[tier]
    if category == "power":
        return POWER_IMBUE[tier]
    if category == "focus":
        return FOCUS_IMBUE[tier]
    if category == "skill":
        return SKILL_IMBUE[tier]
    raise ValueError(f"Unknown category {category!r}")


def gem_from_name(
    name: str,
    warnings: WarningBag,
    effect_group: str | None = None,
    effect_display: str | None = None,
    effect_value: int | None = None,
    realm: str = "Albion",
    effect_type: str | None = None,
) -> Gem | None:
    if "not found" in name.lower():
        return None

    canonical = canonical_gem_name(name)
    try:
        tier, inferred_category, inferred_type = infer_from_gem_name(canonical)
    except ValueError:
        if not (effect_group and effect_display):
            raise
        tier_name, _ = split_tier_from_name(canonical)
        tier = TIER_BY_NAME[tier_name.lower()]
        inferred_category = category_from_effect(effect_group, effect_display)
        inferred_type = effect_type or type_from_display(effect_display, realm)
    category = inferred_category
    gem_type = inferred_type

    if effect_group and effect_display:
        category = category_from_effect(effect_group, effect_display)
        if category == "hits":
            gem_type = "hits"
        elif category == "resist":
            gem_type = clean_key(re.sub(r"\bresist\b", "", effect_display, flags=re.I)).replace(" ", "_")
        elif category == "skill":
            gem_type = effect_type or type_from_display(effect_display, realm)
        elif category == "focus":
            gem_type = effect_type or type_from_display(effect_display, realm)
        elif category == "power":
            gem_type = "power"
        else:
            gem_type = clean_key(effect_display).replace(" ", "_")

    value = effect_value if effect_value is not None else value_for(category, tier)
    display = DISPLAY_BY_TYPE.get(gem_type, title_from_type(gem_type))
    bonus_code = BONUS_CODE_BY_TYPE.get(gem_type)

    if category == "skill" and bonus_code is None:
        warnings.add(
            f"No Template Forge bonusCode is known yet for skill {display!r}; "
            "the .forge will use 0 for that skill until we add a sample/mapping."
        )
        bonus_code = 0

    return Gem(
        name=canonical,
        tier=tier,
        category=category,
        type=gem_type,
        display=display,
        value=value,
        imbue=imbue_for(category, tier),
        bonus_code=bonus_code,
    )


def parse_number(value: str) -> float:
    return float(value.replace(",", "."))


def parse_int_value(value: str) -> int:
    parsed = parse_number(value)
    return int(parsed) if parsed.is_integer() else round(parsed)


def read_text_fallback(path: Path) -> str:
    data = path.read_bytes()
    encodings = ("utf-8-sig", "utf-8", "cp1252")
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def parse_effect_line(line: str) -> tuple[str, str, int] | None:
    match = re.search(r"\(([^)]+)\)\s+([^:]+):\s*\+?([0-9.,]+)%?", line)
    if not match:
        return None
    return match.group(1).strip(), match.group(2).strip(), parse_int_value(match.group(3))


def parse_remastered_report(text: str, warnings: WarningBag, realm: str = "Albion") -> list[Item]:
    items: list[Item] = []
    current: Item | None = None
    pending_name: str | None = None
    in_gem_list = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^Gems:\s*\d+", line, re.I) or re.match(r"^Skill needed", line, re.I):
            in_gem_list = True
            pending_name = None
            continue
        if in_gem_list:
            continue

        heading = re.match(r"^([A-Za-z. ]+):$", line)
        if heading:
            slot = slot_from_label(heading.group(1))
            if slot:
                current = Item(slot=slot)
                items.append(current)
                pending_name = None
                continue

        if current is None:
            continue

        imbue = re.search(r"Imbue Points:\s*([0-9.,]+)\s+of\s+[0-9.,]+\s+\(Quality:\s*(\d+)\)", line, re.I)
        if imbue:
            current.current_imbue = parse_number(imbue.group(1))
            current.quality = int(imbue.group(2))
            continue

        gem_match = re.match(r"Gem\s+\d+:\s+(.+)$", line, re.I)
        if gem_match:
            pending_name = gem_match.group(1).strip()
            continue

        if pending_name:
            effect = parse_effect_line(line)
            if effect:
                gem = gem_from_name(pending_name, warnings, *effect, realm=realm)
                if gem:
                    current.gems.append(gem)
                pending_name = None

    return [item for item in items if item.gems]


def parse_legacy_or_forge_text(text: str, warnings: WarningBag, realm: str = "Albion") -> list[Item]:
    items: list[Item] = []
    current: Item | None = None
    source_type = ""

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading_text = line.rstrip(":")
        if not re.match(r"^\d+\.", line):
            slot = slot_from_label(heading_text)
            if slot:
                current = Item(slot=slot)
                items.append(current)
                source_type = ""
                continue

        if current is None:
            continue

        source_match = re.match(r"Source Type:\s*(.+)$", line, re.I)
        if source_match:
            source_type = source_match.group(1).strip().lower()
            continue

        imbue_match = re.search(r"Imbue Points:\s*([0-9.,]+)\s+of\s+[0-9.,]+", line, re.I)
        if imbue_match:
            current.current_imbue = parse_number(imbue_match.group(1))
            continue
        imbue_match = re.search(r"Imbue Punkte:\s*([0-9.,]+)\s+von\s+[0-9.,]+", line, re.I)
        if imbue_match:
            current.current_imbue = parse_number(imbue_match.group(1))
            quality_match = re.search(r"\((\d+)%\s+Qual\)", line, re.I)
            if quality_match:
                current.quality = int(quality_match.group(1))
            continue

        quality_match = re.search(r"Level:\s*\d+\s+\((\d+)%\s+Quality\)", line, re.I)
        if quality_match:
            current.quality = int(quality_match.group(1))
            continue

        if "5th Slot" in line:
            continue

        has_spellcraft_source = source_type in {"spellcraft", "spellcrafted"} or "[(" in line or re.match(r"^Juwel\s+\d+:", line, re.I)
        if not has_spellcraft_source:
            continue

        parsed = parse_bracketed_gem_line(line)
        if parsed is not None:
            group, display, value, gem_name = parsed
            gem = gem_from_name(gem_name, warnings, group, display, value, realm=realm)
        else:
            effect = parse_numbered_effect_line(line)
            if effect is None:
                continue
            group, display, value = effect
            category = category_from_effect(group, display)
            gem = gem_from_effect(category, display, value, warnings, realm)
        if gem:
            current.gems.append(gem)

    return [item for item in items if item.gems]


def parse_bracketed_gem_line(line: str) -> tuple[str, str, int, str] | None:
    german = re.match(
        r"^Juwel\s+\d+:\s*\+?([0-9.,]+)%?\s+(.+?)\s+-\s+\d+%\s+\(([^)]+)\)\s+(.+)$",
        line,
        flags=re.I,
    )
    if german:
        display = re.sub(r"\bresist\b", "", german.group(2), flags=re.I).strip()
        group = "Resist" if re.search(r"\bresist\b", german.group(2), flags=re.I) else "Stat"
        gem_name = f"{german.group(3)} {german.group(4).strip()}"
        return group, display, parse_int_value(german.group(1)), gem_name

    legacy = re.match(
        r"^(?:\d+\.\s+)?\(([^)]+)\)\s+([^:]+):\s*\+?([0-9.,]+)%?\s+\[\(([^)]+)\)\s+([^\]]+)\]",
        line,
    )
    if legacy:
        gem_name = f"{legacy.group(4)} {legacy.group(5)}"
        return legacy.group(1).strip(), legacy.group(2).strip(), parse_int_value(legacy.group(3)), gem_name

    forge = re.match(
        r"^(?:\d+\.\s+)?\(([^)]+)\)\s+([^:]+):\s*\+?([0-9.,]+)%?\s+\(([^)]+)\)",
        line,
    )
    if forge:
        return forge.group(1).strip(), forge.group(2).strip(), parse_int_value(forge.group(3)), forge.group(4).strip()

    return None


def parse_numbered_effect_line(line: str) -> tuple[str, str, int] | None:
    match = re.match(r"^(?:\d+\.\s+)?\(([^)]+)\)\s+([^:]+):\s*\+?([0-9.,]+)%?", line)
    if not match:
        return None
    group = match.group(1).strip()
    if "5th Slot" in group:
        return None
    return group, match.group(2).strip(), parse_int_value(match.group(3))


def tier_from_value(category: str, value: int) -> int | None:
    tables = {
        "stat": STAT_VALUE,
        "hits": HITS_VALUE,
        "resist": RESIST_VALUE,
        "power": POWER_VALUE,
        "focus": FOCUS_VALUE,
        "skill": SKILL_VALUE,
    }
    table = tables.get(category)
    if not table:
        return None
    for tier, tier_value in table.items():
        if tier_value == value:
            return tier
    return None


def parse_loki_bonus_line(line: str, realm: str = "Albion") -> tuple[str, str, int] | None:
    if "cap increase" in line.lower():
        return None

    colon = re.match(r"^(.+?):\s*\+?([0-9.,]+)(%)?$", line)
    if colon:
        display = colon.group(1).strip()
        value = parse_int_value(colon.group(2))
        if colon.group(3):
            return "resist", display, value
        type_key = type_from_display(display, realm)
        stat_types = set(STAT_BY_ADJECTIVE.values())
        skill_types = set(SKILL_GEM_FAMILY_BY_TYPE)
        if type_key in {"hits", "power"}:
            return type_key, display, value
        if type_key in stat_types:
            return "stat", display, value
        if type_key.startswith("all_focus_") or clean_key(display).endswith("focus"):
            return "focus", display, value
        if type_key in skill_types:
            return "skill", display, value
        return None

    resist = re.match(r"^([0-9.,]+)%\s+(.+)$", line)
    if resist:
        return "resist", resist.group(2).strip(), parse_int_value(resist.group(1))

    bonus = re.match(r"^([0-9.,]+)\s+(.+)$", line)
    if not bonus:
        return None

    value = parse_int_value(bonus.group(1))
    display = bonus.group(2).strip()
    type_key = type_from_display(display, realm)
    stat_types = set(STAT_BY_ADJECTIVE.values())
    skill_types = set(SKILL_GEM_FAMILY_BY_TYPE)

    if type_key in {"hits", "power"}:
        return type_key, display, value
    if type_key in stat_types:
        return "stat", display, value
    if type_key.startswith("all_focus_") or clean_key(display).endswith("focus"):
        return "focus", display, value
    if type_key in skill_types:
        return "skill", display, value
    return None


def gem_from_effect(category: str, display: str, value: int, warnings: WarningBag, realm: str = "Albion") -> Gem | None:
    tier = tier_from_value(category, value)
    if tier is None:
        warnings.add(f"Could not infer a gem tier for {display} +{value}; skipped that bonus.")
        return None

    gem_type = type_from_display(display, realm)
    if category == "hits":
        gem_type = "hits"
    elif category == "power":
        gem_type = "power"
    elif category == "resist":
        gem_type = clean_key(re.sub(r"\bresist\b", "", display, flags=re.I)).replace(" ", "_")

    try:
        gem_name = gem_name_from_parts(tier, category, gem_type)
        group = {
            "hits": "Stat",
            "power": "Power",
            "focus": "Focus",
            "resist": "Resist",
            "skill": "Skill",
            "stat": "Stat",
        }[category]
        return gem_from_name(gem_name, warnings, group, display, value, realm=realm, effect_type=gem_type)
    except (KeyError, StopIteration, ValueError) as exc:
        warnings.add(f"Could not infer a gem name for {display} +{value}: {exc}")
        return None


def parse_loki_report(text: str, warnings: WarningBag, realm: str = "Albion") -> list[Item]:
    items: list[Item] = []
    current: Item | None = None
    in_spellcrafted_item = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading = re.match(r"^(.+):$", line)
        if heading:
            heading_text = re.sub(r"\s*\(.+\)\s*$", "", heading.group(1)).strip()
            slot = slot_from_label(heading_text)
            current = Item(slot=slot) if slot else None
            if current:
                items.append(current)
            in_spellcrafted_item = False
            continue

        if current is None:
            continue

        imbue_match = re.match(r"Imbue:\s*([0-9.,]+)\s*/\s*[0-9.,]+\s+\(Quality:\s*(\d+)\)", line, re.I)
        if imbue_match:
            current.current_imbue = parse_number(imbue_match.group(1))
            current.quality = int(imbue_match.group(2))
            in_spellcrafted_item = True
            continue

        if not in_spellcrafted_item:
            continue
        if re.match(r"^(Utility|TOA Utility):", line, re.I):
            in_spellcrafted_item = False
            continue
        if len(current.gems) >= 4:
            continue

        parsed = parse_loki_bonus_line(line, realm)
        if parsed is None:
            continue

        category, display, value = parsed
        gem = gem_from_effect(category, display, value, warnings, realm)
        if gem:
            current.gems.append(gem)

    return [item for item in items if item.gems]


def gem_name_candidates_by_tier(tier: int, realm: str = "Albion") -> dict[str, str]:
    suffix = realm_suffix(realm)
    categories = {
        "stat": set(STAT_BY_ADJECTIVE.values()),
        "resist": set(RESIST_BY_ADJECTIVE.values()),
        "hits": {"hits"},
        "power": {"power"},
        "focus": {f"all_focus_{suffix}"},
        "skill": REALM_SKILL_TYPES.get(clean_key(canonical_realm(realm)), REALM_SKILL_TYPES["albion"]),
    }
    candidates: dict[str, str] = {}
    for category, gem_types in categories.items():
        for gem_type in gem_types:
            try:
                name = gem_name_from_parts(tier, category, gem_type)
            except (KeyError, StopIteration, ValueError):
                continue
            candidates[clean_key(name)] = name
    return candidates


def clean_freeform_gem_phrase(text: str) -> str:
    text = text.replace("\\\"", "\"").strip().strip("\"'`")
    text = re.sub(r"^\d+\.\s*", "", text)
    text = re.sub(r"^Gem\s+\d+\s*:\s*", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .")


def gem_from_loose_name(text: str, warnings: WarningBag, realm: str = "Albion") -> Gem | None:
    phrase = clean_freeform_gem_phrase(text)
    if not phrase:
        return None

    cleaned = clean_key(phrase)
    words = cleaned.split()
    if not words:
        return None

    tier_word = words[0]
    if tier_word not in TIER_BY_NAME:
        close_tiers = difflib.get_close_matches(tier_word, TIER_BY_NAME.keys(), n=1, cutoff=0.78)
        if not close_tiers:
            if "jewel" in words or "sigil" in words:
                warnings.add(f"Skipped possible gem without a tier: {phrase!r}.")
            return None
        tier_word = close_tiers[0]
        cleaned = " ".join([tier_word, *words[1:]])

    candidates = gem_name_candidates_by_tier(TIER_BY_NAME[tier_word], realm)
    if cleaned in candidates:
        return gem_from_name(candidates[cleaned], warnings, realm=realm)

    matches = difflib.get_close_matches(cleaned, candidates.keys(), n=1, cutoff=0.82)
    if not matches:
        try:
            return gem_from_name(phrase, warnings, realm=realm)
        except ValueError:
            pass
        if "jewel" in words or "sigil" in words:
            warnings.add(f"Could not identify gem text: {phrase!r}.")
        return None

    gem_name = candidates[matches[0]]
    if clean_key(gem_name) != clean_key(phrase):
        warnings.add(f"Corrected {phrase!r} to {gem_name!r}.")
    return gem_from_name(gem_name, warnings, realm=realm)


def freeform_order_lines(text: str) -> Iterable[str]:
    open_markers = list(re.finditer(r"^\*\*\* Chat Log Opened:.*$", text, flags=re.M))
    if open_markers:
        text = text[open_markers[-1].start() :]

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("*** Chat Log"):
            continue
        line = re.sub(r"^\[[0-9:]+\]\s*", "", line)
        quoted = re.findall(r'"((?:\\.|[^"\\])*)"', line)
        if quoted:
            for value in quoted:
                yield value
            continue
        if "@@" in line and ":" in line:
            line = line.split(":", 1)[1].strip()
        cleaned = clean_key(line)
        if any(marker in cleaned for marker in ("jewel", "sigil", "rune", "stone", "shielding", "essence")):
            yield line


def split_freeform_gem_phrases(line: str) -> list[str]:
    return [
        clean_freeform_gem_phrase(part)
        for part in re.split(r"[,;|]+", line)
        if clean_freeform_gem_phrase(part)
    ]


def parse_freeform_gem_text(text: str, warnings: WarningBag, slot_order: list[str], realm: str = "Albion") -> list[Item]:
    items: list[Item] = []
    current: Item | None = None
    anonymous_gems: list[Gem] = []

    for line in freeform_order_lines(text):
        slot = slot_from_label(line.rstrip(":"))
        if slot:
            current = Item(slot=slot)
            items.append(current)
            continue

        for phrase in split_freeform_gem_phrases(line):
            gem = gem_from_loose_name(phrase, warnings, realm)
            if gem is None:
                continue
            if current is not None:
                current.gems.append(gem)
            else:
                anonymous_gems.append(gem)

    for index in range(0, len(anonymous_gems), 4):
        group = anonymous_gems[index : index + 4]
        if not group:
            continue
        slot = slot_order[len(items) % len(slot_order)]
        items.append(Item(slot=slot, gems=group))

    return [item for item in items if item.gems]


def parse_forge_json(text: str, warnings: WarningBag) -> list[Item]:
    data = json.loads(text)
    template = data.get("template", {})
    realm = template.get("character", {}).get("realmName") or "Albion"
    slots = template.get("slots", {})
    items: list[Item] = []

    for slot, slot_data in slots.items():
        item_data = (slot_data or {}).get("item")
        if not item_data:
            continue
        raw_json = item_data.get("rawJson") or {}
        if not raw_json.get("spellcrafted"):
            continue

        bonuses = [
            bonus
            for bonus in item_data.get("bonuses", [])
            if bonus.get("gemName") and "not found" not in str(bonus.get("gemName", "")).lower()
        ]
        item = Item(
            slot=slot,
            quality=int(item_data.get("quality", 99)),
            current_imbue=float(raw_json.get("currentImbue", 0) or 0),
        )

        for index, raw_gem in enumerate(raw_json.get("gemSlots", [])):
            bonus = bonuses[index] if index < len(bonuses) else {}
            name = bonus.get("gemName")
            if not name:
                if not raw_gem.get("tier") or not raw_gem.get("category") or not raw_gem.get("type"):
                    continue
                tier = int(raw_gem.get("tier"))
                category = raw_gem.get("category")
                gem_type = raw_gem.get("type")
                name = gem_name_from_parts(tier, category, gem_type)
            group = bonus.get("bonusType") or raw_gem.get("category", "")
            display = bonus.get("stat") or raw_gem.get("type", "")
            value = int(raw_gem.get("value") or bonus.get("value") or 0)
            gem = gem_from_name(name, warnings, group, display, value, realm=realm, effect_type=raw_gem.get("type"))
            if gem:
                gem.bonus_code = int(bonus.get("bonusCode", gem.bonus_code or 0))
                item.gems.append(gem)

        if item.gems:
            items.append(item)

    return items


def gem_name_from_parts(tier: int, category: str, gem_type: str) -> str:
    tier_name = TIER_NAMES[tier]
    if category == "hits":
        return f"{tier_name} Blood Essence Jewel"
    if category == "power":
        return f"{tier_name} Mystic Essence Jewel"
    if category == "focus":
        if gem_type == "all_focus_mid":
            return f"{tier_name} Brilliant Rune"
        if gem_type == "all_focus_hib":
            return f"{tier_name} Brilliant Stone"
        return f"{tier_name} Brilliant Sigil"
    if category == "stat":
        if gem_type == "acuity":
            return f"{tier_name} Mystical Essence Jewel"
        adjective = next(key for key, value in STAT_BY_ADJECTIVE.items() if value == gem_type)
        return f"{tier_name} {adjective.title()} Essence Jewel"
    if category == "resist":
        adjective = next(key for key, value in RESIST_BY_ADJECTIVE.items() if value == gem_type)
        return f"{tier_name} {adjective.title()} Shielding Jewel"
    family = SKILL_GEM_FAMILY_BY_TYPE.get(gem_type)
    if family:
        return f"{tier_name} {family.title()}"
    raise ValueError(f"Cannot build gem name for {category}/{gem_type}/tier {tier}")


def parse_gem_list(text: str, warnings: WarningBag, slot_order: list[str], realm: str = "Albion") -> list[Item]:
    items: list[Item] = []
    current: Item | None = None
    anonymous_gems: list[Gem] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        label = line.rstrip(":")
        slot = slot_from_label(label)
        if slot and ":" in line:
            current = Item(slot=slot)
            items.append(current)
            continue

        try:
            gem = gem_from_name(line, warnings, realm=realm)
        except ValueError as exc:
            warnings.add(str(exc))
            continue

        if gem is None:
            continue
        if current is not None:
            current.gems.append(gem)
        else:
            anonymous_gems.append(gem)

    for index in range(0, len(anonymous_gems), 4):
        group = anonymous_gems[index : index + 4]
        if not group:
            continue
        slot = slot_order[len(items) % len(slot_order)]
        items.append(Item(slot=slot, gems=group))

    return [item for item in items if item.gems]


def detect_and_parse(path: Path, slot_order: list[str], warnings: WarningBag, realm: str = "Albion") -> list[Item]:
    text = read_text_fallback(path)
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return parse_forge_json(text, warnings)
    if re.search(r"^Gem\s+\d+:", text, re.M):
        return parse_remastered_report(text, warnings, realm)

    report_items = parse_legacy_or_forge_text(text, warnings, realm)
    if report_items:
        return report_items
    loki_items = parse_loki_report(text, warnings, realm)
    if loki_items:
        return loki_items
    freeform_items = parse_freeform_gem_text(text, warnings, slot_order, realm)
    if freeform_items:
        return freeform_items
    return parse_gem_list(text, warnings, slot_order, realm)


def format_number(value: float) -> str:
    if abs(value - int(value)) < 0.00001:
        return str(int(value))
    return f"{value:.1f}".rstrip("0").rstrip(".")


def zenk_report_title(template_name: str, default_class: str = DEFAULT_ZENK_CLASS) -> str:
    clean_name = (template_name or "Import").strip()
    if not clean_name:
        clean_name = "Import"
    class_by_lower = {name.lower(): name for name in ALBION_CLASS_NAMES}
    parts = [part.strip() for part in clean_name.split("-") if part.strip()]
    if parts:
        class_name = class_by_lower.get(parts[-1].lower())
        if class_name:
            return f"{' - '.join(parts[:-1]) or clean_name} - {class_name}"
    return f"{clean_name} - {default_class}"


def render_zenk_report(items: list[Item], template_name: str) -> str:
    lines = [
        "Zenkcraft Spellcrafting Tool - Remastered Version",
        "store.steampowered.com/app/2098510/Zenkcraft",
        f"Last Saved: {datetime.now().strftime('%I:%M %p on %b %d, %Y')}",
        "Version: 1.3.007",
        "",
        f"Spellcraft Report for {zenk_report_title(template_name)}",
        "",
    ]

    all_gems: list[Gem] = []
    for item in items:
        lines.append(f"{item.title}:")
        lines.append(f"Imbue Points: {format_number(item.imbue)} of 37.5  (Quality: {item.quality})")
        for index, gem in enumerate(item.gems, start=1):
            all_gems.append(gem)
            lines.append(f"Gem {index}: {gem.zenk_gem_name}")
            lines.append(f"        ({gem.zenk_group}) {gem.zenk_display}: +{gem.value}{gem.zenk_suffix}")
            lines.append("")
        lines.append("")

    lines.extend(["", "Skill needed for craft: 0", "", "", "", f"Gems: {len(all_gems)}", ""])
    lines.extend(gem.zenk_gem_name for gem in all_gems)
    lines.append("")
    return "\n".join(lines)


def render_forge(items: list[Item], template_name: str, realm: str, server: str) -> dict:
    realm = canonical_realm(realm)
    slot_items = {slot: {"item": None} for slot in SLOT_KEYS}
    for item in items:
        if item.slot not in slot_items:
            continue
        slot_items[item.slot] = {"item": forge_item(item)}

    return {
        "format": "template-forge",
        "version": 1,
        "exportedAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "template": {
            "name": template_name,
            "serverName": server,
            "character": {
                "realmId": REALM_ID_BY_NAME.get(realm),
                "realmName": realm,
                "raceId": None,
                "raceName": "",
                "classId": None,
                "className": "",
                "level": 50,
            },
            "racialResists": {
                "crush": 0,
                "slash": 0,
                "thrust": 0,
                "heat": 0,
                "cold": 0,
                "matter": 0,
                "energy": 0,
                "body": 0,
                "spirit": 0,
            },
            "slots": slot_items,
            "weaponOutfits": [
                {"mainhand": None, "offhand": None, "twohanded": None, "ranged": None, "activeWeaponSet": "melee"}
                for _ in range(5)
            ],
            "activeOutfitIndex": 0,
            "activeWeaponSet": "melee",
            "disabledSlots": [],
        },
    }


def forge_item(item: Item) -> dict:
    return {
        "name": f"SC {item.title}",
        "slot": item.slot,
        "level": 51,
        "quality": item.quality,
        "itemType": "Spellcrafted",
        "utility": item.utility,
        "bonuses": [
            {
                "bonusType": gem.forge_bonus_type,
                "bonusCode": gem.bonus_code if gem.bonus_code is not None else 0,
                "stat": gem.forge_stat,
                "value": gem.value,
                "utility": gem.utility,
                "gemName": gem.forge_gem_name,
            }
            for gem in item.gems
        ],
        "rawJson": {
            "spellcrafted": True,
            "gemSlots": [
                {
                    "id": index,
                    "category": gem.category,
                    "type": gem.type,
                    "tier": gem.tier,
                    "value": gem.value,
                    "imbue": gem.imbue,
                }
                for index, gem in enumerate(item.gems, start=1)
            ],
            "maxImbue": 37.5,
            "currentImbue": item.imbue,
            "overcharge": max(0, round(item.imbue - 32, 1)),
        },
    }


def quickbar_section_name(quickbar: int) -> str:
    if quickbar < 1:
        raise ValueError("Quickbar must be 1 or higher.")
    return "Quickbar" if quickbar == 1 else f"Quickbar{quickbar}"


def quickbar_hotkey_index(page: int, slot: int) -> int:
    if not 1 <= page <= 10:
        raise ValueError("Page must be between 1 and 10.")
    if not 1 <= slot <= 10:
        raise ValueError("Slot must be between 1 and 10.")
    return (page - 1) * 10 + (slot - 1)


def icon_for_gem(gem: Gem) -> int:
    _, rest = split_tier_from_name(gem.zenk_gem_name)
    first_word = clean_key(rest).split(" ", 1)[0]
    return ICON_BY_FIRST_WORD.get(first_word, 150)


def hotbar_item_id(gem: Gem, base_ids: dict[str, int]) -> int:
    base_id = base_ids.get(gem.type)
    if base_id is None:
        raise ValueError(f"No DAoC hotbar item ID is known for {gem.display} ({gem.name}).")
    return base_id * 10 + (gem.tier - 1)


def hotbar_display(gem: Gem) -> str:
    tier_name, rest = split_tier_from_name(gem.zenk_gem_name)
    label = gem.zenk_display
    if gem.category == "stat":
        suffix = f"{label} Stat"
    elif gem.category == "hits":
        suffix = "Hitpoints Stat"
    elif gem.category == "power":
        suffix = "Power Stat"
    elif gem.category == "resist":
        suffix = f"{label} Resist"
    elif gem.category == "focus":
        suffix = f"{label} Focus"
    else:
        suffix = f"{label} Skill"
    return f"{tier_name.lower()} {rest} ({suffix})"


def build_bar_entries(
    items: list[Item],
    start_index: int,
    base_ids: dict[str, int],
    include_item_separators: bool = True,
    existing_hotkeys: dict[int, str] | None = None,
) -> tuple[dict[str, str], dict[str, str], int]:
    hotkeys: dict[str, str] = {}
    macros: dict[str, str] = {}
    existing_hotkeys = existing_hotkeys or {}
    hotkey_index = start_index
    macro_id = 20

    for item in items:
        if include_item_separators:
            if macro_id > 27:
                raise ValueError("Item separators need more than the DAoC 28 macro slots. Turn off separators or use fewer items.")
            label = separator_macro_label(item)
            icon = hotkey_icon_from_value(existing_hotkeys.get(hotkey_index), default="2385")
            hotkeys[f"Hotkey_{hotkey_index}"] = f"52,{macro_id},Macro #{macro_id},{icon}"
            macros[f"Macro_{macro_id}"] = f"{label},/craftqueue buy 1"
            hotkey_index += 1
            macro_id += 1

        for gem in item.gems:
            if hotkey_index > 99:
                raise ValueError("The selected quickbar/page/slot does not have enough remaining slots for this order.")
            hotkeys[f"Hotkey_{hotkey_index}"] = (
                f"45,{hotbar_item_id(gem, base_ids)},{hotbar_display(gem)},{icon_for_gem(gem)}"
            )
            hotkey_index += 1

    return hotkeys, macros, hotkey_index - start_index


def separator_macro_label(item: Item) -> str:
    return item.title


def planned_hotkey_count(items: list[Item], include_item_separators: bool = True) -> int:
    return sum(len(item.gems) + (1 if include_item_separators else 0) for item in items)


def section_entries(text: str, section: str) -> dict[str, str]:
    lines = text.splitlines()
    section_header = f"[{section}]"
    section_start = None
    section_end = len(lines)

    for index, line in enumerate(lines):
        if line.strip().lower() == section_header.lower():
            section_start = index
            break

    if section_start is None:
        return {}

    for index in range(section_start + 1, len(lines)):
        if re.match(r"^\[[^]]+\]\s*$", lines[index]):
            section_end = index
            break

    entries: dict[str, str] = {}
    for line in lines[section_start + 1 : section_end]:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        entries[key.strip()] = value
    return entries


def section_hotkeys(text: str, section: str) -> dict[int, str]:
    hotkeys: dict[int, str] = {}
    for key, value in section_entries(text, section).items():
        match = re.fullmatch(r"Hotkey_(\d+)", key.strip(), flags=re.IGNORECASE)
        if match:
            hotkeys[int(match.group(1))] = value
    return hotkeys


def hotkey_icon_from_value(value: str | None, default: str = "2385") -> str:
    if not value:
        return default
    parts = value.split(",")
    if len(parts) >= 4 and parts[3].strip():
        return parts[3].strip()
    return default


def set_ini_entries(text: str, section: str, entries: dict[str, str]) -> str:
    lines = text.splitlines()
    section_header = f"[{section}]"
    section_start = None
    section_end = len(lines)

    for index, line in enumerate(lines):
        if line.strip().lower() == section_header.lower():
            section_start = index
            break

    if section_start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(section_header)
        section_start = len(lines) - 1
        section_end = len(lines)
    else:
        for index in range(section_start + 1, len(lines)):
            if re.match(r"^\[[^]]+\]\s*$", lines[index]):
                section_end = index
                break

    entry_by_lower_key = {key.lower(): key for key in entries}
    written_keys: set[str] = set()
    new_body: list[str] = []

    for line in lines[section_start + 1 : section_end]:
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        canonical_key = entry_by_lower_key.get(key.lower())
        if canonical_key:
            new_body.append(f"{canonical_key}={entries[canonical_key]}")
            written_keys.add(canonical_key.lower())
        else:
            new_body.append(line)

    for key, value in entries.items():
        if key.lower() not in written_keys:
            new_body.append(f"{key}={value}")

    lines = lines[: section_start + 1] + new_body + lines[section_end:]
    return "\n".join(lines) + "\n"


def hotkey_position(index: int) -> tuple[int, int]:
    return index // 10 + 1, index % 10 + 1


def backup_ini_path(ini_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return ini_path.with_name(f"{ini_path.stem} - DaocCraftToolBackup_{stamp}{ini_path.suffix}")


def cleanup_ini_backups(ini_path: Path, keep: int = 3) -> int:
    if keep < 1:
        keep = 1
    pattern = f"{ini_path.stem} - DaocCraftToolBackup_*{ini_path.suffix}"
    backups = [path for path in ini_path.parent.glob(pattern) if path.is_file()]
    backups.sort(key=lambda path: (path.stat().st_mtime, path.name), reverse=True)
    deleted = 0
    for backup in backups[keep:]:
        try:
            backup.unlink()
            deleted += 1
        except OSError:
            continue
    return deleted


def read_ini_text(path: Path) -> tuple[str, str, str]:
    data = path.read_bytes()
    newline = "\r\n" if b"\r\n" in data else "\n"
    encodings = ("utf-8-sig", "utf-8", "cp1252") if data.startswith(b"\xef\xbb\xbf") else ("utf-8", "cp1252")
    for encoding in encodings:
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = data.decode("utf-8", errors="replace")
        encoding = "utf-8"
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized, encoding, newline


def write_ini_text_safely(path: Path, text: str, encoding: str, newline: str) -> None:
    output = text.replace("\n", newline)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_bytes(output.encode(encoding))
    if temp_path.stat().st_size == 0:
        raise OSError(f"Refusing to replace {path}: temporary file is empty.")
    temp_path.replace(path)


def setup_bars(
    items: list[Item],
    ini_path: Path,
    quickbar: int,
    page: int,
    slot: int,
    realm: str = "Albion",
    include_item_separators: bool = True,
    zenk_config: str | None = None,
) -> BarSetupResult:
    if not ini_path.exists():
        raise FileNotFoundError(f"INI file does not exist: {ini_path}")

    section = quickbar_section_name(quickbar)
    start_index = quickbar_hotkey_index(page, slot)
    base_ids = load_gem_base_ids(realm, zenk_config)
    text, encoding, newline = read_ini_text(ini_path)
    hotkeys, macros, count = build_bar_entries(
        items,
        start_index,
        base_ids,
        include_item_separators,
        existing_hotkeys=section_hotkeys(text, section),
    )

    backup_path = backup_ini_path(ini_path)
    shutil.copy2(ini_path, backup_path)

    quickbar_entries = {"GroupSize": "10", **hotkeys} if f"[{section}]" not in text else hotkeys
    text = set_ini_entries(text, section, quickbar_entries)
    if macros:
        text = set_ini_entries(text, "Macros", macros)
    write_ini_text_safely(ini_path, text, encoding, newline)
    backup_cleanup_count = cleanup_ini_backups(ini_path, keep=3)

    return BarSetupResult(
        ini_path=ini_path,
        backup_path=backup_path,
        quickbar_section=section,
        start_hotkey=start_index,
        hotkey_count=count,
        macro_count=len(macros),
        backup_cleanup_count=backup_cleanup_count,
    )


def parse_slot_order(value: str) -> list[str]:
    slots: list[str] = []
    for chunk in value.split(","):
        slot = slot_from_label(chunk.strip())
        if slot is None:
            raise argparse.ArgumentTypeError(f"Unknown slot in --slot-order: {chunk!r}")
        slots.append(slot)
    if not slots:
        raise argparse.ArgumentTypeError("--slot-order must include at least one slot")
    return slots


def output_defaults(input_path: Path, out_dir: Path | None) -> tuple[Path, Path]:
    directory = out_dir or input_path.parent / "converted"
    return directory / f"{input_path.stem}.forge", directory / f"{input_path.stem}_SC-Report.txt"


def write_outputs(items: list[Item], args: argparse.Namespace, warnings: WarningBag) -> None:
    input_path = Path(args.input)
    default_forge, default_zenk = output_defaults(input_path, Path(args.out_dir) if args.out_dir else None)
    forge_path = Path(args.forge) if args.forge else default_forge
    zenk_path = Path(args.zenk) if args.zenk else default_zenk

    if args.action == "forge":
        zenk_path = None
    elif args.action == "zenk":
        forge_path = None
    elif args.action == "bars":
        forge_path = None
        zenk_path = None
    else:
        raise ValueError(f"Unknown action {args.action!r}")

    if args.action == "bars":
        result = setup_bars(
            items=items,
            ini_path=Path(args.ini),
            quickbar=args.quickbar,
            page=args.page,
            slot=args.slot,
            realm=args.realm,
            include_item_separators=args.include_item_separators,
            zenk_config=args.zenk_config,
        )
        print(f"Updated {result.ini_path}")
        print(f"Backup saved to {result.backup_path}")
        print(
            f"Wrote {result.hotkey_count} quickbar slot(s) to [{result.quickbar_section}] "
            f"starting at Hotkey_{result.start_hotkey}."
        )
        if result.macro_count:
            print(f"Wrote {result.macro_count} item separator macro(s).")

    if forge_path:
        forge_path.parent.mkdir(parents=True, exist_ok=True)
        forge = render_forge(items, args.name, args.realm, args.server)
        forge_path.write_text(json.dumps(forge, indent=2), encoding="utf-8")
        print(f"Wrote {forge_path}")

    if zenk_path:
        zenk_path.parent.mkdir(parents=True, exist_ok=True)
        zenk_path.write_text(render_zenk_report(items, args.name), encoding="utf-8")
        print(f"Wrote {zenk_path}")

    print(f"Parsed {len(items)} spellcrafted item(s), {sum(len(item.gems) for item in items)} gem(s).")
    for warning in warnings.messages:
        print(f"Warning: {warning}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert DAoC spellcraft gem names/reports to Template Forge .forge and Zenk Remastered .txt."
    )
    parser.add_argument("input", nargs="?", help="Input .txt gem report, gem-name list, or .forge file.")
    parser.add_argument(
        "--action",
        choices=["forge", "zenk", "bars"],
        help="What to do with the parsed spellcraft order.",
    )
    parser.add_argument("--name", default="Import", help="Template/report name to write into generated files.")
    parser.add_argument("--realm", default="Albion", help="Realm name for .forge output.")
    parser.add_argument("--server", default="Eden", help="Server name for .forge output.")
    parser.add_argument("--forge", help="Output .forge path. Defaults to ./converted/<input>.forge.")
    parser.add_argument("--zenk", help="Output Zenk Remastered .txt path. Defaults to ./converted/<input>_SC-Report.txt.")
    parser.add_argument("--out-dir", help="Directory for default outputs.")
    parser.add_argument("--ini", help="Eden character .ini to update for --action bars.")
    parser.add_argument("--quickbar", type=int, help="Quickbar number for --action bars. Defaults to last used.")
    parser.add_argument("--page", type=int, help="Quickbar page for --action bars. Defaults to last used.")
    parser.add_argument("--slot", type=int, help="Quickbar slot for --action bars. Defaults to last used.")
    parser.add_argument(
        "--include-item-separators",
        dest="include_item_separators",
        action="store_true",
        default=None,
        help="Add item-name /craftqueue buy 1 macros between gem groups.",
    )
    parser.add_argument(
        "--no-item-separators",
        dest="include_item_separators",
        action="store_false",
        help="Do not add item-name /craftqueue buy 1 macros between gem groups.",
    )
    parser.add_argument("--zenk-config", help="Optional explicit Eden-ZenkServerConfig.zsc path.")
    parser.add_argument(
        "--slot-order",
        type=parse_slot_order,
        default=parse_slot_order("head,arms,hands,legs,feet,mainhand,offhand,twohanded,ranged"),
        help="Comma-separated slots for plain gem-name lists without slot headings.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = load_settings()

    if args.input is None:
        args.input = settings.get("last_input_path") or ""
    if args.action is None:
        args.action = settings.get("last_action") or "forge"
    if args.ini is None:
        args.ini = settings.get("last_ini_path") or ""
    if args.quickbar is None:
        args.quickbar = int(settings.get("quickbar") or 1)
    if args.page is None:
        args.page = int(settings.get("page") or 3)
    if args.slot is None:
        args.slot = int(settings.get("slot") or 1)
    if args.include_item_separators is None:
        args.include_item_separators = bool(settings.get("include_item_separators", True))

    warnings = WarningBag()
    input_path = Path(args.input)

    if not args.input:
        parser.error("No input file was provided and no last input file is saved yet.")
    if not input_path.exists():
        parser.error(f"Input file does not exist: {input_path}")
    if args.action == "bars" and (not args.ini or not Path(args.ini).exists()):
        parser.error("Bar setup needs a valid Eden character .ini file.")

    items = detect_and_parse(input_path, args.slot_order, warnings, args.realm)
    if not items:
        parser.error("No spellcrafted gems were found in the input.")
    fatal_warnings = blocking_warnings(warnings)
    if fatal_warnings:
        parser.error("Some gem text could not be imported safely:\n" + "\n".join(fatal_warnings))

    write_outputs(items, args, warnings)
    settings.update(
        {
            "last_input_path": str(input_path),
            "last_ini_path": str(Path(args.ini)) if args.ini else settings.get("last_ini_path", ""),
            "last_action": args.action,
            "realm": canonical_realm(args.realm),
            "quickbar": args.quickbar,
            "page": args.page,
            "slot": args.slot,
            "include_item_separators": args.include_item_separators,
        }
    )
    save_settings(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
