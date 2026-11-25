---
title: 锚点大道的挑战
path: /wiki/zh/world/anchor-road/
checked: 1.3.15
sources: Scripts/Locations/AnchorRoadLocation.cs, Scripts/Locations/MainStreetDistricts.cs, Scripts/Core/GameConfig.cs, Scripts/Data/GauntletChampionData.cs, Scripts/Systems/QuestSystem.cs, Scripts/Systems/AlignmentSystem.cs, Scripts/Systems/MonsterGenerator.cs, Scripts/Systems/CombatEngine.cs, Scripts/Locations/MainStreetClassic.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | 契约只有在仍未被接取时才能领取，会显示剩余天数，并说明失败不会损失金币或声望；佣兵馆契约在佣兵馆交付；当你持有强盗契约时，森林和山脉中的强盗遭遇率为 8 场中的 3 场。
history: 1.3.9 | 主街默认以经典布局开放，分区布局可在设置中选择。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | 武器附魔和生命偷取现在会在悬赏追猎和帮派战争战斗中生效，魔法抗性最多可将这些战斗中的法术伤害削减一半。
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | 试炼场中 25 级及以上的怪物和冠军拥有更多 HP 且攻击更狠，与同等级地牢怪物相同。
history: 1.3.2 | 商道上的匪徒契约会计入荒野强盗，需要 3 次击杀，持续 14 天；劫狱每天可尝试一次。
history: 1.3.1 | none
history: 1.3.0 | none
history: 1.2.7 | none
history: 1.2.6 | none
history: 1.2.5 | 被拒绝的佣兵馆交付现在会用文字说明原因，试炼场冠军公告会以每位玩家自己的语言送达。
history: 1.2.4 | none
history: 1.2.3 | none
---
锚点大道是城镇的挑战场地。在主街按 C 进入挑战。使用分区布局时，按 C 打开城堡庭院区，然后再按 C。完整城镇菜单解锁后，它就会出现。

## 挑战

- **B 悬赏追猎：** 与一名名声黑暗的城镇居民战斗，或与一名接近你等级的城镇居民战斗。它消耗一次每日玩家战斗机会。
- **G 帮派战争：** 你的队伍与另一支队伍战斗。你需要一支队伍，并且当天还有剩余团队战次数。
- **T 试炼场：** 十波怪物和冠军，每天一次，入场费随你的等级增长。
- **M 佣兵馆：** 从三个派系处接取自由契约，每天可接几份。

试炼场不是[竞技场](/wiki/zh/online/arena/)，后者是在线玩家对战。

## 悬赏追猎的报酬

悬赏板最多列出 5 名黑暗超过 200 的 NPC，黑暗最高的排在前面；如果没有，则列出 3 名不超过你等级 + 5 的随机 NPC。一场战斗消耗一次每日玩家战斗机会。获胜会支付目标等级 x 100 + 其黑暗值的金币，以及目标等级 x 50 的经验，并将目标打到 0 HP。失败会让你至少留下 1 HP。

## 试炼场

你需要达到 {{balance:GauntletMinLevel}} 级，消耗一次每日玩家战斗机会，并支付 {{balance:GauntletEntryFeeQuadraticCoefficient}} x 你的等级 x 你的等级的金币（30 级时为 9,000）。每天可以挑战一次。

### 试炼场波次

共有 {{balance:GauntletWaveCount}} 波。第 1 到 3 波是一只等级为你的等级 - 3 + 波次的怪物。第 4 到 10 波是七名冠军依次出场，每名都是等级为你的等级 + 其等级加成（最多 100）的怪物，拥有自己的 HP、力量、防御倍率和能力，并以首领方式战斗。你独自作战。

{{table:gauntlet-champions}}

波次之间，你会恢复 {{percent:GauntletHealBetweenWaves}}% 的最大 HP 和 {{percent:GauntletManaRestoreBetweenWaves}}% 的最大法力；在第一波之后的每一波开始前，你都可以停下并保留已赢得的奖励。

