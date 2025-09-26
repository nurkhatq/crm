import { useState } from 'react'

interface ProductFiltersProps {
  filters: {
    search: string
    archived: boolean | undefined
    skip: number
    limit: number
  }
  onFiltersChange: (filters: Partial<typeof filters>) => void
}

export default function ProductFilters({ filters, onFiltersChange }: ProductFiltersProps) {
  const [localSearch, setLocalSearch] = useState(filters.search)

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onFiltersChange({ search: localSearch })
  }

  const handleArchivedChange = (archived: boolean | undefined) => {
    onFiltersChange({ archived })
  }

  return (
    <div className="card">
      <form onSubmit={handleSearchSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
              Поиск
            </label>
            <input
              type="text"
              id="search"
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              placeholder="Название товара..."
              className="input"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Статус
            </label>
            <select
              value={filters.archived === undefined ? '' : filters.archived.toString()}
              onChange={(e) => {
                const value = e.target.value
                handleArchivedChange(
                  value === '' ? undefined : value === 'true'
                )
              }}
              className="input"
            >
              <option value="">Все</option>
              <option value="false">Активные</option>
              <option value="true">Архивные</option>
            </select>
          </div>

          {/* Search Button */}
          <div className="flex items-end">
            <button type="submit" className="btn btn-primary w-full">
              🔍 Найти
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
