import { useState } from 'react'

interface DocumentFiltersProps {
  filters: {
    document_type: string
    customer_id: number | undefined
    applicable: boolean | undefined
    skip: number
    limit: number
  }
  documentTypes: string[]
  onFiltersChange: (filters: Partial<typeof filters>) => void
}

export default function DocumentFilters({ filters, documentTypes, onFiltersChange }: DocumentFiltersProps) {
  const getDocumentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'customerorder': 'Заказ покупателя',
      'demand': 'Отгрузка',
      'invoiceout': 'Счет покупателю',
      'salesreturn': 'Возврат покупателя',
      'retailsale': 'Розничная продажа',
    }
    return labels[type] || type
  }

  return (
    <div className="card">
      <form className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Document Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Тип документа
            </label>
            <select
              value={filters.document_type}
              onChange={(e) => onFiltersChange({ document_type: e.target.value })}
              className="input"
            >
              <option value="">Все типы</option>
              {documentTypes.map((type) => (
                <option key={type} value={type}>
                  {getDocumentTypeLabel(type)}
                </option>
              ))}
            </select>
          </div>

          {/* Customer ID Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ID клиента
            </label>
            <input
              type="number"
              value={filters.customer_id || ''}
              onChange={(e) => onFiltersChange({ 
                customer_id: e.target.value ? Number(e.target.value) : undefined 
              })}
              placeholder="ID клиента..."
              className="input"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Статус
            </label>
            <select
              value={filters.applicable === undefined ? '' : filters.applicable.toString()}
              onChange={(e) => {
                const value = e.target.value
                onFiltersChange({
                  applicable: value === '' ? undefined : value === 'true'
                })
              }}
              className="input"
            >
              <option value="">Все</option>
              <option value="true">Проведенные</option>
              <option value="false">Черновики</option>
            </select>
          </div>

          {/* Clear Filters */}
          <div className="flex items-end">
            <button
              type="button"
              onClick={() => onFiltersChange({
                document_type: '',
                customer_id: undefined,
                applicable: undefined,
              })}
              className="btn btn-secondary w-full"
            >
              🗑️ Очистить
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
