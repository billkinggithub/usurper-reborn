---
title: 精神健康
path: /wiki/zh/characters/mental/
checked: 1.3.14
sources: Scripts/Systems/MentalSystem.cs, Scripts/Core/GameConfig.cs, DOCS/release-notes/RELEASE_NOTES_1.2.0.md, Scripts/Systems/GriefSystem.cs, Scripts/Systems/CombatEngine.cs, Scripts/Core/Character.cs
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | 信仰会成员在治疗师处接受谈话治疗、购买柳叶药剂与进行戒瘾康复时少付 15% 至 35%。
history: 1.3.10 | 当你的配偶在你的战斗之外死亡时，悲恸也会开始：单人中立即开始，在线则在下次登录时开始。
history: 1.3.9 | none
history: 1.3.8 | 被命令在地牢房间中等待的剧情同伴，在等待期间不会减轻新房间带来的劳损。
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | 对倒下的同伴或 NPC 盟友的悲恸及其精神损失，只会在怪物将其了结时产生，绝不会在其刚倒下时产生。
history: 1.3.2 | 每位悲恸达到接受的剧情同伴会给予你 5 点感知，最多 25 点；只要该加成生效，主街就会显示这份感知。
history: 1.3.1 | none
history: 1.3.0 | none
---
精神衡量你的角色应对压力的能力，与 HP 分开计算。状态界面会显示你当前的精神与所处区间。精神会随角色一起保存。

{{table:mental}}

## 劳损与损失

进入新的地牢房间与结束怪物战斗会增加带小数、随深度变化的劳损。重访房间不会收取新房间劳损。种族、职业与存活的剧情同伴会修正该速率。

逃跑、濒死取胜、首领、死亡、悲恸、灾难与药物效果会造成单独的损失。玩家对战不会收取普通的怪物战斗精神损失。待在镇上本身不会缓慢恢复精神。

### 地牢中的精神下降有多快

劳损以千分之一点精神为单位累计：每累计满 {{balance:MentalStrainPerPoint}} 点劳损即扣除 1 点精神。进入新房间会增加楼层数乘以 {{balance:MentalRoomStrainPerFloor}} 的劳损，结束一场怪物战斗会增加楼层数乘以 {{balance:MentalFightStrainPerFloor}} 的劳损，两者再分别乘以下方你的种族与职业百分比。在第 20 层、按 100% 计算，一个房间是 80 点劳损，一场战斗是 240 点：每 12.5 个新房间，或略多于 4 场战斗，损失 1 点精神。

### 战斗结束时损失的精神

怪物战斗结束时还可能扣除整点精神：

- 你逃跑了：{{balance:MentalFleeLoss}}。
- 你在最大生命值不高于 {{balance:MentalNearDeathHpPct}}% 时结束战斗：{{balance:MentalNearDeathLoss}}。
- 对手是楼层首领或小首领：{{balance:MentalBossLoss}}。
- 对手是旧神：{{balance:MentalOldGodLoss}}，取代首领损失。
- 你死亡：{{balance:MentalDeathLoss}}。

## 按种族与职业计算的劳损

你的种族与职业各自缩放地牢劳损，以正常数值的百分比表示：

- 种族：巨魔、兽人、豺狼人与变异人 {{balance:MentalStrainRacePctHardy}}；精灵与霍比特人 {{balance:MentalStrainRacePctSensitive}}；半精灵与侏儒 {{balance:MentalStrainRacePctUneasy}}；人类与矮人 100。
- 职业：刺客、深渊守望者与虚空掠夺者 {{balance:MentalStrainClassPctDark}}；贤者 {{balance:MentalStrainClassPctSage}}；野蛮人 {{balance:MentalStrainClassPctBarbarian}}；牧师、圣骑士与潮誓者 {{balance:MentalStrainClassPctDevout}}；吟游诗人与小丑 {{balance:MentalStrainClassPctPerformer}}；其他所有职业 100。

你的速率是种族百分比乘以职业百分比，再除以 100，并四舍五入到最接近的整数百分比，遇到 .5 时向上取整。变异人贤者、兽人刺客、豺狼人刺客与变异人刺客都按 68% 计算；精灵吟游诗人按 132% 计算。随后，队伍中每位存活的剧情同伴会使劳损降低 {{balance:MentalStrainCompanionCutPct}}%，最多降低 {{balance:MentalStrainCompanionCutMaxPct}}%。这些百分比只适用于地牢劳损，不适用于上方那些单独的损失。[种族](/wiki/zh/characters/races/)列出了各种族不能选择的职业。

## 恢复

恢复需要采取行动。可选方式包括新的一天、地牢扎营、在避风港休息、旅店、家、祈祷、忏悔、与朋友交谈、学习以及治疗师。

- 在旅店睡觉恢复 {{balance:MentalInnSleepGain}} 点精神。
- 在神殿每日祈祷恢复 {{balance:MentalTemplePrayerGain}} 点精神。
- 在地牢中使用柳叶药剂恢复 {{balance:MentalWillowDraughtGain}} 点精神，直至你的上限。
- 地牢扎营与避风港共用一个楼层的休息额度。

每日一次、在你已满上限时不会生效的来源会保留下来，供之后使用。睡眠与每日重置行为在单人与在线模式下有所不同。

### 每种来源恢复多少精神

{{table:mental-recovery}}

所有恢复都会在上限处停止。旅店的桌边休息与和朋友的休息每天共用一次。

### 谈话治疗的费用

