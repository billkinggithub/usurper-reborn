---
title: 护甲与饰品
path: /wiki/zh/items/armor/
checked: 1.3.15
sources: Scripts/Data/EquipmentData.cs, Scripts/Core/Items.cs, Scripts/Systems/GearSetSystem.cs, Scripts/Core/Character.cs, Scripts/Locations/BaseLocation.cs, Scripts/Systems/InventorySystem.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.11 | none
history: 1.3.10 | none
history: 1.3.9 | none
history: 1.3.8 | none
history: 1.3.7 | 穿上或脱下物品时，泰坦的决心提供的最大生命值会立刻显示；战利品物品在被穿戴过后仍保留其效果行。
history: 1.3.6 | none
history: 1.3.5 | 盾牌经过背包时仍会保留附魔赋予它的护甲威力；穿戴时，最大生命值和最大法力值战利品效果会加到你的上限上。
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | 秘术萨满遵循其自身的护甲重量限制。
history: 1.2.5 | 护甲名称以你的语言显示，商店与装备行会以 [Lgt]、[Med] 或 [Hvy] 标记护甲重量。
---
护甲威力、防御加成、抗性和格挡效果是不同的字段。更昂贵的装备可能以一种保护换取另一种。你职业的护甲规则仍然适用。

使用[完整装备目录](/wiki/zh/items/)比较各槽位，并打开物品查看每一项非零属性与限制。

## 整体评估物品

盾牌可以支持需要盾牌的技能。饰品可以增加属性或资源容量，而不必是身体护甲。被诅咒的物品可能带来单个护甲数值无法揭示的后果；[战利品指南](/wiki/zh/items/)列出了诅咒的作用。

服务器生成的库存可能与固定参考不同。购买前请阅读商店的查看信息，装备后请检查状态。

## 套装

共有 8 套套装：皮革、链甲、丝绸、暗影、钢质、加固、锻造和秘银。穿戴同一套装的部件会在 2、4、6 件时获得加成（丝绸为 2、4、5 件），你达到的每一档都会累加。部件按基础名称归属套装，因此同名的商店部件和地牢掉落都计入，无论其稀有度或附魔如何。

{{table:gear-sets}}

## 套装部件如何计数

部件按其占据的槽位计数，因此同套装的两枚戒指计为 2 件。体质加成还会通过体质提高最大生命值，这会在套装提供的任何最大生命值之外额外累加。NPC、同伴和 PvP 对手也获得相同的套装加成。`/gear` 命令（或 `/eq`）会列出你穿戴的每套套装、其部件以及已激活的档位，物品自身的界面也会标明其套装。
