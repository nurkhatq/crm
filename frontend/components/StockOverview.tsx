import { useQuery } from 'react-query'
import { getProductStock, getLowStockProducts } from '@/lib/api'

export default function StockOverview() {
  const { data: stockData, isLoading: stockLoading } = useQuery('product-stock', () => getProductStock())
  const { data: lowStockData, isLoading: lowStockLoading } = useQuery('low-stock-products', () => getLowStockProducts(5))

  if (stockLoading || lowStockLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
      </div>
    )
  }

  const totalStockItems = stockData?.length || 0
  const lowStockCount = lowStockData?.length || 0

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Stock Summary */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Обзор остатков</h2>
        
        <div className="grid grid-cols-1 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{totalStockItems}</div>
            <div className="text-sm text-blue-600">Товаров с остатками</div>
          </div>
        </div>
        
        <div className="mb-4">
          <div className="bg-red-50 p-3 rounded-lg">
            <div className="text-lg font-bold text-red-600">{lowStockCount}</div>
            <div className="text-sm text-red-600">Товаров с низким остатком</div>
          </div>
        </div>

        <div className="space-y-2 max-h-64 overflow-y-auto">
          {stockData?.slice(0, 10).map((item: any) => (
            <div key={item.id} className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded-md">
              <div className="flex-1">
                <div className="font-medium text-gray-900">{item.product?.name || 'Неизвестный товар'}</div>
                <div className="text-sm text-gray-600">
                  {item.product?.code && `Код: ${item.product.code}`}
                  {item.product?.article && ` | Арт: ${item.product.article}`}
                  {item.product?.sale_price && item.product.sale_price > 0 && ` | Цена: ${parseFloat(item.product.sale_price).toLocaleString()} ${item.product.currency || 'ТЕН'}`}
                  {item.product?.buy_price && item.product.buy_price > 0 && !item.product?.sale_price && ` | Цена: ${parseFloat(item.product.buy_price).toLocaleString()} ${item.product.currency || 'ТЕН'}`}
                </div>
              </div>
              <div className="text-right">
                <div className={`font-bold ${item.stock > 10 ? 'text-green-600' : item.stock > 5 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {parseFloat(item.stock).toString()}
                </div>
                <div className="text-xs text-gray-500">
                  {item.reserve > 0 && `Резерв: ${item.reserve}`}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Low Stock Alert */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Товары с низким остатком</h2>
        
        {lowStockData && lowStockData.length > 0 ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {lowStockData.map((item: any) => (
              <div key={item.id} className="flex justify-between items-center py-2 px-3 bg-red-50 rounded-md border border-red-200">
                <div className="flex-1">
                  <div className="font-medium text-red-900">{item.name}</div>
                  <div className="text-sm text-red-600">
                    {item.code && `Код: ${item.code}`}
                    {item.article && ` | Арт: ${item.article}`}
           {item.sale_price > 0 && ` | Цена: ${parseFloat(item.sale_price).toLocaleString()} ${item.currency || 'ТЕН'}`}
           {item.buy_price > 0 && !item.sale_price && ` | Цена: ${parseFloat(item.buy_price).toLocaleString()} ${item.currency || 'ТЕН'}`}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-red-600">{parseFloat(item.stock?.stock || 0).toString()}</div>
                  <div className="text-xs text-red-500">Остаток</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">✅</div>
            <div>Все товары в наличии</div>
          </div>
        )}
      </div>
    </div>
  )
}
