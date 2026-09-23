/**
 * Browser helpers behind the architecture "export / import as code" feature.
 * Framework-free so they can be unit-tested directly with vitest.
 */

export type DiagramFileExtension = 'json' | 'mmd'
export type DiagramImportFormat = 'json' | 'mermaid'

export function sanitizeFilenamePart(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

/** e.g. ("event-intel", "mmd") -> "event-intel-architecture.mmd" */
export function diagramFilename(
  slug: string | null | undefined,
  extension: DiagramFileExtension,
): string {
  const base = sanitizeFilenamePart(slug || '')
  return base ? `${base}-architecture.${extension}` : `architecture.${extension}`
}

/** Wrap Mermaid source in a fenced block that renders in GitHub READMEs. */
export function asMermaidReadmeBlock(code: string): string {
  return ['```mermaid', code.trim(), '```'].join('\n')
}

export function downloadTextFile(
  filename: string,
  text: string,
  mimeType = 'text/plain',
): void {
  const blob = new Blob([text], { type: `${mimeType};charset=utf-8` })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.rel = 'noopener'
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

/** Returns false instead of throwing — clipboard access is often blocked. */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
    // Insecure origin or denied permission; the caller offers manual copying.
  }
  return false
}

/** Turn an axios/FastAPI/JSON error into a single human-readable sentence. */
export function describeImportError(error: unknown, format: DiagramImportFormat): string {
  if (error instanceof SyntaxError) {
    return 'That is not valid JSON — check the file or switch the format to Mermaid.'
  }
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => (item as { msg?: string })?.msg ?? String(item))
    return messages.join('; ')
  }
  return `Import failed — check the ${format === 'json' ? 'JSON bundle' : 'Mermaid syntax'}.`
}
