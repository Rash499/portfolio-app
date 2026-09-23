import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  asMermaidReadmeBlock,
  copyToClipboard,
  describeImportError,
  diagramFilename,
  downloadTextFile,
  sanitizeFilenamePart,
} from './diagramTransfer'

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('sanitizeFilenamePart', () => {
  it('lower-cases and hyphenates anything that is not alphanumeric', () => {
    expect(sanitizeFilenamePart('Event_Intel Platform')).toBe('event-intel-platform')
  })

  it('trims leading and trailing separators', () => {
    expect(sanitizeFilenamePart('  --demo-- ')).toBe('demo')
  })
})

describe('diagramFilename', () => {
  it('builds a slug based filename', () => {
    expect(diagramFilename('event-intel', 'json')).toBe('event-intel-architecture.json')
  })

  it('falls back to a generic name without a slug', () => {
    expect(diagramFilename(undefined, 'mmd')).toBe('architecture.mmd')
    expect(diagramFilename('', 'mmd')).toBe('architecture.mmd')
  })
})

describe('asMermaidReadmeBlock', () => {
  it('wraps the chart in a mermaid fence', () => {
    expect(asMermaidReadmeBlock('flowchart TD\n    a --> b\n')).toBe(
      '```mermaid\nflowchart TD\n    a --> b\n```',
    )
  })
})

describe('downloadTextFile', () => {
  it('downloads the text through a temporary anchor', () => {
    const createObjectURL = vi.fn((_blob: Blob) => 'blob:diagram')
    const revokeObjectURL = vi.fn((_url: string) => undefined)
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL } as unknown as typeof URL)

    const anchors: HTMLAnchorElement[] = []
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(function (this: HTMLAnchorElement) {
        anchors.push(this)
      })

    downloadTextFile('event-intel-architecture.json', '{"nodes":[]}', 'application/json')

    expect(click).toHaveBeenCalledTimes(1)
    expect(anchors).toHaveLength(1)
    expect(anchors[0].download).toBe('event-intel-architecture.json')
    expect(anchors[0].rel).toBe('noopener')
    expect(createObjectURL.mock.calls[0][0].type).toBe('application/json;charset=utf-8')
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:diagram')
    expect(document.querySelector('a')).toBeNull()
  })
})

describe('copyToClipboard', () => {
  it('writes through the async clipboard API', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })

    await expect(copyToClipboard('flowchart TD')).resolves.toBe(true)
    expect(writeText).toHaveBeenCalledWith('flowchart TD')
  })

  it('reports failure when the clipboard is missing or denied', async () => {
    Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true })
    await expect(copyToClipboard('x')).resolves.toBe(false)

    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: vi.fn().mockRejectedValue(new Error('denied')) },
      configurable: true,
    })
    await expect(copyToClipboard('x')).resolves.toBe(false)
  })
})

describe('describeImportError', () => {
  it('passes a FastAPI string detail straight through', () => {
    const error = { response: { data: { detail: "Line 2: could not read the node reference '@@@'." } } }
    expect(describeImportError(error, 'mermaid')).toContain('could not read')
  })

  it('flattens pydantic validation details', () => {
    const error = { response: { data: { detail: [{ msg: 'bad key' }, { msg: 'bad label' }] } } }
    expect(describeImportError(error, 'json')).toBe('bad key; bad label')
  })

  it('explains invalid JSON and generic failures', () => {
    expect(describeImportError(new SyntaxError('Unexpected token'), 'json')).toContain('not valid JSON')
    expect(describeImportError(new Error('boom'), 'json')).toContain('JSON bundle')
    expect(describeImportError(new Error('boom'), 'mermaid')).toContain('Mermaid syntax')
  })
})
