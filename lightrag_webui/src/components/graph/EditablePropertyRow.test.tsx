import { expect, test } from 'bun:test'
import { fireEvent, screen } from '@testing-library/react'
import { renderWithProviders } from '@/test/render'
import EditablePropertyRow from './EditablePropertyRow'

test('relation details display Chinese while editing retains stored codes', () => {
  const { container } = renderWithProviders(
    <EditablePropertyRow name="keywords" entityType="edge" value="PARTICIPATES_IN,OCCURS_AT" isEditable />
  )
  expect(screen.getAllByText('参与、发生地点')).toHaveLength(1)
  const editIcon = container.querySelector('svg.lucide-pencil')
  expect(Boolean(editIcon)).toBe(true)
  fireEvent.click(editIcon!)
  expect((screen.getByRole('textbox') as HTMLTextAreaElement).value).toBe('PARTICIPATES_IN,OCCURS_AT')
})

test('ordinary descriptions are not treated as relation identifiers', () => {
  renderWithProviders(
    <EditablePropertyRow name="description" entityType="edge" value="PARTICIPATES_IN" />
  )
  expect(screen.getAllByText('PARTICIPATES_IN')).toHaveLength(1)
  expect(screen.queryAllByText('参与')).toHaveLength(0)
})
