"""Export and import architecture diagrams as JSON or Mermaid.

Two interchangeable representations are supported:

* **JSON** (``GET /api/projects/{id}/export/json``) — the canonical, lossless
  representation. Every node field (``metadata_json``, version, environment and
  canvas position included) plus every edge is preserved, so a downloaded file
  can be POSTed straight back to ``/api/projects/{id}/import``.
* **Mermaid** (``GET /api/projects/{id}/export/mermaid``) — a ``flowchart`` that
  renders on GitHub, in Notion, or at mermaid.live. ``node_type`` picks the node
  shape and is also written as a ``[type]`` suffix in the label, so
  :func:`from_mermaid` can recover it. Mermaid is intentionally lossy: metadata,
  versions, environments and canvas positions are JSON-only, and imported nodes
  are auto-laid-out on a grid.

Both importers produce the same :class:`app.schemas.DiagramDocument`, which
:func:`apply_document` writes into the database.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app import models, schemas

MERMAID_ID_PREFIX = "n_"
MERMAID_HEADER = "flowchart TD"

DEFAULT_NODE_TYPE = "backend"

# Mirrors the NODE_TYPES list in frontend/src/types/index.ts. Used only to
# recognise the "[type]" suffix the exporter appends to every Mermaid label.
KNOWN_NODE_TYPES = frozenset({
    "user", "frontend", "backend", "api", "microservice", "database", "cache",
    "queue", "container", "docker", "kubernetes", "kubernetes_cluster",
    "kubernetes_namespace", "vm", "server", "load_balancer", "reverse_proxy",
    "firewall", "network", "vpc", "subnet", "cloud_resource", "storage",
    "ci_pipeline", "cd_pipeline", "git_repository", "gitops_repository",
    "container_registry", "github_actions", "jenkins", "gitlab_ci", "helm",
    "kustomize", "argo_cd", "flux_cd", "monitoring", "logging", "security",
    "external_service",
})

# Mermaid shape delimiters, per node type.
_DATABASE_SHAPE = ("[(", ")]")     # cylinder
_USER_SHAPE = ("((", "))")         # circle
_QUEUE_SHAPE = ("([", "])")        # stadium
_JOB_SHAPE = ("[[", "]]")          # subroutine
_GROUP_SHAPE = ("{{", "}}")        # hexagon
_GENERIC_SHAPE = ("[", "]")        # rectangle

SHAPE_FOR_TYPE: Dict[str, Tuple[str, str]] = {
    "user": _USER_SHAPE,
    "database": _DATABASE_SHAPE,
    "cache": _DATABASE_SHAPE,
    "storage": _DATABASE_SHAPE,
    "queue": _QUEUE_SHAPE,
    "git_repository": _QUEUE_SHAPE,
    "gitops_repository": _QUEUE_SHAPE,
    "container_registry": _QUEUE_SHAPE,
    "ci_pipeline": _JOB_SHAPE,
    "cd_pipeline": _JOB_SHAPE,
    "github_actions": _JOB_SHAPE,
    "jenkins": _JOB_SHAPE,
    "gitlab_ci": _JOB_SHAPE,
    "argo_cd": _JOB_SHAPE,
    "flux_cd": _JOB_SHAPE,
    "helm": _JOB_SHAPE,
    "kustomize": _JOB_SHAPE,
    "kubernetes": _GROUP_SHAPE,
    "kubernetes_cluster": _GROUP_SHAPE,
    "kubernetes_namespace": _GROUP_SHAPE,
    "vm": _GROUP_SHAPE,
    "server": _GROUP_SHAPE,
    "cloud_resource": _GROUP_SHAPE,
    "vpc": _GROUP_SHAPE,
    "subnet": _GROUP_SHAPE,
    "network": _GROUP_SHAPE,
    "firewall": _GROUP_SHAPE,
    "load_balancer": _GROUP_SHAPE,
    "reverse_proxy": _GROUP_SHAPE,
}

# Reverse lookup for hand-written Mermaid that carries no "[type]" suffix.
TYPE_FOR_SHAPE_OPEN: Dict[str, str] = {
    _DATABASE_SHAPE[0]: "database",
    _USER_SHAPE[0]: "user",
    _QUEUE_SHAPE[0]: "queue",
    _JOB_SHAPE[0]: "ci_pipeline",
    _GROUP_SHAPE[0]: "cloud_resource",
}

# Coarse visual family per node type -> the "classDef" styling appended to a chart.
GROUP_FOR_TYPE: Dict[str, str] = {
    "database": "storage",
    "cache": "storage",
    "storage": "storage",
    "queue": "storage",
    "container_registry": "delivery",
    "ci_pipeline": "delivery",
    "cd_pipeline": "delivery",
    "github_actions": "delivery",
    "jenkins": "delivery",
    "gitlab_ci": "delivery",
    "argo_cd": "delivery",
    "flux_cd": "delivery",
    "helm": "delivery",
    "kustomize": "delivery",
    "git_repository": "delivery",
    "gitops_repository": "delivery",
    "kubernetes": "infra",
    "kubernetes_cluster": "infra",
    "kubernetes_namespace": "infra",
    "container": "infra",
    "docker": "infra",
    "vm": "infra",
    "server": "infra",
    "cloud_resource": "infra",
    "vpc": "infra",
    "subnet": "infra",
    "network": "infra",
    "firewall": "infra",
    "load_balancer": "infra",
    "reverse_proxy": "infra",
    "monitoring": "observability",
    "logging": "observability",
    "security": "observability",
}
DEFAULT_GROUP = "service"

GROUP_STYLES: Dict[str, str] = {
    "service": "fill:#10202a,stroke:#3bd6c6,color:#e2e8f0",
    "storage": "fill:#1b1630,stroke:#a78bfa,color:#e2e8f0",
    "delivery": "fill:#221b0b,stroke:#f5b545,color:#f8fafc",
    "infra": "fill:#0d1a2b,stroke:#60a5fa,color:#e2e8f0",
    "observability": "fill:#0d1f17,stroke:#34d399,color:#e2e8f0",
}

# Auto-layout applied to Mermaid imports (Mermaid code has no coordinates).
_GRID_COLUMNS = 4
_GRID_X = 80
_GRID_Y = 80
_GRID_STEP_X = 220
_GRID_STEP_Y = 140


class MermaidParseError(ValueError):
    """Raised when pasted Mermaid uses syntax this importer cannot read."""


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def _node_sort_key(node: "models.ArchitectureNode"):
    # ISO strings keep the ordering stable for nodes without a timestamp too.
    created = node.created_at.isoformat() if node.created_at else ""
    return (created, node.name or "", node.id)


def _edge_sort_key(edge: "models.ArchitectureEdge"):
    return (edge.source_node_id, edge.target_node_id, edge.label or "")


def _sanitize_label(text: Optional[str], max_length: int = 120) -> str:
    """Make a value safe to embed inside a quoted Mermaid label."""
    cleaned = (text or "").replace('"', "'")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[: max_length - 1].rstrip() + "…"
    if cleaned.lower() == "end":
        # A bare "end" token breaks several Mermaid versions.
        cleaned = "End"
    return cleaned or "Unnamed"


def _mermaid_id(node_id: str) -> str:
    return MERMAID_ID_PREFIX + re.sub(r"[^A-Za-z0-9_]", "", str(node_id))


def _safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "architecture"


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #
def to_document(project: "models.Project") -> schemas.DiagramDocument:
    """Lossless JSON representation of a project's architecture."""
    ordered_nodes = sorted(project.nodes, key=_node_sort_key)
    keys = {node.id: f"n{index}" for index, node in enumerate(ordered_nodes)}

    nodes = [
        schemas.DiagramNodeItem(
            key=keys[node.id],
            node_type=node.node_type,
            name=node.name,
            description=node.description,
            technology=node.technology,
            version=node.version,
            environment=node.environment,
            position_x=node.position_x or 0,
            position_y=node.position_y or 0,
            metadata_json=node.metadata_json or {},
        )
        for node in ordered_nodes
    ]

    edges = [
        schemas.DiagramEdgeItem(
            source_key=keys[edge.source_node_id],
            target_key=keys[edge.target_node_id],
            label=edge.label,
        )
        for edge in sorted(project.edges, key=_edge_sort_key)
        if edge.source_node_id in keys and edge.target_node_id in keys
    ]

    portfolio = project.portfolio
    return schemas.DiagramDocument(
        project=schemas.DiagramProjectInfo(
            id=project.id,
            slug=project.slug,
            name=project.name,
            portfolio_slug=getattr(portfolio, "slug", None),
        ),
        nodes=nodes,
        edges=edges,
    )


