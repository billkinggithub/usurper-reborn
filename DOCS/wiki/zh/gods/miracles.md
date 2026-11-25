---
title: 每日神迹
path: /wiki/zh/gods/miracles/
checked: 1.3.15
sources: Scripts/Systems/MiracleSystem.cs, Scripts/Systems/CombatEngine.cs, Scripts/Data/BeastData.cs, Scripts/Core/GameConfig.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | none
history: 1.3.9 | none
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | none
---
神迹需要神选者阶位，即 {{balance:GodFavorTierChosenMin}} 点或更多恩宠，每次每日重置只能使用一次。只有当神迹能派上用场时，战斗菜单才会显示神迹按键。队伍中的每位玩家各自拥有一次使用机会。保存并重新读取不会恢复已消耗的神迹。

## 施放神迹需要多少恩宠

神选者阶位从 {{balance:GodFavorTierChosenMin}} 点恩宠开始（见[恩宠表](/wiki/zh/gods/favor/)）。低于此阶位时，神殿的祭坛界面会把神迹显示为锁定。无论是否使用，使用次数都会在每日重置时恢复。

## 治疗与资源

- **阿玛拉：** 你与每一位活着的盟友都会回复至满生命。当队伍中有人受伤时提供。
- **泰兰：** 你的生命回复至满值。当你受伤时提供。
- **阿卡努斯：** 你的法力被充满。当你的法力未满时提供。

## 攻击、控制与脱身

- **索拉里乌斯：** 一名普通的亡灵或恶魔会被驱逐：它当场死亡。首领、小首领或旧神不会被驱逐；改为承受其最大生命值 {{balance:MiracleBanishBossDamagePct}}% 的伤害。仅当你正与活着的亡灵或恶魔战斗时提供。
- **瓦洛里安：** 你发动一次攻击，其第一击必定暴击，造成 {{balance:MiracleCritMultiplier}} 倍伤害。
- **朱迪卡：** 束缚你选中的敌人，或生命值最高的敌人，持续 {{balance:MiracleBindRounds}} 回合；首领可以按通常的定身规则抵抗。
- **迪斯科尔迪亚：** 使每个活着的敌人混乱 {{balance:MiracleConfuseRounds}} 回合，并受群体混乱通常的首领限制。
- **乌姆布拉思：** 你从战斗中消失，且不受通常的逃跑惩罚：不会损失声望、精神或恩宠。仅在可以逃离战斗时提供。
- **西尔瓦娜：** 一头幽灵狼，与你同等级的恐狼，加入你并肩作战，仅限该场战斗。

## 莫提斯与死亡保护

莫提斯会自动生效：当你在怪物战斗中即将死亡，且当天的神迹尚未使用时，你会被留在 1 点生命，战斗随即结束；若没有怪物还站着，则算作胜利，否则算作脱身。队伍中一位信奉莫提斯的追随者也会以 1 点生命留在战斗中。莫提斯在逮捕战或表演战中不会生效，也不会作用于因精神崩溃而导致的死亡。

## 神迹在哪些场合无效

神迹在玩家战斗或世界首领战斗中不可用。不要围绕属于另一战斗场合的神迹按键来规划这些遭遇。

神迹不能取代补给或[精神治疗](/wiki/zh/characters/mental/)。它的每日使用次数必须可用，你的恩宠必须达到该阶位，且它的效果必须对当前战斗有用。
