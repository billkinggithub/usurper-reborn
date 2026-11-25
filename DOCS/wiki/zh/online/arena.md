---
title: 竞技场
path: /wiki/zh/online/arena/
checked: 1.3.15
sources: Scripts/Locations/ArenaLocation.cs, Scripts/Locations/MainStreetDistricts.cs, Scripts/Core/GameConfig.cs, Scripts/Systems/CombatEngine.cs, Scripts/Locations/MainStreetClassic.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | 竞技场菜单的每一行在每种语言下都能容纳在 79 列以内。
history: 1.3.10 | none
history: 1.3.9 | 主街默认以经典布局打开，分区布局可在设置中选择。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | 武器附魔和吸血现在在竞技场战斗中生效，魔法抗性会在那里将法术伤害最多削减一半。
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | none
history: 1.3.1 | none
history: 1.3.0 | 在竞技场战斗中，双持者的挥击使用各自手中的武器；此前，每次挥击都会把两把武器的威力相加。
history: 1.2.7 | none
history: 1.2.6 | none
history: 1.2.5 | 竞技场获胜后，所有语言的玩家现在都能从目标已穿戴的武器和护甲中回收金币；此前英文玩家从来不会。
history: 1.2.4 | 你的竞技场攻击后防御者收到的通知现在会送到其邮箱。
history: 1.2.3 | none
---
竞技场是在线游戏的玩家对玩家场地。它只存在于在线游玩中。

## 竞技场在哪里

从主街按 6 前往竞技场；它位于经典菜单的在线一行。使用分区布局时，用 O 打开在线分区，然后按 A。竞技场不会出现在单人游戏中。锚点大道试炼场是另一种以怪物为基础的挑战。

## 战斗如何进行

竞技场战斗是异步的。你与另一名玩家已保存角色的 AI 控制副本战斗，该副本以满 HP 开始。战斗结束后，你自己受到的伤害仍然保留，所以请先治疗。

按 A 攻击。目标列表会排除：

- 此刻在线的玩家；
- 你自己和你自己的小号；
- 你今天已经攻击过的任何人；
- 今天输掉过 PvP 战斗且此后尚未登录的玩家；
- 在家睡觉或在暗影安全屋休息的玩家。

## 竞技场需要什么等级

你需要达到 {{balance:MinPvPLevel}} 级才能战斗，每天可以攻击 {{balance:MaxPvPAttacksPerDay}} 次，目标必须在你的等级 {{balance:PvPLevelRangeLimit}} 级以内。

## 胜利与失败

### 我在竞技场能赢得多少金币

一次胜利会取走目标携带金币的 {{percent:PvPGoldStealPercent}}%，单场战斗中最多为 {{balance:PvPGoldPerFightCapPerLevel}} 金币乘以你的等级；小号最多可取 {{balance:PvPAltGoldStealBase}} + {{balance:PvPAltGoldStealPerLevel}} 乘以其等级。20 级的主角色最多可取 100,000 金币，20 级的小号最多可取 3,000。胜利还可以从目标已穿戴的武器（30% 几率）和护甲（25% 几率）中按其价值的一半回收金币，回收所得计入同一上限。胜利还会按目标等级的 10 到 29 倍支付奖励金币，领取目标身上的任何悬赏，并增加 10 点声望。如果目标在战斗期间登录，从目标处取走的金币会作废；胜利、经验和悬赏仍然有效。

### 一次 PvP 胜利能获得多少经验

一次胜利支付 50 乘以目标等级再乘以（1 + 0.15 乘以目标等级与你的等级之差）的经验，等级因子保持在 0.25 到 2 之间，且至少为 10。20 级击败 24 级目标：1,200 x 1.6 = 1,920 经验。队伍的 Training（训练场）总部会在此基础上增加。

### 如果我在竞技场输了会失去什么

一次失败会损失 10% 的经验、25% 的金币和 5 点声望，你会在旅店以最大 HP 的一半复活。防御者还会取走你剩余金币的 {{percent:PvPGoldStealPercent}}%，上限同样按其等级计算。

## 记录

- L 显示胜利、失败和掠取金币的排行榜。
- H 显示最近的战斗。
- S 显示你自己的战绩。

PvP 胜利会计入成就。

竞技场战斗遵循[玩家战斗规则](/wiki/zh/combat/pvp/)：普通的精神损耗和每日神迹不适用。对于你和你所战斗的副本，双持者的挥击都使用各自手中的武器。