你每缺少 1 点精神，治疗师的谈话治疗就收取 {{balance:MentalTherapyCostBase}} 金币，再加上你的每级 {{balance:MentalTherapyCostPerLevel}} 金币，不含治疗师的税费。缺少的精神为 100 减去你的精神。处于「崩溃」状态的角色至少按 {{balance:MentalTherapyBrokenMinPoints}} 点收费。30 级、缺少 40 点精神时，价格为 40 乘以 70：2,800 金币。

## 恐惧与表现

较低的区间会降低伤害与防御，并可能在怪物战斗开始时引发恐惧。恐惧会消耗第一次行动；它不代表有敌人出现，也不是永久属性损失。无害的幻象文字只是氛围描写，不是额外的敌人。

### 动摇与濒临崩溃的效果

- 动摇：普通攻击造成的伤害降低 {{percent:MentalShakenCombatPenalty}}%，面对怪物攻击时的防御降低 {{percent:MentalShakenCombatPenalty}}%，并在怪物战斗开始时有 {{balance:MentalShakenFearPct}}% 的几率陷入恐惧。
- 濒临崩溃：上述两项各降低 {{percent:MentalBreakingCombatPenalty}}%，并有 {{balance:MentalBreakingFearPct}}% 的几率陷入恐惧。

稳定与紧绷没有惩罚。在单人模式下，精神与疲劳惩罚合计造成的减益绝不超过 {{percent:MentalFatigueCombatCap}}%；在线游戏没有疲劳。

### 悲恸与精神惩罚会叠加吗

不会。它们绝不会彼此相加。游戏会分别计算悲恸加疲劳、以及精神加疲劳，然后采用两者中更严重的一个。

## 心智崩溃与「崩溃」状态

精神归零时，心智崩溃会在当前活动结束后、下一场连续战斗开始前发生。在镇上或较浅的地牢楼层，你会被抬到治疗师处；更深处发生的心智崩溃则遵循死亡规则。「崩溃」状态会在精神恢复后继续存在，并阻止你前往更深的地牢。

在治疗师处使用谈话治疗可以清除「崩溃」状态并恢复精神。在可进行戒瘾康复时，戒瘾康复也能清除它。仅携带治疗药剂无法治愈「崩溃」状态。

## 成瘾与神明

成瘾会降低你的普通恢复上限。药物带来的亢奋可以暂时超过该上限，但之后会出现药劲反噬；治疗也可以把精神提升到上限之上，直到每日重置。戒瘾康复会移除成瘾及其上限。

### 成瘾会降低多少精神

你的普通精神上限为 100 减去成瘾值的一半。普通恢复会在该上限处停止；当你的精神已经达到或超过上限时，恢复不会产生任何效果。

### 药物亢奋与反噬

一种药物会带来 {{balance:MentalDrugHighGain}} 点精神的亢奋，黑暗精华与恶魔之血则为 {{balance:MentalDrugHighStrongGain}} 点。距上次使用 {{balance:MentalDrugToleranceWindowDays}} 天内每再使用一次，亢奋就减少 {{balance:MentalDrugHighStepPct}}%，最低降至完整亢奋的 {{balance:MentalDrugHighMinPct}}%。随后的反噬会扣除你所获亢奋的两倍，并且每多一次这样的重复使用，再额外扣除一半。

从虔信者等级起，你的[精神结界](/wiki/zh/gods/favor/)会减少某一类精神损失；它不会完全阻挡该损失，也不能消除所有劳损来源。

## 悲恸

当剧情同伴、NPC 队友、配偶或恋人死亡时，悲恸便会开始。若配偶在你的战斗之外死去，也会引发悲恸：单人中立即开始，在线则在下次登录时开始。悲恸会经历多个阶段，每个阶段都会改变你的战斗，直到下一阶段开始：

- 否认，3 天：普通攻击造成的伤害降低 20%。
- 愤怒，5 天：普通攻击造成的伤害提高 30%，面对怪物攻击时的防御降低 20%。
- 讨价还价，3 天：普通攻击造成的伤害降低 10%。
- 抑郁，7 天：上述两项各降低 30%。
- 接受：悲恸结束，不再有任何惩罚。

在线模式下，每个阶段持续 1 天，上述所有数值减半。单人中，多份悲恸的惩罚会相加，最多 50%；在线则只计算最严重的一份。

每一份为剧情同伴而起、并达到接受的悲恸，会使你的感知增加 5 点。为 NPC 队友、配偶或恋人而起的悲恸不会增加感知。

### 悲恸造成的精神损失

剧情同伴死亡会损失 {{balance:MentalCompanionGriefLoss}} 点精神，NPC 队友、配偶或恋人死亡会损失 {{balance:MentalNpcGriefLoss}} 点。进入抑郁阶段会再损失 {{balance:MentalGriefDepressionLoss}} 点。达到接受阶段会恢复 {{balance:MentalGriefAcceptanceGain}} 点。

:::spoiler 精确的隐藏效果与崩溃边界
深层崩溃的边界是地牢第 {{balance:MentalCollapseDeathFloor}} 层。救援会把精神设为 {{balance:MentalCollapseRescueMental}}，并拿走你随身金币的 {{balance:MentalCollapseGoldFeePct}}%。

「崩溃」状态会使造成的伤害、防御与获得的经验降低 {{balance:MentalBrokenPenaltyPct}}%。这一减益取代区间惩罚，且不受单人疲劳上限约束。各区间确切的恐惧与幻象几率见[平衡参考](/wiki/zh/reference/balance/)。
:::