def export_filename(project: "models.Project", extension: str) -> str:
    portfolio = project.portfolio
    prefix = getattr(portfolio, "slug", None) or "portfolio"
    return _safe_filename(f"{prefix}-{project.slug}-architecture.{extension}")


def _node_line(node: "models.ArchitectureNode") -> str:
    shape_open, shape_close = SHAPE_FOR_TYPE.get(node.node_type, _GENERIC_SHAPE)
    label_parts = [_sanitize_label(node.name)]
    if node.technology:
        label_parts.append(_sanitize_label(node.technology, max_length=40))
    label_parts.append(f"[{node.node_type}]")
    label = "<br/>".join(label_parts)
    return f'    {_mermaid_id(node.id)}{shape_open}"{label}"{shape_close}'


def _edge_line(edge: "models.ArchitectureEdge") -> str:
    arrow = "-->"
    if edge.label:
        # "|" delimits Mermaid edge labels, so it cannot survive inside one.
        label = _sanitize_label(edge.label, max_length=48).replace("|", "/")
        arrow = f"-->|{label}|"
    return f"    {_mermaid_id(edge.source_node_id)} {arrow} {_mermaid_id(edge.target_node_id)}"


def to_mermaid(
    nodes: Sequence["models.ArchitectureNode"],
    edges: Iterable["models.ArchitectureEdge"],
    title: Optional[str] = None,
) -> str:
    """Render nodes/edges as a Mermaid flowchart (lossy, but human-readable)."""
    ordered_nodes = sorted(nodes, key=_node_sort_key)
    node_ids = {node.id for node in ordered_nodes}

    lines = ["%% Architecture diagram exported by Interactive System Architecture Portfolio."]
    if title:
        lines.append(f"%% {_sanitize_label(title, max_length=100)}")
    lines.append(MERMAID_HEADER)
    lines.extend(_node_line(node) for node in ordered_nodes)

    drawable_edges = [
        edge
        for edge in sorted(edges, key=_edge_sort_key)
        if edge.source_node_id in node_ids and edge.target_node_id in node_ids
    ]
    if drawable_edges:
        lines.append("")
        lines.extend(_edge_line(edge) for edge in drawable_edges)

    members: Dict[str, List[str]] = {}
    for node in ordered_nodes:
        group = GROUP_FOR_TYPE.get(node.node_type, DEFAULT_GROUP)
        members.setdefault(group, []).append(_mermaid_id(node.id))
    if members:
        lines.append("")
        for group in sorted(members):
            style = GROUP_STYLES.get(group, GROUP_STYLES[DEFAULT_GROUP])
            lines.append(f"classDef {group} {style}")
        for group in sorted(members):
            lines.append(f"class {','.join(members[group])} {group}")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Mermaid parsing
