import { useState } from 'react'
import { useQuery } from 'react-query'
import Layout from '@/components/Layout'
import KPICard from '@/components/KPICard'
import TopProducts from '@/components/TopProducts'
import SyncButton from '@/components/SyncButton'
import StockOverview from '@/components/StockOverview'
import EnhancedProducts from '@/components/EnhancedProducts'
import ApiAnalysis from '@/components/ApiAnalysis'
import { getKPIMetrics } from '@/lib/api'

export default function Dashboard() {
  const [isRefreshing, setIsRefreshing] = useState(false)

  const { data: kpiData, isLoading: kpiLoading, refetch: refetchKPI } = useQuery(
    'kpi-metrics',
    getKPIMetrics,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  )

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refetchKPI()
    setIsRefreshing(false)
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Панель управления</h1>
            <p className="text-gray-600">Обзор данных из МойСклад</p>
          </div>
          <SyncButton onSync={handleRefresh} isLoading={isRefreshing} enhanced={true} />
        </div>

        {/* KPI Cards */}
        {kpiLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="card animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : kpiData ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <KPICard
              title="Товары"
              value={kpiData.total_products}
              icon="📦"
              color="blue"
            />
            <KPICard
              title="Клиенты"
              value={kpiData.total_customers}
              icon="👥"
              color="green"
            />
            <KPICard
              title="Документы"
              value={kpiData.total_documents}
              icon="📄"
              color="purple"
            />
                     <KPICard
                       title="Выручка"
                       value={`${kpiData.total_revenue.toLocaleString()} ${kpiData.currency || 'ТЕН'}`}
                       icon="💰"
                       color="yellow"
                     />
          </div>
        ) : null}

        {/* Additional KPI Cards */}
        {kpiData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <KPICard
              title="Товары с низким остатком"
              value={kpiData.low_stock_products}
              icon="⚠️"
              color="red"
            />
            <KPICard
              title="Последняя синхронизация"
              value={kpiData.last_sync ? new Date(kpiData.last_sync).toLocaleString('ru-RU') : 'Неизвестно'}
              icon="🔄"
              color="gray"
            />
          </div>
        )}

        {/* Top Products */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TopProducts />
        </div>

        {/* Stock Overview */}
        <StockOverview />

        {/* Enhanced Products */}
        <EnhancedProducts />

        {/* API Analysis */}
        <ApiAnalysis />

        {/* Quick Actions */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Быстрые действия</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="/products"
              className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
            >
              <div className="text-2xl mb-2">📦</div>
              <h3 className="font-medium text-gray-900">Товары</h3>
              <p className="text-sm text-gray-600">Просмотр и управление товарами</p>
            </a>
            <a
              href="/customers"
              className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
            >
              <div className="text-2xl mb-2">👥</div>
              <h3 className="font-medium text-gray-900">Клиенты</h3>
              <p className="text-sm text-gray-600">Управление клиентской базой</p>
            </a>
            <a
              href="/documents"
              className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
            >
              <div className="text-2xl mb-2">📄</div>
              <h3 className="font-medium text-gray-900">Документы</h3>
              <p className="text-sm text-gray-600">Просмотр документов</p>
            </a>
          </div>
        </div>
      </div>
    </Layout>
  )
}