### 试炼场奖励

每赢下一波，你会获得 {{balance:GauntletGoldPerWavePerLevel}} x 你的等级的金币和 {{balance:GauntletXPPerWave}} x 波次 x 你的等级的经验，并获得 1 点声望（第 1 到 3 波）、2 点（第 4 到 6 波）、3 点（第 7 到 9 波）或 5 点（第 10 波）。30 级时，全部十波在最终奖励之前支付 15,000 金币和 41,250 经验。完成第 10 波会根据你完成时的等级支付最终奖励；如果这是你目前为止的最好成绩，还会获得该层级的头衔：

{{table:gauntlet-tiers}}

总冠军永久保留 +{{percent:GrandChampionDamageBonus}}% 伤害和 +{{percent:GrandChampionDefenseBonus}}% 防御。试炼场有自己的成就。

### 试炼场冠军战利品

你击败的每名冠军都会掉落自己的物品，并按你的等级生成。每次挑战开始时，会从冠军中选出一名（35% 概率为暴君，其余每名约 11%），其掉落物按你的最高稀有度生成：20 级以下为优秀，20 级起为稀有，40 级起为史诗，60 级起为传奇，80 级起为神器。其余冠军掉落的物品稀有度低 1 或 2 级。

### 我会在试炼场里死吗

每一波都有 {{balance:GauntletDeathChancePercent}}% 的概率是生死战：输掉那一波就是真正的死亡，还会收回本次挑战获得的声望。输掉其他波次会损失 {{percent:GauntletDragoutXPLossPercent}}% 的经验，以及本次挑战的声望 + {{balance:GauntletDragoutFameLossPenalty}}。逃离一波会结束挑战，并保留你已赢得的奖励。

## 佣兵馆契约

王冠、暗影和信仰会各自在板上发布契约，每天刷新一次；未被接取的契约会在 {{balance:MercContractStaleDays}} 天后消失。你每天可以接取 {{balance:MaxMercContractsPerDay}} 份契约，每份有 7 天完成时间，商道上的匪徒则有 14 天。

### 佣兵阶位

你的阶位来自已完成的契约，它决定每个派系向你展示多少契约以及你的报酬。2 阶契约从佣兵阶位开始出现。

{{table:merc-ranks}}

### 佣兵契约报酬

一份契约会支付你的等级 x {{balance:MercContractBaseGoldTier1}} x 契约报酬系数的金币，交付时再乘以你阶位的报酬系数。契约数量为契约基础数量 + 你的等级 / 5，但商道上的匪徒除外，它需要在任意等级下击杀 3 名[荒野](/wiki/zh/world/wilderness/)中的强盗斥候和山贼；当你持有该契约时，那里的遭遇率为 8 场中的 3 场，而不是 8 场中的 1 场。30 级时，不洁亡者（报酬系数 1.0，基础数量 3）在你阶位系数生效前，为 9 只僵尸的击杀支付 4,500 金币。

{{table:merc-contracts}}

完成一份契约会增加 15 点（1 阶）或 20 点（2 阶）对应派系声望，每个派系每天最多获得 {{balance:MaxDailyMercStandingGain}} 点。信仰会契约还会使你向侠义移动 3 点，暗影契约则使你向黑暗移动 3 点。已完成契约的数量会延续到[新游戏+](/wiki/zh/characters/new-game-plus/)。

## 城镇控制

有队伍时，你可以按 C 为你的队伍夺取城镇，或按 F 放弃城镇控制。

## 监狱场地与劫狱

P 通往牢房外的监狱场地。你可以查看囚犯，或每天尝试一次劫狱。概率为（30 + 你的等级 + 灵巧 / 5）%。成功会使你的侠义 +50，并登上新闻。失败会损失五分之一的最大 HP（绝不低于 1），并使你的黑暗 +25。无论成败，都不会有人获释。

## 状态与返回

S 显示你的挑战状态，R 返回主街。
