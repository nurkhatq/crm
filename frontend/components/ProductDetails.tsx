import { Product } from '@/types'

interface ProductDetailsProps {
  product: Product
}

export default function ProductDetails({ product }: ProductDetailsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Basic Information */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Основная информация</h2>
        <dl className="space-y-3">
          <div>
            <dt className="text-sm font-medium text-gray-600">Наименование</dt>
            <dd className="text-lg text-gray-900">{product.name}</dd>
          </div>
          {product.code && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Код</dt>
              <dd className="text-gray-900">{product.code}</dd>
            </div>
          )}
          {product.article && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Артикул</dt>
              <dd className="text-gray-900">{product.article}</dd>
            </div>
          )}
          {product.description && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Описание</dt>
              <dd className="text-gray-900">{product.description}</dd>
            </div>
          )}
          <div>
            <dt className="text-sm font-medium text-gray-600">Статус</dt>
            <dd>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                product.archived
                  ? 'bg-red-100 text-red-800'
                  : 'bg-green-100 text-green-800'
              }`}>
                {product.archived ? 'Архивный' : 'Активный'}
              </span>
            </dd>
          </div>
        </dl>
      </div>

      {/* Pricing Information */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Ценообразование</h2>
        <dl className="space-y-3">
          {product.buy_price && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Цена закупки</dt>
              <dd className="text-lg text-gray-900">
                {product.buy_price.toLocaleString()} {product.currency}
              </dd>
            </div>
          )}
          {product.sale_price && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Цена продажи</dt>
              <dd className="text-lg text-gray-900">
                {product.sale_price.toLocaleString()} {product.currency}
              </dd>
            </div>
          )}
          {product.uom && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Единица измерения</dt>
              <dd className="text-gray-900">{product.uom}</dd>
            </div>
          )}
          {product.group_name && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Группа</dt>
              <dd className="text-gray-900">{product.group_name}</dd>
            </div>
          )}
          {product.supplier_name && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Поставщик</dt>
              <dd className="text-gray-900">{product.supplier_name}</dd>
            </div>
          )}
        </dl>
      </div>

      {/* Stock Information */}
      {product.stock && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Остатки</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-600">Текущий остаток</dt>
              <dd className="text-lg text-gray-900">{product.stock.stock}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-600">Резерв</dt>
              <dd className="text-gray-900">{product.stock.reserve}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-600">В пути</dt>
              <dd className="text-gray-900">{product.stock.in_transit}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-600">Доступно</dt>
              <dd className={`text-lg font-semibold ${
                product.stock.available < 10 ? 'text-red-600' : 'text-gray-900'
              }`}>
                {product.stock.available}
              </dd>
            </div>
            {product.stock.store_name && (
              <div>
                <dt className="text-sm font-medium text-gray-600">Склад</dt>
                <dd className="text-gray-900">{product.stock.store_name}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* External Information */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Внешняя система</h2>
        <dl className="space-y-3">
          <div>
            <dt className="text-sm font-medium text-gray-600">ID в МойСклад</dt>
            <dd className="text-gray-900 font-mono text-sm">{product.external_id}</dd>
          </div>
          {product.external_updated && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Последнее обновление</dt>
              <dd className="text-gray-900">
                {new Date(product.external_updated).toLocaleString('ru-RU')}
              </dd>
            </div>
          )}
          <div>
            <dt className="text-sm font-medium text-gray-600">Создан в системе</dt>
            <dd className="text-gray-900">
              {new Date(product.created_at).toLocaleString('ru-RU')}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-600">Обновлен в системе</dt>
            <dd className="text-gray-900">
              {new Date(product.updated_at).toLocaleString('ru-RU')}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  )
}
