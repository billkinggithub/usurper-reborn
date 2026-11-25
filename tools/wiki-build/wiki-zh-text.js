"use strict";

// Text that the generated reference pages and directive tables share. Entity names come from the
// exported name maps; this table covers the fixed labels, captions, enum values and short rules.
const text = {
  // table chrome
  Rule: "规则",
  Value: "数值",
  Type: "类型",
  Tier: "层级",
  Classes: "职业",
  "Class:": "职业：",
  Class: "职业",
  Races: "种族",
  Race: "种族",
  "All abilities": "全部技能",
  "All spells": "全部法术",
  "All classes": "全部职业",
  "Any season": "任意季节",
  "Every class": "所有职业",
  // equipment / item fields
  Slot: "栏位",
  Handedness: "持握方式",
  "Weapon Type": "武器类型",
  "Armor Type": "护甲类型",
  "Weight Class": "重量等级",
  Rarity: "稀有度",
  "Min Level": "最低等级",
  "Strength Required": "力量要求",
  "Base Value": "基础价值",
  "Base Sell Value": "基础售价",
  "Armor Class": "护甲等级",
  "Weapon Power": "武器威力",
  Attack: "攻击",
  Defense: "防御",
  Defence: "防御",
  "Max HPBonus": "最大生命加成",
  "Max HP": "最大生命",
  "Max Mana": "最大法力",
  "Magic Resistance": "魔法抗性",
  "Strength Bonus": "力量加成",
  "Dexterity Bonus": "敏捷加成",
  "Constitution Bonus": "体质加成",
  "Intelligence Bonus": "智力加成",
  "Wisdom Bonus": "感知加成",
  "Charisma Bonus": "魅力加成",
  "Agility Bonus": "灵巧加成",
  "Stamina Bonus": "体力加成",
  "Max Mana Bonus": "最大法力加成",
  "Defense Bonus": "防御加成",
  "Critical Chance Bonus": "暴击率加成",
  "Critical Damage Bonus": "暴击伤害加成",
  "Life Steal": "生命偷取",
  "Shield Bonus": "盾牌加成",
  "Block Chance": "格挡几率",
  "Magic Power": "魔法威力",
  "Healing Power": "治疗威力",
  Speed: "速度",
  HP: "生命",
  Mana: "法力",
  Gold: "金币",
  // captions
  "Equipment requirements and base values": "装备要求与基础数值",
  "Nonzero equipment stats": "非零装备属性",
  "Equipment flags": "装备标记",
  "Ability template and requirements": "技能模板与要求",
  "Spell values": "法术数值",
  "Class creation values": "职业创建数值",
  "Base class growth per level": "职业每级基础成长",
  "Specialization growth per level": "专精每级成长",
  "Verified translated class names": "已核实的职业译名",
  "Verified translated race names": "已核实的种族译名",
  "Compatible races:": "兼容种族：",
  "Boss base definition": "首领基础定义",
  "All seven seals": "全部七个封印",
  "No template class restriction": "模板没有职业限制",
  "Requires Good": "需要善良",
  "Requires Evil": "需要邪恶",
  "Required Weapon Types": "所需武器类型",
  "Requires Shield": "需要盾牌",
  "Can Target Ally": "可指定盟友",
  "Special Effect": "特殊效果",
  "Level Required": "所需等级",
  "Stamina Cost": "体力消耗",
  "Mana Cost": "法力消耗",
  Cooldown: "冷却",
  "Base Damage": "基础伤害",
  "Base Healing": "基础治疗",
  "Attack Bonus": "攻击加成",
  Duration: "持续时间",
  "Catalog Slot": "目录槽位",
  "Mana Before Wisdom": "感知前的法力消耗",
  "Magic Words": "咒语",
  "Is Multi Target": "多目标",
  "Spell Type": "法术类型",
  "Base Level": "基础等级",
  "Base HP": "基础生命",
  "Base Defense": "基础防御",
  "Is Unique": "唯一",
  "Is Cursed": "被诅咒",
  "Has Fire Enchant": "火焰附魔",
  "Has Frost Enchant": "冰霜附魔",
  "Has Lightning Enchant": "闪电附魔",
  "Has Poison Enchant": "毒素附魔",
  "Has Holy Enchant": "神圣附魔",
  "Has Shadow Enchant": "暗影附魔",
  "Has Boss Slayer": "弑神",
  "Has Titan Resolve": "泰坦的决心",
  "Bonus Strength": "力量加成",
  "Bonus Dexterity": "敏捷加成",
  "Bonus Constitution": "体质加成",
  "Bonus Intelligence": "智力加成",
  "Bonus Wisdom": "感知加成",
  "Bonus Charisma": "魅力加成",
  "Bonus Agility": "灵巧加成",
  "Bonus Stamina": "体力加成",
  "Bonus Max HP": "最大生命加成",
  "Bonus Max Mana": "最大法力加成",
  "Bonus Defense": "防御加成",
  // booleans and values
  true: "是",
  false: "否",
  Yes: "是",
  No: "否",
  None: "无",
  One: "单手",
  Two: "双手",
  OneHanded: "单手",
  TwoHanded: "双手",
  OffHandOnly: "仅副手",
  // slots
  Head: "头部",
  Body: "身体",
  Arms: "手臂",
  Hands: "手部",
  Legs: "腿部",
  Feet: "脚部",
  Waist: "腰部",
  Neck: "颈部",
  Neck2: "颈部 2",
  Face: "面部",
  Cloak: "披风",
  LFinger: "左手指",
  RFinger: "右手指",
  MainHand: "主手",
  OffHand: "副手",
  // rarity / armor / weapons
  Common: "普通",
  Uncommon: "精良",
  Rare: "稀有",
  Epic: "史诗",
  Legendary: "传奇",
  Artifact: "神器",
  Cloth: "布甲",
  Leather: "皮甲",
  Chain: "锁甲",
  Scale: "鳞甲",
  Plate: "板甲",
  Light: "轻甲",
  Medium: "中甲",
  Heavy: "重甲",
  Sword: "剑",
  Axe: "斧",
  Mace: "钉锤",
  Dagger: "匕首",
  Rapier: "细剑",
  Hammer: "战锤",
  Flail: "连枷",
  Scimitar: "弯刀",
  Greatsword: "巨剑",
  Greataxe: "巨斧",
  Polearm: "长柄武器",
  Staff: "法杖",
  Maul: "大锤",
  Instrument: "乐器",
  Bow: "弓",
  Shield: "盾牌",
  Buckler: "小圆盾",
  TowerShield: "塔盾",
  Magic: "魔法",
  Physical: "物理",
  Poison: "毒素",
  Fire: "火焰",
  Frost: "冰霜",
  Lightning: "闪电",
  Holy: "神圣",
  Shadow: "暗影",
  Arcane: "奥术",
  Necrotic: "死灵",
  // races and classes
  Human: "人类",
  Hobbit: "霍比特人",
  Elf: "精灵",
  "Half-Elf": "半精灵",
  Dwarf: "矮人",
  Troll: "巨魔",
  Orc: "兽人",
  Gnome: "侏儒",
  Gnoll: "豺狼人",
  Mutant: "变异人",
  Alchemist: "炼金术士",
  Assassin: "刺客",
  Barbarian: "野蛮人",
  Bard: "吟游诗人",
  Cleric: "牧师",
  Jester: "小丑",
  Magician: "法师",
  Paladin: "圣骑士",
  Ranger: "游侠",
  Sage: "贤者",
  Warrior: "战士",
  Tidesworn: "潮誓者",
  Wavecaller: "唤潮者",
  Cyclebreaker: "破轮者",
  Abysswarden: "深渊守望者",
  Voidreaver: "虚空掠夺者",
  "Mystic Shaman": "秘语萨满",
  MysticShaman: "秘语萨满",
  // stats
  Strength: "力量",
  Dexterity: "敏捷",
  Constitution: "体质",
  Intelligence: "智力",
  Wisdom: "感知",
  Charisma: "魅力",
  Agility: "灵巧",
  Stamina: "体力",
  // ability kinds and short rules
  Heal: "治疗",
  Buff: "增益",
  Debuff: "减益",
  Damage: "伤害",
  Rally: "鼓舞",
  "Second Wind": "背水一战",
  "ends its turn": "结束其回合",
  "it is used again": "再次使用时",
  and: "和",
  "Wisdom lowers the mana a cast costs. See": "感知会降低施法消耗。见",
  "level and mana": "等级与法力",
  "Choosing a specialization": "选择专精",
  "Changes by version": "版本变更",

  // generated reference prose and table labels
  "Classes:": "职业：",
  ". Template numbers are not a prediction of final damage or healing after your attributes, equipment and combat effects.":
    "。模板数值不代表结算属性、装备与战斗效果后的最终伤害或治疗。",
  ". This is a fixed spell definition; your character must still learn it and meet the combat requirements.":
    "。这是固定的法术定义；角色仍需学习并满足战斗要求。",
  "Required Level": "所需等级",
  "The stamina cost above is the template cost: an ability that needs level 50 or more costs 25 percent more stamina, and one that needs level 75 or more costs 40 percent more, rounded down.":
    "上表中的体力消耗是模板消耗：需求等级 50 及以上的技能额外消耗 25% 体力，需求等级 75 及以上额外消耗 40%，向下取整。",
  "Heal abilities:": "治疗技能：",
  "(level 1, 25 stamina, cooldown 5 rounds);": "（1 级，25 体力，冷却 5 回合）；",
  "(level 30, 40 stamina, cooldown 6 rounds).": "（30 级，40 体力，冷却 6 回合）。",
  "Taunt abilities:": "嘲讽技能：",
  "Taunt abilities: none.": "嘲讽技能：无。",
  "Defense abilities:": "防御技能：",
  "Defense abilities: none.": "防御技能：无。",
  "Base Strength": "基础力量",
  "Base Agility": "基础敏捷",
  "Attacks Per Round": "每回合攻击次数",
  "Monster tier samples": "怪物层级示例",
  "Level range": "等级范围",
  "HP at min / max": "生命（最小 / 最大）",
  "Strength at min / max": "力量（最小 / 最大）",
  "Defense at min / max": "防御（最小 / 最大）",
  "Spoiler: family lore": "剧透：家族背景",
  "Spoiler: divine lore": "剧透：神明背景",
  Starting: "初始",
  "Starting class available at character creation when compatible with your race. Starting class values combine with race creation bonuses; they are not the final equipped character sheet.":
    "初始职业在创建角色时可用，但必须与种族兼容。初始职业数值会叠加种族创建加成，并不是最终装备后的角色面板。",
  Platinum: "铂金",
  "Race bonuses and creation ranges": "种族加成与创建范围",
  "HP Bonus": "生命加成",
  "Min Height": "最低身高",
  "Max Height": "最高身高",
  "Min Weight": "最低体重",
  "Max Weight": "最高体重",
  "Skin Color": "肤色",
  "Hair Colors": "发色",
  "Boon constants below are base values. Favor strength and an active prayer change their effective size. Percent fields are percentages, not additional flat attributes.":
    "下列恩赐常量是基础值。恩宠强度与生效中的祈祷会改变实际大小。百分比字段表示百分比，不是额外固定属性。",
  "Base boon rules": "恩赐基础规则",
  "Deeds and taboos": "行为与禁忌",
  "Deed or taboo": "行为或禁忌",
  "Favor change": "恩宠变化",
  "Favor, prayer and sacrifice": "恩宠、祈祷与献祭",
  "Mental and wards": "精神与结界",
  "Warrior, Barbarian": "战士、野蛮人",
  "Warrior, Barbarian, Paladin": "战士、野蛮人、圣骑士",
  "Magician, Sage": "法师、贤者",
  "Light, Medium, Heavy": "轻甲、中甲、重甲",
  "Dungeon Floor": "地牢楼层",
  physical: "物理",
  Progression: "成长",
  Combat: "战斗",
  Abilities: "技能",
  Spells: "法术",
  Silver: "白银",
  Bronze: "青铜",
  Levels: "等级",
  Level: "等级",
  "Phase 1": "第一阶段",
  "Phase 2": "第二阶段",
  "Phase 3": "第三阶段",
  Utility: "通用",
  Social: "社交",
  Control: "控制",
  Element: "元素",
  Special: "特殊",
  "Min Age": "最低年龄",
  "Max Age": "最高年龄",
  Economy: "经济",
  Caverns: "洞穴",
  "Ancient Ruins": "古代遗迹",
  "Demon Lair": "恶魔巢穴",
  "Frozen Depths": "冰封深渊",
  Catacombs: "地下墓穴",
  Sewers: "下水道",
  "Volcanic Pit": "火山坑",
  "Abyssal Void": "深渊虚空",
  // languages
  En: "英语",
  Es: "西班牙语",
  Fr: "法语",
  Hu: "匈牙利语",
  It: "意大利语",
  Zh: "中文",
};

