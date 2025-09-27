import { useQuery } from 'react-query'
import { getProducts } from '@/lib/api'

export default function EnhancedProducts() {
  const { data: productsData, isLoading } = useQuery('enhanced-products', () => getProducts())

  if (isLoading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!productsData?.products) return null

  const products = productsData.products
  const services = products.filter((p: any) => p.is_service)
  const bundles = products.filter((p: any) => p.is_bundle)
  const regularProducts = products.filter((p: any) => !p.is_service && !p.is_bundle)

  const ProductCard = ({ product, type }: { product: any, type: string }) => (
    <div className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h3 className="font-medium text-gray-900 line-clamp-2">{product.name}</h3>
          <div className="text-sm text-gray-600 mt-1">
            {product.code && <span>Код: {product.code}</span>}
            {product.article && <span className="ml-2">Артикул: {product.article}</span>}
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          type === 'service' ? 'bg-green-100 text-green-800' :
          type === 'bundle' ? 'bg-purple-100 text-purple-800' :
          'bg-blue-100 text-blue-800'
        }`}>
          {type === 'service' ? 'Услуга' : type === 'bundle' ? 'Комплект' : 'Товар'}
        </span>
      </div>
      
      <div className="space-y-1 text-sm text-gray-600">
        {product.country && <div>Страна: {product.country}</div>}
        {product.weight && <div>Вес: {product.weight} кг</div>}
        {product.volume && <div>Объем: {product.volume} м³</div>}
        {product.tracking_type && <div>Отслеживание: {product.tracking_type}</div>}
        {product.is_serial_trackable && <div>Серийные номера: Да</div>}
      </div>

      {product.stock && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex justify-between text-sm">
            <span>Остаток:</span>
            <span className={`font-medium ${product.stock.stock > 10 ? 'text-green-600' : product.stock.stock > 5 ? 'text-yellow-600' : 'text-red-600'}`}>
              {product.stock.stock}
            </span>
          </div>
        </div>
      )}
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{regularProducts.length}</div>
          <div className="text-sm text-blue-600">Обычные товары</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{services.length}</div>
          <div className="text-sm text-green-600">Услуги</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">{bundles.length}</div>
          <div className="text-sm text-purple-600">Комплекты</div>
        </div>
      </div>

      {/* Regular Products */}
      {regularProducts.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Обычные товары</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {regularProducts.slice(0, 9).map((product: any) => (
              <ProductCard key={product.id} product={product} type="product" />
            ))}
          </div>
        </div>
      )}

      {/* Services */}
      {services.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Услуги</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map((product: any) => (
              <ProductCard key={product.id} product={product} type="service" />
            ))}
          </div>
        </div>
      )}

      {/* Bundles */}
      {bundles.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Комплекты</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {bundles.slice(0, 9).map((product: any) => (
              <ProductCard key={product.id} product={product} type="bundle" />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}



