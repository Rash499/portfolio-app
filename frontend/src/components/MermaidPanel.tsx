import { useEffect, useState } from 'react'
import api from '../api/client'
import {
  asMermaidReadmeBlock,
  copyToClipboard,
  diagramFilename,
  downloadTextFile,
} from '../utils/diagramTransfer'

interface Props {
  projectId: string
  slug?: string | null
  onClose?: () => void
}

/**
 * Shows the project's architecture as Mermaid source so it can be dropped into
 * a README (or mermaid.live). Works for owners and for public project pages —
 * the backend allows anonymous export of published, public projects.
 */
export default function MermaidPanel({ projectId, slug, onClose }: Props) {
  const [code, setCode] = useState('')
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    api
      .get(`/api/projects/${projectId}/export/mermaid`, { responseType: 'text' })
      .then((response) => {
        if (!cancelled) setCode(typeof response.data === 'string' ? response.data : String(response.data))
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the Mermaid export for this project.')
      })
    return () => {
      cancelled = true
    }
  }, [projectId])

  async function copy(text: string, message: string) {
    const copied = await copyToClipboard(text)
    setStatus(copied ? message : 'Copy failed — select the code and copy it manually.')
  }

  return (
    <div className="panel p-4 w-full space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-medium">Mermaid diagram</h3>
          <p className="text-xs text-slate-400">
            Drop this into a README or mermaid.live. Node metadata stays in the JSON export.
          </p>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-slate-400 hover:text-white" aria-label="Close Mermaid view">
            ✕
          </button>
        )}
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <textarea
        className="input font-mono text-xs"
        rows={14}
        value={code}
        readOnly
        aria-label="Mermaid source"
      />

      <div className="flex flex-wrap gap-2">
        <button className="btn" type="button" onClick={() => copy(code, 'Mermaid code copied.')}>
          Copy code
        </button>
        <button
          className="btn-outline"
          type="button"
          onClick={() => copy(asMermaidReadmeBlock(code), 'README block copied.')}
        >
          Copy README block
        </button>
        <button
          className="btn-outline"
          type="button"
          onClick={() => downloadTextFile(diagramFilename(slug, 'mmd'), code, 'text/plain')}
        >
          Download .mmd
        </button>
        <a className="btn-outline" href="https://mermaid.live" target="_blank" rel="noreferrer">
          Open mermaid.live
        </a>
      </div>

      {status && <p className="text-xs text-accent">{status}</p>}
    </div>
  )
}
