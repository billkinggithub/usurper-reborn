---
title: 职业
path: /wiki/zh/characters/classes/
checked: 1.3.15
sources: Scripts/Core/GameConfig.cs, Scripts/Locations/LevelMasterLocation.cs, Scripts/Core/Character.cs, Scripts/Core/Items.cs, Scripts/Core/EquipmentEnums.cs, Scripts/Data/SpecializationData.cs, Scripts/Data/EquipmentData.cs, Scripts/Systems/CombatEngine.cs, Scripts/Systems/ClassAbilitySystem.cs, Scripts/Systems/SpellSystem.cs, Scripts/Systems/PotionBonus.cs, Scripts/Systems/LootGenerator.cs, Scripts/Systems/ShopItemGenerator.cs, Scripts/Systems/TrainingSystem.cs, Scripts/Locations/HomeLocation.cs, Scripts/Locations/TeamCornerLocation.cs
history: 1.3.15 | none
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | none
history: 1.3.10 | 职业预览会为全部 17 个职业显示肖像。
history: 1.3.9 | none
history: 1.3.8 | none
history: 1.3.7 | 虚空掠夺者每级获得 1.5 点体质，已有的虚空掠夺者也补发了其等级本应给予的属性；虚空饥渴与噬魂者在每次击杀时生效，腐化收割在每次击杀中毒目标时生效，且都在战斗过程中结算；损失一级会从深渊守望者身上扣回 3 点体质，正如升一级会给予的那样。
history: 1.3.6 | NPC 吟游诗人队友现在会提供吟游灵感，可以鼓舞你，但绝不会鼓舞自己；职业技能与法术的描述现在会说明各自的效果。
history: 1.3.5 | 破轮者的闪避只会挡下瞄准破轮者本人的怪物攻击，不会挡下瞄准同伴的攻击；轮回倒转恰好治疗最大生命的 30%；石咬武器与死亡的拥抱的描述现在会说明它们的效果。
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | 战士、刺客、野蛮人、圣骑士、游侠和秘术萨满的战斗加成会在战斗中生效；秘术萨满遵循自己的装备规则，并在每回合恢复法力；进阶职业的法术初始为普通熟练度。
history: 1.3.1 | none
history: 1.3.0 | none
history: 1.2.7 | none
history: 1.2.6 | none
history: 1.2.5 | 角色创建时的职业帮助界面和等级大师的各个界面都会以全部五种语言显示。
history: 1.2.4 | none
history: 1.2.3 | none
---
选择职业时，应根据你想采取的行动来选，而不只是看它的初始数值。请在各职业页面上比较每级成长和专精选项。

本目录区分初始职业与进阶职业。初始可选性仍然取决于种族：秘术萨满仅限巨魔、兽人和豺狼人。进阶职业通过游玩在 NG+ 中解锁，不是普通首次创建角色时的选择。

{{table:classes}}

## 成长与资源

创建数值是职业在种族加成和其他角色创建规则之前的贡献。生成的成长表是升级时职业的基础增量；专精、训练、装备和其他奖励另计。

表中的每级 HP、防御和法力，是一级为该职业的基础数值增加的量。它们包含每个职业每级获得的 5 点最大生命、1 点防御和 1 点体力。

虚空掠夺者的体质成长交替进行：升到偶数等级时 +2，升到奇数等级时 +1，平均每级 1.5。

实际的资源消耗与效果见[技能](/wiki/zh/characters/abilities/)和[法术](/wiki/zh/characters/spells/)。

## 法力职业

