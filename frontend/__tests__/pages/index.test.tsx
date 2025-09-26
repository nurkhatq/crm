import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import Home from '@/pages/index'

// Mock the API
jest.mock('@/lib/api', () => ({
  getKPIMetrics: jest.fn(() => Promise.resolve({
    total_products: 100,
    total_customers: 50,
    total_documents: 200,
    total_revenue: 1000000,
    total_stock_value: 500000,
    low_stock_products: 5,
    last_sync: '2024-01-01T00:00:00Z'
  }))
}))

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe('Home Page', () => {
  it('renders dashboard title', () => {
    renderWithQueryClient(<Home />)
    expect(screen.getByText('Панель управления')).toBeInTheDocument()
  })

  it('renders sync button', () => {
    renderWithQueryClient(<Home />)
    expect(screen.getByText('Синхронизировать')).toBeInTheDocument()
  })

  it('renders quick actions', () => {
    renderWithQueryClient(<Home />)
    expect(screen.getByText('Быстрые действия')).toBeInTheDocument()
    expect(screen.getByText('Товары')).toBeInTheDocument()
    expect(screen.getByText('Клиенты')).toBeInTheDocument()
    expect(screen.getByText('Документы')).toBeInTheDocument()
  })
})
