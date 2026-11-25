---
title: 罪行、监狱与法律
path: /wiki/zh/world/law/
checked: 1.3.14
sources: Scripts/Locations/PrisonLocation.cs, Scripts/Systems/PrisonActivitySystem.cs, Scripts/Systems/StreetEncounterSystem.cs, Scripts/Locations/BaseLocation.cs, Scripts/Locations/CastleLocation.cs, Scripts/Systems/QuestSystem.cs, Scripts/Locations/QuestHallLocation.cs, Scripts/Locations/PrisonWalkLocation.cs, Scripts/Systems/DailySystemManager.cs, Scripts/Systems/WorldSimulator.cs, Scripts/Locations/MagicShopLocation.cs, Scripts/Locations/ChurchLocation.cs, Scripts/Locations/HomeLocation.cs, Scripts/Locations/InnLocation.cs, Scripts/Locations/DungeonLocation.cs, Scripts/Systems/SocialInfluenceSystem.cs, Scripts/Core/NPC.cs, Scripts/Systems/CombatEngine.cs, Scripts/Core/GameConfig.cs
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | 被谋杀的镇民会在一段时间后回来，并记得凶手；其他玩家领取的悬赏不会支付给你；缴纳保释金不再结束会话。
history: 1.3.9 | 卫兵巡逻或任何其他街头遭遇不再吞掉它出现之前输入的按键。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | 血之代价的伤害削减会应用在你的挥击上，状态画面只标明该削减，越狱每天可以尝试一次。
history: 1.3.0 | 你在荣誉决斗中击败的 NPC 会保留其 HP 并留在原地，针对它的击杀契约不会支付；城镇荣誉决斗与旅店决斗共用每天 3 场胜利的上限。
history: 1.2.7 | none
history: 1.2.5 | 监狱活动效果现在会显示每项活动的收益（例如俯卧撑的“+1 力量”），使用屏幕阅读器的囚犯会获得屏幕阅读器监狱菜单。
history: 1.2.4 | 谋杀宿怨战中的暴怒复仇者确实拥有信息框显示的额外 HP，镇民自身的 HP 不再被提高。
history: 1.2.3 | none
---
犯罪在城镇中会有后果。盗窃和谋杀可能成为你神祇的禁忌，黑暗高于 100 会使你成为通缉犯。[城堡](/wiki/zh/world/castle/)的统治者控制着监狱。

## 黑暗到多少卫兵会逮捕我

当你的黑暗高于 100 时，你会被通缉。卫兵巡逻可能在主街和城堡附近拦下被通缉的角色；王冠阵营成员会被放行。巡逻提供：

- **投降（S）：** 在监狱待 1 天，并处以为自己手头金币的四分之一加 50 的罚金。
- **战斗（F）对抗卫兵队长，** 一名你等级 + 3 的战士：获胜会让你带着额外 30 黑暗获释；失败但活下来会让你获得 3 天刑期和额外 30 黑暗。
- **贿赂（B）：** 100 金币，如果你带得够，你就可以离开。
- **逃跑（R）：** 逃跑成功率为 40% 加上你的敏捷值；如果被抓，2 天刑期。

一次严重失败的扒窃尝试，或暗巷中的便衣卫兵，也可能把你送进监狱。统治者可以在每日限额内监禁角色。

## 如果我在城镇里谋杀别人会怎样

被谋杀的镇民会像任何死亡的 NPC 一样在一段时间后回来，并记得是谁杀了他们。在城镇中发生非悬赏击杀的谋杀后，5 名等级为你等级 + 5 的皇家卫兵会来抓你。你可以投降或战斗。赢得战斗会让你带着额外 100 黑暗获释。失败或投降会抛硬币：一面是你被处决，另一面是你入狱。处决会杀死角色；在单人游戏中，会进入正常的死亡与复活选择。谋杀罪入狱会夺走你手头一半的金币，持续 2 天，期间不能越狱、不能保释，也不能要求释放。

对街头袭击者的自卫不算谋杀。荣誉决斗也不算：你击败的 NPC 会保留战斗前的 HP 并留在原地。城镇中的荣誉决斗与旅店决斗共用每天 3 场胜利的上限。

## 血之代价（谋杀权重）

永久杀死一名镇民会增加你的血之代价，这是一种随角色携带的权重：

- 街头发生且背后没有悬赏的谋杀：{{balance:MurderWeightPerDeliberateMurder}}；
- 黑暗魔法击杀：{{balance:MurderWeightPerDarkMagicKill}}；
- 暗影契约击杀：{{balance:MurderWeightPerShadowContract}}，并且有 {{percent:ShadowContractBloodPriceSkipChance}}% 的概率完全不增加；
- 王冠或悬赏板击杀：不增加。

