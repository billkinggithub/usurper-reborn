---
title: 队伍与公会
path: /wiki/zh/online/teams/
checked: 1.3.15
sources: Scripts/Systems/TeamSystem.cs, Scripts/Systems/GuildSystem.cs, Scripts/Locations/TeamCornerLocation.cs, Scripts/Systems/TeamHQBonus.cs, Scripts/Server/GroupSystem.cs, Scripts/Core/GameConfig.cs, Scripts/Server/MudChatSystem.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | 在线时，每位玩家在自己的每日重置时支付队伍中 NPC 的每日工资。
history: 1.3.9 | none
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | 存放在公会金库中的物品会保留其战利品效果，例如火焰、冰霜和吸血。
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | none
history: 1.3.0 | 招募低于 25 级的 NPC 费用更低，其每日工资也遵循相同的曲线；高于你等级的 NPC 每级费用增加 5%，最多增加 50%；城镇保留一个最多 18 名低等级 NPC 的招募池；招募列表会优先显示最接近你等级的 NPC；受雇的 NPC 会带有誓印。
history: 1.2.6 | 新的队伍或公会名称不能包含 < > & 或双引号；现有名称保持不变。
history: 1.2.5 | 队伍新闻现在会显示标题和事件，公会职位会以每位玩家的语言显示，但以英文保存。
history: 1.2.4 | none
---
队伍支持冒险关系和集体参与。公会是独立的在线社交系统。加入公会并不意味着每个成员都会在战斗中自动跟随你。

新的队伍或公会名称不能包含 < > & 或双引号。游戏会说明这一点，不创建任何东西，也不收取费用。现有的队伍和公会名称保持不变。

## 公会：费用、规模与经验加成

公会只存在于在线模式。创建公会需要 {{balance:GuildCreationCost}} 金币。公会最多容纳 {{balance:MaxGuildMembers}} 名成员，其金库最多存放 {{balance:MaxBankItems}} 件物品。每名成员会因公会的每一名成员获得 {{percent:GuildXPBonusPerMember}}% 的额外战斗经验，最多为 {{percent:MaxGuildXPBonus}}%：5 人或以上的公会会提供全额加成。

### 公会职位

职位为会长、官员和成员。会长和官员可以从公会金库取出金币，官员一次最多取出 {{balance:OfficerGoldWithdrawLimit}} 金币；成员不能。只有会长可以移除或提升成员。

## 队伍规模

一支队伍最多容纳 5 名成员，包括你。队伍中的玩家计入，已死亡的 NPC 成员在你移除它之前也计入，除非它永远无法回来。

## 创建队伍

在组队角创建队伍的费用为你每级 500 金币，至少 2,000 金币。

## 招募 NPC 与工资

在组队角，你可以花一笔费用和每日工资把 NPC 招募到你的队伍中，单人游戏和在线游戏皆可。费用、可招募的对象、招募池和工资见[队伍与盟友](/wiki/zh/combat/party/)。受雇的 NPC 会带着你旗帜的誓印：参见[组队](/wiki/zh/combat/groups/)。

## 复活倒下的队员

组队角可以为你队伍中倒下的 NPC 举行复活，费用为该 NPC 每级 1,000 金币。因永久死亡或年老而彻底失去的成员无法复活。

## 队伍总部

在线时，队伍可以在组队角升级其总部。每项设施最高可达 {{balance:MaxTeamFacilityLevel}} 级，下一级的费用为设施基础费用乘以下一级的平方。基础费用：军械库 5,000 金币，兵营 5,000，训练场 8,000，金库 3,000，医务室 4,000。每一级都会为队伍中的每位玩家提供：

- 军械库：造成的伤害增加 5%。
- 兵营：防御增加 5%；你受到的伤害除以 1 加上每级 5%。
- 训练场：你自己那份战斗经验增加 5%。
- 医务室：治疗药剂的治疗效果增加 10%。

## 组队之前

通过可用的菜单招募或邀请，并确认实际组队的是谁。一个在线小队最多容纳 {{balance:GroupMaxSize}} 名玩家，即队长和另外 4 人。盟友姿态以及谁接受命令见[队伍与盟友](/wiki/zh/combat/party/)。

带来互补的行动，而不只是伤害。当小队承受不同种类的压力时，治疗、护佑和承伤都很重要。

## 状态各自独立

组队玩家各自保留自己的精神、神恩、资源和每日限制。队长使用神迹不会消耗每位玩家的每日神迹，健康的队长也无法保护崩溃的追随者免于倒下。

战斗行为见[组队与支援](/wiki/zh/combat/groups/)，小队本身见[队伍与盟友](/wiki/zh/combat/party/)。
