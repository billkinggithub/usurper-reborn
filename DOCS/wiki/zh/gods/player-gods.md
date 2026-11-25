---
title: 不朽者、玩家神明与万神殿
path: /wiki/zh/gods/player-gods/
checked: 1.3.14
sources: Scripts/Systems/EndingsSystem.cs, Scripts/Locations/PantheonLocation.cs, Scripts/Locations/TempleLocation.cs, Scripts/Systems/GodBoonSystem.cs, Scripts/Systems/GodDomainPicker.cs, Scripts/Systems/DivineBoonRegistry.cs, Scripts/Systems/ImmortalDeedSystem.cs, Scripts/Systems/DailySystemManager.cs, Scripts/Systems/WeeklyGodSystem.cs, Scripts/Systems/FaithSystem.cs, Scripts/Systems/CombatEngine.cs, Scripts/Systems/LocationManager.cs, Scripts/Locations/BaseLocation.cs, Scripts/Core/GameEngine.cs, Scripts/Server/MudChatSystem.cs, Scripts/Systems/TeamSystem.cs, Scripts/Systems/GuildSystem.cs, Scripts/Systems/SqlSaveBackend.cs, Scripts/Core/GameConfig.cs, DOCS/release-notes/RELEASE_NOTES_1.2.0.md
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
history: 1.3.1 | none
history: 1.3.0 | none
history: 1.2.7 | none
history: 1.2.6 | 新的神名不能包含 < > & 或双引号；此前已选定的神名予以保留。
history: 1.2.5 | 万神殿界面以全部五种语言显示，神谕、祝福与弃神通知会以每位玩家自己的语言送达。
history: 1.2.4 | 放弃神位会释放玩家追随者，并通知他们；小号在放弃王位、队伍或公会之前就会被拒绝飞升；放弃神位后小号栏位仍然保留；状态界面会显示游戏支付的信徒经验。
---
不朽者是完成了主线故事，并选择飞升而非开始新一生的玩家。该角色会成为一位玩家神明：这位神明生活在万神殿中，聚集信徒，施行神迹，并向信奉这位神明的玩家赐予领域恩赐。凡人在神殿祭坛列表上与十位神殿神明一同找到玩家神明。

## 如何成为不朽者

不朽只在主线故事结束时提供一次。在最终遭遇、结局与制作人员名单之后，游戏会依次提供两个选择：

1. **飞升成神。** 对「要飞升成神吗？」回答 Y。
2. **开始永恒的轮回。** 这就是[新游戏+](/wiki/zh/characters/new-game-plus/)：在下一个轮回中创建新角色。

你必须选择其中之一。若两个都拒绝，游戏会再次询问；已完成故事的角色无法回到普通的凡人游戏。若你在做出选择前断线，下次登录时会再次提供该选择。

飞升时：

- 你选择一个 3 到 30 个字符的神名，不能包含 < > & 或双引号。从此以后，其他玩家看到的就是这个名字。
- 你作为神明的阵营取决于你达成的结局：光明、黑暗或平衡。
- 你选择一个领域，即神殿十位神明的恩赐领域之一。按回车可稍后再定；在你做出选择之前，万神殿每次造访都会再次询问。领域一旦选定便永久不变。
- 若你是君主，你会退位。你会离开你的队伍与公会。
- 账号的小号角色栏位会开放，并永久保持开放。
- 该结局计为已完成，你的轮回次数会增加，与新游戏+相同。这样可为日后的新生保留进阶职业与轮回加成。
- 你会直接前往万神殿。

在线模式下，只有你的主角色可以飞升。小号角色在回答 Y 之后、选择名字之前就会被拒绝，因此能保留自己的王位、队伍与公会。一旦你的主角色完成飞升，你的账号就可以创建小号角色，放弃神位之后同样可以。

## 不朽者会有哪些变化

不朽者永远不会回到凡间。每次登录都从万神殿开始，任何通往其他地点的路径都会把你带回那里。神明本身没有城镇、地牢、商店、旅店、队伍、公会或战斗。在万神殿按 Q 可退出游戏。

在线模式下，其他玩家看到的是神明的神名及其后的神格，例如「低阶神灵」。在 /who 中，玩家神明所在的那一行会标上一颗星（屏幕阅读器模式下为「(Immortal)」），其等级栏显示神格而非职业，众神列在管理员之后、凡人之前，摘要行会统计在线的不朽者人数。

### 神格

一位神明有 {{balance:GodMaxLevel}} 级神格，从低阶神灵直至神明。每位新的不朽者都从 1 级的低阶神灵开始。每一级所需的神性经验、每日给予的神迹次数以及神恩预算如下：

{{table:god-ranks}}

当你拥有足够经验并拜访曼威（V）时，神格会提升，每次拜访提升一级，且该次拜访还会把你的神迹次数补满至新等级的每日数量。每日重置也会把神格提升到你的经验所达到的最高等级。在最高等级，曼威已无可再教。

### 神明如何获得神性经验

