---
title: 药剂、草药与补给
path: /wiki/zh/items/consumables/
checked: 1.3.14
sources: Scripts/Locations/HealerLocation.cs, Scripts/Systems/CombatEngine.cs, Scripts/Systems/PotionBonus.cs, Scripts/Core/GameConfig.cs, Scripts/Core/Character.cs, Scripts/Locations/HomeLocation.cs, Scripts/Locations/MagicShopLocation.cs, Scripts/Locations/BaseLocation.cs, Scripts/Systems/CityControlSystem.cs, Scripts/Systems/MentalSystem.cs, Scripts/Systems/DifficultySystem.cs, Scripts/Systems/MaintenanceSystem.cs, Scripts/Locations/DungeonLocation.cs, Scripts/Systems/OldGodBossSystem.cs
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | 信仰会成员在治疗师处购买药剂、解毒剂和柳叶药剂可少付 15% 到 35%，地牢商人的治疗药剂在任何楼层都按你等级的城镇价格减 15 出售。
history: 1.3.10 | 战斗中饮用的治疗药剂在满生命值时会被拒绝，在缺少不到 10% 最大生命值时则会先询问；地牢前哨或街头商人以城镇价格的 1.25 倍出售药剂，对于你无法携带的药剂不会收取金币。
history: 1.3.9 | none
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | U 消耗一瓶治疗药剂来救助倒下的盟友，在旧神战中，救助会启动药剂冷却。
history: 1.3.2 | 难度的治疗倍率适用于你或你的队伍饮用的每一瓶治疗药剂，秘术萨满会像其他法力职业一样自动饮用同法药剂。
history: 1.3.0 | 治疗药剂至少恢复饮用者最大生命值的 20%，给予盟友的药剂至少恢复该盟友最大生命值的 20%。
history: 1.2.7 | none
history: 1.2.6 | none
history: 1.2.5 | 治疗师菜单以及药剂与草药标签以全部五种语言显示。
history: 1.2.4 | none
---
消耗品解决特定问题。治疗补给恢复生命值，法力补给恢复施法资源，解毒剂治疗中毒，柳叶药剂在地牢中恢复精神健康，草药提供短暂的增益。它们彼此不能替代。

## 使用正确的补给

查看战斗和房间菜单中可用的消耗品操作。草药和药剂可能与治疗加成相互作用；最终数值并不总是物品标签上的原始数值。

## 治疗药剂恢复多少

治疗药剂恢复 30 + 5 × 你的等级 + 10 到 29 的随机值，或当后者更高时恢复饮用者最大生命值的 {{percent:ScaledPotionMaxHPFraction}}%。在 10 级、最大生命值 800 时，固定部分为 90 到 109，20% 为 160，因此药剂恢复 160。它恢复的生命值绝不会超过你缺失的生命值。给予盟友的药剂用该盟友的最大生命值计算 20%。在地牢中战斗之外，随机部分为 10 到 30。

### 药剂精通（炼金术士）

炼金术士的治疗药剂多恢复 {{percent:AlchemistPotionMasteryBonus}}%，炼金术士将药剂给予盟友时也是如此。法力药剂不获得该加成。

## 战斗中的药剂

战斗中，I 饮用治疗药剂：一次操作内喝下填满生命值所需的瓶数，每瓶恢复相同的随机数值。当两种药剂都有、生命值和法力值都缺失时，I 会询问要哪一种。法力药剂恢复 30 + 5 × 你的等级点法力，每次操作一瓶。饮用是本回合你的行动。满生命值时治疗药剂会被拒绝，且不消耗你的行动；当你缺失不到 10% 最大生命值时，游戏会先询问，选择否则不消耗任何东西。H 用药剂或法术治疗盟友，U 消耗一瓶药剂扶起[倒下的盟友](/wiki/zh/combat/party/)。

### 旧神战中的药剂冷却

