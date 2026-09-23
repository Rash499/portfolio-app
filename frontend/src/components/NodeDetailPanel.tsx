import type { ArchNode } from '../types'

export default function NodeDetailPanel({ node, onClose }: { node: ArchNode; onClose: () => void }) {
  const meta = node.metadata_json || {}
  const metaEntries = Object.entries(meta).filter(([, v]) => v !== null && v !== undefined && v !== '')

  return (
    <div className="panel p-4 w-full max-w-sm">
      <div className="flex items-start justify-between mb-2">
        <div>
          <span className="text-[10px] uppercase tracking-wide text-accent">{node.node_type.replace(/_/g, ' ')}</span>
          <h3 className="text-lg font-semibold">{node.name}</h3>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white" aria-label="Close details">✕</button>
      </div>

      {node.description && <p className="text-sm text-slate-300 mb-3">{node.description}</p>}

      <dl className="text-sm space-y-1 mb-3">
        {node.technology && (
          <div className="flex justify-between"><dt className="text-slate-400">Technology</dt><dd>{node.technology}</dd></div>
        )}
        {node.version && (
          <div className="flex justify-between"><dt className="text-slate-400">Version</dt><dd>{node.version}</dd></div>
        )}
        {node.environment && (
          <div className="flex justify-between"><dt className="text-slate-400">Environment</dt><dd>{node.environment}</dd></div>
        )}
      </dl>

      {metaEntries.length > 0 && (
        <div className="border-t border-bg-border pt-3 space-y-2">
          {metaEntries.map(([key, value]) => (
            <div key={key}>
              <dt className="text-xs uppercase tracking-wide text-slate-400">{key.replace(/_/g, ' ')}</dt>
              <dd className="text-sm whitespace-pre-wrap break-words">
                {Array.isArray(value) ? value.join(', ') : typeof value === 'object' ? JSON.stringify(value) : String(value)}
              </dd>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
