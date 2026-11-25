---
title: 专精
path: /wiki/zh/characters/specializations/
checked: 1.3.15
sources: Scripts/Locations/LevelMasterLocation.cs, Scripts/Data/SpecializationData.cs, Scripts/Systems/CombatEngine.cs, Scripts/Systems/ClassAbilitySystem.cs, Scripts/Core/GameConfig.cs
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
history: 1.3.4 | 盾墙阵和神圣谕令，连同它们的防护与守护加成，现在也能对抗曼威的具名技能。
history: 1.3.3 | none
history: 1.3.2 | none
history: 1.3.1 | none
history: 1.3.0 | none
history: 1.2.5 | 专精名称会在等级大师处和维基上以玩家语言显示。
---
对于定义了选项的职业，专精会在等级大师处从 {{balance:SpecializationUnlockLevel}} 级起开放。第一次选择免费；之后更改需要 {{balance:SpecializationRespecCost}} 枚金币。

## 变化内容

专精会在此后每次升级时增加额外的属性成长，并提供少量战斗加成。它不会追溯重建角色此前的等级，也不会教授任何新技能或法术。请围绕你想要的定位来选择，例如伤害、治疗、辅助或坦克。

每个[职业页面](/wiki/zh/characters/classes/)都会列出其专精描述、定位和每级加成。列表为空意味着导出器没有找到为该职业定义的专精；这并不表示缺少翻译。

## 治疗专精

神圣（圣骑士）、恢复（牧师）、秘法（贤者）、游吟歌手（吟游诗人）、药剂师（炼金术士）和灵行（秘术萨满）是治疗专精。它们会使你的技能和法术治疗量提高 20%，但对秘术萨满的治疗图腾、灵魂链接图腾和先祖指引无效。

## 坦克专精

每个坦克专精都会强化其职业的一项 40 级坦克技能：

- 防护（战士）：盾墙阵将受到的伤害降低 40%，而不是 30%。
- 守护（圣骑士）：神圣谕令反射 20% 的伤害，而不是 15%。
- 铁壁（野蛮人）：狂暴挑战每回合恢复 8% 的最大生命，而不是 5%。

装备盾牌时，防护会使每个职业技能的伤害提高 20%，守护则提高 15%。装备盾牌的守护还会使技能治疗量提高 15%。铁壁没有盾牌加成。

## 队友

NPC 队友的专精还会引导其战斗选择：某些专精会让它不使用某类技能，设定盟友受伤到什么程度它才会治疗，并决定它是否担任队伍的治疗或坦克。

## 切换之前

查看显示的价格，并确认新定位适合你使用的武器、护甲和行动。定位名称描述的是一种预期风格，并不保证每场战斗都适合它。
