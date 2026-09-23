import { useRef, useState } from 'react'
import api from '../api/client'
import type { DiagramImportMode, DiagramImportResult } from '../types'
import { describeImportError, type DiagramImportFormat } from '../utils/diagramTransfer'

interface Props {
  projectId: string
  onImported: () => void
  onClose?: () => void
}

/**
 * Paste (or upload) an architecture diagram as a JSON bundle produced by the
 * exporter, or as Mermaid source, and write it into the current project.
 */
export default function DiagramImportPanel({ projectId, onImported, onClose }: Props) {
  const [format, setFormat] = useState<DiagramImportFormat>('json')
  const [mode, setMode] = useState<DiagramImportMode>('merge')
  const [text, setText] = useState('')
  const [result, setResult] = useState<DiagramImportResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  async function loadFile(file: File | undefined) {
    if (!file) return
    setText(await file.text())
    setFormat(file.name.toLowerCase().endsWith('.mmd') ? 'mermaid' : 'json')
    setError(null)
    setResult(null)
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (
      mode === 'replace' &&
      !window.confirm('Replace the current diagram? Its nodes and edges will be deleted.')
    ) {
      return
    }
    setError(null)
    setResult(null)
    setBusy(true)
    try {
      const config = { params: { mode } }
      const { data } = format === 'json'
        ? await api.post(`/api/projects/${projectId}/import`, JSON.parse(text), config)
        : await api.post(`/api/projects/${projectId}/import/mermaid`, { mermaid: text }, config)
      setResult(data)
      onImported()
    } catch (err) {
      setError(describeImportError(err, format))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="panel p-4 w-full space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-medium">Import diagram</h3>
          <p className="text-xs text-slate-400">
            Paste exported JSON or Mermaid code. "Merge" adds to the current diagram, "Replace" clears it first.
          </p>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-slate-400 hover:text-white" type="button" aria-label="Close import panel">
            ✕
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="label" htmlFor="import-format">Format</label>
          <select
            id="import-format"
            className="input"
            value={format}
            onChange={(e) => setFormat(e.target.value as DiagramImportFormat)}
          >
            <option value="json">JSON bundle</option>
            <option value="mermaid">Mermaid</option>
          </select>
        </div>
        <div>
          <label className="label" htmlFor="import-mode">Mode</label>
          <select
            id="import-mode"
            className="input"
            value={mode}
            onChange={(e) => setMode(e.target.value as DiagramImportMode)}
          >
            <option value="merge">Merge</option>
            <option value="replace">Replace</option>
          </select>
        </div>
      </div>

      <div>
        <label className="label" htmlFor="import-text">Diagram source</label>
        <textarea
          id="import-text"
          className="input font-mono text-xs"
          rows={12}
          required
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={format === 'json'
            ? '{ "format": "archport-diagram", "nodes": [...], "edges": [...] }'
            : 'flowchart TD\n    api["Ingestion API<br/>[backend]"]'}
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button className="btn" type="submit" disabled={busy || !text.trim()}>
          {busy ? 'Importing...' : 'Import diagram'}
        </button>
        <button className="btn-outline" type="button" onClick={() => fileInput.current?.click()}>
          Load file…
        </button>
        <input
          ref={fileInput}
          type="file"
          className="hidden"
          accept=".json,.mmd,.txt,application/json,text/plain"
          onChange={(e) => loadFile(e.target.files?.[0])}
        />
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}
      {result && (
        <p className="text-xs text-accent">
          Imported {result.nodes_created} node(s) and {result.edges_created} edge(s)
          {result.nodes_deleted + result.edges_deleted > 0
            ? `, replacing ${result.nodes_deleted} node(s) and ${result.edges_deleted} edge(s).`
            : '.'}
        </p>
      )}
    </form>
  )
}
