import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useModelStore } from './model'

const DEFAULT_NAMES = [
  'Strategy', 'Business', 'Application', 'Technology & Physical',
  'Motivation', 'Implementation & Migration', 'Other', 'Relations', 'Views',
]

// ── helpers ───────────────────────────────────────────────────────────────────

function mockFetchOk(body) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(body),
  })
}

function mockFetchFail() {
  global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
}

// ── setup ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  // Default CSRF cookie
  Object.defineProperty(document, 'cookie', {
    writable: true,
    value: 'csrftoken=test-csrf-token',
  })
})

// ── fetchModel ────────────────────────────────────────────────────────────────

describe('fetchModel', () => {
  it('loads model from /api/model/', async () => {
    const fakeModel = { name: 'ASPICE', type: 'model', children: [] }
    mockFetchOk(fakeModel)
    const store = useModelStore()
    await store.fetchModel()
    expect(store.model).toEqual(fakeModel)
    expect(store.loading).toBe(false)
  })

  it('sets error on network failure', async () => {
    mockFetchFail()
    const store = useModelStore()
    await store.fetchModel()
    expect(store.error).toBe('Network error')
    expect(store.model).toBeNull()
  })
})

// ── resetModel ────────────────────────────────────────────────────────────────

describe('resetModel', () => {
  it('sets model to *New Model with 9 default folders', () => {
    const store = useModelStore()
    store.resetModel()
    expect(store.model.name).toBe('*New Model')
    expect(store.model.children).toHaveLength(9)
  })

  it('default folders have correct names', () => {
    const store = useModelStore()
    store.resetModel()
    const names = store.model.children.map(c => c.name)
    expect(names).toEqual(DEFAULT_NAMES)
  })

  it('all default folders are nodes', () => {
    const store = useModelStore()
    store.resetModel()
    store.model.children.forEach(c => {
      expect(c.type).toBe('node')
    })
  })

  it('Views folder contains Default View', () => {
    const store = useModelStore()
    store.resetModel()
    const views = store.model.children.find(c => c.name === 'Views')
    expect(views.children.some(v => v.name === 'Default View')).toBe(true)
  })

  it('clears selected', () => {
    const store = useModelStore()
    store.selected = { id: 'abc', name: 'Some Node' }
    store.resetModel()
    expect(store.selected).toBeNull()
  })

  it('does NOT call the server', () => {
    global.fetch = vi.fn()
    const store = useModelStore()
    store.resetModel()
    expect(fetch).not.toHaveBeenCalled()
  })

  it('produces an independent copy — mutations do not affect the default', () => {
    const store = useModelStore()
    store.resetModel()
    store.model.name = 'Modified'
    store.resetModel()
    expect(store.model.name).toBe('*New Model')
  })
})

// ── saveModel ─────────────────────────────────────────────────────────────────

describe('saveModel', () => {
  it('POSTs current model as JSON to /api/model/save/', async () => {
    const store = useModelStore()
    store.model = { name: 'My Project', type: 'model', children: [] }
    mockFetchOk({ ok: true, name: 'My Project' })

    await store.saveModel()

    expect(fetch).toHaveBeenCalledWith('/api/model/save/', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify(store.model),
    }))
  })

  it('sends CSRF token in headers', async () => {
    const store = useModelStore()
    store.model = { name: 'X', type: 'model', children: [] }
    mockFetchOk({ ok: true, name: 'X' })

    await store.saveModel()

    const headers = fetch.mock.calls[0][1].headers
    expect(headers['X-CSRFToken']).toBe('test-csrf-token')
  })

  it('returns ok and name on success', async () => {
    const store = useModelStore()
    store.model = { name: 'ASPICE', type: 'model', children: [] }
    mockFetchOk({ ok: true, name: 'ASPICE' })

    const result = await store.saveModel()
    expect(result.ok).toBe(true)
    expect(result.name).toBe('ASPICE')
  })

  it('returns null on network failure', async () => {
    const store = useModelStore()
    store.model = { name: 'X', type: 'model', children: [] }
    global.fetch = vi.fn().mockResolvedValue({ ok: false })

    const result = await store.saveModel()
    expect(result).toBeNull()
  })
})

