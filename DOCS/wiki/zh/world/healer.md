---
title: 治疗师
path: /wiki/zh/world/healer/
checked: 1.3.14
sources: Scripts/Locations/HealerLocation.cs, Scripts/Systems/FactionSystem.cs, Scripts/Systems/MentalSystem.cs, Scripts/Core/GameConfig.cs, Scripts/Core/Character.cs, Scripts/Systems/CityControlSystem.cs, Scripts/Locations/MainStreetDistricts.cs, Scripts/Locations/MainStreetClassic.cs
history: 1.3.14 | none
history: 1.3.13 | none
history: 1.3.12 | none
history: 1.3.11 | 信仰会成员在治疗师的每项价格上都少付 15% 到 35%，治疗师界面不再显示它从未实际采用的阵营或世界事件价格行。
history: 1.3.10 | 圣雨降临时，在治疗师处恢复 HP（H 和 F）免费且免税，菜单行在任何语言下也不再挤在一起。
history: 1.3.9 | 主街默认以经典布局开放，分区布局可在设置中选择。
history: 1.3.8 | none
history: 1.3.7 | none
history: 1.3.6 | none
history: 1.3.5 | none
history: 1.3.4 | none
history: 1.3.3 | none
history: 1.3.2 | none
history: 1.2.5 | 治疗师的 Electron 菜单标签，以及移除诅咒时显示的诅咒物品名称，都会使用玩家的语言。
---
治疗师处理的不只是缺失的 HP。先判断你需要伤口治疗、补给、治愈疾病、戒瘾康复还是精神治疗。在主街按 1 前往治疗师。使用分区布局时，按 G 打开公会街，然后按 H。

## 治疗师恢复 HP 的费用

治疗师以每点 HP 2 金币的价格恢复 HP，另加税。H 恢复你选择的量；F 将你治疗至满。圣雨世界事件持续期间，两者都免费，且免税。

## 治疗师的税

治疗师的每项价格都会加上国王税和城市税，但无论统治者把税率设得多高，两者合计上限为 15%。没有统治者时没有税。治疗师的价格不会随你的阵营或难度变化。信仰会成员按等级在每项治疗师价格上少付 15% 到 35%，这是税前减免，菜单会显示他们实际支付的价格：成员在阶位 0 时 HP 单价为 1.7 金币，在阶位 8 时为 1.3 金币。总额按四舍五入（.5 进位），所以小额费用可能略不同于单价 x HP：1.65 金币单价下的 1 点 HP 会花费 2 金币。其他人的价格不变，圣雨免费的项目仍然免费。

## 药剂与解毒剂

- B，治疗药剂：每瓶 100 + 等级 × 等级 / 2 金币，20 级时为 300。你可以携带 20 +（等级 - 1）瓶。
- M，法力药剂：每瓶 150 + 等级 × 等级 / 2 金币，20 级时为 350，恢复 30 + 等级 × 5 点法力。你可以携带 20 +（等级 - 1）瓶。
- N，解毒剂：每瓶 75 金币。你可以携带 5 + 等级 / 10 瓶，向下取整。

全部为税前价格。见[药剂、草药与补给](/wiki/zh/items/consumables/)。

## 治愈费用

治愈费用为基础价格乘以（1 + 等级的 0.6 次方），另加税。20 级时系数约为 7.03，50 级时约为 11.46，100 级时约为 16.85。

- P，中毒：基础 200，因此 20 级时为 1,406 金币。
- C，疾病：情人之灾 1,000，失明 1,500，瘟疫 2,000，天花 2,500，麻疹 3,000，麻风 3,500。你可以治愈一种或全部。
- D，你穿戴的诅咒物品：基础 500。治疗师会摧毁该物品；[魔法商店](/wiki/zh/items/shops/)会移除诅咒并保留物品。

## 谈话治疗

治疗会恢复精神并清除崩溃。费用取决于缺失的精神、你的等级和治疗师的税。处于崩溃状态的角色即使普通恢复已经提高了精神，也仍有一笔最低费用。

确认前请查看报价和携带的金币。治疗可以把精神提高到成瘾上限之上，但多出的部分不会永久移除上限。

## 戒瘾康复

戒瘾康复（A）花费 {{balance:RehabBaseCost}} 金币，加上每点成瘾 {{balance:RehabPerAddictionCost}} 金币，另加税。它只向已成瘾的角色提供。它会清除成瘾、取消待发的药劲崩溃、重置耐受，并同时清除崩溃。如果你没有成瘾，谈话治疗才是通常的崩溃疗法。

## 柳叶药剂

柳叶药剂（W）是供地牢使用的独立补给。它恢复 {{balance:MentalWillowDraughtGain}} 点精神，直到你的上限，但不恢复 HP。它的价格相当于你当前等级下 {{balance:MentalWillowPotionMultiplier}} 瓶治疗药剂，另加税：20 级时税前为 600 金币。你可以携带 {{balance:MaxWillowDraughts}} 瓶。

完整的恢复规则见[精神](/wiki/zh/characters/mental/)。
