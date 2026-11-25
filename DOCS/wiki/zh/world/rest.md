---
title: 家、旅店与休息
path: /wiki/zh/world/rest/
checked: 1.3.15
sources: Scripts/Locations/HomeLocation.cs, Scripts/Locations/InnLocation.cs, Scripts/Systems/MentalSystem.cs, Scripts/Core/GameConfig.cs
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
history: 1.3.0 | 在旅店，赛斯·阿贝尔以其挑战界面显示的等级战斗，获胜只支付旅店的固定奖励；旅店决斗与城镇荣誉决斗共享每天 3 场胜利的上限；被宽恕的同伴会在那里等候。
history: 1.2.6 | none
history: 1.2.5 | 在线睡眠后，NPC 的攻击现在会出现在醒来报告中，NPC 攻击者会与你幸存的受雇旅店守卫战斗。
history: 1.2.4 | none
---
旅店和家提供不同的休息与社交行动。恢复 HP、恢复精神和开始新的一天是三种不同的效果。

## 旅店

在桌边休息会恢复精神，若有关系亲近的 NPC 朋友在场，效果更好。单人游戏中睡觉，或在线租一间房，都会提供另一种恢复来源。付费选项会在精神已满、恢复不会产生效果时警告你。O 点餐：六道菜各有自己的基础价格，为 15 到 50 金币，再加上每级 2 金币，并加上国王税和城市税；你每天可以吃 3 餐，且同时只能有一种餐食效果生效。

## 旅店的属性训练

旅店的训练大师（W）出售基础属性的 +1：力量、敏捷、体质、智力、感知、魅力、灵巧或体力，每项属性最多训练 {{balance:MaxStatTrainingsPerStat}} 次。价格为等级 x {{balance:StatTrainingBaseCostPerLevel}} x（该属性已训练次数 + 1）的平方，用随身金币支付，不收税。20 级时，同一项属性的五次训练分别花费 10,000、40,000、90,000、160,000 和 250,000 金币。

第 4 次训练一项属性还需要 1 颗海洋之心，第 5 次需要 1 颗海洋之心和 1 颗曼威之眼。见[制作材料](/wiki/zh/items/materials/)。

## 旅店房间费用

在线时，旅店房间（N）花费等级 x {{balance:InnRoomCostPerLevel}} 金币，20 级时为 1,500，先用随身金币支付，再用银行账户支付。它会保存游戏并让你登出。

有了房间，你最多可以雇佣 {{balance:MaxSleepGuards}} 名守卫，与任何在你睡觉时攻击你的人战斗。基础价格和 HP：新手 100 和 80，猎犬 150 和 60，老兵 300 和 150，巨魔 500 和 200，精英 600 和 250，龙兽 1,000 和 300。两者都会乘以（1 + 等级 / 10），并且每名已雇佣的守卫会使下一名的价格增加 50%。在旅店睡觉的人还会以额外 50% 的力量和防御战斗。

## 睡觉时遭到攻击

在线时，在旅店击败熟睡者的玩家（K）会拿走熟睡者随身金币的 {{percent:SleeperGoldTheftPercent}}%，熟睡者则损失 {{balance:SleeperXPLossPercent}}% 的经验。

## 旅店游戏

- **拼酒（G）：** 每局 20 金币，每天 {{balance:MaxDrinkingGamesPerDay}} 局。
- **高低骰子：** 猜中支付底池的 1.2 倍，平局退还底池，你最多可以让底池连续滚存 {{balance:GamblingMaxDoubleDown}} 次胜利。只有你的赌注会离开钱袋。
- **骷髅骨牌：** 一种骨牌游戏，目标为 21 点，对手是抽到 17 点为止的庄家。获胜支付 {{balance:BlackjackPayoutMultiplier}} 倍，即退还赌注并再赢同样多；前两张牌组成 21 点支付 {{balance:BlackjackBonusPayout}} 倍；平局不损失。
- **掰手腕：** 每天 {{balance:MaxArmWrestlesPerDay}} 场，赌注为对手等级 x {{balance:ArmWrestleBetPerLevel}} 金币。

L 打开旅店的赌博游戏。暗巷有自己的赌坊；见[暗巷](/wiki/zh/world/dark-alley/)。

## 旅店里的战斗

赛斯·阿贝尔以其挑战界面显示的等级战斗。获胜只支付旅店的固定奖励，除此之外没有别的：没有单独的战斗奖励，也没有战利品掉落判定。在旅店与 NPC 的决斗与城镇中的荣誉决斗共享每天 3 场胜利的上限。离开你并在[神殿](/wiki/zh/world/temple/)获得宽恕的同伴会在旅店等候。

## 家

在家休息、睡觉以及与配偶或恋人共度时光可以恢复精神。有些恢复每天只能进行一次。单人游戏中睡觉还会开始新的一天；在线时则遵循共享世界的每日行为。在家休息会恢复一定比例的最大 HP 和法力，比例随你的居所提升；具体数字见[家与家人](/wiki/zh/world/home/)。

## 每日恢复

每日重置会给予精神恢复，但站在城里发呆并不是恢复行动。每天一次、在你已满时没有产生效果的恢复，仍会保留到之后使用。

如果你处于崩溃状态，单靠睡觉并不是解药。前往[治疗师](/wiki/zh/characters/afflictions/)接受谈话治疗或适用的戒瘾康复。
