---
title: 主街指南
path: /wiki/zh/world/town/
checked: 1.3.15
sources: Scripts/Locations/MainStreetLocation.cs, Scripts/Locations/MainStreetDistricts.cs, Scripts/Locations/MainStreetClassic.cs, Scripts/Locations/DormitoryLocation.cs, Scripts/Locations/LevelMasterLocation.cs, Scripts/Locations/QuestHallLocation.cs, Scripts/Locations/TeamCornerLocation.cs, Scripts/Locations/MarketplaceLocation.cs, Scripts/Locations/NewsLocation.cs, Scripts/Systems/LocationManager.cs, Scripts/Core/GameConfig.cs, Scripts/Systems/MarketplaceSystem.cs, Scripts/Locations/BaseLocation.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | 宿舍和情缘街的菜单行在所有语言下都能容纳在 79 列以内。
history: 1.3.10 | 善行（G）位于经典主街菜单中，施舍金币给穷人花费你的等级 x 20 金币；离开某个地点会把你带回原城区；单人游戏中在宿舍睡觉会等到傍晚；离线拍卖行允许你撤回上架物品。
history: 1.3.9 | 主街默认以经典布局开放，分区布局可在设置中选择。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | 你从宿舍中击败的熟睡者身上拿走的物品会保留附魔、效果和诅咒。
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | 当已完结故事同伴的悲伤给予感知时，主街会在适用时显示这项加成。
history: 1.3.0 | 组队角的雇佣列表会优先显示最接近你等级的 NPC；25 级以下雇佣更便宜；城镇会保留一批可供雇佣的低等级 NPC。
history: 1.2.6 | 组队角中新队伍的名字不能包含 < > & 或双引号。
history: 1.2.5 | 主街、宿舍、等级大师、组队角和集市会以所有五种语言显示，宿舍谋杀邮件会以受害者的语言送达受害者。
history: 1.2.4 | 过长的新闻行会在 79 列处换行，你袭击宿舍熟睡者时发出的通知会送达其邮箱。
---
主街默认显示经典的单屏菜单，每个地点对应一个按键。随着你获得最初几级，更多地点会出现。可以在设置中选择分区布局（`~`，然后 S）：它会显示少数地点和一个城区列表。按城区的按键打开城区，再按地点的按键；R 返回。从城区打开某个地点后，离开该地点会回到那个城区。只开放一个地点的城区会直接打开那个地点：在 5 级完整菜单解锁之前，城堡庭院区只有城堡，家与炉火区只有家。以下各节按分区布局排列。

## 主街

D 地牢，I 旅店，E 探索，T 组队角，A [暗巷](/wiki/zh/world/dark-alley/)。

## 商人街

按 M，然后 W 武器店、A 防具店、M 魔法商店、U [乐器店](/wiki/zh/world/music-shop/)或 J 拍卖行。见[商店](/wiki/zh/items/shops/)。

## 公会街

按 G，然后 H [治疗师](/wiki/zh/world/healer/)、T [神殿](/wiki/zh/world/temple/)、O [旧教堂](/wiki/zh/world/church/)、B [银行](/wiki/zh/items/banking/)、V 等级大师或 U 任务大厅。

## 家与炉火

按 H，然后 H [家](/wiki/zh/world/home/)、L 住宿或 X [情缘街](/wiki/zh/world/relationships/)。

## 城堡庭院

按 C，然后 K [城堡](/wiki/zh/world/castle/)、C [锚点大道的挑战](/wiki/zh/world/anchor-road/)、S [圣所](/wiki/zh/world/sanctum/)或 E [城郊](/wiki/zh/world/settlement/)（建成后）。

## 状态与公告板

按 S 查看状态、进度、属性记录、声望和善行。按 N 查看新闻和世界事件。

## 在线区

仅在线：按 O，然后 W 谁在线、C 聊天、A [竞技场](/wiki/zh/online/arena/)、B 世界首领或 G 公会。

## 住宿

住宿就是宿舍。你可以列出并查看其他熟睡者，也可以在那里睡觉。单人游戏中睡觉免费，而且和旅店、家一样，只能在傍晚进行：你会完全恢复，并在第二天早晨醒来。在线时，宿舍床位花费 {{balance:DormitorySleepCost}} 金币；睡觉会保存并让你登出，也会在你睡觉时让你暴露在攻击之下。在线时你还可以袭击熟睡者以夺取金币。旅店也在线出租房间；见[旅店](/wiki/zh/world/rest/)。

## 等级大师

等级大师会用你已获得的经验提升你的等级。大师还会教授能力和法术、显示你的进度路线图、训练熟练度、设定你的[专精](/wiki/zh/characters/specializations/)，并允许你把经验给予配偶、队友或同伴。见[升级](/wiki/zh/characters/leveling/)。

## 任务大厅

查看、领取、交付或放弃任务，有每日领取上限，并可阅读悬赏板。见[任务](/wiki/zh/world/quests/)。

## 组队角

创建、加入或离开队伍，以每日工资招募 NPC，装备和复活成员，并查看队伍排名。雇佣列表会优先显示最接近你等级的 NPC；25 级以下雇佣更便宜；城镇会保留一批可供雇佣的低等级 NPC。在线模式还会加入队伍消息、玩家回声、队伍战争和总部。见[队伍](/wiki/zh/online/teams/)。

## 拍卖行与新闻

离线时，拍卖行允许你以自己定的价格上架物品、撤回上架（W）并购买其他上架物品；30 个现实天后仍未售出的上架物品会退还给你。在线时，上架持续 12、24、48 或 72 小时，费用为价格的 5%、4%、3% 或 2%，外加国王税。[商店指南](/wiki/zh/items/shops/)有详细说明。新闻是城镇的新闻板，最新的排在最前面。

旧版本中的健身馆已被移除，无法抵达。
