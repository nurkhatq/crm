import { useState } from 'react'
import { useQuery } from 'react-query'
import Layout from '@/components/Layout'
import { triggerSync, triggerEnhancedSync, getApiAnalysis } from '@/lib/api'

export default function SyncPage() {
  const [isSyncing, setIsSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState<string | null>(null)

  const { data: apiAnalysis, refetch: refetchAnalysis } = useQuery('api-analysis', getApiAnalysis)

  const syncTypes = [
    { key: 'products', name: 'Товары', description: 'Синхронизация товаров, услуг и комплектов' },
    { key: 'customers', name: 'Клиенты', description: 'Синхронизация контрагентов' },
    { key: 'documents', name: 'Документы', description: 'Синхронизация документов продаж и закупок' },
    { key: 'stock', name: 'Остатки', description: 'Синхронизация остатков товаров' },
    { key: 'stores', name: 'Склады', description: 'Синхронизация справочника складов' },
    { key: 'full', name: 'Полная синхронизация', description: 'Синхронизация всех данных' }
  ]

  const enhancedSyncTypes = [
    { key: 'products', name: 'Улучшенные товары', description: 'Товары с расширенными данными' },
    { key: 'services', name: 'Услуги', description: 'Синхронизация услуг' },
    { key: 'bundles', name: 'Комплекты', description: 'Синхронизация комплектов' },
    { key: 'stores', name: 'Склады', description: 'Справочник складов' },
    { key: 'currencies', name: 'Валюты', description: 'Справочник валют' },
    { key: 'turnover', name: 'Обороты', description: 'Отчеты по оборотам товаров' },
    { key: 'retail_documents', name: 'Розничные документы', description: 'Розничные продажи и возвраты' },
    { key: 'employee_context', name: 'Контекст сотрудника', description: 'Информация о текущем пользователе' },
    { key: 'full', name: 'Полная улучшенная синхронизация', description: 'Все доступные данные с расширенной информацией' }
  ]

  const handleSync = async (type: string, enhanced: boolean = false) => {
    setIsSyncing(true)
    setSyncResult(null)
    
    try {
      const result = enhanced 
        ? await triggerEnhancedSync(type, true)
        : await triggerSync(type, true)
      
      setSyncResult(`Синхронизация ${type} запущена успешно!`)
      await refetchAnalysis()
    } catch (error) {
      setSyncResult(`Ошибка синхронизации: ${error}`)
    } finally {
      setIsSyncing(false)
    }
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Управление синхронизацией</h1>
          <p className="text-gray-600">Синхронизация данных с МойСклад</p>
        </div>

        {/* Sync Result */}
        {syncResult && (
          <div className={`p-4 rounded-md ${syncResult.includes('Ошибка') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
            {syncResult}
          </div>
        )}

        {/* Standard Sync */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Стандартная синхронизация</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {syncTypes.map((syncType) => (
              <div key={syncType.key} className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-medium text-gray-900 mb-2">{syncType.name}</h3>
                <p className="text-sm text-gray-600 mb-3">{syncType.description}</p>
                <button
                  onClick={() => handleSync(syncType.key, false)}
                  disabled={isSyncing}
                  className="w-full btn btn-secondary text-sm disabled:opacity-50"
                >
                  {isSyncing ? 'Синхронизация...' : 'Запустить'}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Enhanced Sync */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Расширенная синхронизация
            <span className="ml-2 text-sm font-normal text-blue-600">(Рекомендуется)</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {enhancedSyncTypes.map((syncType) => (
              <div key={syncType.key} className="p-4 border border-blue-200 rounded-lg bg-blue-50">
                <h3 className="font-medium text-blue-900 mb-2">{syncType.name}</h3>
                <p className="text-sm text-blue-700 mb-3">{syncType.description}</p>
                <button
                  onClick={() => handleSync(syncType.key, true)}
                  disabled={isSyncing}
                  className="w-full btn btn-primary text-sm disabled:opacity-50"
                >
                  {isSyncing ? 'Синхронизация...' : 'Запустить'}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* API Analysis Summary */}
        {apiAnalysis && (
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Статистика API</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {Object.keys(apiAnalysis.available_endpoints).length}
                </div>
                <div className="text-sm text-green-600">Доступных endpoints</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {apiAnalysis.unavailable_endpoints.length}
                </div>
                <div className="text-sm text-red-600">Недоступных endpoints</div>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {apiAnalysis.api_errors.length}
                </div>
                <div className="text-sm text-yellow-600">Ошибок API</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {apiAnalysis.recommendations.length}
                </div>
                <div className="text-sm text-blue-600">Рекомендаций</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}



