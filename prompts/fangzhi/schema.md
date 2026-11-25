# 古代方志文献知识图谱：实体与关系规范 v1.0

修订日期：2026-11-21。适用于古代方志及相关历史文献。本文与《抽取提示词_修订版.md》配套使用；历史事实、文献说法、整理生成的连接分别处理。

## 一、基本原则

1. 实体表示可辨识对象或概念；关系表示某条文献在特定语境下提出的一项断言。入库不等于断言已获证实。
2. 不从共现推出关系，不以外部知识补足身份、年代、族属或地名对应。
3. 保留原文、来源、肯否、叙述性质及时间、地域、人群等限定。不同来源或不同肯否分别保存。
4. 研究主数据使用配套 JSON。LightRAG 使用由主数据生成的检索视图，不替代完整研究数据。

## 二、实体类型

以下 13 种类型平级。每个节点只选一种主类型；同一称谓若指向不同对象，分别建节点。

| 中文类型 | 英文标识 | 定义与边界 |
|---|---|---|
| 人物 | Person | 可辨识的具体个人；泛称人群不归此类。历史人物作为被祭对象时仍可保留人物类型；纯神灵或神格对象归 BeliefEntity。 |
| 族群 | EthnicGroup | 原文明示的民族或历史族群；不得凭服饰、姓氏、地域推定族属。 |
| 社会群体 | SocialGroup | 以性别、年龄、职业、亲属等形成的群体，如妇女、童子、商人、家族。族群优先归 EthnicGroup；明确的组织归 Organization。 |
| 组织机构 | Organization | 有组织边界的官署、军队、会社、宗教组织等。寺院僧团作为组织归此类，寺院建筑或地点归 Place。 |
| 地点 | Place | 历史行政区、聚落、山川、建筑场所等。行政区与同名城址不能仅因同名合并。 |
| 时间与节令 | TimeEntity | 朝代、年号、年份、时期、季节、日期及具名节日节期。保留原称；不自行换算公历或推定某年。 |
| 历史事件 | HistoricalEvent | 特定历史语境中的某次事件，如某次迁徙、战争、灾害、修建。一次具体祭祀可归此类，其所体现的惯行习俗另归 CulturalPractice。 |
| 文化习俗 | CulturalPractice | 惯行或反复开展的习俗、仪式、技艺与文化实践。通用习俗概念与有明确差异的地方形态可分开；不得凭同名直接认定内容一致。 |
| 制度与职官 | InstitutionalConcept | 制度、规章、礼制、官职等概念；具体官署归 Organization，任职者归 Person。 |
| 信仰对象 | BeliefEntity | 被崇奉或被叙述为超自然存在的对象。神像、神牌归 PhysicalThing；祖先不自动视为神灵。 |
| 物质对象 | PhysicalThing | 器物、食品、服饰、材料、动植物及地方物产等；可辨识对象类别也可入此类，但具体物件与类别须注明区别。 |
| 文献与作品 | Document | 志书、文书、篇章及可辨识的歌谣、谚语、传说作品。传说只是叙述性质时不另建作品节点。作品、版本、篇章分别标识。 |
| 文献记载 | TextualRecord | 整理生成的支撑节点，表示特定来源、位置和语境下的一条核心记述；保存于 records，不重复放入 entities。 |

### 边界处理

- 寺院：建筑场所与宗教组织确实都被描述时，可建两节点，并以 LOCATED_IN 连接组织与场所；不能仅见寺名就生成两节点。
- 族称：历史名称只在原文明示同指时列为别名。相似称谓、现代对应或族群源流说法不构成合并依据。
- 泛称人群：“妇女这一类别”和“某地某时的妇女人群”须以 identity_scope 区分。本项目的具体习俗断言通常指向后者。
- 神灵与人物：若原文明确区分历史人物与其神格，分开建节点；本版没有专门关系表达神格化，可写入待核说明，不能自行造关系。
- 类型无法容纳的内容进入 review_notes；不输出 Other，不临时增加类型。

## 三、实体身份、命名和别名

### 1. 标识与名称分离

