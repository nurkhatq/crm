import { useState } from 'react'
import { useQuery } from 'react-query'
import { getApiAnalysis, testMoySkladConnection } from '@/lib/api'

export default function ApiAnalysis() {
  const { data: analysis, isLoading, refetch } = useQuery('api-analysis', getApiAnalysis)
  const [isTestingConnection, setIsTestingConnection] = useState(false)

  const handleTestConnection = async () => {
    setIsTestingConnection(true)
    try {
      const result = await testMoySkladConnection()
      alert(`Подключение: ${result.connected ? 'Успешно' : 'Ошибка'}`)
    } catch (error) {
      alert('Ошибка подключения к МойСклад')
    } finally {
      setIsTestingConnection(false)
    }
  }

  if (isLoading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!analysis) return null

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Анализ API МойСклад</h2>
        <button
          onClick={handleTestConnection}
          disabled={isTestingConnection}
          className="btn btn-secondary text-sm disabled:opacity-50"
        >
          {isTestingConnection ? '🔄' : '🔗'} Тест подключения
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Available Endpoints */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">Доступные endpoints</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {Object.entries(analysis.available_endpoints).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center py-2 px-3 bg-green-50 rounded-md">
                <div>
                  <span className="font-medium text-green-800">{value.description}</span>
                  <span className="text-sm text-green-600 ml-2">({key})</span>
                </div>
                <span className="text-sm font-bold text-green-700">
                  {typeof value.count === 'number' ? value.count.toLocaleString() : value.count}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Unavailable Endpoints */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">Недоступные endpoints</h3>
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {analysis.unavailable_endpoints.map((endpoint) => (
              <div key={endpoint} className="py-1 px-3 bg-gray-100 rounded-md text-sm text-gray-600">
                {endpoint}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* API Errors */}
      {analysis.api_errors && analysis.api_errors.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-3">⚠️ Проблемы с API</h3>
          <div className="space-y-2">
            {analysis.api_errors.map((error) => (
              <div key={error} className="py-2 px-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <div className="text-sm font-medium text-yellow-800">
                  {error === 'retailsale' && 'Розничные продажи недоступны'}
                  {error === 'pricetype' && 'Типы цен недоступны'}
                  {error === 'money_cash' && 'Отчет по кассе недоступен'}
                  {error === 'stock_all_current' && 'Текущие остатки недоступны'}
                  {!['retailsale', 'pricetype', 'money_cash', 'stock_all_current'].includes(error) && error}
                </div>
                <div className="text-xs text-yellow-600 mt-1">
                  {error === 'retailsale' && 'Данные о розничных продажах не синхронизируются'}
                  {error === 'pricetype' && 'Информация о типах цен отсутствует'}
                  {error === 'money_cash' && 'Отчеты по кассовым операциям недоступны'}
                  {error === 'stock_all_current' && 'Текущие остатки товаров не обновляются'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="mt-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Рекомендации</h3>
        <div className="space-y-2">
          {analysis.recommendations.map((recommendation, index) => (
            <div key={index} className="py-2 px-3 bg-blue-50 rounded-md text-sm text-blue-800">
              💡 {recommendation}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
