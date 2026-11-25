// Domain relation labels are presentation only; stored identifiers stay unchanged.
const relationshipLabels: Record<string, string> = {
  HAS_ETHNIC_AFFILIATION: '族群归属',
  AFFILIATED_WITH: '组织隶属',
  HOLDS_OFFICE: '担任职官',
  OFFICE_IN_ORGANIZATION: '职官所属机构',
  OFFICE_DEFINED_BY: '职官设置依据',
  OFFICE_JURISDICTION: '职官管辖地域',
  HAS_NATIVE_PLACE: '籍贯为',
  RESIDES_IN: '居住于',
  BORN_IN: '出生于',
  HAS_PARENT: '父母为',
  HAS_SPOUSE: '配偶为',
  DISTRIBUTED_IN: '分布于',
  ADMINISTRATIVELY_WITHIN: '行政隶属',
  LOCATED_IN: '位于',
  PARTICIPATES_IN: '参与',
  OCCURS_AT: '发生地点',
  OCCURS_DURING: '发生时间',
  OCCURS_DURING_CALENDAR: '发生节令',
  PRACTICES_CUSTOM: '实行习俗',
  CUSTOM_PRACTICED_IN: '习俗适用地域',
  ASSOCIATED_WITH_CALENDAR: '关联节令',
  HAS_CALENDAR_DATE: '节令对应日期',
  APPLIES_DURING: '适用时期',
  FOLLOWS_INSTITUTION: '遵循制度',
  INSTITUTION_APPLIES_IN: '制度适用地域',
  INSTITUTION_APPLIES_TO: '制度适用对象',
  USES_OBJECT: '使用物品',
  WORSHIPS: '祭祀对象',
  INVOLVES_WORK: '涉及作品',
  PRODUCES: '出产',
  MADE_OF: '由材料制成',
  HAS_COMPONENT_ACTIVITY: '包含环节',
  ETHNIC_ORIGIN_CLAIM: '族群源出',
  CREATES_WORK: '编撰或创作',
  CITES: '引用',
  EXCERPTED_IN: '摘录见于',
  EDITION_OF: '版本属于',
  RECORDED_IN: '记载于',
  FROM_DOCUMENT: '出自文献',
  DESCRIBES: '记述对象',
  HAS_SOURCE_REGION: '来源地域',
  HAS_APPLICABLE_PLACE: '记载适用地域',
  HAS_APPLICABLE_TIME: '记载适用时间',
  HAS_APPLICABLE_CALENDAR: '记载适用节令',
  CONCERNS_GROUP: '记载涉及人群'
}

/** Translate fixed relation codes, preserving unknown keywords as written. */
export const formatRelationshipKeywords = (value: unknown): string | undefined => {
  if (typeof value !== 'string') return undefined
  return value
    .split(/[,，;；]|<SEP>/)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => Object.hasOwn(relationshipLabels, part) ? relationshipLabels[part] : part)
    .join('、') || undefined
}
