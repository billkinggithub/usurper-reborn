---
title: 荒野探索
path: /wiki/zh/world/wilderness/
checked: 1.3.15
sources: Scripts/Data/WildernessData.cs, Scripts/Locations/WildernessLocation.cs, Scripts/Data/DruidShrineData.cs, Scripts/Core/GameConfig.cs, Scripts/Core/Character.cs, Scripts/Systems/GodBoonSystem.cs, Scripts/Systems/MentalSystem.cs, Scripts/Systems/MonsterGenerator.cs, Scripts/Data/BeastData.cs, Scripts/Systems/CombatEngine.cs, Scripts/Systems/StatEffectsSystem.cs, Scripts/Systems/AlignmentSystem.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | 当你持有强盗契约或强盗突袭进行时，低语森林的强盗斥候和铁峰山脉的山贼在那里的遭遇率为 8 场中的 3 场，而不是 8 场中的 1 场。
history: 1.3.9 | none
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | 25 级及以上的荒野怪物拥有更多 HP 且攻击更狠，与同等级地牢怪物相同。
history: 1.3.2 | 山地山羊的被动文本和三座德鲁伊圣坛的文本现在只说明它们给予什么。
history: 1.2.5 | 野兽和怪物名称会以玩家语言显示，野兽与怪物遭遇行在 79 列处换行。
history: 1.2.4 | 驯服成功文本在 79 列处换行。
history: 1.2.3 | 荒野侦察、野兽种类、圣坛列表和发现新闻已翻译成所有五种语言。
---
荒野位于城镇和地牢之外。它有四个地区，各自按你的等级开放，包含战斗、觅食、废墟、旅人、路边圣坛、可重访的发现，以及五座用于朝圣的德鲁伊圣坛。

## 荒野地区与所需等级

{{table:wilderness-regions}}

等级低于地区要求时，地区会拒绝你。荒野战斗不会产生地牢深度损耗。

## 每天能旅行几次

你每天可以进行 {{balance:WildernessMaxDailyExplorations}} 次探索旅行，并重访 {{balance:WildernessMaxDailyRevisits}} 次发现。单人游戏中，一次旅行消耗 {{balance:WildernessTimeCostMinutes}} 游戏分钟，并增加 {{balance:WildernessFatigueCost}} 点疲劳；在线时两者都不消耗。你每天第一次荒野探索会恢复 {{balance:MentalWildernessGain}} 点精神。

## 旅行中会发生什么

每次旅行是一次遭遇：40% 为战斗，25% 为觅食，15% 为废墟，10% 为旅人，10% 为路边圣坛。之后有 10% 的概率发现该地区的一处新发现，另有 {{balance:BeastEncounterChancePercent}}% 的概率遇到可驯服的野兽（见[野兽](/wiki/zh/combat/companions/)）。

西尔瓦娜的恩赐在恩宠满值时，最多为战斗胜利的荒野额外金币、觅食金币、废墟金币和圣坛经验增加 {{balance:GodBoonSylvanaWildernessPct}}%。它不会改变战斗的击杀奖励。

### 荒野战斗

怪物是该地区八种具名生物之一，每种概率相同；当你持有强盗契约或强盗突袭进行时，森林中的强盗斥候和山脉中的山贼在那里的遭遇率为 8 场中的 3 场，而不是 8 场中的 1 场（是其份额的 3 倍）。怪物的等级取地区等级与（你的等级 - 2 + 0 到 4）中的较高者，并按该等级的地牢怪物构建，拥有自己的族群和能力。你的同伴会与你并肩作战。获胜会支付通常的击杀奖励，外加 10 到 29 乘以（1 + 地区等级 / 10）的额外金币：森林为 1.1 倍，山脉为 2 倍，沼泽为 3 倍，海岸为 4 倍（40 到 116 金币）。

### 觅食

觅食会以相同权重从该地区的五种结果中抽取一种（列在上表中）。只有当你的草药数量低于其上限时，才会获得一株草药。小治疗恢复最大 HP 的十分之一，中治疗恢复五分之一。金币使用 L，即地区等级和你的等级中的较高者：小金币为 30 x L 加上 0 到 20 x L - 1，中金币为 100 x L 加上 0 到 200 x L - 1，大金币为 150 x L 加上 0 到 200 x L - 1。30 级时，大金币为 4,500 到 10,499。

### 废墟

如果你搜索废墟：60% 获得宝藏（中金币，并有 30% 的概率获得一瓶治疗药剂，直到你的携带上限），20% 触发陷阱，损失最大 HP 的十分之一（绝不低于 1 HP），20% 什么也没有。

### 旅人

如果你交谈：40% 的情况下旅人会以 20 到 49 金币出售一瓶治疗药剂，30% 分享一条提示，30% 治疗你最大 HP 的八分之一。

### 路边圣坛

如果你祈祷：30% 恢复最大 HP 和法力的四分之一，25% 永久 +1 力量、敏捷或感知，20% 给予 10 + 5 x 你的等级的经验，25% 什么也没有。

## 荒野发现

每个地区有两处发现，各自有等级（列在上表中）。一次旅行后的 10% 判定会发现一处发现，从该地区你尚未发现且等级符合的发现中抽取。重访发现（D）会进行该发现所属类型的遭遇（战斗、圣坛、废墟或旅人），概率与旅行时相同。重访不消耗旅行次数，不消耗时间或疲劳，也不会判定新的发现或野兽。

## 德鲁伊圣坛：朝圣与共鸣

朝圣（P）会使你与五座德鲁伊圣坛之一共鸣。共鸣在线持续 {{balance:ShrineAttunementHours}} 个现实小时，单人游戏中持续到下一个游戏日结束；你同一时间只能持有一个共鸣，在它结束前不能开始另一个。每次拜访使你在该圣坛的恩宠 +1，并可能改变你的阵营。

{{table:druid-shrines}}

### 每种共鸣有什么效果

- **石环（铁峰山脉）：** 每个战斗回合开始时恢复 {{balance:ShrineTerravokHpRegenPerRound}} 点 HP。
- **断刃祭坛（铁峰山脉）：** 你的基础攻击造成 {{percent:ShrineMaelkethMeleeBonus}}% 额外伤害。
- **月井（黑泥沼泽）：** 暴击率 +{{balance:ShrineNocturaCritChanceBonus}}。
- **提灯圣坛（低语森林）：** 神圣能力伤害 +{{percent:ShrineAurelionHolyDamageBonus}}%，神圣附魔触发 +{{percent:ShrineAurelionHolyProcBonus}}%。
- **潮汐之心（破浪海岸）：** 魅力 +{{balance:ShrineVeloraCharismaBonus}}，NPC 反应提高 {{percent:ShrineVeloraReactionBonus}}%。

### 圣坛恩宠赠礼

第 10 次拜访圣坛会给予一份永久礼物：石环 +25 最大 HP，断刃祭坛 +3 力量，月井 +3 敏捷，提灯圣坛 +5 感知，潮汐之心 +5 魅力。第 25 次和第 50 次拜访只给一条消息，没有别的东西。

## 参考不能承诺的事

内置的地区定义并不能证明某件具名物品一定在那里掉落。本 wiki 不会根据风味文本或稀有度臆造掉落来源。固定装备需求请使用[装备目录](/wiki/zh/items/)。