- **信徒：** 每次每日重置时，每位信徒都会增加你的神格 × {{balance:GodBelieverExpPerLevel}} 点经验。3 级神格拥有 12 位信徒时，每天获得 72 点。
- **神迹：** 每项神迹都会显示它带来的收益（见下文）。
- **玩家追随者的战斗：** 在线模式下，每位玩家追随者获得的战斗经验中有 {{percent:GodBelieverKillXPPercent}}% 归你，至少为 1，并在他们那里显示为向你献祭。
- **你祭坛上的金币与祈祷：** 在线模式下，凡人在你神殿祭坛献祭的金币会按数额增加 1 到 6 点经验：1 点至多 20 枚金币，2 点至多 2,000 枚，3 点至多 45,000 枚，4 点至多 150,000 枚，5 点至多 900,000 枚，6 点则为高于 900,000 枚的数额。追随者的每日祈祷增加 10 点。

## 万神殿

万神殿菜单：

- **S，状态。** 神名、凡人名、阵营、领域及其恩赐比例、神格、升到下一级所需经验、信徒、今日剩余神迹、飞升日期、已配置的恩赐。
- **B，信徒。** 你的追随者，包括 NPC 与玩家，附等级与职业。
- **D，神迹。** 神迹菜单，见下文。
- **F，神恩。** 配置你的追随者获得的额外恩赐。
- **I，不朽者。** 所有玩家神明，按神性经验排名。
- **N，消息。** 今日的凡人消息与神界消息。
- **C，留言。** 向消息发一条信息；不消耗神迹。
- **V，拜访曼威。** 经验足够时提升一级神格。
- **H，飞升者之厅。** 内测元老的雕像。
- **R，放弃。** 舍弃不朽，开始新的一生。
- **Q，退出。** 离开游戏。

### 威望与排名

一位神明的威望是其所有追随者恩宠的总和，再加上每位活着的 NPC 追随者 {{balance:GodNpcFollowerStanding}} 点。每次亵渎该神明的祭坛都会使其降低 {{balance:GodDesecrationStandingPenalty}} 点，直到下一次每周重置，即每 {{balance:GodStandingWeekDays}} 天一次；威望永远不会低于 0。神殿神明与玩家神明共享神殿的排名与祭坛。不朽者界面（I）只对玩家神明按神性经验排名，并显示神格、信徒以及每位神明是否在线。

在每次每周重置时，威望最高的神明会成为本周之神，其追随者在下次每周重置前获得 {{balance:GodWeeklyXpBonusPct}}% 更多的战斗经验。玩家神明也能像任何神殿神明一样占据这个位置。

这些数值会随实时世界而变化。本 wiki 不会导出玩家名字、追随者列表或威望。

### 神迹

每项神迹消耗当天的一次神迹次数，次数会在每日重置时恢复。

- **招募信徒。** 尝试感化一位凡人。异教徒，或只是松散敬奉自己神明的 NPC，有 {{percent:GodRecruitPaganChance}}% 的几率被感化，给予 {{balance:GodRecruitPaganExp}} 点经验；信奉另一位神明的信徒有 25% 的几率被感化，给予 {{balance:GodRecruitStealExp}} 点经验。玩家更难感化，但回报更高：几率提高到 {{balance:GodRecruitPlayerMultiplier}} 倍（24.75% 与 18.75%），经验提高到 {{balance:GodRecruitPlayerExpMultiplier}} 倍（300 与 100）。尝试失败仍会消耗神迹。
- **祝福信徒。** 你的一位追随者获得持续 {{balance:GodBlessCombatDuration}} 场战斗的战斗祝福：信徒的攻击与防御提高 {{percent:GodBlessBonusFollower}}%，虔信者提高 {{percent:GodBlessBonusDevout}}%，狂热者或神选者提高 {{percent:GodBlessBonusZealot}}%，NPC 提高 {{percent:GodBlessBonusNpc}}%。若仍有更强的祝福生效，则保留其加成。玩家追随者还会获得 {{balance:GodBlessFavorGain}} 点[恩宠](/wiki/zh/gods/favor/)，每天最多 {{balance:GodBlessFavorDailyCap}} 点。该祝福给予你 {{balance:GodBlessExp}} 点经验，若对象是玩家则为 {{balance:GodBlessPlayerExpMultiplier}} 倍（30 点）。
- **神罚凡人。** 以随机 {{percent:GodSmiteMinPercent}} 到 {{percent:GodSmiteMaxPercent}}% 的最大生命值打击一名不追随你的凡人，给予 {{balance:GodSmiteExp}} 点经验，若对象是玩家则为 {{balance:GodSmitePlayerExpMultiplier}} 倍（50 点）。神罚绝不致死：目标至少保留 1 点生命。你不能神罚自己的追随者，同一名玩家只能在 {{balance:GodSmitePlayerCooldownMinutes}} 分钟后再次被神罚。
- **离间关系。** 恶化两位 NPC 之间的关系。它成功的几率为 {{percent:GodPoisonRelationshipChance}}%，给予 {{balance:GodPoisonRelationshipExp}} 点经验。
- **释放囚徒。** 释放一名被囚禁的 NPC，给予 {{balance:GodFreePrisonerExp}} 点经验。
- **神谕。** 向消息发送一条信息，在线模式下还会发给游戏中的每位玩家。与留言不同，它消耗一次神迹，并给予 {{balance:GodProclamationExp}} 点经验。
- **惩戒信徒。** 从你的一位玩家追随者身上收回 {{balance:GodChastiseFavorLoss}} 点恩宠，每位追随者每天一次。它不给予经验。