城镇喜欢的受害者（平均印象高于 0.3）会额外增加 {{balance:MurderWeightLikedNPCBonus}}。每次增加权重的击杀还会按每点权重增加 10 黑暗，且你身边的每名同伴会失去 {{balance:CompanionLossPerMurder}} 点忠诚。

### 血之代价有什么作用

- 权重达到 8 或以上时，你的普通挥击伤害降低 10%；达到 15 或以上时降低 20%。
- 在家中、旅店和地牢营地休息时，权重达到 3 或以上只能恢复 75%，达到 6 或以上只能恢复一半。
- 只要你带有任何权重，关于你的流言就更容易传播。
- 进一步的影响属于剧情；见其[结局剧透](/wiki/zh/world/story/#结局-如何达成各个结局)。

从权重 5 起，状态画面会标明你的血之代价等级；从 8 起会标明其伤害削减。没有商店或治疗师会因血之代价多收费。

### 我如何移除血之代价

每过一个完整的现实日，它会在每日重置时下降 {{balance:MurderWeightDecayPerRealDay}}。在教会，带着权重告解会提供血之赦免：花费 {{balance:BloodConfessionBaseCost}} + {{balance:BloodConfessionCostPerWeight}} 金币每点权重，最多移除 {{balance:MurderWeightConfessionReduction}}。6.0 的权重花费 1,700 金币，并留下 3.5。

## 监狱生活

只要你还有剩余刑期，每次出行都会在监狱结束。其菜单提供：

- **W** 列出囚犯，**S** 查看你的状态；
- **A** 活动；
- **E** 越狱；
- **B** 缴纳保释金；
- **P** 向统治者请愿保释或赦免；
- **D** 要求释放，以及 **O** 从打开的牢门走出去。

在牢房里只能使用聊天命令。被监禁的角色不会遵循正常的精神崩溃路径。

## 监狱活动给予什么

你每天可以做 3 项活动。除影子拳击外，每项活动都会永久提升 1 点属性：

- **俯卧撑：** 力量。
- **瑜伽：** 敏捷，并且有一半概率同时提升灵巧。
- **阅读：** 智力，并恢复 5 点法力。
- **冥想：** 感知，并恢复最大 HP 的十分之一。
- **拉伸：** 体力，并恢复最大 HP 的二十分之一。
- **规划：** 魅力。
- **影子拳击：** 恢复 10 点战斗体力，最多到你的上限。
- **祈祷：** 当你的侠义高于黑暗时，给予 10 到 20 侠义，否则给予 10 到 20 黑暗。

## 出狱

- **服完刑期。** 刑期结束时，你会回到主街，HP 至少提升到最大 HP 的一半，并移除最多 75 黑暗。
- **越狱：概率。** 一次尝试的成功率为 40% + 敏捷 / 3 + 等级 / 2，保持在 30% 到 80% 之间：20 级、敏捷 30 时为 60%。成功会让你以满 HP 获释，黑暗保持不变。失败会增加一天刑期并登上新闻。你在每次每日重置时恢复 1 次尝试，最多 {{balance:MaxPrisonEscapeAttempts}} 次；谋杀犯不会恢复任何次数。
- **保释。** 支付统治者设定的保释金。向 NPC 统治者请愿保释会将其设为 1,000 + 500 x 你的等级 金币。这笔钱会进入王室国库。
- **宽赦。** 向 NPC 统治者请求宽赦会以 10% + 侠义 / 50 的概率释放你，保持在 5% 到 40% 之间（侠义 600 时为 22%），你可以立刻再次请求。人类统治者会以消息形式收到你的请求。
- **敞开的门。** 当你的牢门打开时，O 可以让你走出去；游戏中的任何行动都不会打开另一名玩家的牢门。

## 悬赏

统治者会对罪犯发布悬赏，市民可以在王室觐见时举报罪行。未偿还的王室贷款可能使你被悬赏。在任务大厅阅读悬赏板。击败悬赏目标会支付奖励，除非另一名玩家已领取该悬赏；但荣誉决斗中的胜利不会支付针对该 NPC 的击杀契约；针对玩家的悬赏会支付给在决斗或[竞技场](/wiki/zh/online/arena/)中击败他的人。非常令人畏惧的角色也可能在街上遇到赏金猎人。

朱迪卡奖赏恰当的监禁与处决命令，并将盗窃视为禁忌。行为和禁忌见[神祇页面](/wiki/zh/gods/)。
