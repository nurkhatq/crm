import { render, screen } from '@testing-library/react'
import KPICard from '@/components/KPICard'

describe('KPICard', () => {
  it('renders with correct title and value', () => {
    render(
      <KPICard
        title="Test Title"
        value="123"
        icon="📊"
        color="blue"
      />
    )

    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('123')).toBeInTheDocument()
    expect(screen.getByText('📊')).toBeInTheDocument()
  })

  it('applies correct color classes', () => {
    const { container } = render(
      <KPICard
        title="Test Title"
        value="123"
        icon="📊"
        color="red"
      />
    )

    const iconContainer = container.querySelector('.bg-red-50.text-red-600')
    expect(iconContainer).toBeInTheDocument()
  })
})
