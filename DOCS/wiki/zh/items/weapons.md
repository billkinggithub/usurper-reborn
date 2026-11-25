---
title: 武器与限制
path: /wiki/zh/items/weapons/
checked: 1.3.14
sources: Scripts/Data/EquipmentData.cs, Scripts/Core/Items.cs, Scripts/Core/EquipmentEnums.cs
history: 1.3.14 | none
history: 1.3.10 | none
history: 1.3.7 | 战利品武器在被穿戴过后仍保留其效果行。
history: 1.3.6 | 武器毒素现在使怪物中毒 4 回合，而非单次命中；新的触发会刷新该效果，而在玩家对战和世界首领战中它仍是单次命中。
history: 1.3.5 | 暗影之牙、毒刺与蛇牙现在每次命中有 20% 几率造成其毒素伤害。
history: 1.3.2 | 秘术萨满遵循其自身的主手武器规则。
history: 1.2.5 | 武器名称以你的语言显示，装备行会以 [1H] 或 [2H] 标记武器，商店列表会写出完整的武器类型，例如 Greatsword。
---
武器威力只是伤害的一个输入因素。武器类型、持握方式、职业兼容性与技能需求都会改变一把武器是否适合你的构筑。

## 武器槽位

角色有两个武器槽位：主手和副手。副手可持第二把单手武器或一面盾牌。双手武器会占据两个槽位，因此双手武器与盾牌不能随意搭配。全部槽位与持握规则见[装备槽位](/wiki/zh/items/equipment-slots/)。

{{table:items slot=MainHand}}

打开物品页面可查看其等级、力量、阵营和职业限制。唯一或被诅咒的标记在[献祭物品](/wiki/zh/gods/favor/)时也很重要。

## 毒武器

暗影之牙、毒刺与蛇牙，以及名为 Venomous 或带 of Venom 的战利品武器，都带有毒素。用它们命中时有 20% 几率使目标中毒 4 回合，毒素会在这些回合内持续造成伤害，而非一次性结算。在玩家对战和世界首领战中，它改为单次命中，会一次性结算伤害。每回合的伤害见[武器毒素](/wiki/zh/characters/afflictions/)。

