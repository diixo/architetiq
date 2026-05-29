import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useModelStore } from './model'
import { FOLDER_ELEMENTS } from '../archimate-folder-elements.js'

// ── helpers ───────────────────────────────────────────────────────────────────

function makeModelWithFolders() {
  return {
    id: 'root', name: '*New Model', type: 'model',
    children: [
      { id: 'f-str',  name: 'Strategy',    type: 'node', folder_type: 'strategy',                children: [] },
      { id: 'f-bus',  name: 'Business',    type: 'node', folder_type: 'business',                children: [] },
      { id: 'f-app',  name: 'Application', type: 'node', folder_type: 'application',             children: [] },
      { id: 'f-tec',  name: 'Technology',  type: 'node', folder_type: 'technology',              children: [] },
      { id: 'f-mot',  name: 'Motivation',  type: 'node', folder_type: 'motivation',              children: [] },
      { id: 'f-imp',  name: 'Implementation', type: 'node', folder_type: 'implementation_migration', children: [] },
      { id: 'f-oth',  name: 'Other',       type: 'node', folder_type: 'other',                   children: [] },
      { id: 'f-rel',  name: 'Relations',   type: 'node', folder_type: 'relations',               children: [] },
      { id: 'f-view', name: 'Views',       type: 'node', folder_type: 'diagrams',                children: [] },
    ]
  }
}

function mockFetch() {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ ok: true }),
  })
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  Object.defineProperty(document, 'cookie', { writable: true, value: 'csrftoken=test' })
})

// ── Migration: folder ids ─────────────────────────────────────────────────────

describe('migrateFolderTypes', () => {
  it('adds id to folders without one', async () => {
    const store = useModelStore()
    mockFetch()
    // Simulate fetchModel returning model without ids
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        name: 'M', type: 'model',
        children: [
          { name: 'Business', type: 'node', folder_type: 'business', children: [] },
          { name: 'Strategy', type: 'node', folder_type: 'strategy', children: [] },
        ]
      })
    })
    await store.fetchModel()
    expect(store.model.children[0].id).toBeTruthy()
    expect(store.model.children[1].id).toBeTruthy()
    expect(store.model.children[0].id).not.toBe(store.model.children[1].id)
  })

  it('preserves existing ids', async () => {
    const store = useModelStore()
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        name: 'M', type: 'model',
        children: [
          { id: 'custom-uuid-123', name: 'Business', type: 'node', folder_type: 'business', children: [] },
        ]
      })
    })
    await store.fetchModel()
    expect(store.model.children[0].id).toBe('custom-uuid-123')
  })

  it('adds folder_type by name if missing', async () => {
    const store = useModelStore()
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        name: 'M', type: 'model',
        children: [
          { id: 'x', name: 'Business', type: 'node', children: [] },
          { id: 'y', name: 'Motivation', type: 'node', children: [] },
        ]
      })
    })
    await store.fetchModel()
    expect(store.model.children[0].folder_type).toBe('business')
    expect(store.model.children[1].folder_type).toBe('motivation')
  })
})

// ── addElement ────────────────────────────────────────────────────────────────