- entity_id 是唯一身份标识；entity_name 是展示名称，同名允许有多个 ID。
- 新实体 ID：`{dataset_id}_{batch_id}_E001`；新记载 ID：`{dataset_id}_{batch_id}_R001`；新断言 ID：`{dataset_id}_{batch_id}_L001`。序号依首次出现顺序分配。
- dataset_id 和 batch_id 由调用方提供且组合唯一。重跑同一批次必须复用或替换整批结果，不追加重复 ID。大文献须预先划分唯一批次，不依赖模型自行连续计数。
- 复用已有 ID 仅限输入实体登记表中已明确对应的实体。输出中仍附该实体完整条目；登记表原字段保持不变，本次补充证据合并去重，不无依据覆盖旧描述。
- 合并条件：类型兼容，身份与适用范围明确一致，并有原文或输入登记表依据。单凭同名、同姓、相似描述、跨文献邻近位置均不足以合并。

### 2. 身份范围 identity_scope

每个普通实体必填对象：`{"level":"record|batch|registered","key":"对应范围编号","note":"限定说明"}`。level 实际只填其中一个值。

- record：仅此条记载可辨识的局部对象，如未能跨段定位的“男家”。key 填 record_id。
- batch：本批内可明确视为同一对象，但尚未获得跨批统一身份。key 填 dataset_id 与 batch_id 的组合。
- registered：复用输入登记表中的统一实体。key 填该 entity_id，并依据登记表确定身份。
- 不凭知名程度擅自生成全局统一 ID。identity_scope 不等于事实适用地域；后者放在记载 context 或关系 qualifiers。
- 本县、此地等指称只有输入上下文能明确对应时才解析为具体地点；否则保留局部名称与范围，或进入待核，不能根据志书题名直接替换。

### 3. 别名

aliases 为对象数组，每项固定为：`{"name":"原文别称","designation_type":"自称/他称/旧称/别称/未详中的一个","evidence":{"evidence_type":"原文","quote":"明确说明同指的原文","locator":null,"metadata_field":null},"applicable_time_ids":[]}`。

只有名称同指明确时收录；是否自称、他称、旧称不明填未详。别名适用时期无依据时用空数组，不以书的版本年代代替。量词、数量、年龄、频率和条件通常作为属性或限定，不单建实体。

Document 的 attributes.document_kind 必填 `work`、`edition`、`section`、`oral_work` 或 `unspecified`。版本与作品节点不同；版本信息不详可将直接来源标为 unspecified，不虚构具体版本。

## 四、关系类型

除 HAS_SPOUSE 为对称关系，其他关系均按箭头方向保存。每条关系是独立断言，允许同一主体、关系、客体在不同记载或不同限定下出现多条。所有 ID 均引用本次输出中的 entities 或 records。

### 1. 模型抽取的内容关系（30 种）

