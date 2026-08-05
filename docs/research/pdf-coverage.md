# PDF 逐页覆盖与校验报告

生成日期：2026-08-04

## 底本

- 文件：`furuyoni_comprehensive_rule.pdf`
- 物理页数：86
- SHA-256：`b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98`
- 规则语义权威：日文 PDF 原文

## 结构与自动校验

- 校验结论：`passed`
- 核心规则顶层章节：[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
- 追加规则顶层章节：[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
- 已识别规则锚点：361 个
- 卡号页内出现数：373；唯一字面卡号：301
- 表格：9 个，位于 PDF 页 [50, 53, 54, 60, 62, 65, 66, 73]
- 第 65 页的相场表在第 66 页续接 1 行，按同一张跨页表处理。
- 第 45 页包含唯一嵌入图片：机巧五类图标说明；公开站点必须改用原创 CSS 色块和文字标签。
- 红色 `2025-04-25 更新` 涉及 PDF 页：[1, 3, 4, 15, 19, 24, 25, 28, 30, 31, 35, 38, 40, 43, 52, 56, 71, 72, 73, 74, 75, 80, 83, 84, 85, 86]
- 绿色 `2025-06-02 微調整` 涉及 PDF 页：[1, 6, 10, 12, 25, 26, 27, 28, 38, 40, 46, 47, 51, 59, 61, 71, 80]
- 显式交叉引用未解析：[]

## 核验方法

- 使用 `pypdf` 提取每页文本、编号、卡号和交叉引用候选。
- 使用 `pdfplumber` 提取表格、嵌入图片和精确文本颜色。
- 86 页均渲染为 JPEG 并通过全页接触表检查页序、章节过渡、留白和修订色。
- 含表格、嵌入图、红／绿修订或异常的页面另以单页渲染和版面对象复核。
- 文本层只作为索引；源文含义、表格结构与颜色均以页面渲染为最终核验依据。

## 源文异常记录

- PDF 第 12 页，源文移动区域措辞自相矛盾：6-3 写作「移動先と移動後が同じ領域」，但紧随的例子实际比较移动前与移动后的区域。 规范译文依紧随例子表述为移动来源与移动后区域相同，并保留异常标记。
- PDF 第 41 页，源文部件状态措辞自相矛盾：3-9 写作组装后与「組み立てられたパーツ」分开放置，无法区分两种状态。 规范译文依上下文表述为与未组装部件分开放置，并保留异常标记。
- PDF 第 47 页，源文拼写不一致：9-3-1-1 与 9-3-1-5 出现 TransFrom，邻近规则使用 TransForm。 保留原文并在翻译校对时单独裁定，不静默改写。
- PDF 第 69 页，源文主语疑似不一致：22-6-3-2 裂伤处理段落出现「ダメージを受けるプレイヤー」。 保留原文并列为规则语义复核项。
- PDF 第 78 页，卡号前缀不一致：『第四章』チカゲ的替换卡号使用 NA-07-chikage，而本页其他チカゲ卡号与追加规则使用 NA-09。 卡号按 PDF 原样记录，不自行纠正。
- PDF 第 80 页，卡号范围内部不一致：『終章』ウツロ条目把 NA-13-utsuro-A1-S-4-Ex2 同时写作范围起止，后续注记又写 Ex1 至 Ex4。 保留两个原始表述并列入后续卡号核验。
- PDF 第 82 页，卡号格式不一致：カナヱ构想卡在本页写作 P-1 至 P-6，追加规则第 59 页写作 P-01 至 P-06。 两个形式均保留为源文证据，不自行合并。
- PDF 第 82 页，卡号分隔符异常：レンリ切札范围起点写作 NA-22-renri--O-S-1，含连续两个连字符。 按 PDF 原样记录并列入后续卡号核验。

## 86 页覆盖清单

| PDF 页 | 印刷页 | 部分 | 页内起始结构 | 卡号 | 引用标记 | 表格 | 红/绿 | 视觉核验 |
| ---: | ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | 1 | `front-matter` | 续前页 | 0 | 0 | 0 | 2/2 | `individual-render-and-layout-objects` |
| 2 | 1 | `core` | §1 ゲームの基本定義；§2 双掌繚乱；1-1 ゲーム；1-2 プレイヤー | 0 | 6 | 0 | 0/0 | `contact-sheet` |
| 3 | 2 | `core` | §3 眼前構築；§4 桜花決闘；3-1 眼前構築の準備；3-2 眼前構築の進め方 | 0 | 8 | 0 | 1/0 | `individual-render-and-layout-objects` |
| 4 | 3 | `core` | §5 桜花決闘の基本定義と原則；5-1 プレイヤーの持つ情報；5-1-1 ターンプレイヤーか非ターンプレイヤー | 0 | 5 | 0 | 4/0 | `individual-render-and-layout-objects` |
| 5 | 4 | `core` | 5-1-5 ライフ；5-1-6 フレア | 0 | 5 | 0 | 0/0 | `contact-sheet` |
| 6 | 5 | `core` | 5-2-2 達人の間合；5-2-3 ダスト | 0 | 7 | 0 | 0/2 | `individual-render-and-layout-objects` |
| 7 | 6 | `core` | 5-5-2 付与札の破棄；5-5-3 焦燥の発生 | 0 | 7 | 0 | 0/0 | `contact-sheet` |
| 8 | 7 | `core` | 5-8 ダメージ；5-8-1 単一値のダメージ | 0 | 11 | 0 | 0/0 | `contact-sheet` |
| 9 | 8 | `core` | 5-9 支払い；5-10 十分な変化がさせられない場合 | 0 | 3 | 0 | 0/0 | `contact-sheet` |
| 10 | 9 | `core` | §6 桜花決闘におけるオブジェクト；6-1 オブジェクト；6-2 オブジェクト：カードに関するルール | 0 | 9 | 0 | 0/1 | `individual-render-and-layout-objects` |
| 11 | 10 | `core` | 6-2-1-6 サブタイプ；6-2-1-7 テキスト | 0 | 7 | 0 | 0/0 | `contact-sheet` |
| 12 | 11 | `core` | 6-2-2 オブジェクトの取りうる状態；6-2-2-1 表向き/裏向き | 0 | 6 | 0 | 0/1 | `individual-render-and-layout-objects` |
| 13 | 12 | `core` | 6-4-1 オブジェクトの持ちうる情報；6-4-1-1 分類 | 0 | 8 | 0 | 0/0 | `contact-sheet` |
| 14 | 13 | `core` | §7 桜花決闘における領域；6-4-1-8 使用者；7-1 領域 | 0 | 2 | 0 | 0/0 | `contact-sheet` |
| 15 | 14 | `core` | 7-1-1 ＜間合＞；7-1-2 ＜ライフ＞ | 0 | 7 | 0 | 6/0 | `individual-render-and-layout-objects` |
| 16 | 15 | `core` | 7-1-6 ＜山札＞；7-1-7 ＜捨て札＞ | 0 | 3 | 0 | 0/0 | `contact-sheet` |
| 17 | 16 | `core` | 7-1-9 ＜付与札＞；7-1-10 ＜手札＞ | 0 | 3 | 0 | 0/0 | `contact-sheet` |
| 18 | 17 | `core` | 7-1-12 ＜追加札＞；7-1-13 ＜封印＞ | 0 | 5 | 0 | 0/0 | `contact-sheet` |
| 19 | 18 | `core` | §8 ターンの進行；7-2 保有者の不一致；8-1 開始フェイズ | 0 | 5 | 0 | 1/0 | `individual-render-and-layout-objects` |
| 20 | 19 | `core` | 8-2 メインフェイズ；8-2-1 メインフェイズ開始時処理 | 0 | 6 | 0 | 0/0 | `contact-sheet` |
| 21 | 20 | `core` | §9 効果の発生と解決；8-3-2 終了フェイズ既定処理；9-1 効果 | 0 | 5 | 0 | 0/0 | `contact-sheet` |
| 22 | 21 | `core` | 9-1-1-3 【使用時】効果；9-1-1-4 【攻撃後】効果 | 0 | 7 | 0 | 0/0 | `contact-sheet` |
| 23 | 22 | `core` | 9-1-3 特筆すべき効果；9-1-3-1 敗北の代わりに解決される効果 | 0 | 6 | 0 | 0/0 | `contact-sheet` |
| 24 | 23 | `core` | 9-2 カードの使用；9-2-1 《攻撃》カードを使用する際の手順 | 0 | 3 | 0 | 4/0 | `individual-render-and-layout-objects` |
| 25 | 24 | `core` | 9-2-2 《行動》カードを使用する際の手順；9-2-3 《付与》カードを使用する際の手順 | 0 | 3 | 0 | 2/4 | `individual-render-and-layout-objects` |
| 26 | 25 | `core` | 9-3 コストの支払い；9-3-1 消費の支払い | 0 | 4 | 0 | 0/2 | `individual-render-and-layout-objects` |
| 27 | 26 | `core` | 9-4-1 適正距離の確認；9-5 付与札の破棄 | 0 | 3 | 0 | 0/1 | `individual-render-and-layout-objects` |
| 28 | 27 | `core` | 9-6-1 前進；9-6-2 後退 | 0 | 5 | 0 | 1/11 | `individual-render-and-layout-objects` |
| 29 | 28 | `core` | §10 様々な効果の制定；9-7 山札の再構成；9-8 入れ子解決 | 0 | 3 | 0 | 0/0 | `contact-sheet` |
| 30 | 29 | `core` | 10-2 「矢印を逆の向きにする」という記述；10-3 +X/+Y | 0 | 6 | 0 | 6/0 | `individual-render-and-layout-objects` |
| 31 | 30 | `core` | 10-4-4 距離縮小（遠Ｘ）；10-5 「攻撃を行う」という記述 | 0 | 7 | 0 | 1/0 | `individual-render-and-layout-objects` |
| 32 | 31 | `core` | 10-10 焦燥；10-11 「このカード」という記述 | 0 | 4 | 0 | 0/0 | `contact-sheet` |
| 33 | 32 | `core` | 10-14 効果の追加；10-15 他のメガミ | 0 | 8 | 0 | 0/0 | `contact-sheet` |
| 34 | 33 | `core` | 10-20 切札が使用済；10-21 超克 | 0 | 6 | 0 | 0/0 | `contact-sheet` |
| 35 | 34 | `core` | 10-25 S を T と交換する；10-26 両方のダメージを受ける | 0 | 3 | 0 | 11/0 | `individual-render-and-layout-objects` |
| 36 | 35 | `core` | 10-28 この効果が重複したら相殺する；10-29 眼前構築で選んでいない | 0 | 14 | 0 | 0/0 | `contact-sheet` |
| 37 | 36 | `core` | 10-35-2 納；10-35-3 ダメージ | 0 | 10 | 0 | 0/0 | `contact-sheet` |
| 38 | 37 | `core` | 10-41 このカードの上に置かれた桜花結晶をあなたのオーラにあるかのように扱う；10-42 桜花結晶の移動の置換 | 0 | 5 | 0 | 22/6 | `individual-render-and-layout-objects` |
| 39 | - | `additional` | §1 はじめに；§2 追加ルールについて；§3 オボロ；2-1 コアルールとの矛盾；3-1 追加カード・コンポーネント | 5 | 4 | 0 | 0/0 | `contact-sheet` |
| 40 | - | `additional` | 3-4 オブジェクト：パーツ；3-4-1 メインパーツ | 0 | 8 | 0 | 3/1 | `individual-render-and-layout-objects` |
| 41 | - | `additional` | §4 ユキヒ；3-6 デジ設置；3-7 X 個のパーツを組み立てる | 0 | 9 | 0 | 0/0 | `contact-sheet` |
| 42 | - | `additional` | §5 シンラ；4-3 傘の開閉；4-4 ルール上効果の追加 | 0 | 4 | 0 | 0/0 | `contact-sheet` |
| 43 | - | `additional` | §6 ハガネ；§7 チカゲ；5-3 ルール上効果の追加；6-1 追加カード | 4 | 7 | 0 | 1/0 | `individual-render-and-layout-objects` |
| 44 | - | `additional` | §8 クルル；7-2-1 分類:毒；7-3 領域 | 4 | 6 | 0 | 0/0 | `contact-sheet` |
| 45 | - | `additional` | 8-2 機巧；8-3 機巧の組み立て | 1 | 5 | 0 | 0/0 | `individual-render-and-layout-objects` |
| 46 | - | `additional` | §9 サリヤ；9-1 追加コンポーネント；9-2 オブジェクト：造花結晶 | 6 | 6 | 0 | 0/1 | `individual-render-and-layout-objects` |
| 47 | - | `additional` | 9-3-1 オブジェクトの持ちうる情報；9-3-1-1 分類 | 0 | 10 | 0 | 0/1 | `individual-render-and-layout-objects` |
| 48 | - | `additional` | §10 ライラ；9-6 領域：＜間合＞；9-7 領域：＜追加札＞ | 0 | 6 | 0 | 0/0 | `contact-sheet` |
| 49 | - | `additional` | 10-1 追加カード；10-2 プレイヤーの持つ情報 | 3 | 7 | 0 | 0/0 | `contact-sheet` |
| 50 | - | `additional` | 10-5 嵐の力を使用する | 0 | 2 | 2 | 0/0 | `individual-render-and-layout-objects` |
| 51 | - | `additional` | §11 ウツロ；§12 ホノカ；§13 コルヌ；11-1 追加カード；11-2 終焉の影が蘇る | 17 | 4 | 0 | 0/2 | `individual-render-and-layout-objects` |
| 52 | - | `additional` | §14 ヤツハ；13-2 プレイヤーの持つ情報；13-2-1 凍結 | 0 | 8 | 0 | 6/0 | `individual-render-and-layout-objects` |
| 53 | - | `additional` | 14-2 桜花決闘で参照される情報；14-2-1 鏡映数 | 9 | 4 | 1 | 0/0 | `individual-render-and-layout-objects` |
| 54 | - | `additional` | 14-5 桜降る代の旅路に出発する；14-6 桜花結晶を次の位置へと時計回りに動かす | 0 | 3 | 1 | 0/0 | `individual-render-and-layout-objects` |
| 55 | - | `additional` | §15 ハツミ；15-1 プレイヤーの持つ情報；15-1-1 順風・逆風 | 1 | 4 | 0 | 0/0 | `contact-sheet` |
| 56 | - | `additional` | §16 ミズキ；16-1 追加カード；16-2 オブジェクト：カードの持ちうる情報 | 4 | 7 | 0 | 3/0 | `individual-render-and-layout-objects` |
| 57 | - | `additional` | §17 メグミ；16-5 徴兵を行う；17-1 追加コンポーネント | 0 | 6 | 0 | 0/0 | `contact-sheet` |
| 58 | - | `additional` | 17-4 領域：＜使用中＞；17-5 領域：＜付与札＞ | 0 | 5 | 0 | 0/0 | `contact-sheet` |
| 59 | - | `additional` | §18 カナヱ；18-1 追加カード；18-2 オブジェクト：構想カード | 2 | 9 | 0 | 0/1 | `individual-render-and-layout-objects` |
| 60 | - | `additional` | 18-2-1-6 マス；18-2-2 オブジェクトの取りうる状態 | 0 | 8 | 1 | 0/0 | `individual-render-and-layout-objects` |
| 61 | - | `additional` | 18-4-1 ＜構想＞；18-4-2 ＜達成済＞ | 0 | 6 | 0 | 0/2 | `individual-render-and-layout-objects` |
| 62 | - | `additional` | §19 カムヰ；19-1 追加カード；19-2 プレイヤーの持つ情報 | 1 | 5 | 1 | 0/0 | `individual-render-and-layout-objects` |
| 63 | - | `additional` | §20 レンリ；20-1 追加カード；20-2 領域 | 4 | 8 | 0 | 0/0 | `contact-sheet` |
| 64 | - | `additional` | 20-5 回帰；20-6 ルール上効果の追加 | 1 | 7 | 0 | 0/0 | `contact-sheet` |
| 65 | - | `additional` | §21 アキナ；20-6-3 反証；20-6-4 フェイズを終了する | 0 | 6 | 1 | 0/0 | `individual-render-and-layout-objects` |
| 66 | - | `additional` | 21-2-2 資本；21-3 オブジェクト：カードの持ちうる情報 | 0 | 7 | 1 | 0/0 | `individual-render-and-layout-objects` |
| 67 | - | `additional` | §22 シスイ；21-6-2 回収；21-6-3 ダメージによる相場の変動 | 0 | 4 | 0 | 0/0 | `contact-sheet` |
| 68 | - | `additional` | 22-3 領域：＜ライフ＞；22-4 領域：＜フレア＞ | 0 | 9 | 0 | 0/0 | `contact-sheet` |
| 69 | - | `additional` | 22-7 裂傷トークンのダメージ化；22-7-1 ＜オーラ＞ | 0 | 7 | 0 | 0/0 | `contact-sheet` |
| 70 | - | `additional` | §23 ミソラ；22-9-1 《攻撃》の解決；22-10 コストの支払い | 0 | 9 | 0 | 0/0 | `contact-sheet` |
| 71 | - | `additional` | §24 イニル；23-3 照準が合っている；23-4 追尾 | 12 | 8 | 0 | 27/1 | `individual-render-and-layout-objects` |
| 72 | - | `additional` | 24-2-1-2 名前；24-2-1-3 カード番号 | 0 | 10 | 0 | 39/0 | `individual-render-and-layout-objects` |
| 73 | - | `additional` | 24-5-1 ロスト；24-6 共鳴する | 0 | 5 | 1 | 49/0 | `individual-render-and-layout-objects` |
| 74 | - | `additional` | 续前页 | 0 | 0 | 0 | 9/0 | `individual-render-and-layout-objects` |
| 75 | 1 | `appendix-1` | 续前页 | 22 | 0 | 0 | 1/0 | `individual-render-and-layout-objects` |
| 76 | 2 | `appendix-1` | 续前页 | 34 | 0 | 0 | 0/0 | `contact-sheet` |
| 77 | 3 | `appendix-1` | 续前页 | 36 | 0 | 0 | 0/0 | `contact-sheet` |
| 78 | 4 | `appendix-1` | 续前页 | 32 | 0 | 0 | 0/0 | `contact-sheet` |
| 79 | 5 | `appendix-1` | 续前页 | 37 | 0 | 0 | 0/0 | `contact-sheet` |
| 80 | 6 | `appendix-1` | 续前页 | 30 | 0 | 0 | 4/1 | `individual-render-and-layout-objects` |
| 81 | 7 | `appendix-1` | 续前页 | 29 | 0 | 0 | 0/0 | `contact-sheet` |
| 82 | 8 | `appendix-1` | 续前页 | 32 | 0 | 0 | 0/0 | `contact-sheet` |
| 83 | 9 | `appendix-1` | 续前页 | 43 | 0 | 0 | 23/0 | `individual-render-and-layout-objects` |
| 84 | 10 | `appendix-1` | 续前页 | 2 | 0 | 0 | 2/0 | `individual-render-and-layout-objects` |
| 85 | 1 | `appendix-2` | 续前页 | 1 | 1 | 0 | 8/0 | `individual-render-and-layout-objects` |
| 86 | 2 | `appendix-2` | 续前页 | 1 | 0 | 0 | 2/0 | `individual-render-and-layout-objects` |

## 结论与后续边界

86 个物理页记录连续且文本层均非空；章节、表格、唯一图片和修订色清单通过自动断言。源文异常只记录、不静默修正。该清单同时作为术语锚点与全文保真校验依据；原 PDF 和内部日文校对文本不得进入公开构建。