describe('addElement', () => {
  const FOLDER_MAP = {
    'f-str':  'strategy',
    'f-bus':  'business',
    'f-app':  'application',
    'f-tec':  'technology',
    'f-mot':  'motivation',
    'f-imp':  'implementation_migration',
    'f-oth':  'other',
  }

  it('creates element with correct type and name', async () => {
    const store = useModelStore()
    store.model = makeModelWithFolders()
    mockFetch()
    await store.addElement('f-bus', 'BusinessActor')
    const folder = store.model.children.find(c => c.id === 'f-bus')
    expect(folder.children).toHaveLength(1)
    expect(folder.children[0].type).toBe('element')
    expect(folder.children[0].element_type).toBe('BusinessActor')
    expect(folder.children[0].name).toBe('Business Actor')
  })

  it('generates unique id for each element', async () => {
    const store = useModelStore()
    store.model = makeModelWithFolders()
    mockFetch()
    await store.addElement('f-bus', 'BusinessActor')
    await store.addElement('f-bus', 'BusinessRole')
    const ids = store.model.children.find(c => c.id === 'f-bus').children.map(e => e.id)
    expect(new Set(ids).size).toBe(2)
  })

  it('adds to correct parent folder', async () => {
    const store = useModelStore()
    store.model = makeModelWithFolders()
    mockFetch()
    await store.addElement('f-mot', 'Outcome')
    const motFolder = store.model.children.find(c => c.id === 'f-mot')
    const busFolder = store.model.children.find(c => c.id === 'f-bus')
    expect(motFolder.children).toHaveLength(1)
    expect(busFolder.children).toHaveLength(0)
  })

  // Test one representative type from every folder type
  const REPRESENTATIVE = {
    'f-str': 'Resource',
    'f-bus': 'BusinessActor',
    'f-app': 'ApplicationComponent',
    'f-tec': 'Node',
    'f-mot': 'Outcome',
    'f-imp': 'WorkPackage',
    'f-oth': 'Location',
  }

  Object.entries(REPRESENTATIVE).forEach(([folderId, elemType]) => {
    it(`adds ${elemType} to ${FOLDER_MAP[folderId]} folder`, async () => {
      const store = useModelStore()
      store.model = makeModelWithFolders()
      mockFetch()
      await store.addElement(folderId, elemType)
      const folder = store.model.children.find(c => c.id === folderId)
      expect(folder.children[0].element_type).toBe(elemType)
    })
  })

  // Test ALL element types across all folders
  Object.entries(FOLDER_ELEMENTS).forEach(([folderType, types]) => {
    if (!types.length) return
    const folderId = Object.keys(FOLDER_MAP).find(id => FOLDER_MAP[id] === folderType)
    if (!folderId) return

    types.forEach(elemType => {
      it(`can create ${elemType} in ${folderType}`, async () => {
        const store = useModelStore()
        store.model = makeModelWithFolders()
        mockFetch()
        await store.addElement(folderId, elemType)
        const folder = store.model.children.find(c => c.id === folderId)
        expect(folder.children.some(e => e.element_type === elemType)).toBe(true)
      })
    })
  })

  it('returns without error when parent not found', async () => {
    const store = useModelStore()
    store.model = makeModelWithFolders()
    mockFetch()
    await expect(store.addElement('nonexistent-id', 'BusinessActor')).resolves.toBeUndefined()
  })
})

// ── addView ───────────────────────────────────────────────────────────────────

describe('addView', () => {
  it('adds ArchimateDiagramModel view', async () => {
    const store = useModelStore()
    store.model = makeModelWithFolders()
    mockFetch()
    await store.addView('f-view', 'ArchimateDiagramModel')
    const folder = store.model.children.find(c => c.id === 'f-view')
    expect(folder.children[0].type).toBe('view')
    expect(folder.children[0].element_type).toBe('ArchimateDiagramModel')
    expect(folder.children[0].name).toBe('New View')
  })

  it('adds SketchModel view with correct label', async () => {
    const store = useModelStore()
    store.model = makeModelWithFolders()
    mockFetch()
    await store.addView('f-view', 'SketchModel')
    const folder = store.model.children.find(c => c.id === 'f-view')
    expect(folder.children[0].name).toBe('New Sketch')
    expect(folder.children[0].element_type).toBe('SketchModel')
  })
})

// ── addChildFolder ────────────────────────────────────────────────────────────

describe('addChildFolder', () => {
  it('adds sub-folder with type node', async () => {
    const store = useModelStore()
    store.model = makeModelWithFolders()
    mockFetch()
    await store.addChildFolder('f-bus')
    const folder = store.model.children.find(c => c.id === 'f-bus')
    expect(folder.children[0].type).toBe('node')
    expect(folder.children[0].name).toBe('New Folder')
    expect(folder.children[0].id).toBeTruthy()
  })

  it('new folder has empty children array', async () => {
    const store = useModelStore()
    store.model = makeModelWithFolders()
    mockFetch()
    await store.addChildFolder('f-str')
    const folder = store.model.children.find(c => c.id === 'f-str')
    expect(folder.children[0].children).toEqual([])
  })
})

// ── pendingOpenId ─────────────────────────────────────────────────────────────

describe('pendingOpenId flow', () => {
  it('is null initially', () => {
    const store = useModelStore()
    expect(store.pendingOpenId).toBeNull()
  })

  it('is null after addElement completes', async () => {
    const store = useModelStore()
    store.model = makeModelWithFolders()
    mockFetch()
    await store.addElement('f-bus', 'BusinessActor')
    expect(store.pendingOpenId).toBeNull()
  })
})