// ── selectNode / findById ─────────────────────────────────────────────────────

describe('selectNode', () => {
  it('sets selected to the given node', () => {
    const store = useModelStore()
    const node = { id: '1', name: 'Actor', type: 'element' }
    store.selectNode(node)
    expect(store.selected).toStrictEqual(node)
  })
})

describe('findById', () => {
  beforeEach(() => {
    const store = useModelStore()
    store.model = {
      id: 'root', name: 'Model', type: 'model',
      children: [{
        id: 'f1', name: 'Business', type: 'node',
        children: [
          { id: 'e1', name: 'Customer', type: 'element', element_type: 'BusinessActor', children: [] },
          { id: 'e2', name: 'Order Process', type: 'element', element_type: 'BusinessProcess', children: [] },
        ]
      }]
    }
  })

  it('finds top-level node by id', () => {
    const store = useModelStore()
    expect(store.findById('f1').name).toBe('Business')
  })

  it('finds nested element by id', () => {
    const store = useModelStore()
    expect(store.findById('e1').name).toBe('Customer')
  })

  it('returns null for unknown id', () => {
    const store = useModelStore()
    expect(store.findById('unknown')).toBeNull()
  })

  it('returns null when model is not loaded', () => {
    const store = useModelStore()
    store.model = null
    expect(store.findById('e1')).toBeNull()
  })
})

// ── renameNode ────────────────────────────────────────────────────────────────

describe('renameNode', () => {
  beforeEach(() => {
    const store = useModelStore()
    store.model = {
      id: 'root', name: 'Model', type: 'model',
      children: [{
        id: 'f1', name: 'Business', type: 'node',
        children: [
          { id: 'e1', name: 'Customer', type: 'element', element_type: 'BusinessActor', children: [] },
        ]
      }]
    }
  })

  it('renames a model-tree node and marks model dirty', () => {
    const store = useModelStore()
    store.renameNode('e1', 'Client')
    expect(store.findById('e1').name).toBe('Client')
    expect(store.isDirty).toBe(true)
  })

  it('ignores empty/whitespace name for model-tree node', () => {
    const store = useModelStore()
    store.renameNode('e1', '   ')
    expect(store.findById('e1').name).toBe('Customer')
    expect(store.isDirty).toBe(false)
  })

  it('canvas-level node (unknown id): sets diagramRenameSignal with id and name', () => {
    const store = useModelStore()
    store.renameNode('canvas-uuid-99', 'NewGroupName')
    expect(store.diagramRenameSignal).toEqual({ id: 'canvas-uuid-99', name: 'NewGroupName' })
  })

  it('canvas-level node: each rename creates a new signal reference', () => {
    const store = useModelStore()
    store.renameNode('canvas-uuid-99', 'First')
    const sig1 = store.diagramRenameSignal
    store.renameNode('canvas-uuid-99', 'Second')
    const sig2 = store.diagramRenameSignal
    expect(sig1).not.toBe(sig2)
    expect(sig2.name).toBe('Second')
  })

  it('canvas-level node: marks model dirty', () => {
    const store = useModelStore()
    store.renameNode('canvas-uuid-99', 'NewGroupName')
    expect(store.isDirty).toBe(true)
  })

  it('canvas-level node: ignores empty/whitespace name', () => {
    const store = useModelStore()
    store.renameNode('canvas-uuid-99', '  ')
    expect(store.diagramRenameSignal).toBeNull()
    expect(store.isDirty).toBe(false)
  })
})

// ── deleteNode ────────────────────────────────────────────────────────────────

