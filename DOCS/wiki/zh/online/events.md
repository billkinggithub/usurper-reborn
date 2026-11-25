---
title: 排名、新闻与世界事件
path: /wiki/zh/online/events/
checked: 1.3.13
sources: Scripts/Systems/WorldEventSystem.cs, Scripts/Systems/NewsSystem.cs, Scripts/Locations/MainStreetDistricts.cs, Scripts/Systems/DailySystemManager.cs, Scripts/Systems/WorldSimService.cs, Scripts/Systems/WorldBossSystem.cs, Scripts/Systems/CombatEngine.cs, Scripts/Locations/WeaponShopLocation.cs, Scripts/Locations/ArmorShopLocation.cs, Scripts/Locations/MagicShopLocation.cs, Scripts/Locations/HealerLocation.cs, Scripts/Locations/DarkAlleyLocation.cs, Scripts/Systems/WeeklyGodSystem.cs
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | 治疗师不再显示它从未实际应用的阵营或世界事件价格行，从未启动过的“匪首崛起”事件已从事件列表中移除。
history: 1.3.10 | 在祝福之雨降下期间，在治疗师处治疗 HP 免费；在圣日，静修院的冥想和一次赎罪免费；没有任何事件会改变任何人的属性；事件描述会说明每个事件的作用。
history: 1.3.9 | 网站的 Observatory（天文台）页面显示公开的世界数据和每小时的世界历史。
history: 1.3.8 | NPC 盟友在你身边倒下时，会在新闻中写下一行，而不是两行。
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | 世界事件在在线模式下开始、倒计时并结束，同一时间最多只有一场天下同庆。
history: 1.2.5 | 世界事件标题、描述和皇家诏令会以每位玩家的语言显示，队伍新闻现在会显示标题和事件。
history: 1.2.4 | none
---
使用公告板查看新闻和世界事件，使用面向状态的菜单查看记录和声望。这些画面描述的是一个活着的世界，而不是固定版本的数据。

## 世界事件多久发生一次

在单人游戏中，每个新的游戏日都有 30% 的几率开始一个世界事件，从季节和城镇状态所允许的事件中抽取。每第 7 天还会强制出现锦标赛日、商队来访或丰收节之一，每第 30 天则出现王室庆典、王室悬赏、淘金热或远古遗物之一。每个事件持续其天数，在每个新的一天倒计时。

在线时，服务器在美国东部时间晚上 7 点的每日重置会为整个世界每天执行一次相同的流程：它会让每个事件倒计时，并有 30% 的几率开始一个事件。第 7 天和第 30 天的事件仅限单人游戏。在线游玩还有天下同庆，由击杀世界首领引发；它持续到下一次每日重置，如果在此之前的再次击杀，会保持这一场庆祝，而不会增加第二场。

## 每个世界事件有什么作用

事件可以改变商店价格，以及你赢得的怪物战斗的经验和金币。多个事件同时存在时会相乘，总值会被限制为：价格为 x0.25 到 x4.0，经验为 x0.5 到 x3.0，金币为 x0.25 到 x3.0。价格指的是武器店、防具店和魔法商店以及暗巷的价格；治疗师既不收费也不显示。最后一列显示每日抽取何时能抽到该事件。在标记为 No 的事件中，只有淘金热和天下同庆会以另一种方式出现（见上文）；其余事件永远不会开始。在匪徒劫掠进行期间，[荒野](/wiki/zh/world/wilderness/)中匪徒出现的频率会变为 3 倍。

{{table:world-events}}

瘟疫有其自身的效果：当它活跃时，战斗中的健康角色有 10% 的回合会受到最大 HP 1% 的伤害，并有很小的几率感染瘟疫，而患病角色会受到多 25% 的疾病伤害。没有任何事件会改变任何人的属性。在祝福之雨降下期间，在治疗师处治疗 HP（H 和 F）免费，且不抽税。在圣日，神殿静修院的冥想和一次赎罪免费；归返仪式保持其价格。

## 事件会影响你的精神

灾难（瘟疫、诅咒之地、匪徒劫掠、怪物入侵、恶魔传送门或巨龙现踪）会在你阅读新闻时造成每日的目睹精神损耗。反复阅读并不能让那项每日事件成倍增加。

## 排名

排名反映的是它自己的衡量标准。神殿地位使用虔诚和镇民的信仰；声望和其他记录使用不同的系统。不要把一块榜单当作在每场战斗中都是最强的证明。

每周的神明地位会选出本周之神，其信徒会在下周之前获得更多战斗经验（参见[玩家之神](/wiki/zh/gods/player-gods/)）。请到神殿查看当前的胜者，而不要依赖指南中的示例。

## 使用当前信息

[网站](/)会公开服务器信息。本百科有意不导出排行榜、私人账号或临时事件状态。
