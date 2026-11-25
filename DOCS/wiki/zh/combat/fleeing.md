---
title: 恐惧、撤退与逃跑
path: /wiki/zh/combat/fleeing/
checked: 1.3.15
sources: Scripts/Systems/CombatEngine.cs, Scripts/Systems/MentalSystem.cs, Scripts/Systems/MiracleSystem.cs, Scripts/Systems/FactionSystem.cs, Scripts/Systems/DifficultySystem.cs, Scripts/Systems/GodDeedSystem.cs, Scripts/Core/GameConfig.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | 街头商人的烟雾弹给予黑暗 +2，且不会帮助你逃跑，其文本也如此说明。
history: 1.3.10 | 地牢前哨的烟雾粉会在你的下一场战斗中给予 +2 灵巧；它不是烟雾弹，也不会帮助你逃跑。
history: 1.3.9 | none
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | 小丑的消失魔术与贤者的逃脱现在遵循逃跑规则：它们在噩梦难度下失败，并在旧神战斗或楼层首领仍存活时掷旧神逃跑几率。
history: 1.3.5 | none
history: 1.3.4 | 一次失败的逃跑现在还会使曼威命名技能在本回合剩余时间内的伤害减半。
history: 1.3.3 | 你逃跑时仍处于倒下的盟友会以最大生命的一半站起。
history: 1.3.2 | none
history: 1.3.0 | none
history: 1.2.7 | none
history: 1.2.6 | none
history: 1.2.5 | 恐惧讯息以及逃跑与撤退标签会以玩家语言显示，怪物名称也会翻译。
history: 1.2.4 | none
---
## 恐惧

精神过低引发的恐惧会在怪物战斗开始时判定：动摇时为 {{balance:MentalShakenFearPct}}%，濒临崩溃或崩溃时为 {{balance:MentalBreakingFearPct}}%。恐惧会使你失去第一次行动。每位组队玩家使用自己的精神。你的神明或其他支援可以防止相关效果，但普通治疗无法消除其原因。

## 逃跑几率

你逃离怪物战斗的几率为 40% 加上敏捷的一半，再加上等级的三分之一，最多 75%。在战斗中按 R 尝试。

- 游侠或刺客加 15，小丑或吟游诗人加 10。
- 暗影成员在 0 阶时加 15，最高阶时提升至 45。
- 神明的逃跑恩泽会加上其百分比。
- 无论你加多少，75% 的上限都成立。例如：敏捷 40、等级 15 时为 40 + 20 + 5 = 65%。

楼层首领也使用此几率。

### 逃离旧神

你逃离旧神战斗的几率为 20%。生命低于一半时，生命在 50% 以下每缺少一个百分点，几率增加 1.75，最高 60%：生命为 30% 时为 55%。职业、阵营或恩泽加成都无效。

### 逃跑失败时

逃跑失败会消耗你该回合的行动。该回合剩余时间内，怪物对你的每次命中都会减半，至少 1。

### 烟雾弹

若你携带烟雾弹，按 R 时会优先使用它，让你无需掷骰即可脱身。它在旧神战斗中无效。

### 噩梦

在噩梦难度下你完全无法逃跑，烟雾弹也无法使用。

## 逃跑的代价

从怪物战斗中成功逃跑会消耗 1 点声望与 {{balance:MentalFleeLoss}} 点精神（乌姆布拉思的守护可以降低精神损失），而瓦洛里安会将其视为禁忌：其追随者失去 {{balance:GodTabooMinor}} 点神恩。请阅读结果讯息，不要以为逃脱没有代价。

## 神圣逃脱

乌姆布拉思可用的神迹可以在没有普通逃跑惩罚的情况下将你从怪物战斗中移除：不损失声望、精神或禁忌。神迹有每日使用次数，需要相应的神恩阶层，并不是无限的逃生按钮。

在依赖任何一种保护之前，请阅读[神恩与神迹](/wiki/zh/gods/favor/)与[精神](/wiki/zh/characters/mental/)。

## 逃脱技能

小丑的消失魔术与贤者的逃脱法术按本页的逃跑规则运作。在噩梦难度下，它们无法让你脱身，且会消耗该回合。在旧神战斗中，或当活着的怪物中有楼层首领时，它们会按「逃离旧神」中的旧神几率成功；失败会消耗你的回合，并显示相同的失败讯息，但不会使该回合怪物对你的命中减半。面对其他怪物时，它们总能让你脱身。