describe('deleteNode', () => {
  beforeEach(() => {
    const store = useModelStore()
    store.model = {
      id: 'root', name: 'Model', type: 'model',
      children: [{
        id: 'f1', name: 'Business', type: 'node',
        children: [
          { id: 'e1', name: 'Customer', type: 'element', element_type: 'BusinessActor', children: [] },
          { id: 'e2', name: 'Order Process', type: 'element', element_type: 'BusinessProcess', children: [] },
        ]
      }]
    }
  })

  it('removes the node from the tree', () => {
    const store = useModelStore()
    store.deleteNode('e1')
    expect(store.findById('e1')).toBeNull()
  })

  it('adds deleted id to pendingDeleteIds', () => {
    const store = useModelStore()
    store.deleteNode('e1')
    expect(store.pendingDeleteIds.has('e1')).toBe(true)
  })

  it('accumulates multiple deletions in pendingDeleteIds', () => {
    const store = useModelStore()
    store.deleteNode('e1')
    store.deleteNode('e2')
    expect(store.pendingDeleteIds.has('e1')).toBe(true)
    expect(store.pendingDeleteIds.has('e2')).toBe(true)
  })

  it('emits diagramDeleteSignal with the deleted id', () => {
    const store = useModelStore()
    store.deleteNode('e1')
    expect(store.diagramDeleteSignal).toEqual({ id: 'e1' })
  })

  it('marks model dirty', () => {
    const store = useModelStore()
    store.deleteNode('e1')
    expect(store.isDirty).toBe(true)
  })

  it('clears selected when the deleted node was selected', () => {
    const store = useModelStore()
    store.selectNode(store.findById('e1'))
    store.deleteNode('e1')
    expect(store.selected).toBeNull()
  })

  it('does not clear selected when a different node is deleted', () => {
    const store = useModelStore()
    store.selectNode(store.findById('e2'))
    store.deleteNode('e1')
    expect(store.selected?.id).toBe('e2')
  })

  it('pendingDeleteIds is cleared after fetchModel', async () => {
    const store = useModelStore()
    store.deleteNode('e1')
    expect(store.pendingDeleteIds.size).toBe(1)
    mockFetchOk({ name: 'Model', type: 'model', children: [] })
    await store.fetchModel()
    expect(store.pendingDeleteIds.size).toBe(0)
  })

  it('pendingDeleteIds is cleared after successful saveModel', async () => {
    const store = useModelStore()
    store.deleteNode('e1')
    expect(store.pendingDeleteIds.size).toBe(1)
    mockFetchOk({ ok: true, name: 'Model' })
    await store.saveModel()
    expect(store.pendingDeleteIds.size).toBe(0)
  })

  it('pendingDeleteIds is NOT cleared when saveModel fails', async () => {
    const store = useModelStore()
    store.deleteNode('e1')
    global.fetch = vi.fn().mockResolvedValue({ ok: false })
    await store.saveModel()
    expect(store.pendingDeleteIds.has('e1')).toBe(true)
  })
})

// ── renameNode — model root ───────────────────────────────────────────────────

describe('renameNode — model root', () => {
  const ROOT_ID = '00000000-0000-0000-0000-000000000000'

  beforeEach(() => {
    const store = useModelStore()
    store.model = { id: ROOT_ID, name: '*New Model', type: 'model', children: [] }
  })

  it('renames the model root and marks dirty', () => {
    const store = useModelStore()
    store.renameNode(ROOT_ID, 'My Project')
    expect(store.model.name).toBe('My Project')
    expect(store.isDirty).toBe(true)
  })

  it('does NOT set diagramRenameSignal for model root (not a canvas node)', () => {
    const store = useModelStore()
    store.renameNode(ROOT_ID, 'My Project')
    expect(store.diagramRenameSignal).toBeNull()
  })

  it('ignores empty/whitespace name for model root', () => {
    const store = useModelStore()
    store.renameNode(ROOT_ID, '   ')
    expect(store.model.name).toBe('*New Model')
    expect(store.isDirty).toBe(false)
  })

  it('findById finds model root by its id', () => {
    const store = useModelStore()
    const found = store.findById(ROOT_ID)
    expect(found).not.toBeNull()
    expect(found.name).toBe('*New Model')
    expect(found.type).toBe('model')
  })
})

// ── updateDocumentation ────────────────────────────────────────────────────────

