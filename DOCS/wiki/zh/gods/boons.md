---
title: 每位神明的恩赐有什么作用
path: /wiki/zh/gods/boons/
checked: 1.3.15
sources: Scripts/Systems/GodBoonSystem.cs, Scripts/Systems/DivineBlessingSystem.cs, Scripts/Systems/CombatEngine.cs, Scripts/Systems/StatEffectsSystem.cs, Scripts/Systems/SpellSystem.cs, Scripts/Systems/WorldBossSystem.cs, Scripts/Locations/WildernessLocation.cs, Scripts/Locations/DarkAlleyLocation.cs, Scripts/Locations/HomeLocation.cs, Scripts/Locations/SettlementLocation.cs, Scripts/Systems/QuestSystem.cs, Scripts/Core/Character.cs, Scripts/Core/GameConfig.cs
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
history: 1.3.2 | 索拉里乌斯与瓦洛里安的伤害恩赐、乌姆布拉思的暴击几率以及旧神回响作用于你的普通挥击，恩赐提供的暴击几率对世界首领同样生效。
---
恩赐是你神明的领域效果。下文给出的数值是完整的恩赐，你在狂热者与神选者阶位拥有完整效果；信徒获得每项恩赐的 {{balance:GodBoonFollowerStrengthPct}}%，虔信者获得 {{balance:GodBoonDevoutStrengthPct}}%（见[恩宠表](/wiki/zh/gods/favor/)）。恩赐只在其适用的场合生效。

## 各恩宠阶位的恩赐强度

阿玛拉的一位虔信者信徒的治疗效果提高 {{balance:GodBoonAmaraHealPct}} × {{balance:GodBoonDevoutStrengthPct}} / 100%，约为 10%。取整数的恩赐按四舍五入计算，且在生效时至少为 1。玩家神明的追随者获得其领域的同一恩赐，但会再按该神明的威望缩放（见[玩家神明](/wiki/zh/gods/player-gods/#领域恩赐)）。

## 战斗与治疗恩赐

- **[索拉里乌斯](/wiki/zh/gods/solarius/)：** 当你在战斗中至少面对一个活着的亡灵或恶魔时，你的法术、技能、药剂与治疗草药提供的治疗提高 {{balance:GodBoonSolariusHealPct}}%。它还会让你的普通挥击对亡灵与恶魔造成的伤害提高 {{balance:GodBoonSolariusUndeadDamagePct}}%。
- **[瓦洛里安](/wiki/zh/gods/valorian/)：** 当你的生命低于最大生命值的 {{balance:GodBoonValorianHpThresholdPct}}% 时，你的普通挥击造成的伤害提高 {{balance:GodBoonValorianLowHpDamagePct}}%。
- **[阿玛拉](/wiki/zh/gods/amara/)：** 你施放的每一次治疗（法术、技能与歌曲，作用于自己或盟友）提高 {{balance:GodBoonAmaraHealPct}}%，你为队伍张起的护佑也增强 {{balance:GodBoonAmaraHealPct}}%。
- **[朱迪卡](/wiki/zh/gods/judicar/)：** 每次怪物攻击对你造成的伤害降低 {{balance:GodBoonJudicarDefencePct}}%，且始终至少留下 1 点；你领取的悬赏金币提高 {{balance:GodBoonJudicarBountyPct}}%。
- **[乌姆布拉思](/wiki/zh/gods/umbrath/)：** 你在暗巷的扒窃成功率及其上限提高 {{balance:GodBoonUmbrathTheftPct}} 个百分点。它还会使你的普通挥击的暴击几率提高 {{balance:GodBoonUmbrathCritPct}} 点，并与其他所有暴击加成的上限相同。
- **[阿卡努斯](/wiki/zh/gods/arcanus/)：** 法术伤害提高 {{balance:GodBoonArcanusSpellPct}}%，每个战斗回合回复的法力提高 {{balance:GodBoonArcanusManaRegenPct}}%。更大的法力池是另一种效果。
- **[迪斯科尔迪亚](/wiki/zh/gods/discordia/)：** 对玩家造成的伤害提高 {{balance:GodBoonDiscordiaPvpDamagePct}}%，且每个怪物都有 {{balance:GodBoonDiscordiaFirstActionFailPct}}% 的几率在战斗中的第一次行动失败。

## 生存与奖励恩赐

- **[泰兰](/wiki/zh/gods/terran/)：** 最大生命值提高 {{balance:GodBoonTerranMaxHpPct}}%，每天园中草药产量提高 {{balance:GodBoonTerranYieldPct}}%，并获得更大的聚落议会分红。更高的生命上限并不等于免费治疗。
- **[莫提斯](/wiki/zh/gods/mortis/)：** 死亡时损失的金币减少 {{balance:GodBoonMortisDeathGoldCutPct}}%。救命神迹是神选者的一项独立福利。

## 西尔瓦娜会让荒野金币与经验翻倍吗

会，在完整强度下会。西尔瓦娜的恩赐是提高 {{balance:GodBoonSylvanaWildernessPct}}%，这会让以下的荒野收益在狂热者与神选者阶位翻倍：你赢下荒野战斗后的额外金币、采集时发现的金币、废墟中的金币，以及荒野圣坛给予的经验。信徒获得三分之一加成，虔信者获得三分之二加成。荒野战斗本身的经验与金币，以及荒野之外的奖励，不会翻倍。

## 查看实际强度

每位神明的页面会显示其基础常量、善行与禁忌。神殿中的祭坛界面会显示你当前的恩赐、结界与阶位。

神明结界保护精神，与这些恩赐相互独立；见[恩宠](/wiki/zh/gods/favor/#精神结界)。领域的伤害或奖励恩赐不会消除悲痛、损耗或戒断。