# --------------------------------------------------------------------------- #
# Shape delimiters, longest first so "[(" wins over "[" and "((" over "(".
_SHAPE_DELIMITERS: List[Tuple[str, str]] = [
    _DATABASE_SHAPE,
    _JOB_SHAPE,
    _USER_SHAPE,
    _GROUP_SHAPE,
    _QUEUE_SHAPE,
    _GENERIC_SHAPE,
    ("(", ")"),
    ("{", "}"),
]

_SHAPED_TOKEN_RE = re.compile(
    r"^(?P<id>[A-Za-z_][A-Za-z0-9_]*)\s*(?:"
    + "|".join(
        re.escape(shape_open) + rf"(?P<label{index}>.*?)" + re.escape(shape_close)
        for index, (shape_open, shape_close) in enumerate(_SHAPE_DELIMITERS)
    )
    + r")$",
    re.DOTALL,
)

_BARE_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_HEADER_RE = re.compile(r"^(?:graph|flowchart)\b.*$", re.IGNORECASE)

_DIRECTIVE_RE = re.compile(
    r"^(?:classDef|class|style|linkStyle|direction|subgraph|end|click|title"
    r"|accTitle|accDescr)\b",
    re.IGNORECASE,
)

# "A -- label --> B" (spaces around the dashes are optional in Mermaid)
_EDGE_DASH_LABEL_RE = re.compile(
    r"^(?P<left>.+?)\s*--\s*(?P<label>.+?)\s*-->\s*(?P<right>.+)$"
)
# "A -->|label| B"
_EDGE_BAR_LABEL_RE = re.compile(
    r"^(?P<left>.+?)\s*-{1,2}->\s*\|(?P<label>[^|]*)\|\s*(?P<right>.+)$"
)
# "A --> B", "A -.-> B", "A ==> B", "A --- B"
_EDGE_PLAIN_RE = re.compile(
    r"^(?P<left>.+?)\s*(?:-->|--->|==>|-.->|---|\.->)\s*(?P<right>.+)$"
)

