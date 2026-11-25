---
title: 恩宠、祈祷与献祭
path: /wiki/zh/gods/favor/
checked: 1.3.15
sources: Scripts/Systems/FaithSystem.cs, Scripts/Systems/GodBoonSystem.cs, Scripts/Systems/GodDeedSystem.cs, Scripts/Systems/DivineBlessingSystem.cs, Scripts/Locations/TempleLocation.cs, Scripts/Systems/GodSystem.cs, Scripts/Systems/FactionSystem.cs, Scripts/Systems/CombatEngine.cs, Scripts/Systems/MiracleSystem.cs, Scripts/Core/GameConfig.cs
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
history: 1.3.3 | 救起一名倒下的盟友算作治疗盟友，这是阿玛拉喜欢的善行。
history: 1.3.2 | 神殿祝福（来自每日祈祷或金币献祭）的伤害加成作用于你的普通挥击；神怒会在整场战斗中按屏幕所示的百分比削减你的伤害与防御。
---
恩宠是你与所信奉神明之间的关系：一个从 {{balance:GodFavorMin}} 到 {{balance:GodFavorMax}} 的数值，随你的角色一同保存。你的阶位决定你能获得多少神明的恩赐，并且在你跨过某个阶位的瞬间就会改变。

{{table:favor}}

## 如何获得恩宠

