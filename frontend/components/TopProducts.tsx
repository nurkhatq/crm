import { useQuery } from 'react-query'
import { getTopProducts } from '@/lib/api'

export default function TopProducts() {
  const { data: topProducts, isLoading } = useQuery(
    'top-products',
    () => getTopProducts(5, 30),
    {
      refetchInterval: 60000, // Refresh every minute
    }
  )

  if (isLoading) {
    return (
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Топ товаров</h2>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!topProducts?.products?.length) {
    return (
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Топ товаров</h2>
        <p className="text-gray-600">Нет товаров с остатками</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Топ товаров</h2>
      <div className="space-y-3">
        {topProducts.products.map((product, index) => (
          <div key={product.product_id} className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-sm font-medium">
                {index + 1}
              </div>
              <div>
                <p className="font-medium text-gray-900">{product.product_name}</p>
                <p className="text-sm text-gray-600">
                  Цена покупки: {product.revenue.toLocaleString()} ТЕН
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Остаток</p>
              <p className="font-medium text-gray-900">{product.stock}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
