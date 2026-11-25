---
title: 圣所
path: /wiki/zh/world/sanctum/
checked: 1.3.15
sources: Scripts/Locations/SanctumLocation.cs, Scripts/Systems/AlignmentSystem.cs, Scripts/Data/HonorTournamentData.cs, Scripts/Core/GameConfig.cs, Scripts/Systems/MonsterGenerator.cs, Scripts/Locations/MainStreetDistricts.cs, Scripts/Locations/MainStreetClassic.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | none
history: 1.3.9 | 主街默认以经典布局开放，分区布局可在设置中选择。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | 25 级及以上的荣誉比武大会冠军拥有更多 HP 且攻击更狠，与同等级地牢怪物相同。
history: 1.3.2 | 圣所会像教堂一样在门口拒绝邪恶阵营角色。
history: 1.2.5 | 荣誉比武大会冠军及其掉落物会以每位玩家的语言显示，每日费用行也已翻译成所有五种语言。
---
圣所提供慈善活动和荣誉比武大会。它不同于神殿，也不同于城堡的政治菜单。在主街按 + 前往圣所。使用分区布局时，按 C 打开城堡庭院区，然后按 S。它的神圣结界会像教堂的一样在门口拒绝邪恶阵营角色；其他所有阵营都可以进入。

## 施舍要花多少钱

三项慈善行动会使你向侠义靠近，每项都按你的等级定价：

- **施舍（A）：** {{balance:AlmsGoldPerLevel}} 金币 x 你的等级，每天 {{balance:MaxAlmsPerDay}} 次，每次 {{balance:AlmsChivalryReward}} 点侠义。
- **孤儿院（O）：** {{balance:OrphanageGoldPerLevel}} 金币 x 你的等级，每天 {{balance:MaxOrphanageGiftsPerDay}} 次，{{balance:OrphanageChivalryReward}} 点侠义。
- **济贫院（H）：** {{balance:HospiceGoldPerLevel}} 金币 x 你的等级，每天 {{balance:MaxHospiceTithesPerDay}} 次，{{balance:HospiceChivalryReward}} 点侠义。

信仰会成员少付 {{percent:SanctumFaithMemberDiscount}}%。20 级时，施舍花费 1,000 金币，孤儿院 4,000，济贫院 3,000。侠义遵循通常的阵营增益规则，因此你的侠义变高后，增加量会减少（见[阵营](/wiki/zh/characters/stats/)）。慈善赠礼不是商店购买，不会给予装备。

## 如何解锁荣誉比武大会

荣誉比武大会（T）会在侠义达到 250，即名望达到守护者等级后出现。它需要当天还剩一次玩家战斗机会，并与锚点大道试炼场共享每天一次的挑战次数，所以两者只能选一个。入场费为 {{balance:GauntletEntryFeeQuadraticCoefficient}} x 你的等级平方：20 级时为 4,000 金币。

## 荣誉比武大会支付什么

你要连续与 3 名冠军战斗。每击败一名冠军，你会获得 {{balance:GauntletGoldPerWavePerLevel}} x 你的等级的金币、{{balance:GauntletXPPerWave}} x（冠军序号 + 3）x 你的等级的经验、第一至第三名分别 5、10、15 点声望，以及 10、15、20 点侠义，另加一件主题物品。一场失败会结束比武大会，并保留你在失败前赢得的奖励：有 {{balance:GauntletDeathChancePercent}}% 的概率是真正的死亡，否则你会留下 1 HP。

请像准备其他连续战斗一样认真准备比武大会。精神崩溃可能在下一场战斗前打断连续挑战。

## 英雄大厅

英雄大厅（V）记录荣誉与认可。

有关角色状态与恢复，见[精神](/wiki/zh/characters/mental/)和[治疗师](/wiki/zh/world/healer/)。
