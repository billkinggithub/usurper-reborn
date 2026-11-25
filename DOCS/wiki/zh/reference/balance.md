---
title: 平衡规则
path: /wiki/zh/reference/balance/
checked: 1.3.14
sources: Scripts/Core/GameConfig.cs, Scripts/Systems/GameDataLoader.cs, Scripts/Data/BalanceConfig.cs, Scripts/Systems/WikiDataExporter.cs, Scripts/Systems/StatEffectsSystem.cs, Scripts/Systems/CombatEngine.cs
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
history: 1.3.2 | 不再列出六个没有任何游戏代码读取的平衡数值。
history: 1.3.1 | none
history: 1.3.0 | none
history: 1.2.7 | none
history: 1.2.6 | none
history: 1.2.5 | none
history: 1.2.4 | none
history: 1.2.3 | none
---
可修改的默认值从发行版的平衡模型中导出。服务器可以在自己的平衡文件中覆盖它们，而单个常量并不是每条战斗路径的完整公式。有六个没有任何游戏代码读取的平衡数值被略去：旧的暴击几率与暴击倍率、背刺与狂怒倍率、末日倒计时，以及坦克在范围伤害中的分担比例。

暴击没有单一的几率或倍率：几率来自敏捷与装备，伤害来自敏捷，详见[暴击](/wiki/zh/combat/)。背刺的三倍伤害在游戏中固定，服务器无法更改。

高级折叠区块包含精确的战斗、信仰与精神常量。字段名保留来源标识，以便核对。

{{table:balance}}

构建期间会跨所有数据集校验模式与生成的游戏版本。[实体页面](/wiki/zh/)为各项定义提供背景，但并不保证每个字段都适用于每一场战斗。
