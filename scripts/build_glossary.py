#!/usr/bin/env python3
"""从用户已确认的种子记录生成冻结术语数据与确认记录。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "glossary" / "terms.json"
DECISION_OUTPUT = ROOT / "data" / "glossary" / "decision-record.json"
INITIAL_DECISION_ID = "terminology-freeze-2026-08-04"
REVISION_DECISION_ID = "terminology-revision-2026-08-29"
BASELINE_TERMS_SHA256 = "04b09feb9f5c9d526828e330cd5b993a22bbb8f53a0e8c3136a4cf42166d3f17"
FILLED_WORKBOOK_SHA256 = "417bac075dbcea8e752773ad0e3cbb4effab22cfa94a9b781a8f0dc552f1d1f9"

terms: list[dict[str, object]] = []


def anchor(part: str, page: int, rule: str) -> dict[str, object]:
    return {"part": part, "pdf_page": page, "rule": rule}


def add(
    term_id: str,
    category: str,
    zh: str,
    ja: str,
    aliases: list[str],
    strict: str,
    plain: str,
    anchors: list[dict[str, object]],
    sources: list[str],
    *,
    confidence: str = "medium",
    status: str = "review",
    impact: str = "medium",
    conflict: str = "",
) -> None:
    unique_sources = list(dict.fromkeys(["pdf-1.14.1", *sources]))
    terms.append(
        {
            "id": term_id,
            "category": category,
            "recommended_zh": zh,
            "ja": ja,
            "aliases": aliases,
            "strict_definition": strict,
            "plain_explanation": plain,
            "anchors": anchors,
            "evidence": [
                {"source_id": source_id, "role": "推荐名、别名或用法证据"}
                for source_id in unique_sources
            ],
            "confidence": confidence,
            "review_status": status,
            "impact": impact,
            "conflict_note": conflict,
        }
    )


# 项目与对局概念
add("game.shinmaku", "project_concept", "散樱乱武 新幕", "新幕 桜降る代に決闘を", ["新幕散樱乱武", "散樱乱武"], "本综合规则所规制的一局《新幕 桜降る代に決闘を》游戏。", "本项目翻译的游戏及规则版本名称。", [anchor("core", 2, "1-1")], ["pdf-1.14.1", "steam-radiant-duels-zh-hans"], confidence="high", impact="high")
add("game.dual-palm-selection", "project_concept", "双掌缭乱", "双掌繚乱", [], "双方各自选择并公开两柱编号不同的女神的步骤。", "开局先选两位女神。", [anchor("core", 2, "2-1")], ["pdf-1.14.1", "steam-radiant-duels-zh-hans"], confidence="high", impact="high")
add("game.frontline-deckbuilding", "project_concept", "眼前构筑", "眼前構築", ["眼前组牌"], "从所宿女神的可用牌中秘密选择七张通常牌和三张王牌的步骤。", "看到双方女神后现场组出十张牌。", [anchor("core", 3, "3-1")], ["pdf-1.14.1", "steam-radiant-duels-zh-hans"], confidence="high", impact="high")
add("game.sakura-duel", "project_concept", "樱花决斗", "桜花決闘", ["樱花对决"], "完成双掌缭乱与眼前构筑后，依核心规则进行胜负判定的对战阶段。", "真正打牌并决出胜负的部分。", [anchor("core", 3, "4-1")], ["pdf-1.14.1", "steam-radiant-duels-zh-hans"], confidence="high", impact="high", conflict="社区亦见“樱花对决”；推荐名沿用受监修项目的“樱花决斗”。")
add("actor.goddess", "project_concept", "女神", "メガミ", ["柱"], "女神列表所列、可与卡牌使用者及追加规则关联的游戏要素。", "玩家选择并借用力量的角色。", [anchor("core", 2, "2-1")], ["pdf-1.14.1", "steam-radiant-duels-zh-hans"], confidence="high")
add("actor.mikoto", "project_concept", "尊者", "ミコト", ["御子"], "世界观中能够借用女神力量进行樱花决斗的人。", "对局中玩家所扮演的决斗者身份。", [anchor("core", 2, "1-2")], ["steam-radiant-duels-zh-hans", "bilibili-community-guides"], confidence="high")
add("object.sakura-crystal", "project_concept", "樱花结晶", "桜花結晶", ["樱花指示物"], "在各区域之间移动、用以表示距离、防护、生命和费用等数值的实体对象。", "版图上流转的花瓣资源。", [anchor("core", 12, "6-3")], ["pdf-1.14.1", "steam-radiant-duels-zh-hans"], confidence="high", impact="high")

# 区域与资源
add("zone.distance", "region_resource", "距离", "間合", ["距", "间合"], "共有区域＜間合＞中樱花结晶的数量及由此表示的当前距离。", "中间有几颗结晶，当前距离就是几。", [anchor("core", 15, "7-1-1")], ["steam-radiant-duels-zh-hans", "bilibili-community-guides", "fandom-faq-zh"], confidence="high", impact="high", conflict="旧译和日式玩家口语常保留“间合”；受监修简中项目使用“距离”。")
add("zone.life", "region_resource", "命", "ライフ", ["生命", "血", "自命"], "与玩家关联的＜ライフ＞区域及其中结晶数；满足规则条件时决定败北。", "玩家的生命值。", [anchor("core", 15, "7-1-2")], ["bilibili-community-guides", "old-cr-translation-2022"], confidence="medium", impact="high")
add("zone.aura", "region_resource", "装", "オーラ", ["护盾", "自装"], "与玩家关联的＜オーラ＞区域，通常承受攻击的装伤害。", "先替命挡伤害的防护区。", [anchor("core", 15, "7-1-3")], ["bilibili-community-guides", "fandom-faq-zh"], confidence="medium", impact="high")
add("zone.flare", "region_resource", "气", "フレア", ["能量", "自气"], "与玩家关联的＜フレア＞区域，主要用于支付王牌的消耗。", "发动王牌时花费的能量。", [anchor("core", 15, "7-1-4")], ["bilibili-community-guides", "fandom-faq-zh"], confidence="medium", impact="high")
add("zone.dust", "region_resource", "虚", "ダスト", ["弃晶区", "尘"], "双方共有的＜ダスト＞区域，容纳未处于其他区域的游戏内樱花结晶。", "结晶流转时常汇入、再从中取出的公共池。", [anchor("core", 15, "7-1-5")], ["bilibili-community-guides", "old-cr-translation-2022"], confidence="medium", impact="high")
add("zone.draw-pile", "region_resource", "牌库", "山札", ["山札", "抽牌堆"], "与玩家关联、由背面朝上的通常牌按顺序构成的＜山札＞区域。", "每回合从这里抽牌。", [anchor("core", 16, "7-1-6")], ["bilibili-community-guides", "fandom-faq-zh"], confidence="high", impact="high")
add("zone.discard", "region_resource", "弃牌区", "捨て札", ["弃牌", "捨札"], "与玩家关联、通常放置已使用且表面朝上的通常牌的＜捨て札＞区域。", "打过的通常牌正面朝上放这里。", [anchor("core", 16, "7-1-7")], ["bilibili-community-guides", "fandom-faq-zh"], confidence="high")
add("zone.covered", "region_resource", "盖牌区", "伏せ札", ["伏牌区", "盖牌"], "与玩家关联、通常放置表面朝下的通常牌的＜伏せ札＞区域。", "作为动作代价盖掉或被效果盖伏的牌放这里。", [anchor("core", 16, "7-1-8")], ["bilibili-community-guides", "fandom-faq-zh"], confidence="high")
add("zone.enchantment", "region_resource", "付与牌区", "付与札", ["付与区", "付与札"], "放置正在展开的付与牌及其纳的＜付与札＞区域。", "持续生效的付与牌摆放区。", [anchor("core", 17, "7-1-9")], ["fandom-faq-zh", "old-cr-translation-2022"], confidence="medium", impact="high", conflict="“付与札”既可被理解为牌也可被理解为区域；推荐加“牌区”消歧。")
add("zone.hand", "region_resource", "手牌", "手札", ["手札"], "与玩家关联、由该玩家持有且通常仅自己可见的＜手札＞区域。", "拿在手里、可以使用或盖伏的牌。", [anchor("core", 17, "7-1-10")], ["bilibili-community-guides", "fandom-faq-zh"], confidence="high")
add("zone.trump", "region_resource", "王牌区", "切札", ["切札区"], "与玩家关联、放置其王牌并记录未使用或使用后状态的＜切札＞区域。", "三张王牌所在的区域。", [anchor("core", 17, "7-1-11")], ["steam-radiant-duels-zh-hans", "fandom-faq-zh"], confidence="medium")
add("zone.extra", "region_resource", "追加牌区", "追加札", ["追加区", "追加札"], "放置眼前构筑不能直接选用、由追加规则或效果带入的卡牌的＜追加札＞区域。", "衍生牌和专用牌的备用区。", [anchor("core", 18, "7-1-12")], ["pdf-1.14.1", "old-cr-translation-2022"], confidence="medium")
add("zone.sealed", "region_resource", "封印区", "封印", ["封印"], "放置被封印卡牌的＜封印＞区域；其公开性与移动依核心规则处理。", "被封印的牌暂时放这里。", [anchor("core", 18, "7-1-13")], ["bilibili-keywords-2024", "pdf-1.14.1"], confidence="medium")
add("zone.in-use", "region_resource", "使用中", "使用中", ["使用中区"], "卡牌使用与效果结算期间暂时存在的＜使用中＞区域。", "一张牌正在结算时所在的位置。", [anchor("core", 18, "7-1-14")], ["pdf-1.14.1", "old-cr-translation-2022"], confidence="high")
add("zone.attack-in-progress", "region_resource", "攻击中区", "攻撃中", ["攻击中", "攻击处理区"], "与玩家关联、在攻击生成与结算期间暂时容纳攻击对象的＜攻撃中＞区域。", "一次攻击正在处理时所在的区域。", [anchor("core", 18, "7-1-15")], ["pdf-1.14.1"], confidence="low", status="provisional", impact="high", conflict="底本可确定区域语义，但未取得可复核简中用名；“攻击中区”“攻击处理区”与直留“攻击中”均需裁决。")
add("zone.out-of-game", "region_resource", "游戏外", "ゲーム外", ["移出区", "除外区"], "不属于通常对局内区域流转、由规则指定放置对象的＜ゲーム外＞区域。", "暂时不在正常游戏区域中的对象。", [anchor("core", 18, "7-1-16")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="high")
add("resource.vigor", "region_resource", "集中力", "集中力", ["专注力"], "玩家持有、通常在 0 至 2 之间，用于执行基本动作的公开数值。", "不盖牌时，用它支付基本动作。", [anchor("core", 4, "5-1-2")], ["bilibili-community-guides", "fandom-faq-zh"], confidence="high")
add("range.mastery", "region_resource", "达人距离", "達人の間合", ["达人距", "近身距离", "达人间合"], "当前距离不大于规则阈值时成立的状态，影响前进与离脱。", "贴得足够近时进入的特殊距离状态。", [anchor("core", 6, "5-2-2")], ["bilibili-keywords-2024", "bilibili-community-guides", "old-cr-translation-2022"], confidence="medium", impact="high", conflict="社区常说“达人距”，旧注称官中曾用“近身距离”；推荐“达人距离”兼顾原义与可读性。")

# 卡牌分类、信息与数值
add("card.card", "card_type", "卡牌", "カード", ["牌"], "女神列表所列、由实体卡片表示的卡牌对象。", "构筑和对局中使用的牌。", [anchor("core", 2, "1-3")], ["steam-radiant-duels-zh-hans", "bilibili-community-guides"], confidence="high")
add("card.deck", "card_type", "牌组", "デッキ", ["卡组", "套牌"], "玩家在眼前构筑中选出的七张通常牌和三张王牌的总称。", "本局带入的十张牌。", [anchor("core", 6, "5-3")], ["steam-radiant-duels-zh-hans", "bilibili-community-guides"], confidence="medium", impact="high", conflict="Steam 同页同时使用“牌组”和“卡组”；推荐“牌组”，将“卡组”保留为检索别名。")
add("card.normal", "card_type", "通常牌", "通常札", ["通常札", "普通牌"], "分类为通常札、参与牌库重铸和抽牌循环的卡牌。", "会洗回牌库循环使用的七张牌。", [anchor("core", 10, "6-2-1-1")], ["bilibili-community-guides", "fandom-goddess-pages-zh"], confidence="medium", impact="high", conflict="Fandom 表格常直接保留“通常札”；推荐“通常牌”以符合简中习惯。")
add("card.trump", "card_type", "王牌", "切札", ["切札", "大招"], "分类为切札、通常支付消耗后使用并记录使用状态的卡牌。", "构筑时选三张、花费气使用的强力牌。", [anchor("core", 10, "6-2-1-1")], ["steam-radiant-duels-zh-hans", "fandom-faq-zh"], confidence="high", impact="high")
add("card.type.attack", "card_type", "攻击", "攻撃", ["红牌"], "卡牌类型《攻撃》，使用时生成攻击对象并依攻击流程结算。", "造成装或命伤害的牌型。", [anchor("core", 10, "6-2-1-5")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("card.type.action", "card_type", "行动", "行動", ["蓝牌"], "卡牌类型《行動》，依行动牌使用步骤结算文本。", "直接执行效果的牌型。", [anchor("core", 10, "6-2-1-5")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("card.type.enchantment", "card_type", "付与", "付与", ["绿牌", "赋予"], "卡牌类型《付与》，放入付与牌区并以纳上的结晶维持展开。", "会留在场上一段时间、持续生效的牌型。", [anchor("core", 10, "6-2-1-5")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high", impact="high", conflict="“赋予”更现代，但社区与旧规则长期使用“付与”；推荐保留专名。")
add("card.type.undefined", "card_type", "不定", "不定", [], "卡牌类型《不定》，其实际使用方式由规则或效果决定。", "需要看额外规则才知道怎么用的牌型。", [anchor("core", 10, "6-2-1-5")], ["pdf-1.14.1"], confidence="high")
add("card.subtype.response", "card_type", "对应", "対応", ["响应", "康"], "卡牌副类型《対応》，可在规则允许的攻击对应窗口中使用。", "对手攻击时可以打出的响应牌。", [anchor("core", 11, "6-2-1-6")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high", impact="high")
add("card.subtype.full-power", "card_type", "全力", "全力", ["全力牌"], "卡牌副类型《全力》，其使用受主要阶段与全力行动规则限制。", "通常会占掉主要阶段大部分行动机会的强牌。", [anchor("core", 11, "6-2-1-6")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("card.cost", "card_type", "消耗", "消費", ["费用", "cost"], "王牌持有的数值信息，通常以从气移出相同数量结晶的方式支付。", "打出王牌要花多少气。", [anchor("core", 11, "6-2-1-12")], ["pdf-1.14.1", "fandom-faq-zh"], confidence="medium")
add("card.capacity", "card_type", "纳", "納", ["献", "容纳值"], "付与牌所持、决定展开时放置多少樱花结晶的数值信息。", "付与牌能放几颗结晶，也大致决定能维持多久。", [anchor("core", 11, "6-2-1-11")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="medium", impact="high", conflict="旧注称既有官中曾用“献”，当前社区普遍使用“纳”；建议采用“纳”。")
add("attack.proper-range", "card_type", "攻击距离", "適正距離", ["适正距离", "适当距离", "射程"], "攻击对象持有的距离集合；结算时当前距离属于该集合才视为距离适正。", "这次攻击在哪些距离能命中。", [anchor("core", 13, "6-4-1-3")], ["bilibili-community-guides", "old-cr-translation-2022"], confidence="medium", impact="high", conflict="直译可作“适正距离”，旧译作“适当距离”；社区解释长期使用“攻击距离”。")
add("attack.damage", "card_type", "伤害", "ダメージ", ["打点"], "攻击对象持有的装伤害／命伤害二元值，或规则定义的单一值伤害。", "攻击写成 X/Y 时，前者打装、后者打命。", [anchor("core", 8, "5-8")], ["bilibili-community-guides", "fandom-faq-zh"], confidence="high")

# 效果分类
add("effect.rule-based", "effect_class", "规则上效果", "ルール上効果", ["规则效果"], "由综合规则或追加规则直接定义、并由规则赋予游戏的效果分类。", "不是写在某张牌上，而是规则本身给出的效果。", [anchor("core", 21, "9-1-1-1")], ["pdf-1.14.1"], confidence="high")
add("effect.constant", "effect_class", "常时", "常時", ["持续"], "只要其来源与规则条件有效便持续适用的【常時】效果。", "满足条件时一直生效。", [anchor("core", 21, "9-1-1-2")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="high")
add("effect.on-use", "effect_class", "使用时", "使用時", [], "卡牌被使用时按规则时点进入待解决流程的【使用時】效果。", "打出这张牌时触发。", [anchor("core", 22, "9-1-1-3")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="high")
add("effect.after-attack", "effect_class", "攻击后", "攻撃後", [], "攻击结算完毕后按规则时点解决的【攻撃後】效果。", "这次攻击处理完后触发。", [anchor("core", 22, "9-1-1-4")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("effect.on-deploy", "effect_class", "展开时", "展開時", [], "付与牌进入付与牌区并完成展开时解决的【展開時】效果。", "付与牌刚放上场时触发。", [anchor("core", 22, "9-1-1-5")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("effect.while-deployed", "effect_class", "展开中", "展開中", [], "付与牌在付与牌区展开期间持续适用的【展開中】效果。", "这张付与牌留在场上时一直生效。", [anchor("core", 22, "9-1-1-6")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("effect.on-discard", "effect_class", "破弃时", "破棄時", ["破弃", "弃置时"], "付与牌因纳耗尽而从付与牌区破弃时解决的【破棄時】效果。", "付与牌结束并离场时触发。", [anchor("core", 22, "9-1-1-7")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="medium", impact="high", conflict="“破弃”是社区专名但不够口语；“弃置时”易与一般弃牌混淆。")
add("effect.while-used", "effect_class", "使用后", "使用済", ["已使用"], "仅当其来源王牌处于使用后状态时才会被参照的【使用済】效果。", "王牌开过以后持续或按条件生效的效果。", [anchor("core", 22, "9-1-1-8")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")

# 阶段与动作
add("phase.beginning", "phase_action", "开始阶段", "開始フェイズ", ["准备阶段", "开始阶段"], "回合的第一个阶段，依 8-1 顺序处理开始阶段步骤。", "每回合最先进行重铸、抽牌等处理的阶段。", [anchor("core", 19, "8-1")], ["fandom-faq-zh", "old-cr-translation-2022"], confidence="medium", impact="high", conflict="社区 FAQ 常用“准备阶段”，旧译与日文直译为“开始阶段”；建议规范正文使用“开始阶段”。")
add("phase.main", "phase_action", "主要阶段", "メインフェイズ", ["主阶段"], "开始阶段后、结束阶段前，玩家执行基本动作或使用卡牌的阶段。", "回合中主要操作和出牌的阶段。", [anchor("core", 20, "8-2")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("phase.ending", "phase_action", "结束阶段", "終了フェイズ", ["结束阶段"], "主要阶段后，按 8-3 处理结束阶段步骤并结束回合的阶段。", "回合收尾、处理结束触发的阶段。", [anchor("core", 20, "8-3")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("action.standard", "phase_action", "标准行动", "標準行動", ["普通行动"], "主要阶段开始时可选的行动方式；可反复使用非全力牌或进行基本动作，直至主动或被效果结束主要阶段。", "普通回合模式，可以连续出牌和做基本动作。", [anchor("core", 20, "8-2-2 A")], ["pdf-1.14.1", "fandom-faq-zh"], confidence="high")
add("action.full-power", "phase_action", "全力行动", "全力行動", ["全力回合"], "主要阶段开始时可选的行动方式；使用一张手牌或未使用王牌并完成相关效果后结束主要阶段。", "选择全力模式后通常只做一次出牌行动。", [anchor("core", 20, "8-2-2 B")], ["pdf-1.14.1", "fandom-faq-zh"], confidence="high")
add("action.basic", "phase_action", "基本动作", "基本動作", [], "规则列举的前进、后退、装附、聚气及满足条件时的离脱。", "花 1 集中力或盖 1 张牌来做的五种基础操作。", [anchor("core", 27, "9-6")], ["bilibili-community-guides", "fandom-faq-zh"], confidence="high")
add("action.advance", "phase_action", "前进", "前進", [], "基本动作：按规则将一枚樱花结晶从距离移至自己的装。", "拉近距离并补一装。", [anchor("core", 28, "9-6-1")], ["bilibili-keywords-2024", "bilibili-community-guides"], confidence="high")
add("action.retreat", "phase_action", "后退", "後退", [], "基本动作：按规则将一枚樱花结晶从自己的装移至距离。", "花一装把距离拉远。", [anchor("core", 28, "9-6-2")], ["bilibili-keywords-2024", "bilibili-community-guides"], confidence="high")
add("action.ward", "phase_action", "装附", "纏い", ["缠绕", "装付"], "基本动作：按规则将一枚樱花结晶从虚移至自己的装。", "从虚补一装。", [anchor("core", 28, "9-6-3")], ["bilibili-keywords-2024", "bilibili-community-guides"], confidence="high", impact="high", conflict="社区同时出现“装附”和“装付”；建议用“装附”，与区域简称“装”及附着含义一致。")
add("action.channel", "phase_action", "聚气", "宿し", ["蓄气", "宿"], "基本动作：按规则将一枚樱花结晶从自己的装移至自己的气。", "把一装转成一气。", [anchor("core", 28, "9-6-4")], ["bilibili-keywords-2024", "bilibili-community-guides"], confidence="high")
add("action.disengage", "phase_action", "离脱", "離脱", [], "处于达人距离时取代前进的基本动作，按规则将一枚结晶从虚移至距离。", "贴身时用来把距离拉开一格。", [anchor("core", 28, "9-6-5")], ["bilibili-keywords-2024", "bilibili-community-guides"], confidence="high")
add("action.reconstruct", "phase_action", "重铸牌库", "山札の再構成", ["牌库重铸", "牌库重组", "洗牌"], "若由规则生成，先令该玩家的命承受 1 点伤害；再将其弃牌区与盖牌区的全部通常牌移入牌库并洗牌。", "把弃牌和盖牌洗回牌库；规则强制重铸时还会损失命。", [anchor("core", 29, "9-7")], ["bilibili-keywords-2024", "fandom-faq-zh", "old-cr-translation-2022"], confidence="high", impact="high", conflict="“牌库重组”更直译；两项独立社区来源共同使用“重铸牌库”。")
add("resolution.nested", "phase_action", "嵌套结算", "入れ子解決", ["入嵌结算"], "某效果解决期间发生另一效果时，先完整解决后发生的效果，再返回原效果。", "结算中又触发新东西时，先把里面那层做完。", [anchor("core", 29, "9-8")], ["pdf-1.14.1", "old-cr-translation-2022"], confidence="medium", impact="high")

# 通用规则关键字与状态
add("state.flinched", "rule_keyword", "畏缩", "畏縮", ["畏缩状态"], "玩家可持有的公开状态；畏缩玩家将要获得集中力时，改为解除畏缩。", "下次本该获得集中力时，先用来解除这个状态。", [anchor("core", 4, "5-1-4")], ["bilibili-keywords-2024", "pdf-1.14.1"], confidence="high")
add("state.unused", "rule_keyword", "未使用状态", "未使用", [], "王牌可持有、允许其按通常条件使用的状态。", "这张王牌还可以开。", [anchor("core", 12, "6-2-2-3")], ["fandom-faq-zh", "old-cr-translation-2022"], confidence="high")
add("state.in-use", "rule_keyword", "使用中状态", "使用中", ["结算中"], "王牌从被使用到完成相应移动前可持有的中间状态。", "这张王牌正在结算。", [anchor("core", 12, "6-2-2-3")], ["pdf-1.14.1", "old-cr-translation-2022"], confidence="high")
add("state.used", "rule_keyword", "使用后状态", "使用済", ["已使用", "使用完毕"], "王牌在王牌区内可能具有的已使用状态，与未使用状态相对。", "这张王牌本局已经开过，暂时不能再用。", [anchor("core", 12, "6-2-2-3")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="medium", impact="high", conflict="社区把状态简称为“使用后”，但该词也像时点；建议数据与正文写“使用后状态”。")
add("rule.owner", "rule_keyword", "所有者", "保有者", ["保有者", "持有者"], "规则为每张卡牌确定的归属玩家；区域移动等规则可据此引用与该玩家关联的区域。", "这张牌在规则上属于谁。", [anchor("core", 6, "5-4")], ["pdf-1.14.1", "old-cr-translation-2022"], confidence="medium", impact="high", conflict="旧译为“保有者”；“持有者”易误解为当前拿在手中的玩家，建议用“所有者”。")
add("rule.object", "rule_keyword", "对象", "オブジェクト", ["游戏对象"], "卡牌、樱花结晶和攻击等在规则中可持有信息和状态的事物总称。", "规则会追踪信息和状态的东西。", [anchor("core", 10, "6-1")], ["old-cr-translation-2022", "pdf-1.14.1"], confidence="high")
add("rule.information", "rule_keyword", "信息", "情報", ["情报"], "规则可由玩家、对象或区域持有并被公开或隐藏的属性。", "游戏需要记录或查看的属性。", [anchor("core", 10, "6-2-1")], ["old-cr-translation-2022", "pdf-1.14.1"], confidence="medium", impact="high", conflict="旧译用“情报”；简中规则文体通常用“信息”。")
add("rule.zone", "rule_keyword", "区域", "領域", ["领域"], "对象在樱花决斗中可以存在、并由规则定义其容纳对象与状态的位置。", "牌或结晶能待的规则位置。", [anchor("core", 14, "7-1")], ["fandom-faq-zh", "old-cr-translation-2022"], confidence="high")
add("rule.impatience", "rule_keyword", "焦躁", "焦燥", ["焦燥"], "抽牌时牌库为空所引发的状态触发处理；承受装 1／命 1 的伤害，并依伤害规则从中选择。", "没牌可抽时受到的一次 1/1 牌库耗尽惩罚。", [anchor("core", 7, "5-5-3"), anchor("core", 32, "10-10")], ["fandom-faq-zh", "old-cr-translation-2022"], confidence="medium", impact="high", conflict="日文原词写作“焦燥”；简中社区使用常用字形“焦躁”。推荐正文用“焦躁”，保留原词供检索。")
add("rule.situation-based", "rule_keyword", "状态触发处理", "状況起因", ["状况起因", "状态触发"], "不由玩家选择发动、在规则条件成立时依优先顺序自动检查并解决的处理。", "条件一满足就自动检查并处理的规则事件。", [anchor("core", 6, "5-5")], ["pdf-1.14.1", "old-cr-translation-2022"], confidence="low", status="provisional", impact="high", conflict="旧译“状况起因”生硬；“状态触发处理”更清晰，但尚无高等级简中证据。")
add("rule.full-power-augmentation", "rule_keyword", "全力化", "全力化", [], "效果持有的信息；含该信息的效果仅在卡牌通过全力行动使用时有效。", "用全力行动打牌时才开启的增强文本。", [anchor("core", 22, "9-1-2")], ["pdf-1.14.1", "fandom-faq-zh"], confidence="high")
add("keyword.gap", "rule_keyword", "破绽", "隙", ["隙"], "付与牌持有的展开中效果：其所有者受到非牌库重铸来源的至少 1 点命伤害时，将该牌盖伏，再把牌上的全部樱花结晶移至虚。", "挂着这张付与时一旦命受伤，它会立即盖伏并失去上面的结晶。", [anchor("core", 31, "10-6")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("keyword.overwhelm", "rule_keyword", "超克", "超克", [], "使攻击的装伤害不受通常装上限替代规则限制的关键字。", "大装伤不能只用满装挡住。", [anchor("core", 34, "10-21")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="high")
add("keyword.terminal", "rule_keyword", "终端", "終端", ["终止"], "带有终端的卡牌结算后，其使用者在该回合不能再使用其他卡牌或进行基本动作。", "处理完它后，本回合不能再出牌或做基本动作。", [anchor("core", 24, "9-2（卡牌使用后的终端处理）")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="high")
add("keyword.unrespondable", "rule_keyword", "不可对应", "対応不可", ["不可被对应", "不可对"], "攻击持有的常时效果；对该攻击使用对应牌时，不能选择符合括号内指定信息的牌，“不可对应”是“不可对应（全部）”的略记。", "括号写了哪类牌，对手就不能用那类对应牌；不带括号时全部禁用。", [anchor("core", 34, "10-22")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="medium", impact="high", conflict="社区常说“不可被对应”；推荐标签式“不可对应”，句中可依语法写“不可被对应”。")
add("keyword.unavoidable", "rule_keyword", "不可闪避", "不可避", ["不可避", "锁定"], "攻击持有的规则信息；在对应窗口之后，该攻击直接视为成功，不再重新检查当前距离是否属于攻击距离。", "不能靠对应后跳出攻击距离来躲掉。", [anchor("core", 27, "9-4 ⅲ")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="medium", impact="high", conflict="旧注称既有官中用“锁定”，社区也用“不可避／不可闪避”；推荐语义透明的“不可闪避”。")
add("keyword.recover", "rule_keyword", "再起", "再起", [], "王牌持有的使用后效果；在所有者的结束阶段满足牌面条件时，将该牌变为未使用。", "结束阶段达成条件，就能把王牌重新开一次。", [anchor("core", 31, "10-7")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("keyword.immediate-recover", "rule_keyword", "即再起", "即再起", [], "王牌持有的使用后效果；牌面条件成立时立即将该牌变为未使用。", "条件一满足，王牌马上恢复。", [anchor("core", 31, "10-8")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("keyword.arrow", "rule_keyword", "箭头效果", "矢印効果", ["箭头"], "以区域图、箭头和结晶数量共同表示樱花结晶移动的规则效果。", "把结晶按箭头从一处移到另一处。", [anchor("core", 29, "10-1")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="high")
add("keyword.range-expand-far", "rule_keyword", "距离扩大（远）", "距離拡大（遠）", ["远增", "远 X"], "从攻击距离集合的最大值起，向更远侧增加 X 个连续整数的修正。", "把能打到的最远距离往外扩。", [anchor("core", 30, "10-4-2")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="medium")
add("keyword.range-expand-near", "rule_keyword", "距离扩大（近）", "距離拡大（近）", ["近增", "近 X"], "从攻击距离集合的最小值起，向更近侧增加 X 个连续非负整数的修正。", "把能打到的最近距离往内扩。", [anchor("core", 30, "10-4-1")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="medium")
add("keyword.range-shrink-far", "rule_keyword", "距离缩小（远）", "距離縮小（遠）", ["远减"], "从攻击距离集合的最大值起移除 X 个连续整数的修正。", "削掉最远侧的一段攻击距离。", [anchor("core", 31, "10-4-4")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="medium")
add("keyword.range-shrink-near", "rule_keyword", "距离缩小（近）", "距離縮小（近）", ["近减"], "从攻击距离集合的最小值起移除 X 个连续整数的修正。", "削掉最近侧的一段攻击距离。", [anchor("core", 30, "10-4-3")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="medium")
add("resolution.cancel", "rule_keyword", "打消", "打ち消す", ["无效", "康掉"], "使攻击、其伤害或攻击后效果在攻击结算的相应步骤不再按原流程解决的规则处理。", "让那次攻击或其中一部分不生效。", [anchor("core", 27, "9-4 ⅱ／ⅳ／ⅵ")], ["bilibili-keywords-2024", "fandom-faq-zh"], confidence="high")
add("action.remove", "rule_keyword", "移出游戏", "取り除く", ["除外"], "将指定卡牌表面朝上移动至游戏外的规则动作。", "把牌正面朝上放到游戏外。", [anchor("core", 33, "10-18")], ["bilibili-keywords-2024", "old-cr-translation-2022"], confidence="high")
add("action.seal", "rule_keyword", "封印", "封印する", ["压在此牌下"], "将所选卡牌移至封印区，并与执行封印的特定卡牌关联的规则动作。", "把一张牌压在指定牌下，暂时停用其效果。", [anchor("core", 31, "10-9")], ["bilibili-keywords-2024", "pdf-1.14.1"], confidence="high")
add("action.exchange", "rule_keyword", "交换", "交換", [], "依 10-25 在交换来源与交换目标的区域之间移动两张卡牌的处理。", "让两张指定牌互换位置。", [anchor("core", 35, "10-25")], ["pdf-1.14.1", "old-cr-translation-2022"], confidence="high")

# 女神名。前 18 柱有可复核社区页面；后 8 柱证据不足处维持 provisional。
goddesses = [
    ("01", "摇波", "ユリナ", ["YURINA", "遥波"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("02", "细音", "サイネ", ["SAINE"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("03", "绯弥香", "ヒミカ", ["HIMIKA"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("04", "常世", "トコヨ", ["TOKOYO"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("05", "胧", "オボロ", ["OBORO", "朧"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("06", "雪灯", "ユキヒ", ["YUKIHI"], "fandom-goddess-pages-zh", "high", "review", ""),
    ("07", "森罗", "シンラ", ["SHINRA"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("08", "破钟", "ハガネ", ["HAGANE"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("09", "千影", "チカゲ", ["CHIKAGE"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("10", "枢", "クルル", ["KURURU"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("11", "萨莉娅", "サリヤ", ["THALLYA", "莎莉娅"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("12", "雷螺", "ライラ", ["RAIRA"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("13", "虚路", "ウツロ", ["UTSURO"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("14", "仄佳", "ホノカ", ["HONOKA"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("15", "凝努", "コルヌ", ["KORUNU", "科尔努"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("16", "八叶", "ヤツハ", ["YATSUHA"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("17", "波津", "ハツミ", ["HATSUMI", "初海"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("18", "水津城", "ミズキ", ["MIZUKI"], "fandom-goddess-pages-zh", "medium", "review", ""),
    ("19", "希", "メグミ", ["MEGUMI", "惠", "梅古美"], "bilibili-community-guides", "medium", "provisional", "仅检出单一社区体系明确使用“希”。"),
    ("20", "叶慧", "カナヱ", ["KANAE", "KANAWE", "奏", "卡娜艾"], "bilibili-community-guides", "medium", "provisional", "社区使用“叶慧”，但缺少第二独立来源交叉确认。"),
    ("21", "卡姆伊", "カムヰ", ["KAMUWI", "卡姆依"], "pdf-1.14.1", "low", "provisional", "无充分简中来源，当前采用音译。"),
    ("22", "恋离", "レンリ", ["RENRI", "莲理"], "bilibili-community-guides", "medium", "provisional", "社区使用“恋离”，但缺少第二独立来源交叉确认。"),
    ("23", "安岐那", "アキナ", ["AKINA", "秋奈", "阿琪娜"], "bilibili-community-guides", "medium", "provisional", "社区攻略检出“安岐那”，仍需确认是否沿用。"),
    ("24", "西斯伊", "シスイ", ["SHISUI", "锯子", "志水", "紫水"], "pdf-1.14.1", "low", "provisional", "无充分简中来源；当前为音译，社区俗称“锯子”不可进入规范正文。"),
    ("25", "御空", "ミソラ", ["MISORA", "美空"], "bilibili-community-guides", "medium", "provisional", "社区使用“御空”，但缺少第二独立来源交叉确认。"),
    ("26", "伊尼尔", "イニル", ["INNEALRA", "因尼尔", "依尼尔"], "pdf-1.14.1", "low", "provisional", "第十季新女神缺少可复核简中来源，当前采用音译。"),
]
for number, zh, ja, aliases, source, confidence, status, conflict in goddesses:
    add(
        f"goddess.{number}",
        "goddess",
        zh,
        ja,
        aliases,
        f"附则一女神列表中编号为 {number} 的可选女神。",
        f"女神 {ja} 的当前推荐简中名。",
        [anchor("appendix-1", 75, "附则1 女神列表")],
        ["pdf-1.14.1", source] if source != "pdf-1.14.1" else ["pdf-1.14.1"],
        confidence=confidence,
        status=status,
        impact="high",
        conflict=conflict,
    )

nonselectable = [
    ("kodama", "科达玛", "コダマ", ["KODAMA", "木灵"]),
    ("kiriko", "桐子", "キリコ", ["KIRIKO"]),
    ("zanka", "赞卡", "ザンカ", ["ZANKA", "斩华"]),
    ("wouka", "沃卡", "ヲウカ", ["WOUKA", "樱华"]),
]
for slug, zh, ja, aliases in nonselectable:
    add(
        f"goddess.nonselectable.{slug}",
        "goddess",
        zh,
        ja,
        aliases,
        "附则一列出的不可在双掌缭乱中选择、但可作为卡牌使用者出现的女神。",
        f"规则里会出现，但不能直接选择的女神 {ja}。",
        [anchor("appendix-1", 75, "附则1 女神列表")],
        ["pdf-1.14.1"],
        confidence="low",
        status="provisional",
        impact="low",
        conflict="缺少可复核简中来源，当前采用音译；不应在确认前固化。",
    )

# 女神专属机制。推荐名均以日文规则定义为边界，中文证据不足者保持暂定。
mechanisms = [
    ("yurina.resolve", "决死", "決死", ["残血"], "自己的命中樱花结晶不多于 3 时成立的条件。", "低血量时强化摇波的部分牌。", 75, "附则1", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "medium", ""),
    ("saine.eight-form", "八相", "八相", [], "自己的装中没有樱花结晶时成立的条件。", "空装时强化细音的部分牌。", 75, "附则1", ["fandom-goddess-pages-zh"], "medium", "review", "medium", ""),
    ("himika.rapid-fire", "连火", "連火", [], "同一回合已使用至少两张牌时成立的条件。", "一回合连打多张牌后强化绯弥香。", 75, "附则1", ["fandom-goddess-pages-zh"], "medium", "review", "medium", ""),
    ("tokoyo.poise", "境地", "境地", [], "自己的集中力等于 2 时成立的条件。", "满集中时强化常世的部分牌。", 75, "附则1", ["fandom-goddess-pages-zh"], "medium", "review", "medium", ""),
    ("oboro.install", "设置", "設置", ["设伏"], "牌面关键字，由牌库重铸前的规则效果允许从盖牌区使用一张带设置的牌。", "洗牌前可从盖牌区发动一张伏击牌。", 39, "3-2 至 3-3", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "high", ""),
    ("oboro.digital-install", "数码设置", "デジ設置", ["数设", "电子设置"], "『消失』胧的部件关键字，供其替代牌库重铸的规则效果参照。", "电子部件组好后触发的特殊设置。", 41, "3-6", ["pdf-1.14.1"], "low", "provisional", "medium", "“デジ”译为“数码”还是“电子”缺少社区共识。"),
    ("oboro.cyberwar-zone", "电子战区", "電子戦ゾーン", ["电子战区域"], "与『消失』胧玩家关联、仅容纳部件的专属区域。", "胧放置并组装主部件和定制部件的区域。", 41, "3-9", ["pdf-1.14.1"], "medium", "review", "medium", ""),
    ("yukihi.umbrella", "伞面开合", "傘の開閉", ["开闭伞", "变貌"], "在开伞与闭伞两个公开状态之间切换，并据状态读取卡牌相应信息。", "切换伞面，让同一张牌改用另一侧数据。", 41, "4-1 至 4-4", ["fandom-goddess-pages-zh", "bilibili-community-guides"], "high", "review", "high", ""),
    ("shinra.scheme", "计略", "計略", ["神算", "鬼谋"], "森罗玩家秘密持有神算或鬼谋状态，执行后准备下一计略。", "在两种秘密策略间轮换并触发不同效果。", 42, "5-1 至 5-3", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "high", ""),
    ("hagane.centrifugality", "远心", "遠心", [], "仅在当前距离较回合开始时远至少 2 且本回合未进行攻击时允许使用的关键字。", "本回合先把距离拉远、还没攻击，才能打远心牌。", 43, "6-2", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "high", ""),
    ("chikage.poison", "毒", "毒", ["毒牌", "毒袋"], "无使用者信息、由千影追加规则加入并可进入对手牌库等区域的专属卡牌分类。", "塞进对手循环里妨碍其行动的毒牌。", 43, "7-1 至 7-5", ["fandom-goddess-pages-zh", "bilibili-community-guides"], "high", "review", "high", ""),
    ("kururu.contraption", "机巧", "機巧", [], "以牌面机巧图标检查弃牌区、盖牌区等公开信息，满足组合后才可使用的条件。", "凑齐指定类型图标才能开动枢的机关牌。", 45, "8-2 至 8-3", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "high", ""),
    ("thallya.artificial-flower", "造花结晶", "造花結晶", ["造花"], "萨莉娅专属、在机器区域内具有燃烧状态的结晶对象。", "车辆引擎里的五颗燃料结晶。", 46, "9-2", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "medium", "review", "high", ""),
    ("thallya.transform", "变形", "TransForm", ["TRANSFORM", "形态转换"], "萨莉娅专属 TransForm 牌及相应机器状态变更。", "用专用牌改变车辆形态和能力。", 46, "9-3", ["bilibili-keywords-2024", "pdf-1.14.1"], "medium", "review", "medium", "PDF 第 47 页存在 TransFrom／TransForm 源文拼写不一致，数据保留原异常记录。"),
    ("thallya.combustion", "燃烧", "燃焼", [], "将未燃烧的造花结晶变为燃烧状态的规则动作。", "消耗一颗引擎燃料。", 48, "9-8", ["bilibili-keywords-2024", "pdf-1.14.1"], "high", "review", "medium", ""),
    ("thallya.ride", "骑动", "騎動", [], "依萨莉娅追加规则进行移动并改变造花结晶状态的关键字处理。", "开车移动距离并联动燃料。", 48, "9-9", ["bilibili-community-guides", "pdf-1.14.1"], "medium", "review", "high", ""),
    ("raira.wind-thunder", "风雷", "風雷", ["风雷槽"], "雷螺玩家持有风神槽与雷神槽并通过带电牌增加其数值的机制。", "为风、雷两个槽蓄力。", 49, "10-2 至 10-4", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "high", ""),
    ("raira.charged", "带电", "帯電", ["充电"], "雷螺规则为其他女神的牌记录、可被解除以增加风神槽或雷神槽的状态。", "其他女神的牌打出后带电，横置解除来加槽。", 49, "10-3 至 10-4", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "medium", ""),
    ("raira.storm-force", "岚之力", "嵐の力", ["风雷表"], "支付风神槽或雷神槽数值并按表执行对应效果。", "花槽点数换移动、抽牌或攻击等奖励。", 50, "10-5", ["fandom-goddess-pages-zh", "bilibili-community-guides"], "high", "review", "high", ""),
    ("utsuro.dust", "灰尘", "塵", ["尘", "灰塵"], "虚中樱花结晶达到牌面指定阈值时，使虚路部分牌满足的强化条件。", "公共虚很多时，虚路的部分牌会强化。", 75, "附则1 女神列表（关联锚点）", ["fandom-goddess-pages-zh"], "low", "provisional", "medium", "综合规则只在附则列出虚路，未定义该牌面词；现有简中定义来自单一社区体系，需保留证据缺口。"),
    ("utsuro.revival", "终焉之影复苏", "終焉の影が蘇る", ["终焉复苏"], "满足追加规则条件后交换虚路相关追加牌并改变其可用牌的处理。", "虚路终章形态触发的专属转变。", 51, "11-2", ["pdf-1.14.1"], "low", "provisional", "medium", "推荐名为直译，尚无简中共识。"),
    ("honoka.bloom", "开花", "開花", [], "仄佳的部分牌使用后可与追加牌中的指定牌交换的机制。", "打出一张牌后让它成长为下一张牌。", 51, "12-1", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "high", ""),
    ("korunu.freeze", "冻结", "凍結", [], "在对手装的空位放置冻结标记，并改变其聚气处理的机制。", "占住对手装的容量，对方要先解冻才能正常聚气。", 52, "13-2 至 13-6", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "high", ""),
    ("yatsuha.reflection", "镜映", "鏡映", [], "比较双方对应的装、气、命区域，计算结晶数相同的区域数量。", "数一数双方有多少对对应资源区的结晶数量相同。", 53, "14-2-1", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "high", ""),
    ("yatsuha.perfect-form", "完全态", "完全態", [], "满足追加规则条件后使用八叶完全态追加牌组的状态与处理。", "八叶进入另一套牌面的强化形态。", 53, "14-3", ["fandom-goddess-pages-zh", "pdf-1.14.1"], "high", "review", "medium", ""),
    ("yatsuha.memory", "回忆区", "思い出", ["思念区"], "与八叶相关、容纳特定追加牌的专属区域＜思い出＞。", "八叶旅途机制保存牌的位置。", 53, "14-4", ["pdf-1.14.1"], "low", "provisional", "medium", "“思い出”可译“回忆”或“回忆区”，缺少简中共识。"),
    ("hatsumi.wind", "顺风／逆风", "順風・逆風", ["顺逆风"], "依据对手上一回合是否进行攻击决定的波津公开状态。", "对手上回合没攻击就是顺风，否则是逆风。", 55, "15-1-1", ["fandom-goddess-pages-zh", "bilibili-keywords-2024"], "high", "review", "high", ""),
    ("hatsumi.dive", "潜水", "潜水", [], "波津牌面指示并依 15-2 解决的专属处理。", "按波津规则暂避并在之后处理的动作。", 55, "15-2", ["pdf-1.14.1"], "medium", "review", "medium", ""),
    ("mizuki.barracks", "兵舍", "兵舎", ["兵营"], "与水津城玩家关联、容纳无使用者信息的兵员牌的专属区域。", "存放盾兵、枪兵和骑兵的区域。", 56, "16-4", ["fandom-goddess-pages-zh", "pdf-1.14.1"], "medium", "review", "high", ""),
    ("mizuki.recruit", "征兵", "徴兵", [], "从兵舍选择一张未征兵的兵员牌，并将其改为已征兵状态的规则动作。", "把兵舍里一张尚未征用的兵员准备好。", 57, "16-5", ["pdf-1.14.1", "fandom-goddess-pages-zh"], "high", "review", "medium", ""),
    ("megumi.seed-crystal", "种结晶", "種結晶", ["种子结晶"], "希的专属结晶对象，在土壤、付与牌等位置间移动并可代替樱花结晶。", "用来培养付与牌的种子资源。", 57, "17-2", ["bilibili-community-guides", "pdf-1.14.1"], "medium", "review", "high", ""),
    ("megumi.soil", "土壤", "土壌", ["土壤区"], "与希玩家关联、放置种结晶的专属区域。", "未萌发的种子待的地方。", 57, "17-3", ["bilibili-community-guides", "pdf-1.14.1"], "high", "review", "medium", ""),
    ("megumi.growth", "生长", "生育", ["生育", "成长"], "牌可持有的数值信息，本身不产生效果；使用付与牌时，17-7-1 依其 X 值限制可从土壤选择的已萌芽种结晶数量。", "展开付与牌时，最多可再放入 X 颗已萌芽种子。", 58, "17-6 至 17-7-1", ["bilibili-keywords-2024", "bilibili-community-guides"], "medium", "review", "high", "社区同时使用“生长”和“生育”；日文术语为“生育”，推荐“生长”更符合简中游戏语感。"),
    ("kanawe.conception", "构想", "構想", ["剧本"], "叶慧专属构想牌、构想区、达成区和幕数共同构成的任务推进机制。", "准备小剧本，完成条件后推进幕数。", 59, "18-1 至 18-7", ["bilibili-community-guides", "fandom-faq-zh"], "medium", "review", "high", ""),
    ("kanawe.act", "幕", "幕", ["幕数", "当前幕"], "规则记录的“当前幕颜色”和“当前幕数值”两项公开信息；颜色可带有效果，数值用于表示构想进度。", "记录当前剧本演到哪一幕，以及这一幕的颜色效果。", 60, "18-3-1 至 18-3-2", ["pdf-1.14.1", "bilibili-community-guides"], "medium", "review", "medium", ""),
    ("kamuwi.oath", "誓约", "誓約", [], "卡姆伊部分牌持有、依据禁忌值和追加规则约束使用的关键字。", "使用强力牌时要遵守的禁忌条件。", 62, "19-3", ["pdf-1.14.1", "bilibili-keywords-2024"], "high", "review", "high", ""),
    ("kamuwi.taboo", "禁忌", "禁忌", ["禁忌值"], "卡姆伊玩家持有的公开数值；达到规则界限会触发败北相关处理。", "力量越用越危险，数值过高会输。", 62, "19-2 至 19-4", ["bilibili-keywords-2024", "pdf-1.14.1"], "high", "review", "high", ""),
    ("renri.perjury", "伪证", "偽証", ["伪装"], "恋离将满足条件的手牌作为另一张牌使用并在之后接受反证检查的机制。", "把手里的牌冒充成另一张牌来打。", 63, "20-3", ["bilibili-community-guides", "pdf-1.14.1"], "high", "review", "high", ""),
    ("renri.perjury-install", "伪证设置", "偽証設置", ["伪设置"], "以伪证方式从盖牌区使用带设置关键字之牌的专属处理。", "从盖牌区冒充并发动一张设置牌。", 63, "20-4", ["pdf-1.14.1", "bilibili-community-guides"], "medium", "review", "medium", ""),
    ("renri.regression", "回归", "回帰", [], "依 20-5 将指定对象或状态恢复到规则所述位置的恋离专属处理。", "让恋离的相关牌回到可再次利用的位置。", 64, "20-5", ["pdf-1.14.1"], "medium", "review", "medium", ""),
    ("renri.disproof", "反证", "反証", [], "对伪证宣言进行验证并依真假执行后果的规则处理。", "检查恋离刚才是不是在说谎。", 65, "20-6-3", ["pdf-1.14.1", "bilibili-community-guides"], "high", "review", "high", ""),
    ("akina.flow", "资金流", "フロー", ["流", "FLOW"], "与安岐那玩家关联、用于记录资本移动的专属区域＜フロー＞。", "经济机制中资金流转的区域。", 65, "21-1", ["pdf-1.14.1", "bilibili-community-guides"], "low", "provisional", "high", "“フロー”社区常简称“流”，规范名尚待确认。"),
    ("akina.capital", "资本", "資本", [], "安岐那玩家持有、由规则依相场与结晶位置计算的公开数值。", "决定投资和回收收益的资金量。", 66, "21-2-2", ["pdf-1.14.1", "bilibili-community-guides"], "high", "review", "high", ""),
    ("akina.investment", "投资券", "投資券", [], "安岐那卡牌持有、改变费用与资本处理的专属信息。", "把一张牌当作投资项目来积累收益。", 66, "21-4", ["bilibili-keywords-2024", "bilibili-community-guides"], "high", "review", "high", ""),
    ("akina.recovery", "回收", "回収", [], "安岐那依规则从投资状态取回资源或卡牌的专属处理。", "把投资的资本和收益收回来。", 66, "21-5 至 21-6", ["bilibili-keywords-2024", "pdf-1.14.1"], "high", "review", "high", ""),
    ("akina.market", "相场", "相場", ["行情"], "安岐那玩家持有的 1 至 4 的公开整数，开局为 2；不同数值对应不同区域，并按追加规则升降。", "当前市场行情，决定投资等效果参照哪个区域。", 65, "21-2-1", ["pdf-1.14.1", "bilibili-community-guides"], "medium", "review", "medium", ""),
    ("shisui.laceration", "裂伤", "裂傷", ["裂", "锯伤"], "以裂伤标记占据装、命或气的容量，并可转化为相应伤害的机制。", "在资源区留下伤口，之后变成伤害。", 67, "22-1 至 22-11", ["bilibili-keywords-2024", "bilibili-community-guides"], "high", "review", "high", ""),
    ("misora.aim", "瞄准", "照準", ["准星"], "御空玩家持有、取“无”或整数值的公开信息，用于判断攻击是否瞄准吻合。", "把准星记录在某个距离上，之后用来检查攻击。", 70, "23-1-1 至 23-3", ["pdf-1.14.1", "bilibili-community-guides"], "medium", "review", "high", ""),
    ("misora.on-target", "瞄准吻合", "照準が合っている", ["对准", "瞄准成功"], "攻击的适正距离与当前瞄准值满足 23-3 条件的状态。", "攻击距离覆盖准星时，相关效果成立。", 71, "23-3", ["pdf-1.14.1"], "low", "provisional", "high", "“照準が合っている”尚无稳定简中术语，当前采用说明式译名。"),
    ("misora.tracking", "追尾", "追尾", [], "按 23-4 改变御空瞄准值并修正攻击的关键字处理。", "让准星追着目标距离移动。", 71, "23-4", ["bilibili-keywords-2024", "pdf-1.14.1"], "high", "review", "medium", ""),
    ("innealra.fate-card", "命运牌", "運命カード", ["命运卡"], "伊尼尔专属、具有名字、编号、命运值和箭头等信息的卡牌对象。", "决定伊尼尔路线和变化的专用牌。", 71, "24-1 至 24-2", ["pdf-1.14.1"], "medium", "review", "high", ""),
    ("innealra.fate-zone", "命运区", "運命", [], "与伊尼尔玩家关联、放置命运牌的专属区域＜運命＞。", "当前命运牌所在的区域。", 72, "24-3", ["pdf-1.14.1"], "medium", "review", "medium", ""),
    ("innealra.lost", "迷失区", "ロスト", ["LOST", "失落区"], "与伊尼尔玩家关联、放置失去的命运牌等对象的专属区域＜ロスト＞。", "离开当前命运路线的牌所去的区域。", 72, "24-4", ["pdf-1.14.1"], "low", "provisional", "medium", "“ロスト”可译“迷失／失落”或保留英文，尚无简中证据。"),
    ("innealra.resonate", "共鸣", "共鳴", [], "满足 24-6 条件时依命运牌信息执行相应处理的伊尼尔机制。", "命运牌条件对上后触发额外效果。", 73, "24-6", ["bilibili-keywords-2024", "pdf-1.14.1"], "high", "review", "high", ""),
]
for (
    slug,
    zh,
    ja,
    aliases,
    strict,
    plain,
    page,
    rule,
    sources,
    confidence,
    status,
    impact,
    conflict,
) in mechanisms:
    add(
        f"mechanic.{slug}",
        "goddess_mechanism",
        zh,
        ja,
        aliases,
        strict,
        plain,
        [anchor("additional" if page < 75 else "appendix-1", page, rule)],
        ["pdf-1.14.1", *sources],
        confidence=confidence,
        status=status,
        impact=impact,
        conflict=conflict,
    )


pre_lock_status_counts = {
    status: sum(item["review_status"] == status for item in terms)
    for status in ("review", "provisional")
}
provisional_term_ids = [
    str(item["id"]) for item in terms if item["review_status"] == "provisional"
]

if len(terms) != 171 or pre_lock_status_counts != {"review": 150, "provisional": 21}:
    raise ValueError(
        "术语冻结基线与用户审核时的 171／150／21 计数不一致："
        f"terms={len(terms)}, statuses={pre_lock_status_counts}"
    )

for term in terms:
    term["review_status"] = "locked"

baseline_document = {
    "schema_version": 1,
    "source_pdf_sha256": "b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98",
    "generated_at": "2026-08-04",
    "status_policy": {
        "locked": "用户已于 2026-08-04 批量接受全部 171 条推荐方案；规范正文必须使用推荐简中",
        "review": "冻结前历史状态：已有推荐方案、等待用户审核",
        "provisional": "冻结前历史状态：证据不足或冲突显著；21 条当前推荐名已由用户明确接受"
    },
    "terms": terms,
}
baseline_payload = json.dumps(baseline_document, ensure_ascii=False, indent=2) + "\n"
baseline_sha256 = hashlib.sha256(baseline_payload.encode("utf-8")).hexdigest()
if baseline_sha256 != BASELINE_TERMS_SHA256:
    raise ValueError(
        "2026-08-04 冻结术语基线发生漂移："
        f"expected={BASELINE_TERMS_SHA256}, actual={baseline_sha256}"
    )

# 统一消除推荐名与自身别名的历史重复；这两项只属于数据卫生修正，不改变规范译名。
self_alias_cleanup_ids: list[str] = []
for term in terms:
    original_aliases = list(term["aliases"])
    normalized_aliases = list(
        dict.fromkeys(
            alias
            for alias in original_aliases
            if alias and alias != term["recommended_zh"]
        )
    )
    if normalized_aliases != original_aliases:
        self_alias_cleanup_ids.append(str(term["id"]))
        term["aliases"] = normalized_aliases

revision_seed = [
    (
        "zone.attack-in-progress",
        "攻击中区",
        "攻击中",
        "冻结前简中证据不足；2026-08-29 用户依据实卡整体比对明确将规范名从“攻击中区”修订为“攻击中”。",
    ),
    (
        "goddess.21",
        "卡姆伊",
        "神居",
        "冻结前无充分简中来源，曾采用音译“卡姆伊”；2026-08-29 用户依据实卡整体比对明确修订为“神居”。",
    ),
    (
        "goddess.24",
        "西斯伊",
        "志水",
        "冻结前无充分简中来源，曾采用音译“西斯伊”；2026-08-29 用户依据实卡整体比对明确修订为“志水”。社区俗称“锯子”仍仅作检索别名。",
    ),
    (
        "goddess.nonselectable.kodama",
        "科达玛",
        "菰珠",
        "冻结前缺少可复核简中来源，曾采用音译“科达玛”；2026-08-29 用户依据实卡整体比对明确修订为“菰珠”。",
    ),
    (
        "goddess.nonselectable.zanka",
        "赞卡",
        "斩华",
        "冻结前缺少可复核简中来源，曾采用音译“赞卡”；2026-08-29 用户依据实卡整体比对明确修订为“斩华”。",
    ),
    (
        "goddess.nonselectable.wouka",
        "沃卡",
        "奥华",
        "冻结前缺少可复核简中来源，曾采用音译“沃卡”；2026-08-29 用户依据实卡整体比对明确修订为“奥华”。",
    ),
]
term_map = {str(item["id"]): item for item in terms}
revision_changes: list[dict[str, object]] = []
for term_id, old_name, new_name, revised_conflict_note in revision_seed:
    term = term_map[term_id]
    if term["recommended_zh"] != old_name:
        raise ValueError(
            f"{term_id} 修订前推荐名应为“{old_name}”，实际为“{term['recommended_zh']}”"
        )
    aliases_before = list(term["aliases"])
    aliases_after = [alias for alias in aliases_before if alias != new_name]
    if old_name not in aliases_after:
        aliases_after.append(old_name)
    aliases_after = list(dict.fromkeys(aliases_after))
    conflict_note_before = str(term["conflict_note"])
    term["recommended_zh"] = new_name
    term["aliases"] = aliases_after
    term["conflict_note"] = revised_conflict_note
    revision_changes.append(
        {
            "term_id": term_id,
            "from": old_name,
            "to": new_name,
            "aliases_before": aliases_before,
            "aliases_after": aliases_after,
            "conflict_note_before": conflict_note_before,
            "conflict_note_after": revised_conflict_note,
        }
    )

# 女神机制定义引用现行规范名；稳定 ID、英文 slug 与卡号保持不变。
for term_id in ("mechanic.kamuwi.oath", "mechanic.kamuwi.taboo"):
    term_map[term_id]["strict_definition"] = str(
        term_map[term_id]["strict_definition"]
    ).replace("卡姆伊", "神居")

document = {
    "schema_version": 2,
    "source_pdf_sha256": "b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98",
    "generated_at": "2026-08-29",
    "applied_decision_ids": [INITIAL_DECISION_ID, REVISION_DECISION_ID],
    "status_policy": {
        "locked": "171 条术语于 2026-08-04 初始冻结，其中 6 条于 2026-08-29 经用户明确修订；规范正文必须使用现行推荐简中",
        "review": "冻结前历史状态：已有推荐方案、等待用户审核",
        "provisional": "冻结前历史状态：证据不足或冲突显著；21 条初始推荐名曾由用户明确接受",
    },
    "terms": terms,
}

decision_record = {
    "schema_version": 2,
    "decision_id": INITIAL_DECISION_ID,
    "confirmed_at": "2026-08-04",
    "decision_source": "用户在当前任务中明确确认",
    "user_statement": "接受审核文档全部 171 条推荐方案，包括 21 条 provisional 的当前推荐名。",
    "baseline_commit": "7738d71",
    "term_count": len(terms),
    "pre_lock_status_counts": pre_lock_status_counts,
    "locked_count": sum(item["review_status"] == "locked" for item in terms),
    "provisional_term_ids": provisional_term_ids,
    "accepted_term_ids": [str(item["id"]) for item in terms],
    "effect": "全部推荐简中转为 locked；原 provisional 状态只保留在本记录中用于审计。",
    "baseline_terms_artifact": {
        "commit": "542178b",
        "sha256": BASELINE_TERMS_SHA256,
    },
    "current_decision_id": REVISION_DECISION_ID,
    "applied_decision_ids": [INITIAL_DECISION_ID, REVISION_DECISION_ID],
    "amendments": [
        {
            "amendment_id": REVISION_DECISION_ID,
            "base_decision_id": INITIAL_DECISION_ID,
            "confirmed_at": "2026-08-29",
            "decision_source": "用户填写术语修改意见表并在当前任务中明确确认",
            "user_statement": "需修改内容已填写。对应的旧翻译放入别名，而新翻译若过去已存在于别名中，则从别名中删去，以免别名与新翻译内容重复。",
            "scope": "整个规则集",
            "evidence_basis": "用户基于多张实卡的整体比对确认；不要求逐词条记录适用范围或实卡索源。",
            "source_artifact": {
                "filename": "术语修改意见填写表_2026-08-29.xlsx",
                "sha256": FILLED_WORKBOOK_SHA256,
                "filled_change_count": len(revision_changes),
            },
            "alias_policy": "从别名中删除新推荐名；将旧推荐名加入别名；按原顺序保序去重。",
            "term_changes": revision_changes,
            "additional_alias_normalization_ids": self_alias_cleanup_ids,
            "effect": "六项现行推荐名及整个规则集中的规范用法同步修订；全部 171 条术语保持 locked。",
        }
    ],
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
DECISION_OUTPUT.write_text(
    json.dumps(decision_record, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"generated {len(terms)} terms -> {OUTPUT.relative_to(ROOT)}")
print(f"generated decision record -> {DECISION_OUTPUT.relative_to(ROOT)}")
