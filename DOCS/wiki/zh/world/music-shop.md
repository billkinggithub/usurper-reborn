---
title: 乐器店
path: /wiki/zh/world/music-shop/
checked: 1.3.15
sources: Scripts/Locations/MusicShopLocation.cs, Scripts/Data/EquipmentData.cs, Scripts/Core/GameConfig.cs, Scripts/Systems/CombatEngine.cs
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
history: 1.3.2 | 买下的乐器只在柜台为吟游诗人或进阶职业装备，不会为秘法萨满装备。
history: 1.3.0 | 因怨恨离开你的乐器店同伴会暂时不在店里，直到在神殿的信仰会厅堂完成宽恕，使同伴回来。
history: 1.2.5 | 乐器名称和 Electron 菜单标签以玩家语言显示，较长的购买消息在 79 列处换行。
---
乐器店专门经营乐器、演奏和歌曲，而不是普通武器。乐器是装备，有自己的武器类型和限制。

## 乐器

浏览商店，比较等级和购买要求，并确认预定的使用者能否装备这件乐器。商店并不会简单地向高级顾客隐藏所有低级乐器。

对吟游诗人来说，乐器可能与你使用的动作有关。它不会仅仅因为和剑一样占一个武器栏就可以与剑互换。

## 乐器店的歌曲：价格与效果

雇人演奏（P）是一种服务，而不是购买乐器。一次演奏会给你一个歌曲增益，作用于接下来的 {{balance:SongBuffDuration}} 场战斗，新歌会替换你当前的歌。吟游诗人少付 25%。以下价格不含税：

- **战争进行曲：** 200 + 等级 x 10 金币。攻击伤害 +{{percent:SongWarMarchBonus}}%。
- **铁之摇篮曲：** 200 + 等级 x 10 金币。防御 +{{percent:SongIronLullabyBonus}}%。
- **幸运曲调：** 300 + 等级 x 15 金币。击杀获得的金币 +{{percent:SongFortuneBonus}}%。
- **战斗圣歌：** 400 + 等级 x 20 金币。攻击 +{{percent:SongBattleHymnBonus}}%，防御 +{{percent:SongBattleHymnBonus}}%。

20 级时，战争进行曲花费 400 金币，吟游诗人则为 300 金币。

## 传说之歌与同伴

传说之歌（L）是面向故事的活动，可以揭示历史。与同伴相关的商店选项取决于故事状态。因怨恨离开你的同伴会不在店里，商店此时会提示：在神殿的信仰会厅堂完成宽恕，可以让同伴回来。

有关更广泛的区别，见[同伴](/wiki/zh/combat/companions/)和[商店](/wiki/zh/items/shops/)。