首先在神殿选择一位神明；[众神与信仰](/wiki/zh/gods/#在神殿选择一位神明)页面给出了步骤。恩宠有四种来源，每种都有自己的每日上限：

- **每日祈祷：** {{balance:GodFavorPrayerGain}} 点恩宠，每天一次，在正殿按 Y。
- **金币献祭：** 每天最多 {{balance:GodFavorGoldDailyCap}} 点恩宠。
- **物品献祭：** 每天最多 {{balance:GodFavorItemDailyCap}} 点恩宠。
- **你神明喜欢的善行：** 每天合计最多 {{balance:GodFavorDeedDailyCap}} 点恩宠。

禁忌会损失恩宠，但不占用任何每日额度。每日额度会被保存，因此读档无法重复获取。

### 金币献祭：多少金币换多少恩宠

向自己信奉的神明献祭金币时，每（你的等级 × {{balance:GodFavorGoldPerLevel}}）枚金币可换 1 点恩宠，每天最多 {{balance:GodFavorGoldDailyCap}} 点。10 级时，1,000 枚金币换 1 点恩宠，5,000 枚金币可达到当日上限。超过上限的金币仍会献给神明，但当天不再换得更多恩宠。

### 物品献祭：一件物品换多少恩宠

物品献祭换得的恩宠，等同于其转售价值（价格的一半）按金币献祭所能换得的恩宠，最低不少于 {{balance:GodFavorItemMin}}，最高不超过 {{balance:GodFavorItemMax}}。10 级时，一件标价 6,000 金币的物品转售价值为 3,000，即 3 点恩宠。物品会从你献出的栏位中取走并永久消失。诅咒物品与唯一物品会被拒绝。

### 善行与禁忌

你神明喜欢的善行，常见之举给予 {{balance:GodDeedMinor}} 点恩宠，较罕见之举给予 {{balance:GodDeedMajor}} 点，例如完成一次悬赏或学会一个法术；一次亵渎则以 {{balance:GodDeedDesecration}} 点取悦黑暗诸神。禁忌按其轻重扣除 {{balance:GodTabooMinor}}、{{balance:GodTabooMajor}} 或 {{balance:GodTabooGrave}} 点恩宠。每位神明自己的清单在其页面上，例如[阿卡努斯](/wiki/zh/gods/arcanus/)，他的追随者若连续 {{balance:GodTabooNoCastDays}} 次每日重置都不施放法术，便会触犯一项重大禁忌。

## 如果我不再祈祷，会失去恩宠吗

会。在连续超过 {{balance:GodNeglectGraceDays}} 次每日重置没有虔诚之举后，每次每日重置都会扣除 {{balance:GodNeglectDailyLoss}} 点恩宠。虔诚之举是指一次祈祷、向你神明献祭金币或物品，或一件你神明喜欢的善行；其中任何一项都会让计数重新开始。

## 每日祈祷祝福

每日在神殿祈祷会给予 {{balance:GodFavorPrayerGain}} 点恩宠，若信奉的是神殿神明，还会额外获得一个有计时的祝福。它持续 120 现实分钟，在狂热者与神选者阶位持续时间延长为 {{balance:GodPrayerBlessingZealotMultiplier}} 倍，而信仰会成员还会更久（见[派系](/wiki/zh/world/castle/)）。在祝福持续期间：

- 每次怪物击中你造成的伤害降低 3 + 5 × 神明力量百分比，向下取整；
- 你赢下怪物战斗获得的经验提高 5 + 10 × 神明力量百分比，向下取整。

神明的力量是把其神性经验换算到 0.1 到 1.0 的标度：经验值以 10 为底的对数除以 7。一位神殿神明初始拥有 5,000 到 20,000 点经验，力量约为 0.53 到 0.61，因此这位神明的祝福能削减 5% 或 6% 的伤害，并增加 10% 或 11% 的经验。该祝福还会让你的普通挥击获得与削减幅度相同大小的伤害加成。

向玩家神明祈祷时，会取该神明所配置神恩中伤害与防御百分比的较大者，将其翻倍，并作为祝福赐予你，使你的攻击与防御都提高相应数值，持续 {{balance:GodPrayerBlessingCombats}} 场战斗，在狂热者与神选者阶位则翻倍。10% 的伤害神恩会给出 20% 的祝福。没有伤害或防御神恩的神明不会给予祝福。见[玩家神明](/wiki/zh/gods/player-gods/#神恩)。

### 金币献祭祝福

向自己信奉的神殿神明献祭 100 枚或更多金币，也会给予一个祝福。它的强度是金币数以 10 为底的对数除以 2，范围从 0.5 到 3，持续 30 + 15 × 该强度 分钟，信仰会成员更久。它给予的效果取决于神明：

- **索拉里乌斯、瓦洛里安、阿玛拉、朱迪卡、泰兰与西尔瓦娜：** 怪物击中你造成的伤害降低 5 + 强度 × 神明力量 × 10%。
- **阿卡努斯：** 赢下战斗获得的经验提高 10 + 强度 × 神明力量 × 15%。
- **乌姆布拉思、莫提斯与迪斯科尔迪亚：** 你的普通挥击获得 5 + 强度 × 神明力量 × 10% 的伤害加成。

1,000 枚金币的强度为 1.5：对一位力量为 0.5 的善良神明，它带来 12% 的减伤，持续 52 分钟。你一次只能持有一个祝福：献祭祝福会取代生效中的祈祷祝福，而祈祷也会取代献祭祝福。

## 向另一位神明献祭金币

向自己神明以外的神明献祭金币不会换得恩宠，反而会为你记下神怒：当那位神明与你所信的神明站在同一阵营时为 1 级，站在对立阵营时为 2 级，向对立阵营献祭 500 枚或更多金币时为 3 级。当一位神明的黑暗高于其善良时，该神明便属于黑暗阵营：乌姆布拉思、莫提斯与迪斯科尔迪亚。神怒的后果见[众神与信仰](/wiki/zh/gods/#地牢中的神怒)。

## 精神结界

从虔信者阶位起，你的领域会保护你免受一种精神损失。结界将该损失削减 {{balance:GodWardLossCutPct}}%；迪斯科尔迪亚的结界则改为把陷入恐惧的几率降低 {{balance:GodWardLossCutPct}}%，西尔瓦娜的结界把地牢损耗降低 {{balance:GodWardSylvanaStrainCutPct}}%。莫提斯守护两种。结界并不能防护所有类型的伤害；各神明的页面会列出各自的结界。

## 神迹

神选者阶位（从 {{balance:GodFavorTierChosenMin}} 点恩宠起）每天解锁一次神迹。当神迹能派上用场时，战斗按键才会出现。各领域提供治疗、法力、控制、一次必定暴击、脱身、灵体盟友或免死；[每日神迹](/wiki/zh/gods/miracles/)给出了每一项的数值。神迹在怪物与剧情首领战斗中有效，在玩家战斗或世界首领战斗中无效。保存并重新读取不会恢复已用掉的神迹。

## 更换神明

离开一位神明会丢弃你在那位神明那里的全部恩宠；新神明从 0 开始。带着恩宠离开会招来神怒或玩家神明的神雷，轻重取决于损失的恩宠，正如[众神与信仰](/wiki/zh/gods/#更换或离开你的神明)所解释的。神殿会在更换前显示代价并询问确认。

参见[神殿各厅](/wiki/zh/world/temple/)与[玩家神明](/wiki/zh/gods/player-gods/)。
