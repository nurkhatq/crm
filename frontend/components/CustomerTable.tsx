import { Customer } from '@/types'

interface CustomerTableProps {
  customers: Customer[]
  onPageChange: (page: number) => void
  currentPage: number
  pageSize: number
}

export default function CustomerTable({ customers, onPageChange, currentPage, pageSize }: CustomerTableProps) {
  const totalPages = Math.ceil(customers.length / pageSize)
  const startIndex = currentPage * pageSize
  const endIndex = startIndex + pageSize
  const currentCustomers = customers.slice(startIndex, endIndex)

  return (
    <div className="card">
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>Наименование</th>
              <th>Код</th>
              <th>Email</th>
              <th>Телефон</th>
              <th>ИНН</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            {currentCustomers.map((customer) => (
              <tr key={customer.id}>
                <td>
                  <div>
                    <p className="font-medium text-gray-900">{customer.name}</p>
                    {customer.legal_title && customer.legal_title !== customer.name && (
                      <p className="text-sm text-gray-600">{customer.legal_title}</p>
                    )}
                  </div>
                </td>
                <td>{customer.code || '-'}</td>
                <td>
                  {customer.email ? (
                    <a href={`mailto:${customer.email}`} className="text-primary-600 hover:text-primary-700">
                      {customer.email}
                    </a>
                  ) : (
                    '-'
                  )}
                </td>
                <td>
                  {customer.phone ? (
                    <a href={`tel:${customer.phone}`} className="text-primary-600 hover:text-primary-700">
                      {customer.phone}
                    </a>
                  ) : (
                    '-'
                  )}
                </td>
                <td>{customer.inn || '-'}</td>
                <td>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    customer.archived
                      ? 'bg-red-100 text-red-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {customer.archived ? 'Архивный' : 'Активный'}
                  </span>
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
            Показано {startIndex + 1}-{Math.min(endIndex, customers.length)} из {customers.length}
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
