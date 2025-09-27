import { useState } from 'react'
import { useQuery } from 'react-query'
import Layout from '@/components/Layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown,
  Package,
  Users,
  FileText,
  DollarSign,
  Calendar,
  RefreshCw,
  Download,
  Activity,
  PieChart,
  LineChart,
  AlertTriangle
} from 'lucide-react'
import { getKPIMetrics, getTopProducts } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState('30d')

  const { data: kpiData, isLoading: kpiLoading, refetch: refetchKPI } = useQuery(
    'kpi-metrics',
    getKPIMetrics,
    {
      refetchInterval: 60000, // Refresh every minute
    }
  )

  const { data: topProducts, isLoading: topProductsLoading } = useQuery(
    'top-products',
    getTopProducts,
    {
      refetchInterval: 300000, // Refresh every 5 minutes
    }
  )

  const handleRefresh = async () => {
    await refetchKPI()
  }

  const timeRanges = [
    { value: '7d', label: '7 дней' },
    { value: '30d', label: '30 дней' },
    { value: '90d', label: '90 дней' },
    { value: '1y', label: '1 год' },
  ]

  const kpiCards = [
    {
      title: 'Общая выручка',
      value: formatCurrency(parseFloat(kpiData?.total_revenue || '0')),
      icon: DollarSign,
      trend: '+15.3%',
      trendUp: true,
      description: 'За выбранный период'
    },
    {
      title: 'Товары в каталоге',
      value: kpiData?.total_products || 0,
      icon: Package,
      trend: '+8.2%',
      trendUp: true,
      description: 'Активных товаров'
    },
    {
      title: 'Клиенты',
      value: kpiData?.total_customers || 0,
      icon: Users,
      trend: '+12.1%',
      trendUp: true,
      description: 'Активных клиентов'
    },
    {
      title: 'Документы',
      value: kpiData?.total_documents || 0,
      icon: FileText,
      trend: '+23.7%',
      trendUp: true,
      description: 'Обработанных документов'
    }
  ]

  if (kpiLoading) {
    return (
      <Layout>
        <div className="space-y-6 animate-fade-in">
          <div className="flex items-center justify-between">
            <div>
              <div className="h-8 w-48 bg-muted animate-pulse rounded"></div>
              <div className="h-4 w-64 bg-muted animate-pulse rounded mt-2"></div>
            </div>
            <div className="h-10 w-32 bg-muted animate-pulse rounded"></div>
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Card key={i}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <div className="h-4 w-20 bg-muted animate-pulse rounded"></div>
                  <div className="h-4 w-4 bg-muted animate-pulse rounded"></div>
                </CardHeader>
                <CardContent>
                  <div className="h-8 w-16 bg-muted animate-pulse rounded"></div>
                  <div className="h-4 w-24 bg-muted animate-pulse rounded mt-2"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-8 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-foreground">
              Аналитика
            </h1>
            <p className="text-muted-foreground mt-2">
              Анализ показателей и трендов вашего бизнеса
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              {timeRanges.map((range) => (
                <Button
                  key={range.value}
                  variant={timeRange === range.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTimeRange(range.value)}
                >
                  {range.label}
                </Button>
              ))}
            </div>
            <Button
              onClick={handleRefresh}
              disabled={kpiLoading}
              size="sm"
            >
              {kpiLoading ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Обновление...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Обновить
                </>
              )}
            </Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {kpiCards.map((card, index) => (
            <Card key={card.title} className="animate-slide-up" style={{ animationDelay: `${index * 100}ms` }}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {card.title}
                </CardTitle>
                <card.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">
                  {card.value}
                </div>
                <div className="flex items-center space-x-2 mt-2">
                  {card.trendUp ? (
                    <TrendingUp className="h-4 w-4 text-green-600" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  )}
                  <p className={`text-xs ${card.trendUp ? 'text-green-600' : 'text-red-600'}`}>
                    {card.trend}
                  </p>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {card.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Revenue Chart */}
          <Card className="animate-slide-up">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <LineChart className="h-5 w-5" />
                <span>Динамика выручки</span>
              </CardTitle>
              <CardDescription>
                Изменение выручки по периодам
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center bg-muted/50 rounded-lg">
                <div className="text-center">
                  <LineChart className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">График будет добавлен в следующей версии</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Products Distribution */}
          <Card className="animate-slide-up">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <PieChart className="h-5 w-5" />
                <span>Распределение товаров</span>
              </CardTitle>
              <CardDescription>
                По категориям и группам
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center bg-muted/50 rounded-lg">
                <div className="text-center">
                  <PieChart className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">Диаграмма будет добавлена в следующей версии</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Top Products */}
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Топ товары по продажам</span>
            </CardTitle>
            <CardDescription>
              Самые продаваемые товары за период
            </CardDescription>
          </CardHeader>
          <CardContent>
            {topProductsLoading ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg animate-pulse">
                    <div className="h-4 w-3/4 bg-muted rounded"></div>
                    <div className="h-4 w-1/4 bg-muted rounded"></div>
                  </div>
                ))}
              </div>
            ) : topProducts && topProducts.length > 0 ? (
              <div className="space-y-3">
                {topProducts.slice(0, 10).map((product, index) => (
                  <div key={product.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg hover:bg-muted/70 transition-colors">
                    <div className="flex items-center space-x-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                        {index + 1}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground line-clamp-1">
                          {product.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Продано: {product.total_sold} шт
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-green-600">
                        {formatCurrency(product.revenue)}
                      </p>
                      <Badge variant="secondary" className="text-xs">
                        #{product.id}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Нет данных о продажах</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Stock Analysis */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="animate-slide-up">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Package className="h-5 w-5" />
                <span>Анализ остатков</span>
              </CardTitle>
              <CardDescription>
                Товары с низким остатком
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Товары с низким остатком</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {kpiData?.low_stock_products || 0}
                  </p>
                </div>
                <div className="h-12 w-12 bg-orange-100 rounded-full flex items-center justify-center">
                  <AlertTriangle className="h-6 w-6 text-orange-600" />
                </div>
              </div>
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Стоимость остатков</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatCurrency(parseFloat(kpiData?.total_stock_value || '0'))}
                  </p>
                </div>
                <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <Package className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="animate-slide-up">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Активность системы</span>
              </CardTitle>
              <CardDescription>
                Статистика синхронизации
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Последняя синхронизация</p>
                  <p className="text-sm font-medium text-foreground">
                    {kpiData?.last_sync ? formatDate(kpiData.last_sync) : 'Никогда'}
                  </p>
                </div>
                <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Activity className="h-6 w-6 text-green-600" />
                </div>
              </div>
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Статус подключения</p>
                  <Badge variant="success" className="text-xs">
                    Активно
                  </Badge>
                </div>
                <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Export Section */}
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Download className="h-5 w-5" />
              <span>Экспорт данных</span>
            </CardTitle>
            <CardDescription>
              Скачать отчеты и данные в различных форматах
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <Download className="h-6 w-6" />
                <span>Отчет по продажам</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <Package className="h-6 w-6" />
                <span>Остатки товаров</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <Users className="h-6 w-6" />
                <span>База клиентов</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <FileText className="h-6 w-6" />
                <span>Документооборот</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}

