---
title: 世界首领
path: /wiki/zh/online/world-boss/
checked: 1.3.15
sources: Scripts/Systems/WorldBossSystem.cs, Scripts/Systems/WorldBossMath.cs, Scripts/Data/WorldBossData.cs, Scripts/Locations/MainStreetDistricts.cs, Scripts/Systems/DivineBlessingSystem.cs, Scripts/Systems/WorldEventSystem.cs, Scripts/Core/GameConfig.cs, Scripts/Locations/MainStreetClassic.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | none
history: 1.3.9 | 主街默认以经典布局打开，分区布局可在设置中选择。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | 你的攻击、强力攻击和精准打击现在会在世界首领身上触发主手武器的效果，你装备的吸血会在那里治疗你，世界首领护甲上的泰坦之志会以增加 5% 最大 HP 取代防御。
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | 你对世界首领的攻击会按你的完整暴击几率掷骰，第二次击杀世界首领会刷新正在进行的天下同庆。
---
世界首领是一场共享的在线战斗：每个加入的玩家都在与同一个首领战斗，其 HP 是共享的。它只存在于在线游玩中。首领及其能力见[首领参考](/wiki/zh/monsters/bosses/)。

## 世界首领在哪里

从主街按 7 前往世界首领；它位于经典菜单的在线一行。使用分区布局时，用 O 打开在线分区，然后按 B。你需要达到 {{balance:WorldBossMinLevel}} 级才能加入。你不在时首领被击杀所产生的奖励，会在你下次打开它时发放。

## 世界首领何时出现

世界首领每天在美国东部时间 {{balance:WorldBossSpawnHourEastern}}:00 出现，无论是否有人在线，并停留 {{balance:WorldBossWindowHours}} 小时。在它出现前 {{balance:WorldBossNoticeHoursBefore}} 小时会发出通知。

### 会出现哪个世界首领

游戏会取过去 {{balance:WorldBossActiveDays}} 天内活跃玩家的等级中位数，并在基础等级最多高出该中位数 {{balance:WorldBossPickLevelSlack}} 级的首领中随机挑选。首领以其基础等级和该中位数中较高的那个进行战斗。

### 如果世界首领没有被击杀会怎样

在其窗口结束时仍然存活的首领会撤退，并在第二天晚上回来，恢复其最大 HP 的 {{percent:WorldBossNightRegenFraction}}%，最多持续 {{balance:WorldBossMaxNights}} 个夜晚。当无人攻击它达到 {{balance:WorldBossRallyIdleMinutes}} 分钟时，它每 30 秒恢复其最大 HP 的 0.5%。

## 世界首领战斗如何进行

一次访问最多持续 {{balance:WorldBossMaxRoundsPerSession}} 个回合，随后你休息，游戏会保存。撤退或休息后，你可以在 {{balance:WorldBossRetreatCooldownSeconds}} 秒后回来；倒下后则需 {{balance:WorldBossFallCooldownSeconds}} 秒。

### 世界首领伤害上限

你一个回合造成的伤害最多计入首领最大 HP 的 0.6%，在它失衡时为 1.5 倍（0.9%）。等级低于首领的玩家，其伤害会按 N(你的等级) / N(首领等级) 缩小，其中 N(L) = 2 x L + 1.5 x L^1.05：30 级对 40 级首领时约为 0.75。

你的攻击、强力攻击和精准打击会在与怪物战斗时相同的几率和命中占比下触发主手武器的火焰、闪电、毒素、神圣和暗影效果，它们的伤害会计入该回合的伤害，然后再应用上限。闪电不会眩晕首领，冰霜在这里没有作用，神圣不会造成它对亡灵怪物造成的双倍伤害，武器毒素是一次相当于命中伤害 10% 或武器毒素值的伤害，而不是 4 个回合的中毒。你装备的吸血会按命中伤害的百分比治疗你。法术、职业技能和物品不会触发其中任何一项。

### 世界首领的阶段、焦点和预兆

- **阶段：** 第 2 阶段在其 HP 的 {{percent:WorldBossPhase2Threshold}}% 时开始，第 3 阶段在 {{percent:WorldBossPhase3Threshold}}% 时开始。
- **焦点：** 首领的普通攻击对它聚焦的玩家造成 {{balance:WorldBossFocusMultiplier}} 倍伤害，对其他所有人造成 {{balance:WorldBossOffFocusMultiplier}} 倍伤害。F（挑战）会夺取焦点 {{balance:WorldBossChallengeHoldSeconds}} 秒。
- **打击：** 有预兆的打击在你格挡（B）时消耗你最大 HP 的 {{percent:WorldBossTelegraphAnsweredPercent}}%，如果没有格挡，则消耗 {{percent:WorldBossTelegraphUnansweredPercent}}% 并附加其状态效果。
- **引导：** 有预兆的引导会被打断（T）破坏：所需的打断次数等于参战玩家数，最多 {{balance:WorldBossInterruptsMax}} 次。被破坏的引导会使首领失衡 {{balance:WorldBossStaggerSeconds}} 秒。成功落地的引导会消耗每个人最大 HP 的 {{percent:WorldBossTelegraphUnansweredPercent}}%，格挡的玩家则减半。
- **无法避免的命中：** 一次最多消耗你最大 HP 的 {{percent:WorldBossUnavoidableCapPercent}}%。

每个回答和挑战都会消耗你的回合。每日神迹在世界首领战斗中不起作用。你的神明的伤害恩赐和祈祷祝福的伤害加成为此会计入（参见[恩赐](/wiki/zh/gods/boons/)）。

## 造成多少伤害才能获得世界首领战利品

你的得分是你对首领造成的伤害除以一名玩家应分担的 HP，即其最大值的三分之一（首领是按 {{balance:WorldBossKillBudgetPlayers}} 名玩家设计的），最高为 1.0。得分达到 {{balance:WorldBossQualifyScore}} 或以上，你就有资格获得击杀奖励。

## 世界首领奖励

一次击杀会为每位符合条件的玩家支付 450 x 等级^1.5 x (0.25 + 0.75 x 得分) 的经验，以及 150 x 等级^1.5 乘以相同系数的金币，两者都再乘以协力加成：每多一名其他符合条件的玩家，增加 {{percent:WorldBossTogetherBonusPerAlly}}%，最多为 {{balance:WorldBossTogetherBonusCap}} 倍。经验上限为你升到下一级所需经验的一半。符合条件的玩家还会获得 {{balance:WorldBossFameQualified}} 点声望和一件物品：得分低于 0.25 为普通，0.25 起为精良，0.5 起为稀有，0.75 起为史诗。史诗或更高品质的世界首领护甲物品（不是武器）带有泰坦之志：穿戴者最大 HP 增加 5%，同伴或盟友也算，无论穿戴多少件带有该效果的物品都只生效一次。伤害最高的玩家额外获得 {{balance:WorldBossFameMvpExtra}} 点声望，并且当有 {{balance:WorldBossMvpLegendaryMinHumans}} 名或更多玩家符合条件时，还会获得一件传说物品。一次击杀还会开启天下同庆，怪物战斗经验增加 10%，直到下一次每日重置；在此之前的第二次击杀不会增加另一场（参见[世界事件](/wiki/zh/online/events/)）。

首领存活的夜晚，会向与它战斗过的人支付当晚击杀经验和金币的 {{percent:WorldBossWithdrawalPayFraction}}%。

单人独自一人的报酬，按等级列出：

{{table:world-boss-rewards}}

在较低等级时由上限决定：在表格中直到 30 级，即使只是合格分数也会支付全额封顶经验。
