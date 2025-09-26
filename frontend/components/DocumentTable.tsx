import { Document } from '@/types'

interface DocumentTableProps {
  documents: Document[]
  onPageChange: (page: number) => void
  currentPage: number
  pageSize: number
}

export default function DocumentTable({ documents, onPageChange, currentPage, pageSize }: DocumentTableProps) {
  const totalPages = Math.ceil(documents.length / pageSize)
  const startIndex = currentPage * pageSize
  const endIndex = startIndex + pageSize
  const currentDocuments = documents.slice(startIndex, endIndex)

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

  const getDocumentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'customerorder': 'bg-blue-100 text-blue-800',
      'demand': 'bg-green-100 text-green-800',
      'invoiceout': 'bg-purple-100 text-purple-800',
      'salesreturn': 'bg-red-100 text-red-800',
      'retailsale': 'bg-yellow-100 text-yellow-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="card">
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>Номер</th>
              <th>Тип</th>
              <th>Дата</th>
              <th>Сумма</th>
              <th>Организация</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            {currentDocuments.map((document) => (
              <tr key={document.id}>
                <td>
                  <p className="font-medium text-gray-900">{document.name}</p>
                </td>
                <td>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getDocumentTypeColor(document.document_type)}`}>
                    {getDocumentTypeLabel(document.document_type)}
                  </span>
                </td>
                <td>
                  {document.moment ? (
                    <span className="text-gray-900">
                      {new Date(document.moment).toLocaleDateString('ru-RU')}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>
                <td>
                  {document.sum ? (
                    <span className="font-medium">
                      {document.sum.toLocaleString()} {document.currency}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>
                <td>{document.organization_name || '-'}</td>
                <td>
                  <div className="flex flex-col space-y-1">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      document.applicable
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {document.applicable ? 'Проведен' : 'Черновик'}
                    </span>
                    {document.state_name && (
                      <span className="text-xs text-gray-600">{document.state_name}</span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-gray-700">
            Показано {startIndex + 1}-{Math.min(endIndex, documents.length)} из {documents.length}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 0}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Назад
            </button>
            <span className="px-3 py-1 text-sm text-gray-700">
              {currentPage + 1} из {totalPages}
            </span>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages - 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Вперед
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
