import { useState } from 'react'
import { triggerSync, triggerEnhancedSync } from '@/lib/api'

interface SyncButtonProps {
  onSync: () => void
  isLoading: boolean
  enhanced?: boolean
}

export default function SyncButton({ onSync, isLoading, enhanced = false }: SyncButtonProps) {
  const [isSyncing, setIsSyncing] = useState(false)
  const [syncType, setSyncType] = useState<'standard' | 'enhanced'>('enhanced')

  const handleSync = async () => {
    setIsSyncing(true)
    try {
      if (enhanced || syncType === 'enhanced') {
        await triggerEnhancedSync('full', false)
      } else {
        await triggerSync('full', false)
      }
      onSync()
    } catch (error) {
      console.error('Sync failed:', error)
    } finally {
      setIsSyncing(false)
    }
  }

  return (
    <div className="flex items-center space-x-2">
      {enhanced && (
        <select
          value={syncType}
          onChange={(e) => setSyncType(e.target.value as 'standard' | 'enhanced')}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          disabled={isSyncing}
        >
          <option value="enhanced">Расширенная</option>
          <option value="standard">Стандартная</option>
        </select>
      )}
      
      <button
        onClick={handleSync}
        disabled={isSyncing || isLoading}
        className="btn btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className="text-lg">
          {isSyncing ? '🔄' : '🔄'}
        </span>
        <span>
          {isSyncing ? 'Синхронизация...' : 
           syncType === 'enhanced' ? 'Полная синхронизация' : 'Синхронизировать'}
        </span>
      </button>
    </div>
  )
}