_LABEL_BREAK_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TYPE_SUFFIX_RE = re.compile(r"^\[([a-z][a-z0-9_]*)\]$")


def _grid_position(index: int) -> Tuple[int, int]:
    return (
        _GRID_X + (index % _GRID_COLUMNS) * _GRID_STEP_X,
        _GRID_Y + (index // _GRID_COLUMNS) * _GRID_STEP_Y,
    )


def _strip_delimiters(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[:1] == value[-1:] and value[0] in {'"', "`"}:
        return value[1:-1].strip()
    return value


def _split_label(label: str, fallback_type: str) -> Tuple[str, Optional[str], str]:
    """Split ``Name<br/>Technology<br/>[node_type]`` into its three parts."""
    segments = [s.strip() for s in _LABEL_BREAK_RE.split(label) if s.strip()]
    node_type = fallback_type

    if len(segments) > 1:
        suffix = _TYPE_SUFFIX_RE.match(segments[-1])
        if suffix and suffix.group(1) in KNOWN_NODE_TYPES:
            node_type = suffix.group(1)
            segments = segments[:-1]

    name = segments[0] if segments else ""
    technology = " ".join(segments[1:]) or None
    return name or "Unnamed node", technology, node_type


def _parse_shaped_token(token: str) -> Optional[Tuple[str, str, Optional[str], str]]:
    match = _SHAPED_TOKEN_RE.match(token)
    if not match:
        return None
    for index, (shape_open, _) in enumerate(_SHAPE_DELIMITERS):
        raw_label = match.group(f"label{index}")
        if raw_label is None:
            continue
        fallback = TYPE_FOR_SHAPE_OPEN.get(shape_open, DEFAULT_NODE_TYPE)
        name, technology, node_type = _split_label(_strip_delimiters(raw_label), fallback)
        return match.group("id"), name, technology, node_type
    return None


def _register(
    nodes: Dict[str, schemas.DiagramNodeItem],
    node_id: str,
    name: str,
    technology: Optional[str],
    node_type: str,
    *,
    defined: bool,
) -> None:
    """Add a node; a real definition always wins over a bare-id placeholder."""
    if nodes.get(node_id) is not None and not defined:
        return
    position_x, position_y = _grid_position(len(nodes))
    nodes[node_id] = schemas.DiagramNodeItem(
        key=node_id,
        node_type=node_type,
        name=name,
        technology=technology,
        position_x=position_x,
        position_y=position_y,
    )


def _resolve_ref(
    raw: str, nodes: Dict[str, schemas.DiagramNodeItem], line_number: int
) -> str:
    token = raw.strip()
    parsed = _parse_shaped_token(token)
    if parsed is not None:
        node_id, name, technology, node_type = parsed
        _register(nodes, node_id, name, technology, node_type, defined=True)
        return node_id
    if _BARE_ID_RE.match(token):
        _register(nodes, token, token, None, DEFAULT_NODE_TYPE, defined=False)
        return token
    raise MermaidParseError(
        f"Line {line_number}: could not read the node reference '{token}'."
    )


def _mask_quoted(line: str) -> str:
    """Blank out anything inside double quotes so arrows in labels are ignored.

    The returned string keeps the original length/offsets, so match spans can be
    sliced out of the untouched line.
    """
    chars = list(line)
    inside = False
    for index, char in enumerate(chars):
        if char == '"':
            inside = not inside
        elif inside:
            chars[index] = "x"
    return "".join(chars)


def _split_edge(line: str) -> Optional[Tuple[str, Optional[str], str]]:
    masked = _mask_quoted(line)
    for pattern in (_EDGE_DASH_LABEL_RE, _EDGE_BAR_LABEL_RE, _EDGE_PLAIN_RE):
        match = pattern.match(masked)
        if match:
            label = match.groupdict().get("label")
            return (
                line[match.start("left"):match.end("left")].strip(),
                line[match.start("label"):match.end("label")].strip() if label is not None else None,
                line[match.start("right"):match.end("right")].strip(),
            )
    return None


def from_mermaid(text: str) -> schemas.DiagramDocument:
    """Parse a Mermaid flowchart into a :class:`schemas.DiagramDocument`.

    Supports the subset produced by :func:`to_mermaid`: node definitions with
    optional shapes/labels, ``A --> B``, ``A -->|label| B`` and
    ``A -- label --> B`` edges, plus comments, ``classDef``/``class``/``style``
    lines and (ignored) ``subgraph`` blocks.
    """
    if not text or not text.strip():
        raise MermaidParseError("No Mermaid code provided.")

    nodes: Dict[str, schemas.DiagramNodeItem] = {}
    edges: List[schemas.DiagramEdgeItem] = []
    in_front_matter = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if line.startswith("---"):
            in_front_matter = not in_front_matter
            continue
        if in_front_matter or not line or line.startswith("%%"):
            continue
        if _HEADER_RE.match(line) or _DIRECTIVE_RE.match(line):
            continue

        parts = _split_edge(line)
        if parts is None:
            _resolve_ref(line, nodes, line_number)
            continue

        left, label, right = parts
        source = _resolve_ref(left, nodes, line_number)
        target = _resolve_ref(right, nodes, line_number)
        edges.append(
            schemas.DiagramEdgeItem(
                source_key=source,
                target_key=target,
                label=_sanitize_label(label, max_length=120) if label else None,
            )
        )

    if not nodes:
        raise MermaidParseError(
            "No nodes found — expected a flowchart such as 'flowchart TD'."
        )

    return schemas.DiagramDocument(nodes=list(nodes.values()), edges=edges)


# --------------------------------------------------------------------------- #
# Import
# --------------------------------------------------------------------------- #
def apply_document(
    project: "models.Project",
    document: schemas.DiagramDocument,
    db: Session,
    mode: str = "merge",
) -> schemas.ImportResult:
    """Write an imported diagram into ``project``.

    ``mode="merge"`` appends the imported nodes/edges to the existing diagram
    (handy for pasting a fragment), while ``mode="replace"`` first clears the
    project's current diagram.
    """
    nodes_deleted = 0
    edges_deleted = 0
    if mode == "replace":
        edges_deleted = (
            db.query(models.ArchitectureEdge)
            .filter(models.ArchitectureEdge.project_id == project.id)
            .delete(synchronize_session=False)
        )
        nodes_deleted = (
            db.query(models.ArchitectureNode)
            .filter(models.ArchitectureNode.project_id == project.id)
            .delete(synchronize_session=False)
        )
        db.flush()

    key_to_id: Dict[str, str] = {}
    for item in document.nodes:
        node = models.ArchitectureNode(
            project_id=project.id,
            node_type=item.node_type,
            name=item.name,
            description=item.description,
            technology=item.technology,
            version=item.version,
            environment=item.environment,
            position_x=item.position_x,
            position_y=item.position_y,
            metadata_json=item.metadata_json or {},
        )
        db.add(node)
        db.flush()
        key_to_id[item.key] = node.id

    edges_created = 0
    for edge in document.edges:
        source = key_to_id.get(edge.source_key)
        target = key_to_id.get(edge.target_key)
        if not source or not target or source == target:
            continue
        db.add(
            models.ArchitectureEdge(
                project_id=project.id,
                source_node_id=source,
                target_node_id=target,
                label=edge.label,
            )
        )
        edges_created += 1

    db.commit()
    return schemas.ImportResult(
        nodes_created=len(document.nodes),
        edges_created=edges_created,
        nodes_deleted=nodes_deleted,
        edges_deleted=edges_deleted,
    )