let generated = {};
try {
  generated = require("./wiki-zh-generated.json");
} catch (_) {
  generated = {};
}
const allText = { ...text, ...generated };

const entities = {
  "&amp;": "&",
  "&lt;": "<",
  "&gt;": ">",
  "&quot;": '"',
  "&#39;": "'",
};
const decode = (value) =>
  value.replace(/&(?:amp|lt|gt|quot|#39);/g, (m) => entities[m]);

function buildNameMap(data) {
  const map = new Map();
  const add = (value) => {
    if (!value || typeof value !== "object" || Array.isArray(value)) return;
    if (value.en && value.zh) map.set(value.en, value.zh);
  };
  const walk = (value) => {
    if (!value || typeof value !== "object") return;
    if (Array.isArray(value)) {
      for (const item of value) walk(item);
      return;
    }
    add(value.name);
    add(value.title);
    for (const [key, child] of Object.entries(value)) {
      if (key === "name" || key === "title") continue;
      walk(child);
    }
  };
  walk(data);
  // Longest first only matters for substring passes; text-node matching is exact.
  return map;
}

function localize(html, locale, names) {
  if (locale !== "zh") return html;
  let out = html.replace(/href="\/wiki\/en\/([^"#]*)#[^"]*"/g, 'href="/wiki/zh/$1"');
  out = out.replaceAll('href="/wiki/en/', 'href="/wiki/zh/');
  out = out.replace(
    /Built-in template ID (\d+)\. Randomly generated shop stock, modifiers and server mods are not included\. Acquisition is not inferred from rarity or value\./g,
    "内置模板 ID $1。不包含随机生成的商店库存、词缀与服务器模组；获取方式不根据稀有度或价值推断。",
  );
  out = out.replace(
    /Attack type: ([a-z]+)\. Samples are normal non-boss monsters at the tier endpoints\. NG\+, server mods and special encounters change live values\./g,
    (_all, kind) =>
      `攻击类型：${text[kind[0].toUpperCase() + kind.slice(1)] || kind}。样本是层级端点上的普通非首领怪物；NG+、服务器模组与特殊遭遇会改变实际数值。`,
  );
  out = out.replace(
    /Prestige class\. Unlock it through play, not the initial character selector\. Starting class values combine with race creation bonuses; they are not the final equipped character sheet\./g,
    "进阶职业。通过游玩解锁，不能在初始角色选择器中直接选择。初始职业数值会叠加种族创建加成，并不是最终装备后的角色面板。",
  );
  out = out.replace(/>([^<>]+)</g, (whole, raw) => {
    const trimmed = raw.trim();
    if (!trimmed) return whole;
    const value = decode(trimmed);
    const translated = names.get(value) ?? allText[value];
    if (!translated) return whole;
    return whole.replace(raw, raw.replace(trimmed, translated));
  });
  return out;
}

module.exports = { text, buildNameMap, localize };
