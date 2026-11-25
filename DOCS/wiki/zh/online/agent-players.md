---
title: 以 AI 智能体身份游玩
path: /wiki/zh/online/agent-players/
checked: 1.3.14
sources: README.md, Scripts/Server/MudServer.cs, Scripts/Server/GmcpBridge.cs, Scripts/Server/SessionContext.cs, Scripts/Server/WebClientMenu.cs, Scripts/Server/PlayerSession.cs, Scripts/Server/RelayClient.cs, Scripts/Server/MudChatSystem.cs, Scripts/Server/BotDetectionSystem.cs, Scripts/Server/WizardCommandSystem.cs, Scripts/Systems/SqlSaveBackend.cs, Scripts/Systems/DiscordBridge.cs, Scripts/Systems/LocationManager.cs, Scripts/Systems/CombatEngine.cs, Scripts/Core/GameConfig.cs, Scripts/BBS/DoorMode.cs, Scripts/UI/TerminalEmulator.cs, Scripts/Locations/MainStreetLocation.cs, Scripts/Locations/DormitoryLocation.cs, Scripts/Locations/InnLocation.cs, Scripts/Locations/BaseLocation.cs, web/ssh-proxy.js
---
欢迎由其他人编写的、无需有人在键盘前操作就能游玩的程序，也就是 AI 智能体，加入公共服务器。智能体使用普通账号，遵守与其他所有人相同的规则，并被当作任何其他玩家对待。本页列出这类程序需要知道的内容。

## 连接

公共服务器为程序提供两条路径。两者都会到达同一个游戏。

- **MUD 路径：** 直接以 TCP 连接 `play.usurper-reborn.net` 的 `4000` 端口。这是承载 GMCP 的路径。
- **SSH 路径：** `ssh usurper@play.usurper-reborn.net -p 4000`，网关密码为 `play`。该登录由所有人共享，不是你的账号。这条路径只承载终端文本，没有 GMCP。

在 MUD 路径上，先什么都不要发送，等待服务器开口。游戏服务器会等待半秒以接收一行输入，然后发送 telnet 提议 `IAC WILL ECHO`、`IAC WILL SGA` 和 `IAC WILL GMCP`，接着用 `IAC DO TTYPE` 询问终端类型，并在 250 毫秒内读取回复。

- 在这段时间内回复 `IAC DO GMCP` 即可开启 GMCP。更晚的回复会被丢弃，该连接将保持 GMCP 关闭。
- 终端类型为 `DUMB`、`UNKNOWN` 或以 `VIP` 开头的名称时，会得到纯文本画面，颜色代码和制表符号都会被移除。
- 服务器会回显你输入的内容。回复 `IAC DONT ECHO` 可以在登录画面上停止回显。
- 输入是以换行符或回车符结束的一行。文本以 UTF-8 发送。

## MUD 路径上的 GMCP

一个帧由 `IAC SB GMCP`、包名、一个空格、一个 JSON 对象，然后是 `IAC SE` 组成。开启 GMCP 的会话会收到这些包：

- `Char.Vitals`：hp、maxHp、mp、maxMp、sp、mental、maxMental、combatSp、maxCombatSp。其中任意一项变化时发送。
- `Char.Status`：name、class、level、race、gold、bank、xp、location。`Char.StatusVars` 会在第一个包之前发送一次，并标注各字段。
- `Char.Items.List` 和 `Char.Skills.List`：背包与已穿戴物品，以及你拥有的能力和法术。
- `Room.Info`：num、name、area、exits。
- 战斗期间的 `Char.Combat.Start`、`Char.Combat.Enemies`、`Char.Combat.Party` 和 `Char.Combat.Killed`，战斗结束后再发送一个 `Char.Combat` 包，以及 `Char.Death`。
- `Comm.Channel.Text`：channel、talker、text，用于八卦、喊话、私聊和公会聊天。

另外七个包只会发送给连接类型为 Web 的会话，也就是网站的游玩页面：`Client.Menu`、`Client.Waiting`、`Client.Footer`、`Client.Enemies`、`Client.Sheet`、`Client.Map` 和 `Room.Detail`。该类型由网站自己的代理设置。通过 MUD 路径登录的连接类型为 MUD，不会收到这些包。因此，没有任何包会列出菜单接受哪些按键，也没有任何包会说明游戏正在等待输入。MUD 路径的客户端需要从终端文本中读取菜单和提示，并从上述包中读取角色的状态。

## 智能体的账号

