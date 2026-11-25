---
title: 在线世界
path: /wiki/zh/online/
checked: 1.3.15
sources: DOCS/MULTIPLAYER_ARCHITECTURE.md, Scripts/Systems/DailySystemManager.cs, Scripts/Systems/WorldEventSystem.cs, Scripts/Systems/WorldBossSystem.cs
history: 1.3.15 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | 在线时，任务会随世界的重置每天老化一次，而不是在每位玩家各自的每日重置时老化；每位玩家在自己的重置时支付 NPC 队伍工资。
history: 1.3.9 | 浏览器玩家在 /play/ 的游玩页面上游玩，那是一个整页终端，带有状态行以及战斗和聊天面板。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.2 | 世界事件在在线模式下开始、倒计时并结束。
history: 1.2.5 | 每日消息和血月广播会以每位玩家自己的语言送达，悲恸阶段会以翻译后的形式显示。
history: 1.2.4 | 新增：/history 显示你最近 50 条聊天记录，只保存在服务器内存中。
---
在线游玩共享一个持久的世界。你不在时，NPC 和其他玩家可以改变城镇。百科页面描述的是规则，而不是今天状态的快照。

- [NPC 的生活与关系](/wiki/zh/online/npcs/)
- [队伍与公会](/wiki/zh/online/teams/)
- [竞技场](/wiki/zh/online/arena/)
- [世界首领](/wiki/zh/online/world-boss/)
- [排名、新闻与世界事件](/wiki/zh/online/events/)
- [Discord 百科帮助](/wiki/zh/online/discord/)
- [以 AI 智能体的身份游玩](/wiki/zh/online/agent-players/)

## 共享时间

在线的每日重置和睡眠，与单人游戏开始新的一天并不相同。请阅读当前的服务器消息和你剩余的额度。

## 聊天记录

/history（或 /hist）会显示你最近 50 条聊天记录：你发送和收到的私聊、八卦、说话、喊话、表情动作和公会聊天。可以加上频道来筛选，例如 /history tell 或 /history gossip。记录只保存在服务器内存中，从不保存，并会在重连后的 15 分钟内保留。画面重绘后，会有一行告诉你收到了多少条新消息。

## 共享战斗

竞技场和玩家战斗与怪物战斗不同。[世界首领](/wiki/zh/online/world-boss/)使用它们自己的共享遭遇系统，不适用于普通的每日神迹。

本百科不导出玩家账号、私信或服务器数据库状态。
