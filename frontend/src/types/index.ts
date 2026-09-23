export interface User {
  id: string
  email: string
  username: string
  full_name?: string | null
}

export interface Portfolio {
  id: string
  owner_id: string
  slug: string
  title: string
  professional_title?: string | null
  about?: string | null
  skills: string[]
  github_url?: string | null
  linkedin_url?: string | null
  website_url?: string | null
  contact_email?: string | null
  is_public: boolean
  theme: string
}

export interface Project {
  id: string
  portfolio_id: string
  slug: string
  name: string
  short_description?: string | null
  full_description?: string | null
  status: string
  technologies: string[]
  github_url?: string | null
  live_url?: string | null
  documentation_url?: string | null
  key_features: string[]
  challenges?: string | null
  solutions?: string | null
  is_published: boolean
}

export interface ArchNode {
  id: string
  project_id: string
  node_type: string
  name: string
  description?: string | null
  technology?: string | null
  version?: string | null
  environment?: string | null
  position_x: number
  position_y: number
  metadata_json: Record<string, any>
}

export interface ArchEdge {
  id: string
  project_id: string
  source_node_id: string
  target_node_id: string
  label?: string | null
}

export interface ApiEndpoint {
  id: string
  project_id: string
  method: string
  path: string
  description?: string | null
  requires_auth: boolean
  request_body?: string | null
  response_body?: string | null
  status_codes: number[]
}

/** JSON bundle produced by `/api/projects/{id}/export/json`. */
export interface DiagramProjectInfo {
  id: string
  slug: string
  name: string
  portfolio_slug?: string | null
}

export interface DiagramNodeItem {
  key: string
  node_type: string
  name: string
  description?: string | null
  technology?: string | null
  version?: string | null
  environment?: string | null
  position_x: number
  position_y: number
  metadata_json: Record<string, any>
}

export interface DiagramEdgeItem {
  source_key: string
  target_key: string
  label?: string | null
}

export interface DiagramDocument {
  format: string
  version: number
  project?: DiagramProjectInfo | null
  nodes: DiagramNodeItem[]
  edges: DiagramEdgeItem[]
}

export type DiagramImportMode = 'merge' | 'replace'

export interface DiagramImportResult {
  nodes_created: number
  edges_created: number
  nodes_deleted: number
  edges_deleted: number
}

export const NODE_TYPES = [
  'user', 'frontend', 'backend', 'api', 'microservice', 'database', 'cache', 'queue',
  'container', 'docker', 'kubernetes', 'kubernetes_cluster', 'kubernetes_namespace', 'vm',
  'server', 'load_balancer', 'reverse_proxy', 'firewall', 'network', 'vpc', 'subnet',
  'cloud_resource', 'storage', 'ci_pipeline', 'cd_pipeline', 'git_repository',
  'gitops_repository', 'container_registry', 'github_actions', 'jenkins', 'gitlab_ci',
  'helm', 'kustomize', 'argo_cd', 'flux_cd', 'monitoring', 'logging', 'security',
  'external_service',
] as const