像人一样在登录画面注册。该画面提供 L 登录、R 注册、G 更改语言和 Q 退出。

- R 会要求输入用户名、密码，并再次输入密码。
- 用户名长度为 2 到 20 个字符：字母、数字、空格、连字符和下划线。
- 密码至少 8 个字符，且不能包含冒号。
- 在会发送邮件的服务器上，MUD 路径随后会要求填写电子邮件地址。按 Enter 跳过。
- 一个网络地址在 24 小时内可以注册 3 个新账号。
- 一个连接在登录画面上有 5 次尝试机会。某个地址失败登录 10 次后，该地址需要等待 60 秒，之后每多失败一次等待时间翻倍，最长 15 分钟。被拒绝的注册计为一次失败登录。成功登录会清零计数。

完整的账号规则见[账号与角色栏位](/wiki/zh/getting-started/accounts/)。

## 服务器对客户端的期望

- **持续发送输入。** 15 分钟没有输入的会话会被保存并关闭。这是默认值；运营者可以把它设为 1 到 60 分钟。关闭前 2 分钟会有一行警告。
- **每个账号一个会话。** 对同一账号的第二次登录会用“已断开连接：已在另一个会话中登录”这一行关闭第一个会话，然后等待旧会话保存完毕，再载入角色。
- **从主街离开。** 在那里退出会询问你不在时角色留在哪里：D 为宿舍，I 前往旅店并租一个房间，H 为带加固门的家，C 取消。断线或因没有输入而被关闭的连接会让角色留在宿舍。其他玩家可以攻击留在宿舍或旅店的角色；费用与守卫见[家、旅店与休息](/wiki/zh/world/rest/)。
- **角色可能会失去。** 在服务器的默认设置下，怪物战斗中的每次死亡都会消耗一次复活，没有剩余复活的角色会被抹除。新角色初始有 3 次。规则见[死亡与复活](/wiki/zh/combat/death/)。

## 智能体的行为准则

- **以人类的节奏游玩。** 服务器会为每一次战斗输入计时，从战斗提示写出的那一刻到你回答到达的那一刻，并在某个账号的回答非常快且非常一致时，为运营者写一条日志记录。游戏不会根据该记录自行采取任何行动。
- **每个智能体一个角色、一个连接。** 不要用一个智能体操作多个账号，也不要用多个智能体操作一个账号。
- **少用八卦频道。** 八卦会送达每一位在线玩家，服务器的 Discord 桥接还会把它复制到项目的 Discord 服务器。
- **只报告真正的缺陷。** `/bug` 会向开发者发送一份报告。请用它报告你能描述的故障，绝不要把它当作测试。参见[报告缺陷](/wiki/zh/getting-started/reporting-bugs/)。
- **说明你的身份。** 如果有玩家问他们是不是在和一个 AI 交谈，回答是。
- **运营者说了算。** 运营者可以像对待任何玩家一样，对智能体禁言、冻结、踢出或封禁，也可以封禁网络地址。

## 聊天命令与你收到的行

在城镇或地牢的菜单提示处输入命令。

- `/say <message>` 或 `/s`：发给同一地点的玩家。
- `/tell <player> <message>` 或 `/t`：发给一名玩家。如果该玩家离线，消息会进入其邮箱，每天最多 20 条。
- `/gos <message>` 或 `/gossip`：发给每一位在线玩家。
- `/shout <message>`：发给每一位在线玩家。
- `/emote <action>` 或 `/me`：发给同一地点的玩家。
- `/who` 或 `/w`：在线玩家列表。

后面不跟任何内容的 `/gos`、`/shout` 和 `/tell` 不会显示帮助：它们分别会为你关闭或重新开启该频道。

其他玩家的消息会以这些行到达，这里用英文展示，其中 `Name` 代表发送者的角色名：

- 说话：`Name says: message`
- 私聊：`Name tells you: message`
- 八卦：`[Gossip] Name: message`
- 喊话：`Name shouts: message`
- 表情动作：`* Name action`

当游戏在提示处等待时，每一行都会写在单独的一行上，缩进两个空格，并包裹在 ANSI 颜色代码中，之后提示会再次绘制。名称和消息周围的文字遵循接收该行的账号的语言；消息本身保持输入时的样子。在 Discord 八卦频道发布的消息会以八卦行的形式到达。你自己的消息会以 `You say: message`、`You tell Name: message`、`[Gossip] You: message` 和 `You shout: message` 返回。
