---
title: 游玩方式
path: /wiki/zh/getting-started/connections/
checked: 1.3.14
sources: README.md, DOCS/BBS_DOOR_SETUP.md, DOCS/SERVER_DEPLOYMENT.md, web/index.html
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | 游玩页面在每种语言的 Enter 画面上显示 Continue 键，以彩色绘制 256 色和真彩色美术，显示完整的主街文本，在右侧页面超出窗口时添加滚动条，并为写作 (E)quip 或 (P)ray、(D)esecrate 或 (L)eave 的选项提供按键按钮；除非设置了 WEB_BIND_HOST，否则 Web 服务只监听回环地址。
history: 1.3.10 | Docker 页面会链接到 /play/ 的游玩页面。
history: 1.3.9 | 网站的 Play 按钮会打开 /play/ 的游玩页面，那是一个整页终端，在手机上有触控板，提供 Classic 页面或 Chronicle 书页视图的 View 选项，登录前也可用，还有单键菜单，默认开启，可在 Settings 中用 E 更改。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | none
history: 1.3.1 | none
history: 1.3.0 | none
history: 1.2.7 | none
history: 1.2.6 | none
history: 1.2.5 | SSH 登录菜单有 G，可以在登录前更改其画面的语言。
history: 1.2.4 | 重连会等待旧会话保存完毕，之后你仍会保留在 /who、/tell、群组和广播中。
history: 1.2.3 | none
---
## 浏览器与 SSH

[网站的 Play 区](/#connect)提供连接信息，其 Play 按钮会在新标签页中打开浏览器终端，即 /play/ 的游玩页面。浏览器显示的是同一个文字游戏；游玩期间请保持标签页打开。连接地址应放在网站上，而不是放在这份带版本的规则参考中。

SSH 客户端是访问托管游戏的另一种方式。请使用服务器运营者公布的连接说明。连接断开并不等于选择退出，因此请重新连接并检查你的角色，然后再继续。在线时，重连会等待你的旧会话保存完毕（通常不到一秒），然后才载入你的角色，并且你会保持在线状态。

## 本地单人游戏

从[项目发布页](https://github.com/binary-knight/usurper-reborn/releases)下载一个版本，并使用为你的平台提供的启动器。本地存档与托管的在线角色是分开的。

## BBS door

BBS 运营者可以使用 dropfile 集成，把游戏作为 door 运行。玩家通过该 BBS 的 door 菜单进入；运营者应使用仓库中的 [BBS 设置指南](https://github.com/binary-knight/usurper-reborn/blob/v1.2.0/DOCS/BBS_DOOR_SETUP.md)。

## 易读菜单

当网格或装饰性的终端布局让导航变得困难时，请使用游戏的屏幕阅读模式。请阅读当前的提示，尤其是在更改菜单呈现方式或在城区之间移动时。
