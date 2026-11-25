---
title: 众神与信仰
path: /wiki/zh/gods/
checked: 1.3.15
sources: Scripts/Systems/GodSystem.cs, Scripts/Systems/GodBoonSystem.cs, Scripts/Locations/TempleLocation.cs, Scripts/Systems/FaithSystem.cs, Scripts/Locations/MainStreetDistricts.cs, Scripts/Core/Character.cs, Scripts/Locations/DungeonLocation.cs, Scripts/Systems/CombatEngine.cs, Scripts/Core/GameConfig.cs, Scripts/Locations/MainStreetClassic.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | none
history: 1.3.9 | 主街默认以经典布局打开，街区布局可在设置中选择。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | 神怒会在整场战斗中把你的伤害与防御降低 10%、20% 或 30%，正如屏幕所示。
history: 1.3.0 | none
history: 1.2.5 | 神殿祭司现在会从 10 级起为你指出第一道封印，神殿界面以全部五种语言显示，献祭通知会以该神明的语言送达玩家神明。
history: 1.2.4 | 你在玩家神明的祭坛献祭金币时，该神明收到的通知现在会送达它的信箱。
---
你一次只信奉一位神明。神殿的十位神明与玩家神明争夺追随者。你与自己的神明之间的个人恩宠，从 {{balance:GodFavorMin}} 到 {{balance:GodFavorMax}}，决定你能获得多少这位神明的恩赐。

{{table:gods}}

## 在神殿选择一位神明

1. 在主街按 T 前往神殿。使用街区布局时，先按 G 打开公会街街区，再按 T。神殿会在你最初几级之后出现在菜单中。
2. 按 A 进入众神正殿。
3. 按 W，选择「信奉一位神明，或改换你的神明」。
4. 祭坛会列出。输入神明的名字，或名字的一部分，并在询问你是否确定时按 Y 确认。在列表处按回车即可取消。
5. 游戏会提示你现在已是信徒。每天在正殿按 Y 祈祷，以积累[恩宠](/wiki/zh/gods/favor/)。

地下堂（在神殿各厅按 U）有自己的一套 W，只列出黑暗祭坛。玩家神明与神殿众神出现在同一份祭坛列表中。想了解玩家如何成神，以及不朽者做些什么，请阅读[不朽者、玩家神明与万神殿](/wiki/zh/gods/player-gods/)。

## 更换或离开你的神明

在正殿使用同一个 W。游戏会显示你当前的神明，并询问你是否已经失去信仰。按 Y 回答，可以选择给你的旧神明留一封信，然后从列表中选择新神明。若想不留神明，直接在列表处按回车即可。

更换神明会丢弃你在旧神明那里的全部恩宠，而你在新神明处从 0 开始。游戏会在确认前显示代价。由游戏或其他玩家造成的更换，例如玩家神明招募你，不会带来额外代价。

### 如果我更换神明会怎样

离开一位神殿神明会按你损失的恩宠记录神怒：损失 1 到 24 点恩宠为 1 级，25 到 49 点为 2 级，50 点或以上为 3 级。带着 0 点恩宠离开则不会记录。你已背负的神怒会累加，最多到 3 级。

离开一位玩家神明则立刻招来一记神雷，伤害为你最大生命值的 {{percent:GodSmiteMinPercent}} 到 {{percent:GodSmiteMaxPercent}}，具体取决于你损失的恩宠：10% 加上每点恩宠 0.15%。带着 60 点恩宠离开会损失 19% 的最大生命值。神雷绝不会把你的生命降到 1 以下，带着 0 点恩宠离开则不会遭到雷击。

## 地牢中的神怒

神怒会在地牢战斗开始前降临。每次战斗开始时，每级神怒有 20% 的触发几率：即 20%、40% 或 60%。

- **1 级：** 只显示神明的怒火，别无其他。
- **2 级：** 你失去当前生命值的四分之一，但不会低于 1。
- **3 级：** 你失去当前生命值的一半，但不会低于 1，同时失去一半法力；有一半的几率陷入失明，或染上瘟疫或麻疹。

随后，在这场战斗中，你的普通挥击造成的伤害降低 10%、20% 或 30%，你对怪物攻击的防御也降低 10%、20% 或 30%，正如屏幕所示。神怒降临之后，3 级降至 1 级，1 级与 2 级则被清除。

未降临的神怒会逐渐消退：每次战斗开始时若未触发，计数会从 50 + 20 × 上次记录的等级开始递减，降到 0 时等级降低一级，计数从 30 重新开始。

## 培养关系

关于阶位、虔诚、结界与神迹，请参阅[恩宠、祈祷与献祭](/wiki/zh/gods/favor/)。每位神明的单独页面会列出该神明生成的恩赐常量、善行与禁忌。
阅读[每种恩赐的作用](/wiki/zh/gods/boons/)与[每日神迹](/wiki/zh/gods/miracles/)，了解它们在战斗与奖励中的实际作用。

神殿的排名描述的是一个不断变化的世界，而不是本 wiki 中一成不变的表格。玩家神明的领域使用相同的标准领域机制，但另有额外的强度与活跃度规则。
