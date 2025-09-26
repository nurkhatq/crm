import { useState } from 'react'
import { useQuery } from 'react-query'
import Layout from '@/components/Layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Users, 
  Search, 
  Plus, 
  Eye, 
  Edit, 
  Mail, 
  Phone,
  MapPin,
  Building,
  User,
  ChevronLeft,
  ChevronRight,
  Grid,
  List,
  Filter
} from 'lucide-react'
import { getCustomers } from '@/lib/api'
import { Customer } from '@/types'
import { formatDate } from '@/lib/utils'

export default function CustomersPage() {
  const [filters, setFilters] = useState({
    search: '',
    skip: 0,
    limit: 50,
  })
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  const { data: customers, isLoading, error } = useQuery(
    ['customers', filters],
    () => getCustomers(filters),
    {
      keepPreviousData: true,
    }
  )

  const handleFiltersChange = (newFilters: Partial<typeof filters>) => {
    setFilters(prev => ({ ...prev, ...newFilters, skip: 0 }))
  }

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, skip: page * prev.limit }))
  }

  const totalPages = customers ? Math.ceil(customers.length / filters.limit) : 0
  const currentPage = Math.floor(filters.skip / filters.limit)

  if (isLoading) {
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="h-4 w-3/4 bg-muted animate-pulse rounded"></div>
                  <div className="h-3 w-1/2 bg-muted animate-pulse rounded"></div>
                </CardHeader>
                <CardContent>
                  <div className="h-8 w-1/3 bg-muted animate-pulse rounded"></div>
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
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-foreground">
              Клиенты
            </h1>
            <p className="text-muted-foreground mt-2">
              Управление клиентской базой • {customers?.length || 0} клиентов
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open('/api/v1/customers/export/csv', '_blank')}
            >
              Экспорт CSV
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Добавить клиента
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col space-y-4 md:flex-row md:items-center md:space-y-0 md:space-x-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Поиск клиентов..."
                  value={filters.search}
                  onChange={(e) => handleFiltersChange({ search: e.target.value })}
                  className="w-full pl-10 pr-4 py-2 text-sm border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant={viewMode === 'grid' ? "default" : "outline"}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  <Grid className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? "default" : "outline"}
                  size="sm"
                  onClick={() => setViewMode('list')}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Customers */}
        {error ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <div className="text-destructive text-lg mb-2">Ошибка загрузки</div>
                <p className="text-muted-foreground">Не удалось загрузить клиентов</p>
              </div>
            </CardContent>
          </Card>
        ) : customers && customers.length > 0 ? (
          <>
            {viewMode === 'grid' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {customers.map((customer, index) => (
                  <Card key={customer.id} className="animate-slide-up hover:shadow-md transition-shadow" style={{ animationDelay: `${index * 50}ms` }}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <CardTitle className="text-lg line-clamp-2">
                            {customer.name}
                          </CardTitle>
                          <CardDescription>
                            {customer.code && `Код: ${customer.code}`}
                          </CardDescription>
                        </div>
                        <div className="flex items-center space-x-1">
                          {customer.archived && (
                            <Badge variant="secondary" className="text-xs">
                              Архив
                            </Badge>
                          )}
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="space-y-2">
                        {customer.email && (
                          <div className="flex items-center space-x-2 text-sm">
                            <Mail className="h-4 w-4 text-muted-foreground" />
                            <span className="text-muted-foreground">{customer.email}</span>
                          </div>
                        )}
                        {customer.phone && (
                          <div className="flex items-center space-x-2 text-sm">
                            <Phone className="h-4 w-4 text-muted-foreground" />
                            <span className="text-muted-foreground">{customer.phone}</span>
                          </div>
                        )}
                        {customer.address && (
                          <div className="flex items-center space-x-2 text-sm">
                            <MapPin className="h-4 w-4 text-muted-foreground" />
                            <span className="text-muted-foreground line-clamp-1">{customer.address}</span>
                          </div>
                        )}
                        {customer.inn && (
                          <div className="flex items-center space-x-2 text-sm">
                            <Building className="h-4 w-4 text-muted-foreground" />
                            <span className="text-muted-foreground">ИНН: {customer.inn}</span>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center justify-between pt-2">
                        <div className="text-xs text-muted-foreground">
                          Обновлено {formatDate(customer.updated_at)}
                        </div>
                        <div className="flex items-center space-x-1">
                          <Button variant="ghost" size="icon" className="h-8 w-8" asChild>
                            <a href={`/customers/${customer.id}`}>
                              <Eye className="h-4 w-4" />
                            </a>
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="border-b">
                        <tr className="text-left">
                          <th className="p-4 font-medium">Клиент</th>
                          <th className="p-4 font-medium">Код</th>
                          <th className="p-4 font-medium">Email</th>
                          <th className="p-4 font-medium">Телефон</th>
                          <th className="p-4 font-medium">Адрес</th>
                          <th className="p-4 font-medium">Статус</th>
                          <th className="p-4 font-medium">Действия</th>
                        </tr>
                      </thead>
                      <tbody>
                        {customers.map((customer) => (
                          <tr key={customer.id} className="border-b hover:bg-muted/50 transition-colors">
                            <td className="p-4">
                              <div className="flex items-center space-x-3">
                                <div className="h-10 w-10 bg-primary/10 rounded-full flex items-center justify-center">
                                  <User className="h-5 w-5 text-primary" />
                                </div>
                                <div>
                                  <div className="font-medium">{customer.name}</div>
                                  {customer.inn && (
                                    <div className="text-sm text-muted-foreground">ИНН: {customer.inn}</div>
                                  )}
                                </div>
                              </div>
                            </td>
                            <td className="p-4 text-sm text-muted-foreground">
                              {customer.code || '-'}
                            </td>
                            <td className="p-4 text-sm text-muted-foreground">
                              {customer.email || '-'}
                            </td>
                            <td className="p-4 text-sm text-muted-foreground">
                              {customer.phone || '-'}
                            </td>
                            <td className="p-4 text-sm text-muted-foreground max-w-xs">
                              <div className="truncate">{customer.address || '-'}</div>
                            </td>
                            <td className="p-4">
                              {customer.archived ? (
                                <Badge variant="secondary">Архив</Badge>
                              ) : (
                                <Badge variant="success">Активный</Badge>
                              )}
                            </td>
                            <td className="p-4">
                              <div className="flex items-center space-x-1">
                                <Button variant="ghost" size="icon" className="h-8 w-8" asChild>
                                  <a href={`/customers/${customer.id}`}>
                                    <Eye className="h-4 w-4" />
                                  </a>
                                </Button>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <Edit className="h-4 w-4" />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      Показано {filters.skip + 1}-{Math.min(filters.skip + filters.limit, customers.length)} из {customers.length} клиентов
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 0}
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Предыдущая
                      </Button>
                      <div className="flex items-center space-x-1">
                        {[...Array(Math.min(5, totalPages))].map((_, i) => {
                          const page = i
                          return (
                            <Button
                              key={page}
                              variant={currentPage === page ? "default" : "outline"}
                              size="sm"
                              onClick={() => handlePageChange(page)}
                            >
                              {page + 1}
                            </Button>
                          )
                        })}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage >= totalPages - 1}
                      >
                        Следующая
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        ) : (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">Клиенты не найдены</h3>
                <p className="text-muted-foreground mb-4">
                  Попробуйте изменить фильтры или добавить новых клиентов
                </p>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Добавить клиента
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  )
}