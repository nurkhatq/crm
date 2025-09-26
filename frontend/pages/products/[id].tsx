import { useRouter } from 'next/router'
import { useQuery } from 'react-query'
import Layout from '@/components/Layout'
import ProductDetails from '@/components/ProductDetails'
import ProductForecast from '@/components/ProductForecast'
import { getProduct } from '@/lib/api'

export default function ProductDetailPage() {
  const router = useRouter()
  const { id } = router.query

  const { data: product, isLoading, error } = useQuery(
    ['product', id],
    () => getProduct(Number(id)),
    {
      enabled: !!id,
    }
  )

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="card">
              <div className="space-y-4">
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    )
  }

  if (error || !product) {
    return (
      <Layout>
        <div className="space-y-6">
          <div className="card">
            <div className="text-center py-8">
              <div className="text-red-500 text-lg mb-2">Товар не найден</div>
              <p className="text-gray-600">Товар с ID {id} не существует</p>
              <button
                onClick={() => router.push('/products')}
                className="btn btn-primary mt-4"
              >
                Вернуться к списку
              </button>
            </div>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <button
              onClick={() => router.push('/products')}
              className="text-primary-600 hover:text-primary-700 mb-2"
            >
              ← Назад к товарам
            </button>
            <h1 className="text-3xl font-bold text-gray-900">{product.name}</h1>
            <p className="text-gray-600">Детальная информация о товаре</p>
          </div>
        </div>

        {/* Product Details */}
        <ProductDetails product={product} />

        {/* Product Forecast */}
        <ProductForecast productId={product.id} />
      </div>
    </Layout>
  )
}