| 中文关系 | 英文标识 | 主体 → 客体 | 范围与约束 |
|---|---|---|---|
| 族群归属 | HAS_ETHNIC_AFFILIATION | Person / SocialGroup → EthnicGroup | 仅明确族属，不据姓氏推断。 |
| 组织隶属 | AFFILIATED_WITH | Person / Organization → Organization | 成员归属或上下级组织关系。 |
| 担任职官 | HOLDS_OFFICE | Person → InstitutionalConcept | 保留任期、任地和职责。 |
| 籍贯为 | HAS_NATIVE_PLACE | Person → Place | 与出生地、居住地分开。 |
| 居住于 | RESIDES_IN | Person → Place | 原文明确居住或定居；行经不算。本版新增。 |
| 出生于 | BORN_IN | Person → Place | 仅明确出生地，不能由籍贯推得。本版新增。 |
| 父母为 | HAS_PARENT | Person → Person | 子女指向父母，qualifiers.role 保存父亲/母亲/未详。 |
| 配偶为 | HAS_SPOUSE | Person ↔ Person | 对称；每条记载内按 ID 字符串升序存端点，只存一次；否定、时期或不同记载分别保留。 |
| 分布于 | DISTRIBUTED_IN | EthnicGroup / SocialGroup → Place | 某一时期的分布或居住，不表示永久分布。 |
| 行政隶属 | ADMINISTRATIVELY_WITHIN | Place → Place | 仅行政区隶属，保留时期。 |
| 位于 | LOCATED_IN | Place / Organization / PhysicalThing → Place | 地理位置；不替代人物居住或行政隶属。 |
| 参与 | PARTICIPATES_IN | Person / EthnicGroup / SocialGroup / Organization → HistoricalEvent / CulturalPractice | 一次参与用此项；群体惯行某习俗优先用 PRACTICES_CUSTOM，不能仅凭同一事实重复两项。 |
| 发生地点 | OCCURS_AT | HistoricalEvent → Place | 某次事件发生地。 |
| 发生时间 | OCCURS_DURING | HistoricalEvent → TimeEntity | 某次事件时间。 |
| 实行习俗 | PRACTICES_CUSTOM | EthnicGroup / SocialGroup / Organization → CulturalPractice | 群体或组织惯行某习俗；个人一次参与用 PARTICIPATES_IN。 |
| 习俗适用地域 | CUSTOM_PRACTICED_IN | CulturalPractice → Place | 正文明示该习俗在某地流行/实行；不能用来源地域代替。原文否定则 polarity=否定。 |
| 关联节令 | ASSOCIATED_WITH_CALENDAR | CulturalPractice → TimeEntity | 节日、日期、季节联系。 |
| 适用时期 | APPLIES_DURING | CulturalPractice / InstitutionalConcept → TimeEntity | 历史时期，非版本年份；任职者任期放 HOLDS_OFFICE 的限定。 |
| 遵循制度 | FOLLOWS_INSTITUTION | Person / SocialGroup / Organization / CulturalPractice → InstitutionalConcept | 有明确遵循或受规范约束的记述。 |
| 使用物品 | USES_OBJECT | CulturalPractice / HistoricalEvent → PhysicalThing | 实际使用及用途；否定仍按肯否限定处理。 |
| 祭祀对象 | WORSHIPS | CulturalPractice → BeliefEntity / Person / SocialGroup | 活动所祭祀或祈请的对象；祖先群体不自动神灵化。 |
| 涉及作品 | INVOLVES_WORK | CulturalPractice → Document | 活动使用、唱诵、讲述的作品。 |
| 出产 | PRODUCES | Place → PhysicalThing | 明确物产记述。 |
| 由材料制成 | MADE_OF | PhysicalThing → PhysicalThing | 器物指向材料。 |
| 包含环节 | HAS_COMPONENT_ACTIVITY | CulturalPractice → CulturalPractice；HistoricalEvent → HistoricalEvent | 仅允许两组同类型配对，不是类型继承；无证据不分解普通动作。 |
| 族群源出 | ETHNIC_ORIGIN_CLAIM | EthnicGroup → EthnicGroup / SocialGroup / Place | 记录来源提出的源流说法，不转写为已证实族源。 |
| 编撰或创作 | CREATES_WORK | Person / Organization → Document | qualifiers.role 保留编、纂、修、撰等职责。 |
| 引用 | CITES | Document → Document | 引用方指向被引作品；引文从当前直接来源取得时仍以当前直接来源建记录，不伪装成亲见被引书。 |
| 摘录见于 | EXCERPTED_IN | Document → Document | 原作品指向收录其摘录的作品；与 CITES 方向不同，无明确收录依据不推断。 |
| 版本属于 | EDITION_OF | Document → Document | edition 指向 work；书目证据明确时才建立。 |

### 2. 程序派生的结构关系（7 种）

以下不由模型重复填写进 relationships，以记录字段为唯一来源。派生边使用 derived=true，承接 record_id 和证据来源，不冒充正文中的历史断言。

| 中文关系 | 英文标识 | 方向 | 派生规则 |
|---|---|---|---|
| 出自文献 | FROM_DOCUMENT | TextualRecord → Document | 每条记录的 source_document_id 非空时生成。 |
| 记述对象 | DESCRIBES | TextualRecord → 非 TextualRecord 实体 | 由 main_entity_ids 去重生成；这些 ID 必须包含本记录所有内容关系的两端实体。 |
| 记载于 | RECORDED_IN | 非 TextualRecord 实体 → Document | 由同条记录的 main_entity_ids 与 source_document_id 生成，不把该连接视为事实真实性背书。 |
| 来源地域 | HAS_SOURCE_REGION | TextualRecord → Place | 由 context.source_region_ids 生成；只能解释来源背景。 |
| 记载适用地域 | HAS_APPLICABLE_PLACE | TextualRecord → Place | 由 context.applicable_place_ids 生成。 |
| 记载适用时间 | HAS_APPLICABLE_TIME | TextualRecord → TimeEntity | 由 context.applicable_time_ids 生成。 |
| 记载涉及人群 | CONCERNS_GROUP | TextualRecord → EthnicGroup / SocialGroup | 由 context.concerned_group_ids 生成，不推定实际参与。 |

本版共 37 种关系，其中 30 种内容关系、7 种派生结构关系。与原版相比，仅增加人物居住与出生地两项内容关系。

## 五、证据、记载和限定

### 1. 证据来源

证据固定为：`{"evidence_type":"原文或输入元数据","quote":"逐字证据","locator":null,"metadata_field":null}`。

