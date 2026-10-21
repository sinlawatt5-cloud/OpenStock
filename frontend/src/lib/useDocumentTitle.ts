import { useEffect } from 'react'

export function useDocumentTitle(title: string) {
  useEffect(() => {
    document.title = `OpenStock · ${title}`
    return () => {
      document.title = 'OpenStock'
    }
  }, [title])
}
