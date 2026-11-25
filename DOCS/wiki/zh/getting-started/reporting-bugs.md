---
title: 报告缺陷
path: /wiki/zh/getting-started/reporting-bugs/
checked: 1.3.11
sources: Scripts/Systems/BugReportSystem.cs, Scripts/Locations/BaseLocation.cs
history: 1.3.11 | none
history: 1.3.10 | none
history: 1.3.9 | none
history: 1.3.5 | none
history: 1.3.2 | none
history: 1.3.0 | none
history: 1.2.7 | none
history: 1.2.5 | 缺陷报告画面的标题会以你的语言显示。
history: 1.2.4 | none
history: 1.2.3 | none
---
发现了缺陷？有两种报告方式：游戏内的缺陷报告，或项目 GitHub 页面上的 issue。两者都会送达开发者。

## 在游戏中报告缺陷

在命令可用的任何画面上按 `!` 或输入 `/bug`。`/report` 和 `/bugreport` 的作用相同。

1. 游戏会要求你简要描述缺陷。写下发生了什么，以及你原本期望发生什么。
2. 按 Enter 提交。要取消，则在空行上按 Enter。
3. 游戏会收集诊断信息，保存一份报告副本，并通过篡位者重生网站发送给开发者。

随后画面会告诉你报告是否已发送。如果无法发送，例如没有网络连接，或在没有网络访问的 BBS 上，保存的副本会留在这台机器上，以便站长转发。

## 报告包含什么

除了你的描述，报告还会自动附带以下信息：

- 游戏版本。
- 你的平台：操作系统和处理器类型。
- 你的游玩方式：Steam、BBS door、在线或本地。
- BBS 名称，当你通过 BBS door 游玩时。
- 你角色的名称、等级、种族和职业。
- 你在游戏中的位置，以及你在地牢中时的地牢楼层。
- 游戏调试日志的最后几行。

保存的副本还会列出发布名称、报告日期和时间，以及你角色的当前和最大生命值与总游玩时间。它会被写入游戏旁边的 `bug_reports` 文件夹。不会附带任何存档文件或账号数据。

## 在 GitHub 上打开 issue

你也可以在 GitHub 上的[篡位者重生 issue 跟踪器](https://github.com/binary-knight/usurper-reborn/issues)打开 issue。这需要一个免费的 GitHub 账号。请包含：

- 游戏版本，显示在标题画面上。
- 导致缺陷的步骤，按顺序列出。
- 你原本期望发生什么，以及实际发生了什么。
- 有帮助的话，截图或复制的画面文本。

GitHub 上的 issue 是公开的。不要发布密码、电子邮件地址或其他个人详细信息。

## 写出好报告的技巧

- 每份报告只报告一个缺陷。
- 给出确切的步骤：你在哪里、按了哪些键、选择了什么。
- 始终包含游戏版本。
- 说明缺陷是每次都会发生，还是只是有时发生。