有九个职业拥有法力：牧师、魔法师、贤者、秘术萨满、潮誓者、唤潮者、破轮者、深渊守望者和虚空掠夺者。其余八个职业，炼金术士、刺客、野蛮人、吟游诗人、小丑、圣骑士、游侠和战士，最大法力为 0，只能以[战斗体力](/wiki/zh/characters/stats/#战斗体力)支付技能消耗。秘术萨满的图腾和附魔消耗法力，而不是体力。

## 职业定位：坦克、嘲讽、治疗与伤害

游戏并不给职业排名。它只为专精命名定位（输出、坦克、治疗、辅助或削弱），并且，对五个进阶职业而言，还在一份固定的列表里命名定位，用于按定位查找 NPC。下面各节给出每个职业的数值。

### 哪些职业能当坦克

雷霆咆哮是第一个嘲讽：20 级，消耗 40 点体力，供战士、圣骑士、野蛮人和潮誓者使用。它会让每个活着的怪物转而攻击你，持续 3 回合，每回合每只怪物都有 {{balance:SoftTauntStickChance}}% 的几率继续锁定你。40 级的嘲讽（盾墙阵、神圣谕令、狂暴挑战）以及潮誓者的暗流姿态和深渊之锚，都以相同的 {{balance:SoftTauntStickChance}}% 几率维持。永恒守望则始终维持。

每个职业在战斗中还有基础的嘲讽动作。它会让一只怪物转而攻击你，持续 2 回合，始终维持，并使该怪物的防御降低 3、护甲威力降低 2。

首领的范围攻击会寻找一名坦克。如果某位队友握有首领的嘲讽，该队友就是坦克；如果是你握有，那你就是坦克。完全没有嘲讽时，战士、圣骑士、野蛮人或潮誓者玩家仍会被视为坦克。此时其他人受到的范围攻击伤害降低 60%，坦克受到的伤害则提高 30%。没有坦克时，所有人承受全额伤害。

对 NPC 队友而言，战士、圣骑士和野蛮人职业算作队伍坦克，坦克[专精](/wiki/zh/characters/specializations/#坦克专精)也算。

### 哪些职业能治疗

有六个专精拥有治疗定位：神圣（圣骑士）、恢复（牧师）、秘法（贤者）、游吟歌手（吟游诗人）、药剂师（炼金术士）和灵行（秘术萨满）。每个专精都会使技能与法术的治疗量提高 {{percent:HealerSpecHealBonus}}%，但对秘术萨满的治疗图腾、灵魂链接图腾和先祖指引无效。游戏为进阶职业列出的定位名单中，唤潮者被列为治疗。另有四个职业无论专精为何，技能治疗量都更高：见下文的职业被动。

### 各职业的定位数值

{{table:class-roles}}

## 职业被动

职业被动对该职业始终生效。任何等级、专精或物品都不会给予其他职业的被动。

### 药剂精通（炼金术士）

药剂精通使炼金术士使用的每一瓶治疗药剂多恢复 {{percent:AlchemistPotionMasteryBonus}}% 的生命。只有炼金术士拥有它。

- 技能：炼金术士的技能治疗量提高 {{percent:AlchemistPotionMasteryBonus}}%。这项加成会加到护盾治疗加成上，而不是与它相乘。
- 治疗草药：对炼金术士而言，它恢复 37.5% 的最大生命，而不是 {{percent:HerbHealPercent}}%。
- 其他草药：效果持续时间变为 1.5 倍，向下取整：由 {{balance:HerbBuffDuration}} 场战斗变为 7 场，疾风蓟则由 {{balance:HerbSwiftDuration}} 场变为 4 场。

### 奥术精通（魔法师）

奥术精通使魔法师的法术伤害乘以 {{balance:MagicianArcaneSpellBonus}}。见[法术如何成长](/wiki/zh/characters/spells/)。

### 神恩（牧师）

神恩使牧师来自法术和技能的治疗量提高 {{percent:ClericDivineGraceBonus}}%。

### 神圣决心（圣骑士）

神圣决心使圣骑士以普通攻击或强力攻击对亡灵和恶魔造成的伤害提高 {{percent:PaladinDivineResolveDamageBonus}}%，并有 {{percent:PaladinDivineResolveStatusResist}}% 的几率抵抗怪物试图施加的每个负面状态。

### 吟游灵感（吟游诗人）

吟游诗人每次使用技能后，都有 {{balance:BardInspirationChance}}% 的几率触发吟游灵感：一名随机的存活同伴或 NPC 队友获得 {{balance:BardInspirationAttackBonus}} 点攻击力，持续至少 {{balance:BardInspirationDuration}} 回合。若没有这样的队友，则不会产生效果。吟游诗人盟友的技能也有相同的几率，并且吟游诗人盟友可以鼓舞你或其他盟友，绝不会鼓舞自己。

### 诡术师之运（小丑）

小丑的每次普通攻击都有 {{balance:JesterTrickstersLuckChance}}% 的几率触发诡术师之运。随后会出现三种结果之一，每种结果的几率相同：该次挥击的攻击力提高 {{percent:JesterLuckBonusDamage}}%，闪避下一次针对你的攻击，或返还 {{balance:JesterLuckStaminaRefund}} 点战斗体力。

### 致命精准（刺客）

致命精准作用于刺客的普通攻击。主手匕首造成暴击时，额外附加该次挥击攻击力的 {{percent:AssassinLethalPrecisionCritBonus}}%；对带有中毒状态的怪物挥击时，则额外附加 {{percent:AssassinLethalPrecisionPoisonBonus}}%（仅有武器毒素不算）。

### 元素精通（秘术萨满）

秘术萨满的武器附魔会把出手那只手的武器威力的一部分加到每次命中上：{{percent:ShamanEnchantBaseDamage}}% 加上每点智力 {{percent:ShamanElementalMastery}}%，最高不超过 {{balance:ShamanEnchantPowerCap}}%。智力为 80 时，该比例为 100%。一项附魔持续 {{balance:ShamanEnchantDuration}} 回合，一个图腾持续 {{balance:ShamanTotemBaseDuration}} 回合。见[图腾](/wiki/zh/characters/abilities/)。

### 海洋祝福与海洋坚韧（潮誓者）

海洋祝福使潮誓者技能的治疗量提高 {{percent:TideswornOceansBlessingBonus}}%。拥有海洋坚韧时，你在每个战斗回合结束时恢复最大生命的 {{percent:TideswornOceansResiliencePercent}}%，生命低于一半时再多 {{percent:TideswornOceansResilienceBelowHalfBonus}} 个百分点，且至少恢复 1 点生命。

### 谐波共鸣与海洋之声（唤潮者）

谐波共鸣使唤潮者技能的治疗量提高 {{percent:WavecallerHarmonicResonanceBonus}}%。拥有海洋之声时，只要你持有攻击加成，一次未造成暴击的普通攻击或技能就会获得第二次判定，有 {{percent:WavecallerOceansVoiceCritBonus}}% 的几率将其变为暴击。当唤潮者带有反射状态时，对它造成伤害的怪物会受到该伤害 {{percent:WavecallerReflectionPercent}}% 的反伤。

### 概率操纵与轮回记忆（破轮者）

概率操纵使破轮者有 {{balance:CyclebreakerPassiveEvadePercent}}% 的几率闪避每一次瞄准它的怪物攻击，且每次攻击都会单独判定；同时有 {{percent:CyclebreakerDebuffResistChance}}% 的几率抵抗每个减益。轮回记忆会按你已完成的轮回数，使击杀怪物获得的经验提高 {{percent:CyclebreakerCycleXPBonus}}%，最多 {{percent:CyclebreakerCycleXPBonusCap}}%。在第一轮中，它不提供任何加成。

### 深渊虹吸、典狱长坚韧与腐化收割（深渊守望者）

深渊虹吸会为深渊守望者恢复每次命中伤害的 {{percent:AbysswardenAbyssalSiphonPercent}}% 的生命，至少 1 点，且受游戏吸血上限限制。拥有典狱长坚韧时，怪物的命中造成的伤害降低 {{percent:AbysswardenPrisonWardResist}}%。腐化收割会为每只在死亡时处于中毒状态的怪物恢复 {{percent:AbysswardenCorruptionHealPercent}}% 的最大生命，在每只中毒怪物倒下时于战斗中即时结算。

### 虚空饥渴、噬魂者与痛觉阈值（虚空掠夺者）

拥有虚空饥渴时，每击杀一只怪物都会为虚空掠夺者恢复最大生命的 {{percent:VoidreaverVoidHungerPercent}}%；拥有噬魂者时，还会恢复最大法力的 {{percent:VoidreaverSoulEaterManaPercent}}%。两者都在每只怪物倒下时于战斗中即时结算。痛觉阈值使你在生命低于一半时，技能造成的伤害提高 {{percent:VoidreaverPainThresholdBonus}}%。当虚空掠夺者带有反射状态时，对它造成伤害的怪物会受到该伤害 {{percent:VoidreaverReflectionPercent}}% 的反伤。

### 职业的逃跑加成

游侠或刺客会使逃离怪物战斗的几率提高 15，小丑或吟游诗人则提高 10。完整的几率说明见[敏捷](/wiki/zh/characters/stats/#力量-敏捷与灵巧)。

### 职业战斗加成

有六个职业在每场战斗中都有加成。该加成对你以及该职业的队友或同伴都有效；背刺、惩击和狂怒按键由你使用。

- **战士：** 每次普通挥击都会把等级 / 5 加到攻击力上：10 级时 +2，100 级时 +20。
- **刺客：** 刺客对怪物命中的每次近战攻击都有 5% 的几率使其中毒 3 回合，除非它已经中毒。这不会来自法术、魔法技能、远程技能，也不会来自手持弓的挥击。只有刺客能[背刺](/wiki/zh/combat/)。
- **野蛮人与秘术萨满：** 怪物的普通攻击造成的伤害降低 2，但不会低于最小值；其特殊能力仍造成全额伤害。野蛮人可以使用[狂怒](/wiki/zh/combat/)。
- **圣骑士：** 只要队伍中有一名活着的圣骑士，怪物命中你所需的骰点就增加 2，队友和同伴的防御也增加 2；两名圣骑士不会叠加。圣骑士每天有 1 + 等级 / 10 次[惩击](/wiki/zh/combat/)充能。
- **游侠：** 用弓挥击、弓类技能和远程攻击的伤害各增加 4。

### 打断首领的引导

只有同伴或 NPC 队友会尝试打断正在引导的首领；你自己不进行判定。该队友需要灵巧加上其敏捷的一半至少达到 {{balance:BossChannelInterruptSpeedThreshold}}。此时几率为 {{percent:BossChannelInterruptChance}}%，若其为刺客或游侠再加 20 个百分点，若为虚空掠夺者则加 15。

## 各职业装备：护甲重量、武器与盾牌

一件物品可能受等级、力量、阵营、职业列表限制，护甲还会受重量限制。槽位本身见[装备槽位](/wiki/zh/items/equipment-slots/)。

### 护甲重量

每个职业都有自己能穿的最重护甲重量：轻型、中型或重型。下表逐职业列出该限制，并在其上标出每种护甲类型的重量。

### 霍比特人或侏儒能穿重型护甲吗

霍比特人和侏儒无论是什么职业，都不能穿重型护甲。进阶职业是例外。

### 穿重型护甲所需的力量

一件自身没有力量要求的重型护甲，需要 15 点力量加上该物品等级的五分之一，向下取整。50 级的装备需要 25 点。

### 各职业可用的武器与盾牌

有一条规则把武器类型与职业绑定：秘术萨满的主手只能握剑、斧、钉头锤、战锤、连枷或大槌。其他所有限制都来自职业列表，这些列表同样约束秘术萨满。商店存货和地牢战利品背后的武器与盾牌模板，各自带有职业列表，或对所有职业开放。表中针对每个职业和每种类型，统计该职业在该类型全部模板中可用的模板数量。弓不计入：模板中有一套游侠专用弓和一套全职业通用弓，且有四个名称同时出现在两者中。

进阶职业会跳过所有职业列表和护甲重量限制。

手写的基础物品，也就是拥有独立[物品页面](/wiki/zh/items/weapons/)的那些，不带职业列表。限制它们的只有等级、力量、阵营和护甲重量，秘术萨满的主手规则同样适用于它们。

{{table:class-equipment}}

{{table:weapon-templates}}
