import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ReactFlow, {
  Background, Controls, MiniMap, addEdge, applyNodeChanges, applyEdgeChanges,
  type Node, type Edge, type Connection, type NodeChange, type EdgeChange,
} from 'reactflow'
import 'reactflow/dist/style.css'
import api from '../api/client'
import type { ArchNode, ArchEdge, Project } from '../types'
import { NODE_TYPES } from '../types'
import DiagramImportPanel from '../components/DiagramImportPanel'
import MermaidPanel from '../components/MermaidPanel'
import { diagramFilename, downloadTextFile } from '../utils/diagramTransfer'

type SidePanel = 'node' | 'mermaid' | 'import'

function toFlowNode(n: ArchNode): Node {
  return {
    id: n.id,
    position: { x: n.position_x, y: n.position_y },
    data: { label: `${n.name}\n[${n.node_type}]` },
    style: {
      background: '#111823', color: '#e2e8f0', border: '1px solid #1e2a38',
      borderRadius: 8, padding: 8, fontSize: 12, whiteSpace: 'pre-line', width: 160,
    },
  }
}

function toFlowEdge(e: ArchEdge): Edge {
  return { id: e.id, source: e.source_node_id, target: e.target_node_id, label: e.label || undefined, animated: true }
}

export default function ArchitectureEditor() {
  const { projectId } = useParams()
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [raw, setRaw] = useState<ArchNode[]>([])
  const [selected, setSelected] = useState<ArchNode | null>(null)
  const [metaText, setMetaText] = useState('{}')
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState<string>('backend')
  const [panel, setPanel] = useState<SidePanel | null>(null)
  const [project, setProject] = useState<Project | null>(null)

  function load() {
    api.get(`/api/projects/${projectId}/diagram`).then((r) => {
      const data: { nodes: ArchNode[]; edges: ArchEdge[] } = r.data
      setRaw(data.nodes)
      setNodes(data.nodes.map(toFlowNode))
      setEdges(data.edges.map(toFlowEdge))
    })
  }
  useEffect(load, [projectId])

  useEffect(() => {
    api.get(`/api/projects/${projectId}`).then((r) => setProject(r.data)).catch(() => setProject(null))
  }, [projectId])

  const onNodesChange = useCallback((changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)), [])
  const onEdgesChange = useCallback((changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)), [])

  async function onNodeDragStop(_: any, node: Node) {
    await api.put(`/api/nodes/${node.id}`, { position_x: Math.round(node.position.x), position_y: Math.round(node.position.y) })
  }

  async function onConnect(connection: Connection) {
    setEdges((eds) => addEdge({ ...connection, animated: true }, eds))
    const { data } = await api.post(`/api/projects/${projectId}/edges`, {
      source_node_id: connection.source, target_node_id: connection.target,
    })
    load()
    return data
  }

  function onNodeClick(_: any, node: Node) {
    const found = raw.find((n) => n.id === node.id)
    if (found) {
      setSelected(found)
      setMetaText(JSON.stringify(found.metadata_json || {}, null, 2))
      setPanel('node')
    }
  }

  async function addNode(e: React.FormEvent) {
    e.preventDefault()
    if (!newName) return
    await api.post(`/api/projects/${projectId}/nodes`, {
      node_type: newType, name: newName, position_x: 80 + Math.random() * 300, position_y: 80 + Math.random() * 300,
      metadata_json: {},
    })
    setNewName('')
    load()
  }

  async function saveSelected(e: React.FormEvent) {
    e.preventDefault()
    if (!selected) return
    let parsedMeta: Record<string, any> = {}
    try {
      parsedMeta = JSON.parse(metaText)
    } catch {
      alert('Metadata must be valid JSON')
      return
    }
    await api.put(`/api/nodes/${selected.id}`, {
      name: selected.name, node_type: selected.node_type, description: selected.description,
      technology: selected.technology, version: selected.version, environment: selected.environment,
      metadata_json: parsedMeta,
    })
    setSelected(null)
    setPanel(null)
    load()
  }

  async function deleteSelected() {
    if (!selected) return
    await api.delete(`/api/nodes/${selected.id}`)
    setSelected(null)
    setPanel(null)
    load()
  }

  /** Download the lossless JSON bundle for this project's diagram. */
  async function downloadJson() {
    const { data } = await api.get(`/api/projects/${projectId}/export/json`)
    const slug = project?.slug || data?.project?.slug
    downloadTextFile(
      diagramFilename(slug, 'json'),
      JSON.stringify(data, null, 2),
      'application/json',
    )
  }

  return (
    <div className="h-[calc(100vh-56px)] flex flex-col">
      <div className="px-4 py-2 border-b border-bg-border flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <Link to={`/dashboard/projects/${projectId}`} className="text-sm text-accent">← Back to project</Link>
          {project && <span className="text-sm text-slate-400">{project.name}</span>}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            className={`btn-outline !py-1 text-xs ${panel === 'mermaid' ? 'border-accent text-accent' : ''}`}
            type="button"
            onClick={() => setPanel(panel === 'mermaid' ? null : 'mermaid')}
          >
            Mermaid
          </button>
          <button className="btn-outline !py-1 text-xs" type="button" onClick={downloadJson}>
            Export JSON
          </button>
          <button
            className={`btn-outline !py-1 text-xs ${panel === 'import' ? 'border-accent text-accent' : ''}`}
            type="button"
            onClick={() => setPanel(panel === 'import' ? null : 'import')}
          >
            Import
          </button>

          <form onSubmit={addNode} className="flex items-center gap-2 border-l border-bg-border pl-2">
            <select className="input !py-1 !w-auto" value={newType} onChange={(e) => setNewType(e.target.value)}>
              {NODE_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
            </select>
            <input className="input !py-1 !w-48" placeholder="Node name" value={newName} onChange={(e) => setNewName(e.target.value)} />
            <button className="btn" type="submit">+ Add node</button>
          </form>
        </div>
      </div>

      <div className="flex-1 flex">
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeDragStop={onNodeDragStop}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            fitView
          >
            <Background color="#1e2a38" gap={16} />
            <Controls />
            <MiniMap pannable zoomable style={{ background: '#111823' }} />
          </ReactFlow>
        </div>

        {panel && (
          <div className="w-96 border-l border-bg-border p-4 space-y-3 overflow-y-auto">
            {panel === 'node' && selected && (
              <form onSubmit={saveSelected} className="space-y-3">
                <h3 className="font-medium">Edit node</h3>
              <div>
                <label className="label">Name</label>
                <input className="input" value={selected.name} onChange={(e) => setSelected({ ...selected, name: e.target.value })} />
              </div>
              <div>
                <label className="label">Type</label>
                <select className="input" value={selected.node_type} onChange={(e) => setSelected({ ...selected, node_type: e.target.value })}>
                  {NODE_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Description</label>
                <textarea className="input" rows={2} value={selected.description || ''}
                          onChange={(e) => setSelected({ ...selected, description: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="label">Technology</label>
                  <input className="input" value={selected.technology || ''} onChange={(e) => setSelected({ ...selected, technology: e.target.value })} />
                </div>
                <div>
                  <label className="label">Version</label>
                  <input className="input" value={selected.version || ''} onChange={(e) => setSelected({ ...selected, version: e.target.value })} />
                </div>
              </div>
              <div>
                <label className="label">Environment</label>
                <input className="input" value={selected.environment || ''} onChange={(e) => setSelected({ ...selected, environment: e.target.value })} />
              </div>
              <div>
                <label className="label">
                  Metadata (JSON — e.g. endpoints, CI stages, GitOps sync info, security controls, dependencies)
                </label>
                <textarea className="input font-mono text-xs" rows={10} value={metaText} onChange={(e) => setMetaText(e.target.value)} />
              </div>
              <div className="flex gap-2">
                <button className="btn" type="submit">Save node</button>
                <button className="btn-outline text-red-400" type="button" onClick={deleteSelected}>Delete</button>
                <button className="btn-outline" type="button" onClick={() => { setSelected(null); setPanel(null) }}>Close</button>
              </div>
              </form>
            )}

            {panel === 'mermaid' && (
              <MermaidPanel projectId={projectId!} slug={project?.slug} onClose={() => setPanel(null)} />
            )}

            {panel === 'import' && (
              <DiagramImportPanel
                projectId={projectId!}
                onImported={() => { setPanel(null); load() }}
                onClose={() => setPanel(null)}
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