在旧神战中，饮用治疗或法力药剂、或用药剂救助倒下的盟友之后，你在 {{balance:bossPotionCooldownRounds}} 回合内不能再次饮用；尝试会消耗你的行动，且冷却结束前不会提供救助选项。普通战斗和楼层首领没有药剂冷却，草药在任何地方都没有冷却。

### 难度与药剂

在简单难度下，你或你的队伍饮用的每瓶治疗药剂多恢复 25%，在噩梦难度下少恢复 25%，无论战斗内外。该倍率在药剂精通和医务室之前计算，菜单显示的治疗量和回满生命值所需瓶数都已包含它。在与其他玩家的对战中，对手的药剂不受影响。

### 自动战斗与自动治疗

自动战斗会在你的生命值等于或低于阈值时饮用一瓶治疗药剂：默认 {{balance:AutoCombatHealPercentDefault}}%，可在 {{balance:AutoCombatHealPercentMin}} 到 {{balance:AutoCombatHealPercentMax}} 之间以 10 为步长设置。

开启自动治疗后，战斗结束后你会饮用治疗药剂，直到你缺失的生命值少于半瓶平均药剂。平均药剂为 50 + 5 × 你的等级，或当后者更高时为最大生命值的 20%，再乘以上述难度倍率（有药剂精通时再多 50%）。有法力的职业对法力药剂也如此处理，按 30 + 5 × 等级计算。

柳叶药剂会在你正常的精神健康上限处停止，若没有需要恢复的部分则会被保留。成瘾与崩溃需要各自的治疗决定。

## 治疗药剂价格与携带数量

一瓶治疗药剂在税前花费 {{balance:HealingPotionBaseCost}} + 等级平方 / 2 金币：20 级时为 300，50 级时为 1,350，100 级时为 5,100。你可携带 20 +（等级 - 1）瓶治疗药剂：20 级时为 39 瓶。这也是治疗师和魔法商店允许你购买的上限。每日维护时，若你携带的治疗药剂比 20 多出 2 瓶或更多，超出 20 的部分会有一半腐坏。治疗师（B）和魔法商店（H）都出售它们；魔法商店会在相同基础价格上应用自己的价格修正。

## 法力药剂

一瓶法力药剂恢复 30 + 等级 × 5 点法力，税前花费 {{balance:ManaPotionBaseCost}} + 等级平方 / 2 金币：20 级时为 350 金币恢复 130 点法力。你可携带 20 +（等级 - 1）瓶。任何职业都可以购买，用以交给队友。治疗师（M）和魔法商店（M）都出售它们。

## 解毒剂

解毒剂在治疗师处（N）税前花费 75 金币，可治疗中毒。你可携带 5 + 等级 / 10 瓶，向下取整：20 级时为 7 瓶，100 级时为 15 瓶。

## 柳叶药剂

一瓶柳叶药剂的价钱等于你等级下 {{balance:MentalWillowPotionMultiplier}} 瓶治疗药剂，另加税：20 级时税前 600 金币。它在地牢中恢复 {{balance:MentalWillowDraughtGain}} 点精神健康，你可携带 {{balance:MaxWillowDraughts}} 瓶。在[治疗师](/wiki/zh/world/healer/)处购买（W）。

## 草药

草药生长在[家](/wiki/zh/world/home/)的草药园中。草药园每升一级会解锁下一种草药，并每天多采一种，5 级时每天最多 5 种。可在任何地方用 `/herb`（或 `/j`）使用草药，在家按 J，或在战斗中使用。

{{table:herbs}}

同一时间只能有一种草药增益生效；新的草药增益会替换旧的。增益按战斗场次递减。炼金术士的治疗草药多恢复 {{percent:AlchemistPotionMasteryBonus}}%（最大生命值的 37.5%），炼金术士的草药增益持续时间延长一半：7 场战斗取代 {{balance:HerbBuffDuration}}，4 场取代 {{balance:HerbSwiftDuration}}。

## 保留储备

带上足够的补给，以便安全返回，而不仅仅是为了赢下一场战斗。露营或城镇治疗可以节省消耗品，但两者并非在所有情况下都可用。
