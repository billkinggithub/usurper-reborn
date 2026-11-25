---
title: 城堡、国王与王座
path: /wiki/zh/world/castle/
checked: 1.3.14
sources: Scripts/Locations/CastleLocation.cs, Scripts/Locations/MainStreetDistricts.cs, Scripts/Core/King.cs, Scripts/Systems/ChallengeSystem.cs, Scripts/Systems/QuestSystem.cs, Scripts/Systems/DailySystemManager.cs, Scripts/Locations/BaseLocation.cs, Scripts/Systems/FactionSystem.cs, Scripts/Systems/CombatEngine.cs, Scripts/Systems/TrainingSystem.cs, Scripts/Core/Character.cs, Scripts/Systems/StreetEncounterSystem.cs, Scripts/Locations/DarkAlleyLocation.cs, Scripts/Locations/WeaponShopLocation.cs, Scripts/Locations/ArmorShopLocation.cs, Scripts/Locations/MagicShopLocation.cs, Scripts/Locations/TempleLocation.cs, Scripts/Systems/DivineBlessingSystem.cs, Scripts/Core/GameConfig.cs, Scripts/Locations/MainStreetClassic.cs
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | 信仰会成员在治疗师处少付 15% 到 35%，王座厅的菜单行在每种语言中都能容纳在 79 列内，当阴谋只涉及宫廷头衔时，逮捕会描述阴谋者被逐出宫廷，而不是被监禁。
history: 1.3.10 | 侦测威胁有 50% 的概率发现一个活跃的阴谋，被发现的阴谋会等待国王 7 天来逮捕，逾期则失效；国王不再处决你救过的 NPC；找回被盗神器的王室任务会在一个指定地牢楼层放置一名神器窃贼。
history: 1.3.9 | 主街默认以经典布局开放，地区布局可在设置中选择。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | 玩家在其王座挑战到期前雇用的 NPC 会留在该队伍中，不会执行挑战。
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | 王冠怪物悬赏会支付其层级金币和经验的两倍，王室任务提议会显示预付款和报酬，怪物市场会显示国王收取和给予的费用与属性。
history: 1.3.0 | 玩家队伍中的 NPC 不再会被选中挑战 NPC 统治者或在空王座上被加冕，一次击杀只会推进一次王室任务目标。
history: 1.2.5 | 任何语言的玩家都不能再接受第二个王室任务，清除地牢楼层的王室任务现在会要求你清空一层。
history: 1.2.4 | none
---
城堡是王国统治者开庭理政的地方。从主街按 K 进入城堡。使用地区布局时，用 C 打开城堡庭院地区，然后按 K。当城堡是那里唯一开放的地方时（3 级和 4 级），按 C 会直接打开它。它会在你最初几级之后出现在菜单中。

## 以平民身份拜访

