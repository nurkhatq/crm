// pages/index.tsx - Современная главная страница Dashboard
import { useState, useEffect } from 'react'
import { NextPage } from 'next'
import Head from 'next/head'
import { getProducts, getCustomers, getKPIMetrics, getSyncStatus, triggerSync, testMoySkladConnection } from '@/lib/api'
import { 
  Package, 
  Users, 
  FileText, 
  TrendingUp, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  BarChart3,
  Activity,
  DollarSign,
  ShoppingCart,
  Warehouse,
  Zap
} from 'lucide-react'
import Layout from '../components/Layout'

interface DashboardStats {
  products: { total: number; recent: number }
  customers: { total: number; recent: number }
  documents: { total: number; recent: number }
  revenue: { total: number; trend: number }
}

interface SyncStatus {
  id: number
  sync_type: string
  entity_type?: string
  status: string
  started_at: string
  completed_at?: string
  records_processed: number
  records_created: number
  records_updated: number
  records_errors: number
}

const Dashboard: NextPage = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [syncStatuses, setSyncStatuses] = useState<SyncStatus[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSyncing, setIsSyncing] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<any>(null)

  useEffect(() => {
    loadDashboardData()
    loadSyncStatus()
    checkConnection()
  }, [])

  const loadDashboardData = async () => {
    try {
      setIsLoading(true)
      
      // Загружаем статистику
      const [productsData, customersData, kpiData] = await Promise.all([
        getProducts({ limit: 1 }),
        getCustomers({ limit: 1 }),
        getKPIMetrics()
      ])

      setStats({
        products: { 
          total: kpiData.total_products || 0, 
          recent: productsData.length || 0 
        },
        customers: { 
          total: kpiData.total_customers || 0, 
          recent: customersData.length || 0 
        },
        documents: { 
          total: kpiData.total_documents || 0, 
          recent: 0 
        },
        revenue: { 
          total: kpiData.total_revenue || 0, 
          trend: 0 
        }
      })
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadSyncStatus = async () => {
    try {
      const data = await getSyncStatus()
      setSyncStatuses(data)
    } catch (error) {
      console.error('Ошибка загрузки статуса синхронизации:', error)
    }
  }

  const checkConnection = async () => {
    try {
      const data = await testMoySkladConnection()
      setConnectionStatus(data)
    } catch (error) {
      console.error('Ошибка проверки соединения:', error)
    }
  }

  const handleSync = async (syncType: string = 'full') => {
    try {
      setIsSyncing(true)
      
      const result = await triggerSync(syncType, false)
      console.log('Синхронизация запущена:', result)
      
      // Обновляем статус через несколько секунд
      setTimeout(() => {
        loadSyncStatus()
        loadDashboardData()
      }, 2000)
    } catch (error) {
      console.error('Ошибка запроса синхронизации:', error)
    } finally {
      setIsSyncing(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'in_progress':
        return <Clock className="h-5 w-5 text-blue-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const formatDateTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <>
      <Head>
        <title>Dashboard - CRM МойСклад</title>
      </Head>
      <Layout>
        <div className="space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Dashboard
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Обзор системы CRM с интеграцией МойСклад
              </p>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => handleSync('products')}
                disabled={isSyncing}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              >
                <Package className="h-4 w-4 mr-2" />
                Товары
              </button>
              
              <button
                onClick={() => handleSync('customers')}
                disabled={isSyncing}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              >
                <Users className="h-4 w-4 mr-2" />
                Клиенты
              </button>
              
              <button
                onClick={() => handleSync('full')}
                disabled={isSyncing}
                className="inline-flex items-center px-6 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 transform hover:scale-105"
              >
                {isSyncing ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4 mr-2" />
                )}
                {isSyncing ? 'Синхронизация...' : 'Полная синхронизация'}
              </button>
            </div>
          </div>

          {/* Connection Status */}
          {connectionStatus && (
            <div className={`rounded-xl border-l-4 p-4 ${
              connectionStatus.api_accessible 
                ? 'bg-green-50 border-green-400 dark:bg-green-900/20 dark:border-green-500' 
                : 'bg-red-50 border-red-400 dark:bg-red-900/20 dark:border-red-500'
            }`}>
              <div className="flex">
                <div className="flex-shrink-0">
                  {connectionStatus.api_accessible ? (
                    <CheckCircle className="h-5 w-5 text-green-400" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-400" />
                  )}
                </div>
                <div className="ml-3">
                  <h3 className={`text-sm font-medium ${
                    connectionStatus.api_accessible ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'
                  }`}>
                    {connectionStatus.api_accessible ? 'Подключение активно' : 'Проблемы с подключением'}
                  </h3>
                  <p className={`mt-1 text-sm ${
                    connectionStatus.api_accessible ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'
                  }`}>
                    {connectionStatus.message}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Stats Cards */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-white dark:bg-gray-800 overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Package className="h-8 w-8 text-blue-600" />
                  </div>
                  <div className="ml-4 w-0 flex-1">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {isLoading ? '...' : (stats?.products.total || 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Товаров</div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 px-6 py-3">
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Добавлено недавно: {stats?.products.recent || 0}
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Users className="h-8 w-8 text-green-600" />
                  </div>
                  <div className="ml-4 w-0 flex-1">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {isLoading ? '...' : (stats?.customers.total || 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Клиентов</div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 px-6 py-3">
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Новых за неделю: {stats?.customers.recent || 0}
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <FileText className="h-8 w-8 text-purple-600" />
                  </div>
                  <div className="ml-4 w-0 flex-1">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {isLoading ? '...' : (stats?.documents.total || 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Документов</div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 px-6 py-3">
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  За сегодня: {stats?.documents.recent || 0}
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <TrendingUp className="h-8 w-8 text-yellow-600" />
                  </div>
                  <div className="ml-4 w-0 flex-1">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {isLoading ? '...' : '₽' + (stats?.revenue.total || 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Оборот</div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 px-6 py-3">
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Тренд: {stats?.revenue.trend || 0}%
                </div>
              </div>
            </div>
          </div>

          {/* Sync Status */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  История синхронизации
                </h2>
                <button
                  onClick={loadSyncStatus}
                  className="inline-flex items-center px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Обновить
                </button>
              </div>
            </div>
            
            <div className="p-6">
              {syncStatuses.length > 0 ? (
                <div className="space-y-4">
                  {syncStatuses.slice(0, 5).map((sync) => (
                    <div key={sync.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(sync.status)}
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {sync.sync_type}{sync.entity_type ? ` - ${sync.entity_type}` : ''}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            {formatDateTime(sync.started_at)}
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {sync.records_processed} записей
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          +{sync.records_created} / ~{sync.records_updated}
                          {sync.records_errors > 0 && (
                            <span className="text-red-500"> / !{sync.records_errors}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Activity className="h-8 w-8 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600 dark:text-gray-400">
                    Синхронизации еще не было
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Товары</h3>
                  <p className="text-blue-100 text-sm mb-4">
                    Управление ассортиментом и остатками
                  </p>
                  <a 
                    href="/products"
                    className="inline-flex items-center px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors"
                  >
                    Перейти
                    <Package className="h-4 w-4 ml-2" />
                  </a>
                </div>
                <Package className="h-12 w-12 text-blue-200" />
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Клиенты</h3>
                  <p className="text-green-100 text-sm mb-4">
                    База контрагентов и история взаимодействий
                  </p>
                  <a 
                    href="/customers"
                    className="inline-flex items-center px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors"
                  >
                    Перейти
                    <Users className="h-4 w-4 ml-2" />
                  </a>
                </div>
                <Users className="h-12 w-12 text-green-200" />
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Документы</h3>
                  <p className="text-purple-100 text-sm mb-4">
                    Отгрузки, приемки и другие документы
                  </p>
                  <a 
                    href="/documents"
                    className="inline-flex items-center px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors"
                  >
                    Перейти
                    <FileText className="h-4 w-4 ml-2" />
                  </a>
                </div>
                <FileText className="h-12 w-12 text-purple-200" />
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </>
  )
}

export default Dashboard