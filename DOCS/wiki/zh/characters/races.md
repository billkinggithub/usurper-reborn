---
title: 种族
path: /wiki/zh/characters/races/
checked: 1.3.14
sources: Scripts/Core/GameConfig.cs, Scripts/Systems/WorldSimulator.cs, Scripts/Systems/CharacterCreationSystem.cs, Scripts/Systems/MentalSystem.cs, Scripts/Systems/CombatEngine.cs, Scripts/Core/Items.cs, Scripts/Systems/HagglingEngine.cs, Scripts/Locations/WeaponShopLocation.cs
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | none
history: 1.3.9 | none
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | 被豺狼人毒咬中毒的怪物不再打得更狠，首领的物理免疫与神圣护甲会削减该毒素，且毒咬不再由炼金术士投掷的炸弹触发。
history: 1.3.5 | 豺狼人的毒咬与武器触发、生命偷取一样，不再由那些被算作近战命中的魔法职业技能触发。
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | 巨魔在武器店购买武器时少付 10%。
history: 1.3.1 | none
history: 1.3.0 | 豺狼人的毒咬只会在近战命中时使目标中毒；它不再由法术、魔法技能、远程技能或手持弓进行的挥击触发。
history: 1.2.7 | none
history: 1.2.6 | none
history: 1.2.5 | 种族描述、职业限制原因与种族帮助界面均以五种语言显示。
history: 1.2.4 | none
history: 1.2.3 | none
---
种族在角色创建时提供加成，并限制部分职业选择。种族还会影响地牢中的精神劳损；请查看自己的状态，而不要假定两个等级相同的角色恢复或劳损的速度一样。

{{table:races}}

打开某个种族的页面可查看其创建属性范围。外观字段是生成器设置，不是战斗加成。

## 各种族的 NPC 能活多久

表格还列出各种族 NPC 的寿命。NPC 每 {{balance:NpcLifecycleHoursPerYear}} 个现实小时长一游戏岁，并在达到本种族寿命时因年老而死：精灵 NPC 活 200 游戏年，从其出生算起约 80 个现实日。你自己的角色不会这样衰老。[NPC 的一生](/wiki/zh/online/npcs/)涵盖完整的生命周期。

## 创建加成

在角色创建时，种族只会把加值加到力量、体力、防御与生命值上。灵巧、魅力、敏捷、感知、智力与体质来自掷骰和你的职业，没有种族加成。完整的创建掷骰见[属性](/wiki/zh/characters/stats/)。

## 各种族不能选择的职业

职业兼容性在[角色创建](/wiki/zh/getting-started/)期间强制执行。以下是各种族不能选择的初始职业：

- 人类：秘术萨满。
- 霍比特人：野蛮人、秘术萨满。
- 精灵：野蛮人、秘术萨满。
- 半精灵：秘术萨满。
- 矮人：魔法师、贤者、秘术萨满。
- 巨魔：炼金术士、刺客、吟游诗人、牧师、小丑、魔法师、圣骑士、贤者。
- 兽人：吟游诗人、魔法师、圣骑士、贤者。
- 侏儒：野蛮人、秘术萨满。
- 豺狼人：炼金术士、牧师、魔法师、圣骑士、贤者。
- 变异人：秘术萨满。

因此，秘术萨满只对巨魔、兽人与豺狼人开放。种族对 NG+ 的进阶职业没有任何限制。每个[职业页面](/wiki/zh/characters/classes/)也会列出其兼容种族。

## 精神劳损

种族会缩放你在地牢中承受的精神劳损：

- 巨魔、兽人、豺狼人与变异人：正常劳损的 {{balance:MentalStrainRacePctHardy}}%。
- 精灵与霍比特人：{{balance:MentalStrainRacePctSensitive}}%。
- 半精灵与侏儒：{{balance:MentalStrainRacePctUneasy}}%。
- 人类与矮人：100%。

你的职业会再缩放一次。[精神指南](/wiki/zh/characters/mental/)说明两者如何相乘。

## 种族被动：巨魔与豺狼人

有两个种族在战斗中拥有自己的被动：巨魔会再生，豺狼人拥有毒咬。其余八个种族的差异体现在创建加成、职业限制与精神劳损上。霍比特人与侏儒还不能穿戴重型护甲：见[按职业划分的装备](/wiki/zh/characters/classes/)。

在战斗之外，巨魔在武器店购买武器时也少付 10%。

## 巨魔再生

你扮演的巨魔在未满血时，每战斗回合结束时恢复最大生命值的 2%，且每次不少于 3 点 HP。提升体质的药物会把该加成的十分之一加到恢复量上。

## 豺狼人的毒咬

豺狼人拥有被动技能毒咬。豺狼人每次以近战命中怪物时，有 15% 的几率使其中毒 3 回合。毒咬绝不会使已经中毒的目标再次中毒。它不会由法术、魔法技能、远程技能或手持弓进行的挥击触发。
