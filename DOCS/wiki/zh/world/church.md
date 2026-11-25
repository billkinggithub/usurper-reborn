---
title: 旧教堂
path: /wiki/zh/world/church/
checked: 1.3.14
sources: Scripts/Locations/ChurchLocation.cs, Scripts/Systems/GodDeedSystem.cs, Scripts/Systems/AlignmentSystem.cs, Scripts/Systems/RelationshipSystem.cs, Scripts/Systems/FactionSystem.cs, Scripts/Systems/MentalSystem.cs, Scripts/Core/Character.cs, Scripts/Core/GameConfig.cs
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | 当黑暗超过侠义的 3 倍时，教堂的阵营行显示为魔性；超过 2 倍时显示为非常邪恶；其余情况显示为邪恶。
history: 1.3.9 | 主街默认以经典布局开放，分区布局可在设置中选择。教堂的婚姻步骤会列出你所使用的主街布局对应的按键。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | 教堂祝福文本不再承诺持续多少天。
history: 1.2.5 | 教堂界面和 Electron 教堂菜单会以所有五种语言显示，过长的拒婚消息在 79 列处换行。
---
教堂与神殿不同。教堂菜单提供捐献（C）、购买祝福（B）、治疗服务、婚姻、忏悔（F）、记录以及与主教交谈（S）。

## 为什么我不能进入教堂

教堂会拒绝邪恶阵营的角色，以及黑暗超过 600 的黑暗阵营角色。其他所有阵营都可以进入。阵营的说明见[阵营](/wiki/zh/characters/stats/)。

## 向教堂捐献能得到什么

一次捐献会给予金币 / 11 的侠义，从 1 点起，最多为 {{balance:MaxChivalryGainPerChurchAction}} 点；使你的黑暗降低 1 点；并给予金币 / 100 的信仰声望，至少 1 点，没有上限。275 金币会给予 25 点侠义和 2 点信仰声望。捐献不是献给你所信奉神明的供品，不会给予恩宠。

## 教堂祝福能消除多少黑暗

购买的祝福至少需要 1 点黑暗。它会给予金币 / 15 的侠义，从 1 点起，最多为 {{balance:MaxChivalryGainPerChurchAction}} 点；消除金币 / 100 的黑暗（至少 1 点，且绝不超过你现有的黑暗）；并给予金币 / 75 的信仰声望，至少 1 点。1,000 金币会给予 25 点侠义、消除 10 点黑暗，并给予 13 点信仰声望。祝福没有战斗效果，也没有持续时间：它所做的就是这三项改变。

如果完全没有黑暗，且侠义至少为 {{balance:FreeBlessingMinRenownChivalry}}，那么请求祝福会改为每天给予一次免费祝福，这同样不会在战斗中产生任何效果。

## 教堂治疗收费多少

基础价格为 50 x 你的等级 + 100 金币；当你的侠义高于黑暗时乘以 0.8，当你的黑暗超过侠义的两倍时乘以 1.5，但绝不低于 50。

- 恢复全部 HP：基础价格的一半。
- 失明、天花或麻疹：基础价格。
- 瘟疫：基础价格的两倍。
- 麻风，或同时患有全部疾病：基础价格的三倍。

20 级且侠义高于黑暗时，基础价格为 880，因此恢复全部 HP 需要 440 金币。

## 忏悔要花多少钱

忏悔至少需要 1 点黑暗，费用为 {{balance:ConfessionBaseCost}} + {{balance:ConfessionCostPerDarkness}} x 你的黑暗金币：300 点黑暗时为 1,600 金币。它会消除 5 到 10 点黑暗，增加 2 到 5 点侠义，并每天恢复一次 {{balance:MentalConfessionGain}} 点精神；黑暗和侠义在每次忏悔时都会改变，精神只有当天第一次忏悔才会恢复。乌姆布拉思将忏悔视为禁忌。背负[血债](/wiki/zh/world/law/)的角色随后会被提供血之赦免。

## 主教做什么

当你的侠义超过黑暗的两倍时，与主教交谈有 25% 的概率使你获得 5 点侠义。当你的黑暗超过侠义的两倍时，他有 30% 的概率主动提出忏悔。没有每日次数限制。

## 婚礼要花多少钱

教堂婚礼的标准仪式花费 {{balance:MarriageCost}} 金币，隆重仪式 2,000 金币，皇家仪式 5,000 金币；更昂贵的仪式不会多给任何东西。婚礼会使你获得 10 点侠义，并永久给予 5 点魅力。双方都必须年满 18 岁且未婚，你们必须至少亲密过一次，双方都必须相爱，必须已经在一起 7 个游戏日，并且 NPC 必须答应。如果婚姻失败，金币会退还。

NPC 接受的概率为 50% + 20 x 其浪漫度 + 15 x 其承诺度 - 10 x（1 - 承诺度）- 8 x（1 - 浪漫度），加上你的魅力 / 4（最多 15），再加上在一起天数的一半（最多 15），最终限制在 20% 到 95% 之间。婚姻可以是阿玛拉的善举，也可以是迪斯科尔迪亚的禁忌。见[关系](/wiki/zh/world/relationships/)和[家与家人](/wiki/zh/world/home/)。
