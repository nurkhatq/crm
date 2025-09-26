import { useQuery } from 'react-query'
import { getProductForecast } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface ProductForecastProps {
  productId: number
}

export default function ProductForecast({ productId }: ProductForecastProps) {
  const { data: forecast, isLoading, error } = useQuery(
    ['product-forecast', productId],
    () => getProductForecast(productId, 30),
    {
      refetchInterval: 300000, // Refresh every 5 minutes
    }
  )

  if (isLoading) {
    return (
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Прогноз продаж</h2>
        <div className="h-64 bg-gray-100 rounded-lg animate-pulse"></div>
      </div>
    )
  }

  if (error || !forecast) {
    return (
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Прогноз продаж</h2>
        <div className="text-center py-8">
          <div className="text-gray-500 text-lg mb-2">📊</div>
          <p className="text-gray-600">Недостаточно данных для прогноза</p>
        </div>
      </div>
    )
  }

  // Prepare data for chart
  const chartData = forecast.forecast_points.map(point => ({
    date: new Date(point.date).toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' }),
    predicted: point.predicted_sales,
    lower: point.confidence_lower,
    upper: point.confidence_upper,
  }))

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Прогноз продаж</h2>
        <div className="text-sm text-gray-600">
          Метод: {forecast.method}
          {forecast.accuracy && (
            <span className="ml-2">
              • Точность: {(forecast.accuracy * 100).toFixed(1)}%
            </span>
          )}
        </div>
      </div>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip 
              formatter={(value, name) => [
                Number(value).toFixed(1),
                name === 'predicted' ? 'Прогноз' : 
                name === 'lower' ? 'Нижняя граница' : 'Верхняя граница'
              ]}
              labelFormatter={(label) => `Дата: ${label}`}
            />
            <Line
              type="monotone"
              dataKey="upper"
              stroke="#ef4444"
              strokeDasharray="5 5"
              strokeWidth={1}
              dot={false}
              name="upper"
            />
            <Line
              type="monotone"
              dataKey="lower"
              stroke="#ef4444"
              strokeDasharray="5 5"
              strokeWidth={1}
              dot={false}
              name="lower"
            />
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 4 }}
              name="predicted"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-4 text-sm text-gray-600">
        <p>Прогноз основан на исторических данных и может не отражать реальные продажи.</p>
      </div>
    </div>
  )
}