- 原文：quote 必须是输入原文中的连续原样片段；保留异体字、标点和疑字。locator 是调用方给出的定位或可验证的段落位置。metadata_field=null。
- 输入元数据：只引用调用方提供的书名、版本、书目信息、题名来源地域或登记表身份等。metadata_field 必须写明输入字段路径，quote 必须逐字取自该字段；locator 可为 null。
- 空缺信息不补造。输入的版本年份只能用于版本属性，不能转作内容发生年代。书名可支持来源地域背景，但不能直接支持正文事实适用地域。
- 程序生成 ID、记载节点和连接不需要伪造原文逐字提及；其生成依据是已有记录字段。名称未知时可用明确标识的整理标签，不把标签当史料原称。

### 2. 记载单位

- 一条 TextualRecord 围绕一项核心陈述组织。来源、适用范围、肯否或叙述性质需要分别处理时拆分；同一句可拆出数条记录。
- records.quote 保存核心陈述及理解必要的连续上下文。拆分后的不同记录允许引用同一句完整原文。
- source_document_id 指向直接读取的来源 Document；完全未知时为 null，并在 review_notes 说明，不虚构书名。书名已知但版本不详时允许建 unspecified 来源节点。
- statement_type 只取：作者叙述、转引、传说、信仰说法、作者推测、未详。
- context 的四个 *_ids 数组必须存在；每个非空字段须在 context_evidence 中按同名字段列出至少一条证据。不可见的前后文不能作为推断依据。

### 3. 内容断言

- relationships 只放内容关系；每项 record_ids 恰好含一个记录 ID。不同来源或不同记录分别建断言，不在抽取时跨记录合并。
- polarity 只取肯定、否定、存疑。它表示原文陈述性质，不是模型置信度。模型自己拿不准而原文不存疑时，放待核，不捏造“存疑事实”。
- 每条内容关系的 quote 必须逐字包含在所引 records.quote 中。所有源、目标、限定实体 ID 必须存在。
- qualifiers 固定包含 time_ids、place_ids、group_ids、role、conditions、other。前三项为实体 ID 数组，role 为字符串或 null，conditions 为原文条件字符串数组，other 为附加限定对象。无依据分别用 []、null 或 {}。
- 记录 context 是整条记录的范围；qualifiers 是单条断言的额外限定。实际范围须联合阅读两者；不要求反复复制相同限定，也不能擅自放宽记录范围。
- 否定仅作用于原文明示否定的谓词及其条件；不把整条句子里的所有关系一并否定。“不行某俗”不证明该俗本身不存在，也不自动否定其他地区实行。
- 同一记录内，仅在主体、关系、客体、肯否、限定均一致时去重；对称配偶关系先规范端点顺序。不同记录不去重成一条。
- 父母、自身配偶、组成与行政隶属等不允许无意义自环。出现身份冲突须待核，不为满足输出而强行连接。

## 六、输出契约与缺失值

完整示例见《抽取结果_演示.json》，示例为虚构文本，不是史料结论。顶层固定包含 schema_version、dataset_id、batch_id、entities、records、relationships、review_notes。

- schema_version 固定为 "1.0"。entities 不包含 TextualRecord；records 专门保存它。
- entity_name、entity_type、description、ID、内容关系 quote 不得为空或 null；没有结果的数组为 []；未知的可空值为 null；没有附加属性的对象为 {}。
- evidence 为数组。非生成的普通实体至少有一条原文或输入元数据证据。不要把来源 Document 的书目证据假写为正文摘句。
- 新实体 descriptions 根据原文或允许的输入元数据填写，不补百科。复用登记表的实体保留既有描述及来源，不宣称它来自本批原文。
- review_notes 每项固定包含 note_id、issue_type、message、entity_ids、record_ids、evidence。issue_type 取指代不明、身份待核、类型未覆盖、关系未覆盖、元数据缺失、疑似讹字、其他。ID 引用必须存在；未建节点的问题用空数组。
- 拒绝抽取某关系时说明原因和证据；空数组不是省略本批应处理的内容的理由。输入过长时由调用方拆批，不静默截断。

## 七、验收要求

类型与关系须来自白名单；关系两端类型、方向、配偶对称性合法；全部 ID 唯一且引用存在；每个内容断言恰好对应一条记录；记录主要实体覆盖断言端点；证据逐字可定位；书目元数据与正文依据分开；否定、存疑、转引及局部范围完整保留。

模型自检只能减少错误，不能代替程序校验和人工核对。生产使用前，至少检查同名异人、局部人群、正反说法、元数据来源、对称配偶五类样例。
