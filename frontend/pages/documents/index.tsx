import { useState } from 'react'
import { useQuery } from 'react-query'
import Layout from '@/components/Layout'
import { getDocuments } from '@/lib/api'

interface Document {
  id: number
  document_type: string
  number: string
  date: string
  counterparty_name: string
  total_amount: number
  currency: string
  status: string
  description: string
  external_id: string
  created_at: string
  updated_at: string
}

export default function DocumentsPage() {
  const [filters, setFilters] = useState({
    search: '',
    document_type: '',
    skip: 0,
    limit: 20,
  })

  const { data: documents, isLoading, error } = useQuery(
    ['documents', filters],
    () => getDocuments(filters),
    {
      keepPreviousData: true,
    }
  )

  const handleFiltersChange = (newFilters: Partial<typeof filters>) => {
    setFilters(prev => ({ ...prev, ...newFilters, skip: 0 }))
  }

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, skip: page * prev.limit }))
  }

  const getDocumentTypeLabel = (type: string) => {
    const types: { [key: string]: string } = {
      'demand': 'Отгрузка',
      'salesreturn': 'Возврат покупателя',
      'purchaseorder': 'Заказ поставщику',
      'supply': 'Приемка',
      'invoicein': 'Счет поставщика',
      'purchasereturn': 'Возврат поставщику',
      'enter': 'Оприходование',
      'loss': 'Списание',
      'move': 'Перемещение',
      'inventory': 'Инвентаризация',
      'retaildemand': 'Розничная продажа',
      'retailsalesreturn': 'Возврат розничной продажи'
    }
    return types[type] || type
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'выполнен':
        return 'bg-green-100 text-green-800'
      case 'pending':
      case 'ожидает':
        return 'bg-yellow-100 text-yellow-800'
      case 'cancelled':
      case 'отменен':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const totalPages = documents ? Math.ceil(documents.length / filters.limit) : 0
  const currentPage = filters.skip / filters.limit

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Документы</h1>
            <p className="text-gray-600">Управление документами из МойСклад</p>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">
              Всего документов: {documents?.length || 0}
            </span>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Поиск по номеру или контрагенту
              </label>
              <input
                type="text"
                placeholder="Введите номер документа или название контрагента..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={filters.search}
                onChange={(e) => handleFiltersChange({ search: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Тип документа
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={filters.document_type}
                onChange={(e) => handleFiltersChange({ document_type: e.target.value })}
              >
                <option value="">Все типы</option>
                <option value="demand">Отгрузка</option>
                <option value="salesreturn">Возврат покупателя</option>
                <option value="purchaseorder">Заказ поставщику</option>
                <option value="supply">Приемка</option>
                <option value="invoicein">Счет поставщика</option>
                <option value="purchasereturn">Возврат поставщику</option>
                <option value="enter">Оприходование</option>
                <option value="loss">Списание</option>
                <option value="move">Перемещение</option>
                <option value="inventory">Инвентаризация</option>
                <option value="retaildemand">Розничная продажа</option>
                <option value="retailsalesreturn">Возврат розничной продажи</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Документов на странице
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={filters.limit}
                onChange={(e) => handleFiltersChange({ limit: parseInt(e.target.value) })}
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>
        </div>

        {/* Documents List */}
        <div className="bg-white rounded-lg shadow">
          {isLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Загрузка документов...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center">
              <p className="text-red-600">Ошибка загрузки документов</p>
            </div>
          ) : !documents || documents.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-600">Документы не найдены</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Документ
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Контрагент
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Сумма
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Дата
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Статус
                      </th>
                      <th scope="col" className="relative px-6 py-3">
                        <span className="sr-only">Действия</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {documents.map((document: Document) => (
                      <tr key={document.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="ml-0">
                              <div className="text-sm font-medium text-gray-900">
                                {getDocumentTypeLabel(document.document_type)}
                              </div>
                              <div className="text-sm text-gray-500">
                                № {document.number}
                              </div>
                              {document.description && (
                                <div className="text-xs text-gray-400 mt-1">
                                  {document.description.substring(0, 50)}...
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {document.counterparty_name || 'Не указан'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {document.total_amount > 0 
                              ? `${parseFloat(document.total_amount).toLocaleString()} ${document.currency || 'ТЕН'}`
                              : 'Не указана'
                            }
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {new Date(document.date).toLocaleDateString('ru-RU')}
                          </div>
                          <div className="text-xs text-gray-500">
                            {new Date(document.date).toLocaleTimeString('ru-RU', { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(document.status)}`}>
                            {document.status || 'Не указан'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => window.open(`https://app.moysklad.ru/app/#${document.document_type}/edit?id=${document.external_id}`, '_blank')}
                              className="text-blue-600 hover:text-blue-900"
                              title="Открыть в МойСклад"
                            >
                              👁️ Открыть
                            </button>
                            <button
                              onClick={() => navigator.clipboard.writeText(document.external_id)}
                              className="text-gray-600 hover:text-gray-900"
                              title="Скопировать ID"
                            >
                              📋 ID
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 flex justify-between sm:hidden">
                      <button
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 0}
                        className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Назад
                      </button>
                      <button
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage >= totalPages - 1}
                        className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Вперед
                      </button>
                    </div>
                    <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm text-gray-700">
                          Показано{' '}
                          <span className="font-medium">{filters.skip + 1}</span>
                          {' '}до{' '}
                          <span className="font-medium">
                            {Math.min(filters.skip + filters.limit, documents?.length || 0)}
                          </span>
                          {' '}из{' '}
                          <span className="font-medium">{documents?.length || 0}</span>
                          {' '}результатов
                        </p>
                      </div>
                      <div>
                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                          <button
                            onClick={() => handlePageChange(currentPage - 1)}
                            disabled={currentPage === 0}
                            className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            ‹
                          </button>
                          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                            const page = Math.max(0, Math.min(totalPages - 5, currentPage - 2)) + i
                            return (
                              <button
                                key={page}
                                onClick={() => handlePageChange(page)}
                                className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                  page === currentPage
                                    ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                    : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                                }`}
                              >
                                {page + 1}
                              </button>
                            )
                          })}
                          <button
                            onClick={() => handlePageChange(currentPage + 1)}
                            disabled={currentPage >= totalPages - 1}
                            className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            ›
                          </button>
                        </nav>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </Layout>
  )
}