不是统治者的角色可以查看皇家卫队和监狱牢房、向王室金库捐献金币、阅读君主历史、请求觐见，以及申请加入皇家卫队。等级和侠义足够且没有犯罪记录的角色还可以加入王冠阵营，从而打开王室军械库（见[阵营](#阵营-王冠-暗影与信仰会)）。

### 加入皇家卫队及其薪酬

如果你的黑暗不超过侠义 + 50，且服役卫兵少于 {{balance:MaxRoyalGuards}} 名，你可以从 5 级起加入皇家卫队。卫兵会在每次每日重置时从国库领取 {{balance:BaseGuardSalary}} + 20 x 你的等级 金币，加入会使你朝侠义方向移动 10 点。在 20 级时，薪酬为每天 700 金币。

当有人挑战王座时，玩家卫兵会收到警报，战斗会等待 2 个世界刻。回答 Y 会把你带到城堡亲自防守。回答 N 会损失 25 点忠诚，忠诚在 20 或以下时你会被解职；未及时回答会损失 15 点。

### 向王室金库捐献会得到什么

向王室金库捐献会给予 金币 / 100 的侠义，最高 50，以及 金币 / 50 的王冠声望，没有上限；对王冠成员来说，该声望也会计入爵位。5,000 金币会给予 50 侠义和 100 王冠声望。

## 请求觐见：声誉

城堡对你的声誉为（侠义 + 声望）/ 2。觐见需要 25。更高的声誉会解锁更多请求：50 起可请求王室任务，75 起可请求王室贷款，100 起可请求王室祝福，150 起可请求减税请愿。骑士册封和赦免各有自己的条件。

### 我如何获得骑士册封

骑士册封需要 200 侠义、150 声望、15 级，并且黑暗低于你的侠义，或为均衡阵营。骑士被称为爵士或女爵士，永久造成 {{percent:KnightDamageBonus}}% 更多伤害，并拥有 {{percent:KnightDefenseBonus}}% 更多防御。

### 王室赦免要多少钱

赦免会以 黑暗 x 50 x（1 + 你的等级 / 10，向下取整）金币清除你的黑暗：声誉 100 时打 25% 折扣，200 时打 50% 折扣。在 25 级、黑暗 300、声誉 120 时，花费为 300 x 50 x 3 x 0.75 = 33,750 金币。

### 王室贷款：利息与到期日

王室贷款最多为 国库一半 和 声誉 x 10 x 你的等级 两者中的较低者，且至少 500。你需在 30 天内以 10% 利息偿还。逾期期间，前 7 天每天损失 {{balance:RoyalLoanChivalryLossEarly}} 侠义，第 8 到 14 天每天损失 {{balance:RoyalLoanChivalryLossMid}}，之后每天损失 {{balance:RoyalLoanChivalryLossLate}}，并且可能对你发布悬赏。

### 王室祝福有什么作用

王室祝福花费 500 金币 x 你的等级，声誉 200 时减半，300 时免费。它会立刻恢复最多 25 HP 和 25 法力，并持续 {{balance:RoyalBlessingDuration}} 个战斗回合，跨战斗计算：攻击提高 10%，防御提高 10%，命中判定将怪物的护甲等级视为低 2 点。

## 如何成为国王

通往王座的两种方式都需要等级 {{balance:MinLevelKing}}。

- **夺取空王座。** 无人统治时，菜单会提供 C 来夺取。你会带着 {{balance:DefaultRoyalTreasury}} 金币的国库建立一个全新的宫廷。
- **挑战统治者。** 有人统治时，按 I 潜入城堡。你要先与怪物守卫战斗，然后与雇佣守卫战斗，最后与统治者战斗，其战斗时拥有 {{balance:KingDefenderHPBonus}} 倍 HP 和 {{balance:KingDefenderDefBonus}} 倍防御。你每天可以尝试一次，不能在加冕后的 24 个现实小时内尝试，也不能在统治者比你高 {{balance:KingChallengeLevelRange}} 级以上时尝试。

在挑战战中，忠诚低于 30 的雇佣守卫有 30% 的概率逃跑，低于 15 的守卫可能有 20% 的概率转而攻击其统治者。玩家卫兵会亲自防守，不参与那场战斗。

你必须在登上王座前离开你的队伍，游戏会先询问。如果失败，你会活着被丢回主街。如果获胜，你会继承国库、囚犯和孤儿，但不继承卫兵。在线模式下，离线统治者会用其角色的 AI 副本防守，队伍也可以按 B 围攻城堡。

### NPC 能夺走我的王座吗

可以。NPC 只有在其等级达到 {{balance:NPCMinLevelToChallenge}} 或以上、与统治者等级相差不超过 {{balance:NPCChallengeLevelRange}} 级、野心高于 {{balance:NPCMinAmbitionToChallenge}}、不在监狱中，且不是剧情角色时，才会挑战玩家统治者；每天最多有 {{balance:MaxNPCChallengesPerDay}} 名 NPC 挑战。挑战失败的 NPC 会入狱。玩家队伍中的 NPC 不会被选中挑战 NPC 统治者；一旦玩家雇用其队伍中的 NPC，它就不会对玩家统治者执行挑战，也不会作为指定继承人或觊觎者在空王座上被加冕。

## 当国王能得到什么

玩家统治者每天获得 {{balance:KingDailyStipend}} + {{balance:KingStipendPerLevel}} x 等级 金币的津贴、{{balance:KingCombatStrengthBonus}} 倍攻击伤害、{{balance:KingCombatDefenseBonus}} 倍防御和 {{balance:KingCombatHPBonus}} 倍最大 HP。在 40 级时，津贴为每天 4,500 金币。

## 统治者的权力与职责

统治者的菜单会增加这些行动：

- **监狱牢房：** 监禁、赦免、处决或设定保释金。统治者每天可以监禁 {{balance:DailyPrisonSentences}} 名角色，处决 {{balance:DailyExecutions}} 名。NPC 最多可被监禁 30 天。在线模式下，当你输入数字时，玩家最多可被监禁 1 天；输入为空或无效会给予 7 天。
- **命令：** 开启或关闭城镇设施，发布公告，或发布由国库支付的悬赏。
- **安全：** 雇用或解雇卫兵和怪物守卫，并支付卫兵奖金。
- **财政事务：** 设定市民税、销售税和队伍税，并向国库存入或提取金币。
- **宫廷：** 王室魔法、孤儿院、王室婚礼、宫廷政治、继承与继承人，以及保镖佣兵。
- **退位：** 输入 yes 将王冠交给 NPC 继承人。

## 国库：税收收入与每日开支

国库每天会获得市民税：税率 x 纳税人 x {{balance:KingTaxIncomeMultiplier}}。向所有人征税会统计城镇的 NPC，至少 45 名；只向一个阵营征税只统计该阵营的 NPC，至少 1 名。在默认税率 {{balance:DefaultTaxRateNew}} 金币和 100 名 NPC 时，每天为 10,000 金币。销售税、捐款、赦免、贷款偿还和其他王室费用也会填充国库。

国库每天支付卫兵薪水、怪物守卫的喂养费、每名孤儿 {{balance:OrphanCareCost}} 金币和 {{balance:BaseCourtMaintenance}} 金币的宫廷维护费，并向魔法预算注入 {{balance:DailyMagicReplenishment}} 金币，魔法预算最多持有 {{balance:MaxMagicBudget}}。国库永远不会低于 0。保镖佣兵从你自己的金币支付，而不是从国库。

### 城堡卫兵：数量与费用

统治者最多雇用 {{balance:MaxNPCGuards}} 名 NPC 卫兵，每名从国库花费 {{balance:GuardRecruitmentCost}} 金币；加入皇家卫队的玩家会填补其 {{balance:MaxRoyalGuards}} 个名额中的其余部分。雇佣卫兵的每日薪水为 {{balance:BaseGuardSalary}} + {{balance:GuardSalaryPerGuardLevel}} x 统治者等级：在 40 级统治者手下每天 1,100 金币。

当国库足以支付当天开支时，卫兵每天获得 1 点忠诚，服役 30 天后额外获得 1 点，否则失去 5 点。卫兵在忠诚 10 或以下时会逃跑，在 25 或以下时每天有 10% 的概率离开。卫兵奖金会为每名卫兵花费相应金额，每名最多 1,000,000，并使每名卫兵的忠诚提高 金额 / 100，最高 100：给 4 名卫兵各 1,000 金币会花费 4,000，并给予 10 点忠诚。

### 怪物守卫：价格、HP 与喂养

统治者最多购买 {{balance:MaxMonsterGuards}} 名怪物守卫。你每已拥有一名，下一名的价格就会增加 500 金币。

{{table:monster-guards}}

### 国库无法支付时

当国库持有的金币少于一天的开支时，每名卫兵额外失去 3 点忠诚，每名怪物守卫有 10% 的概率逃跑。

### 王室魔法、孤儿院与宫廷政治

- **王室魔法，** 从魔法预算支付：祝福王国 1,000（25 点侠义）、侦测威胁 500（有一半的施放会发现最深入的秘密阴谋，其策划者会离开宫廷，之后可被逮捕；每次施放还会指出最多三名黑暗高于 300 的镇民）、保护 2,000（每名卫兵 10 点忠诚）和占卜 1,500（一名 NPC 的等级、地点和金币）。
- **孤儿院**最多收容 {{balance:MaxRoyalOrphans}} 名孤儿。收养一名 3 到 12 岁的孤儿会从国库花费 500 + 100 x 已收容的孤儿数，并使你朝侠义方向移动 15 点。年满 {{balance:OrphanCommissionAge}} 岁的真正孤儿可以花 {{balance:OrphanCommissionCost}} 金币被委任为卫兵（薪水 300、忠诚 90、10 点侠义），也可以成为佣兵或镇民。被收养的孤儿不是真正孤儿，不能被委任。
- **宫廷政治**从国库花费：逮捕一名策划者 {{balance:ArrestTrialCost}}，提拔一名宫廷成员 {{balance:PromoteCost}}（+10 忠诚），以及贿赂 {{balance:BribeBaseCost}} + 50 x（100 减去该成员的忠诚）。一名忠诚 40 的成员需要 3,500 金币才能贿赂。

## 叛乱：多少次处决

统治者的第 5 次处决会引发叛乱，第 3 次和第 4 次会有警告；关闭城镇 75% 或以上的设施也会如此。叛乱会结束统治并抛硬币。一面是角色被永久删除。另一面是你失去手头和银行中的所有金币以及所有声望，侠义下降 5,000（因此归零），朝黑暗方向移动 500 点，处决计数重新开始。

## 阵营：王冠、暗影与信仰会

你可以加入三个阵营之一，从 10 级起，且未加入其他阵营：

- **王冠，** 在城堡：侠义高于 500、黑暗不高于 500，且王冠声望不低于 0。
- **暗影，** 在[暗巷](/wiki/zh/world/dark-alley/#暗影阵营)：黑暗高于 200，或为他们做过一次人情。他们只会在声望 -50 或更差时拒绝，若黑暗高于 200 则连那时也不会拒绝。
- **信仰会，** 在[神殿](/wiki/zh/world/temple/)：信仰会声望 100 或以上。

加入会把你与该阵营的声望至少提升到 100，然后再提升 100，并降低你与其他阵营的声望。离开会损失旧阵营 500 点声望。

### 阵营爵位要求

你的爵位会随着加入后在阵营中赢得的声誉而提升：王冠声誉来自王室金库，信仰声誉来自教会捐款、祝福和良好的神殿供奉，暗影声誉来自黑暗行为，等等。声誉提升也会改变你与其他两个阵营的声望。

{{table:faction-ranks}}

### 每个阵营给予什么

- **王冠：** 武器、防具和魔法商店折扣；当街头的怨恨演变成战斗时，卫兵有概率介入；死亡时少损失 {{percent:CrownTaxExemptionRate}}% 金币；巡逻不会拦下被通缉的王冠成员；王室军械库。
- **暗影：** 在武器、防具和魔法商店出售时获得更多金币；逃跑概率加成；黑市折扣，黑市会向成员开放；线人。
- **信仰会：** 更长的祈祷和献祭祝福；在与怪物的战斗中有概率从致命一击中被救下，留下最大 HP 的十分之一，每场战斗一次；静修院。

{{table:faction-bonuses}}

信仰会成员在治疗师处按爵位少付 15% 到 35%，这发生在计税之前（[治疗师税](/wiki/zh/world/healer/)）。

## 王室任务

通过觐见获得的王室任务会要求你杀死怪物、从等待在地牢某层的窃贼手中找回被盗神器（任务会指明楼层）、清空一个地牢楼层、击杀一名地牢楼层首领，或抵达某个楼层进行调查。它有期限，在你接受时支付预付款金币和经验，完成时支付每级 1,000 金币，并且你一次只能持有一个。统治者的任务画面会显示王室悬赏，你可以在[任务大厅](/wiki/zh/world/town/)领取。

关于囚犯的命运，见[罪行与监狱](/wiki/zh/world/law/)。