对一位已经离开你的玩家追随者施行神迹会被拒绝，且不消耗任何次数。祝福或惩戒也能触及不在线的玩家：它会改变对方的存档，消息会以邮件送达。若当时无法访问对方的存档，该神迹会被拒绝，且不消耗任何次数。

### 领域恩赐

你的追随者会获得你所在领域的恩赐与精神结界，机制与该领域的神殿神明相同：见[恩赐](/wiki/zh/gods/boons/)。你的恩宠阶位照常适用，只有虔信者及以上的追随者才能获得结界。

恩赐的强度是同一阶位神殿神明恩赐的一个比例：以你从玩家处获得的威望，占最强神殿神明威望的百分比，并限制在 {{balance:GodPlayerBoonFloorPct}}% 到 {{balance:GodPlayerBoonCapPct}}% 之间。威望为最强神殿神明一半的玩家神明，赐予 50% 的强度；威望超过所有神殿神明的玩家神明，最多赐予 120%。当没有任何神殿神明拥有玩家追随者时，有威望的神明为 120%，没有威望的为 50%。状态界面（S）会显示当前比例。

恩赐会随不活跃而衰减。在 {{balance:GodPlayerInactiveDays}} 天未登录之后，每多离开一天，比例就下降 {{balance:GodPlayerInactiveDecayPctPerDay}} 点，但绝不会低于 {{balance:GodPlayerBoonFloorPct}}%。再次登录后它会恢复。

### 神恩

神恩（F）会在领域恩赐之上增加额外恩赐。共有 13 项神恩，分为三组，每组 3 个层级；每一层级各自消耗对应的点数，因此第三层级消耗的点数是第一层级的三倍。有些神恩只对光明、黑暗或平衡阵营的神明开放。你的预算是每级神格 {{balance:GodBoonBudgetPerLevel}} 点，外加最多 {{balance:GodBoonConcentrationMax}} 点的集中加成，每有一位信徒就减少 {{balance:GodBoonConcentrationPerBeliever}} 点，因此小群信徒能得到更强的赠礼。一位 3 级神格、4 位信徒的神明拥有 30 + 12 = 42 点。输入数字以添加或升级恩赐，输入 R 及其编号以移除一项，输入 0 或按回车完成。在线模式下，正在游戏的追随者会立刻看到变化。

{{table:divine-boons}}

在你的祭坛祈祷时，会把一位追随者的伤害与防御神恩中较大的一项翻倍，作为持续 {{balance:GodPrayerBlessingCombats}} 场战斗的祝福；见[每日祈祷祝福](/wiki/zh/gods/favor/#每日祈祷祝福)。

## 在线与单人

飞升在两种模式下运作方式相同。区别在于谁能追随你：

- 单人模式下，你的信徒是 NPC。不朽者界面只列出你自己，以玩家为目标的神迹不可用，也没有玩家会获得你的领域恩赐或神恩。
- 在线模式下，玩家可以在神殿信奉你，获得你的领域恩赐与神恩，并把一部分战斗经验献给你。其他不朽者会出现在排名中，你的飞升会向所有在线者公告。

## 放弃不朽

在万神殿按 R 可永久放弃神位。你需要确认两次：输入 YES，然后准确输入你的神名。

失去的内容：

- 神名、神格、经验与神迹；
- 你的信徒，包括 NPC 与玩家，他们将被留在没有神明的状态。正在游戏中的玩家追随者会立刻收到通知；不在线的则通过邮件通知；
- 角色本身：其存档会被一个全新的角色取代，与新游戏+相同。

保留的内容：

- 你的轮回次数与已完成的结局，因此新生会带着[新游戏+](/wiki/zh/characters/new-game-plus/)的轮回加成开始；
- 账号的小号角色栏位。

若你放弃时是君主，你会先退位；若退位失败，则不会放弃任何东西。新生会在下一个轮回开始，旧神重置，与新游戏+的开始方式相同。

:::spoiler 剧透：结局与神明阵营
救赎者结局给予光明阵营，篡位者结局给予黑暗阵营，不屈者与真结局给予平衡阵营。放弃神位时，为下一个轮回记录的结局会按同样的对应关系回溯：光明计为救赎者，黑暗计为篡位者，平衡计为不屈者。

隐藏的消融结局不提供这两个选择。它会删除存档，只把该结局记录在你的终身进度中。

在提供选择时，曼威会问你能否超越凡俗、成为神明，并列出神明的作为：出现在神殿中供凡人信奉，管理追随者并施行神迹，与其他神明争夺信徒，并在神格等级中不断攀升。
:::