describe('updateDocumentation', () => {
  const ROOT_ID = '00000000-0000-0000-0000-000000000000'

  beforeEach(() => {
    const store = useModelStore()
    store.model = {
      id: ROOT_ID, name: 'M', type: 'model',
      children: [{
        id: 'f1', name: 'Business', type: 'node',
        children: [
          { id: 'e1', name: 'Actor', type: 'element', element_type: 'BusinessActor',
            documentation: '', children: [] },
        ]
      }]
    }
  })

  it('updates documentation on an element and marks dirty', () => {
    const store = useModelStore()
    store.updateDocumentation('e1', 'Main actor')
    expect(store.findById('e1').documentation).toBe('Main actor')
    expect(store.isDirty).toBe(true)
  })

  it('updates documentation on model root and marks dirty', () => {
    const store = useModelStore()
    store.updateDocumentation(ROOT_ID, 'Top-level model description')
    expect(store.model.documentation).toBe('Top-level model description')
    expect(store.isDirty).toBe(true)
  })

  it('does nothing for unknown id', () => {
    const store = useModelStore()
    store.updateDocumentation('no-such-id', 'Ignored')
    expect(store.isDirty).toBe(false)
  })
})

// ── updateProperties ──────────────────────────────────────────────────────────

describe('updateProperties', () => {
  const ROOT_ID = '00000000-0000-0000-0000-000000000000'

  beforeEach(() => {
    const store = useModelStore()
    store.model = {
      id: ROOT_ID, name: 'M', type: 'model',
      children: [{
        id: 'f1', name: 'Business', type: 'node',
        children: [
          { id: 'e1', name: 'Actor', type: 'element', element_type: 'BusinessActor',
            properties: [], children: [] },
        ]
      }]
    }
  })

  it('updates properties on an element and marks dirty', () => {
    const store = useModelStore()
    store.updateProperties('e1', [{ key: 'owner', value: 'Alice' }])
    expect(store.findById('e1').properties).toEqual([{ key: 'owner', value: 'Alice' }])
    expect(store.isDirty).toBe(true)
  })

  it('updates properties on model root and marks dirty', () => {
    const store = useModelStore()
    store.updateProperties(ROOT_ID, [{ key: 'version', value: '1.0' }])
    expect(store.model.properties).toEqual([{ key: 'version', value: '1.0' }])
    expect(store.isDirty).toBe(true)
  })

  it('does nothing for unknown id', () => {
    const store = useModelStore()
    store.updateProperties('no-such-id', [{ key: 'k', value: 'v' }])
    expect(store.isDirty).toBe(false)
  })
})

// ── migrateFolderTypes — root id ──────────────────────────────────────────────

describe('migrateFolderTypes (via fetchModel)', () => {
  it('fetchModel assigns canonical id to root when server returns id=""', async () => {
    mockFetchOk({ name: 'ASPICE', type: 'model', id: '', children: [] })
    const store = useModelStore()
    await store.fetchModel()
    expect(store.model.id).toBe('00000000-0000-0000-0000-000000000000')
  })

  it('fetchModel preserves existing root id', async () => {
    mockFetchOk({ name: 'ASPICE', type: 'model', id: 'custom-root-id', children: [] })
    const store = useModelStore()
    await store.fetchModel()
    expect(store.model.id).toBe('custom-root-id')
  })

  it('after fetchModel with id="", renameNode on root marks dirty', async () => {
    mockFetchOk({ name: 'ASPICE', type: 'model', id: '', children: [] })
    const store = useModelStore()
    await store.fetchModel()
    store.renameNode(store.model.id, 'New Name')
    expect(store.model.name).toBe('New Name')
    expect(store.isDirty).toBe(true)
  })
})

// ── New does not touch server (integration) ───────────────────────────────────

describe('New → Save workflow', () => {
  it('resetModel followed by saveModel saves the new empty model', async () => {
    const store = useModelStore()
    // Simulate previous state
    store.model = { name: 'ASPICE', type: 'model', children: [{ name: 'Business' }] }

    store.resetModel()
    expect(store.model.name).toBe('*New Model')

    mockFetchOk({ ok: true, name: '*New Model' })
    const result = await store.saveModel()

    // Verify the NEW (empty) model was sent, not the old ASPICE
    const sentBody = JSON.parse(fetch.mock.calls[0][1].body)
    expect(sentBody.name).toBe('*New Model')
    expect(sentBody.children).toHaveLength(9)
    expect(result.ok).toBe(true)
  })
})
