import { describe, expect, test } from 'bun:test'
import { formatRelationshipKeywords } from './relationshipLabels'

describe('domain relationship labels', () => {
  test('uses the Chinese schema labels for graph relations', () => {
    expect(formatRelationshipKeywords('PARTICIPATES_IN')).toBe('参与')
    expect(formatRelationshipKeywords('HAS_ETHNIC_AFFILIATION')).toBe('族群归属')
    expect(formatRelationshipKeywords('OCCURS_DURING_CALENDAR')).toBe('发生节令')
    expect(formatRelationshipKeywords('OFFICE_IN_ORGANIZATION')).toBe('职官所属机构')
  })

  test('displays merged relations separately and preserves unknown keywords', () => {
    expect(formatRelationshipKeywords('DESCRIBES,HAS_APPLICABLE_PLACE')).toBe('记述对象、记载适用地域')
    expect(formatRelationshipKeywords('RECORDED_IN<SEP>OCCURS_AT；自定义关系')).toBe('记载于、发生地点、自定义关系')
    expect(formatRelationshipKeywords('UNRECOGNIZED_CODE')).toBe('UNRECOGNIZED_CODE')
    expect(formatRelationshipKeywords('__proto__')).toBe('__proto__')
  })

  test('handles empty or absent relationship properties', () => {
    expect(formatRelationshipKeywords(undefined)).toBeUndefined()
    expect(formatRelationshipKeywords(null)).toBeUndefined()
    expect(formatRelationshipKeywords(' , ')).toBeUndefined()
  })
})
