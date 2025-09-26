import { Product } from '@/types'
import Link from 'next/link'

interface ProductTableProps {
  products: Product[]
  onPageChange: (page: number) => void
  currentPage: number
  pageSize: number
}

export default function ProductTable({ products, onPageChange, currentPage, pageSize }: ProductTableProps) {
  const totalPages = Math.ceil(products.length / pageSize)
  const startIndex = currentPage * pageSize
  const endIndex = startIndex + pageSize
  const currentProducts = products.slice(startIndex, endIndex)

  return (
    <div className="card">
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>Наименование</th>
              <th>Код</th>
              <th>Артикул</th>
              <th>Цена продажи</th>
              <th>Остаток</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {currentProducts.map((product) => (
              <tr key={product.id}>
                <td>
                  <div>
                    <p className="font-medium text-gray-900">{product.name}</p>
                    {product.description && (
                      <p className="text-sm text-gray-600 truncate max-w-xs">
                        {product.description}
                      </p>
                    )}
                  </div>
                </td>
                <td>{product.code || '-'}</td>
                <td>{product.article || '-'}</td>
                <td>
                  {product.sale_price ? (
                    <span className="font-medium">
                      {product.sale_price.toLocaleString()} {product.currency}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>
                <td>
                  {product.stock ? (
                    <span className={`font-medium ${
                      product.stock.available < 10 ? 'text-red-600' : 'text-gray-900'
                    }`}>
                      {product.stock.available}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>
                <td>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    product.archived
                      ? 'bg-red-100 text-red-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {product.archived ? 'Архивный' : 'Активный'}
                  </span>
                </td>
                <td>
                  <Link
                    href={`/products/${product.id}`}
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                  >
                    Подробнее
                  </Link>
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
            Показано {startIndex + 1}-{Math.min(endIndex, products.length)} из {products.length}
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
