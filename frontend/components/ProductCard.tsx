import { Product } from '@/lib/api'

interface ProductCardProps {
  product: Product
}

export default function ProductCard({ product }: ProductCardProps) {
  const getStockColor = (stock: number) => {
    if (stock > 10) return 'text-green-600 bg-green-50'
    if (stock > 5) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getPriceDisplay = () => {
    if (product.sale_price > 0) {
      return `${parseFloat(product.sale_price).toLocaleString()} ${product.currency || 'ТЕН'}`
    }
    if (product.buy_price > 0) {
      return `${parseFloat(product.buy_price).toLocaleString()} ${product.currency || 'ТЕН'}`
    }
    return 'Цена не указана'
  }


  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
              {product.name}
            </h3>
            <div className="mt-2 space-y-1">
              {product.code && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Код:</span> {product.code}
                </div>
              )}
              {product.article && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Арт:</span> {product.article}
                </div>
              )}
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            product.archived 
              ? 'bg-gray-100 text-gray-800' 
              : 'bg-green-100 text-green-800'
          }`}>
            {product.archived ? 'Архивный' : 'Активный'}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Group and Supplier */}
        {(product.group_name || product.supplier_name) && (
          <div className="space-y-2">
            {product.group_name && (
              <div className="text-sm">
                <span className="font-medium text-gray-700">Группа:</span>
                <span className="ml-2 text-gray-600">{product.group_name}</span>
              </div>
            )}
            {product.supplier_name && (
              <div className="text-sm">
                <span className="font-medium text-gray-700">Поставщик:</span>
                <span className="ml-2 text-gray-600">{product.supplier_name}</span>
              </div>
            )}
          </div>
        )}

        {/* Prices */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-sm text-blue-600 font-medium">Цена продажи</div>
            <div className="text-lg font-bold text-blue-800">
              {product.sale_price > 0 
                ? `${parseFloat(product.sale_price).toLocaleString()} ${product.currency || 'ТЕН'}`
                : 'Не указана'
              }
            </div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-sm text-green-600 font-medium">Цена покупки</div>
            <div className="text-lg font-bold text-green-800">
              {product.buy_price > 0 
                ? `${parseFloat(product.buy_price).toLocaleString()} ${product.currency || 'ТЕН'}`
                : 'Не указана'
              }
            </div>
          </div>
        </div>

        {/* Stock Information */}
        {product.stock && (
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Остаток на складе:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-bold ${getStockColor(product.stock.stock)}`}>
                {parseFloat(product.stock.stock).toString()}
              </span>
            </div>
            

            {(product.stock.reserve > 0 || product.stock.available > 0) && (
              <div className="grid grid-cols-2 gap-2 text-xs">
                {product.stock.reserve > 0 && (
                  <div className="text-center p-2 bg-orange-50 rounded">
                    <div className="text-orange-600 font-medium">Резерв</div>
                    <div className="text-orange-800 font-bold">{parseFloat(product.stock.reserve).toString()}</div>
                  </div>
                )}
                {product.stock.available > 0 && (
                  <div className="text-center p-2 bg-blue-50 rounded">
                    <div className="text-blue-600 font-medium">Доступно</div>
                    <div className="text-blue-800 font-bold">{parseFloat(product.stock.available).toString()}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Description */}
        {product.description && (
          <div className="text-sm text-gray-600">
            <span className="font-medium">Описание:</span>
            <div className="mt-1 line-clamp-2">{product.description}</div>
          </div>
        )}

        {/* Additional Info */}
        <div className="flex justify-between items-center text-xs text-gray-500 border-t border-gray-100 pt-3">
          <span>
            Обновлен: {new Date(product.updated_at).toLocaleDateString('ru-RU')}
          </span>
          {product.uom && (
            <span className="px-2 py-1 bg-gray-100 rounded">
              {product.uom}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
