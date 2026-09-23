import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ReactFlow, { Background, Controls, MiniMap, type Node, type Edge } from 'reactflow'
import 'reactflow/dist/style.css'
import api from '../api/client'
import type { ApiEndpoint, ArchEdge, ArchNode, Project } from '../types'
import NodeDetailPanel from '../components/NodeDetailPanel'

function toFlowNode(n: ArchNode): Node {
  return {
    id: n.id,
    position: { x: n.position_x, y: n.position_y },
    data: { label: `${n.name}\n[${n.node_type}]` },
    style: {
      background: '#111823', color: '#e2e8f0', border: '1px solid #1e2a38',
      borderRadius: 8, padding: 8, fontSize: 12, whiteSpace: 'pre-line', width: 160, cursor: 'pointer',
    },
  }
}

function toFlowEdge(e: ArchEdge): Edge {
  return { id: e.id, source: e.source_node_id, target: e.target_node_id, label: e.label || undefined, animated: true }
}

export default function PublicProject() {
  const { slug, projectSlug } = useParams()
  const [project, setProject] = useState<Project | null>(null)
  const [rawNodes, setRawNodes] = useState<ArchNode[]>([])
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [endpoints, setEndpoints] = useState<ApiEndpoint[]>([])
  const [selected, setSelected] = useState<ArchNode | null>(null)
  const [methodFilter, setMethodFilter] = useState('ALL')

  useEffect(() => {
    api.get(`/api/projects/public/${slug}/${projectSlug}`).then((r) => {
      const proj: Project = r.data
      setProject(proj)
      api.get(`/api/projects/${proj.id}/diagram`).then((d) => {
        setRawNodes(d.data.nodes)
        setNodes(d.data.nodes.map(toFlowNode))
        setEdges(d.data.edges.map(toFlowEdge))
      })
      api.get(`/api/projects/${proj.id}/endpoints`).then((e) => setEndpoints(e.data))
    })
  }, [slug, projectSlug])

  function onNodeClick(_: any, node: Node) {
    const found = rawNodes.find((n) => n.id === node.id)
    if (found) setSelected(found)
  }

  if (!project) return <p className="p-8 text-slate-400">Loading...</p>

  const filteredEndpoints = methodFilter === 'ALL' ? endpoints : endpoints.filter((e) => e.method === methodFilter)

  return (
    <div className="max-w-6xl mx-auto py-10 space-y-8 px-4">
      <Link to={`/p/${slug}`} className="text-sm text-accent">← Back to portfolio</Link>

      <header>
        <h1 className="text-2xl font-bold">{project.name}</h1>
        {project.short_description && <p className="text-slate-400 mt-1">{project.short_description}</p>}
        {project.full_description && <p className="text-slate-300 mt-3 max-w-3xl">{project.full_description}</p>}
        <div className="flex flex-wrap gap-1 mt-3">
          {project.technologies.map((t) => (
            <span key={t} className="text-[10px] px-2 py-0.5 rounded bg-bg-border text-slate-300">{t}</span>
          ))}
        </div>
        <div className="flex gap-4 mt-3 text-sm">
          {project.github_url && <a className="text-accent" href={project.github_url} target="_blank" rel="noreferrer">Repository</a>}
          {project.live_url && <a className="text-accent" href={project.live_url} target="_blank" rel="noreferrer">Live demo</a>}
        </div>
      </header>

      <section>
        <h2 className="text-lg font-semibold mb-2">Interactive architecture</h2>
        <p className="text-sm text-slate-400 mb-3">Click any component to inspect its details.</p>
        <div className="panel" style={{ height: 480 }}>
          <div className="h-full flex">
            <div className="flex-1">
              <ReactFlow nodes={nodes} edges={edges} onNodeClick={onNodeClick} fitView nodesDraggable={false} nodesConnectable={false}>
                <Background color="#1e2a38" gap={16} />
                <Controls showInteractive={false} />
                <MiniMap pannable zoomable style={{ background: '#0b0f14' }} />
              </ReactFlow>
            </div>
            {selected && (
              <div className="p-3 overflow-y-auto">
                <NodeDetailPanel node={selected} onClose={() => setSelected(null)} />
              </div>
            )}
          </div>
        </div>
      </section>

      {endpoints.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">API Explorer</h2>
            <select className="input !w-auto !py-1" value={methodFilter} onChange={(e) => setMethodFilter(e.target.value)}>
              {['ALL', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map((m) => <option key={m}>{m}</option>)}
            </select>
          </div>
          <div className="panel divide-y divide-bg-border">
            {filteredEndpoints.map((ep) => (
              <div key={ep.id} className="p-3 text-sm flex items-center gap-3">
                <span className="font-mono text-accent w-16">{ep.method}</span>
                <span className="font-mono">{ep.path}</span>
                {ep.description && <span className="text-slate-400">— {ep.description}</span>}
                {ep.requires_auth && <span className="text-[10px] ml-auto px-2 py-0.5 rounded bg-bg-border">auth required</span>}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
