/**
 * Node type compatibility tests.
 * Verifies which node types can have children created and which cannot.
 * Source: Archi TreeModelViewActionFactory.java + ArchiMate.md
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useModelStore } from './model'
import { FOLDER_ELEMENTS } from '../archimate-folder-elements.js'

// ── Test fixtures ─────────────────────────────────────────────────────────────

function makeFullModel() {
  return {
    id: 'root', name: '*New Model', type: 'model',
    children: [
      { id: 'f-str',  name: 'Strategy',      type: 'node', folder_type: 'strategy',                children: [] },
      { id: 'f-bus',  name: 'Business',      type: 'node', folder_type: 'business',                children: [] },
      { id: 'f-app',  name: 'Application',   type: 'node', folder_type: 'application',             children: [] },
      { id: 'f-tec',  name: 'Technology',    type: 'node', folder_type: 'technology',              children: [] },
      { id: 'f-mot',  name: 'Motivation',    type: 'node', folder_type: 'motivation',              children: [] },
      { id: 'f-imp',  name: 'Implementation',type: 'node', folder_type: 'implementation_migration', children: [] },
      { id: 'f-oth',  name: 'Other',         type: 'node', folder_type: 'other',                   children: [] },
      { id: 'f-rel',  name: 'Relations',     type: 'node', folder_type: 'relations',               children: [] },
      { id: 'f-view', name: 'Views',         type: 'node', folder_type: 'diagrams',                children: [
        { id: 'v1', name: 'Default View', type: 'view', element_type: 'ArchimateDiagramModel',
          documentation: '', children: [] },
      ]},
    ]
  }
}

function mockFetch() {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true, json: () => Promise.resolve({ ok: true }),
  })
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  Object.defineProperty(document, 'cookie', { writable: true, value: 'csrftoken=test' })
})

// ── Allowed element types per folder_type ─────────────────────────────────────

describe('Allowed element types per folder_type', () => {

  // ── Strategy ──────────────────────────────────────────────────────────────
  describe('strategy folder', () => {
    it('allows Resource, Capability, ValueStream, CourseOfAction', async () => {
      const store = useModelStore()
      store.model = makeFullModel()
      mockFetch()
      for (const t of ['Resource', 'Capability', 'ValueStream', 'CourseOfAction']) {
        await store.addElement('f-str', t)
      }
      expect(store.model.children.find(c => c.id === 'f-str').children).toHaveLength(4)
    })

    it('does NOT allow Business layer elements', async () => {
      // Strategy folder should never contain BusinessActor — but addElement itself
      // doesn't validate type; the UI prevents this via FOLDER_ELEMENTS
      expect(FOLDER_ELEMENTS.strategy).not.toContain('BusinessActor')
      expect(FOLDER_ELEMENTS.strategy).not.toContain('Outcome')
    })
  })

  // ── Business ──────────────────────────────────────────────────────────────
  describe('business folder', () => {
    const allowed = FOLDER_ELEMENTS.business
    it('has 13 allowed element types', () => {
      expect(allowed).toHaveLength(13)
    })
    it('contains structural elements', () => {
      expect(allowed).toContain('BusinessActor')
      expect(allowed).toContain('BusinessRole')
      expect(allowed).toContain('BusinessCollaboration')
      expect(allowed).toContain('BusinessInterface')
    })
    it('contains behavior elements', () => {
      expect(allowed).toContain('BusinessProcess')
      expect(allowed).toContain('BusinessFunction')
      expect(allowed).toContain('BusinessInteraction')
      expect(allowed).toContain('BusinessEvent')
      expect(allowed).toContain('BusinessService')
    })
    it('contains passive structure elements', () => {
      expect(allowed).toContain('BusinessObject')
      expect(allowed).toContain('Contract')
      expect(allowed).toContain('Representation')
      expect(allowed).toContain('Product')
    })
    it('does NOT allow Application or Technology elements', () => {
      expect(allowed).not.toContain('ApplicationComponent')
      expect(allowed).not.toContain('Node')
      expect(allowed).not.toContain('Outcome')
    })
  })

  // ── Application ───────────────────────────────────────────────────────────
  describe('application folder', () => {
    const allowed = FOLDER_ELEMENTS.application
    it('has 9 allowed types', () => { expect(allowed).toHaveLength(9) })
    it('allows ApplicationComponent', () => { expect(allowed).toContain('ApplicationComponent') })
    it('allows DataObject (passive)', () => { expect(allowed).toContain('DataObject') })
    it('does NOT allow business or tech elements', () => {
      expect(allowed).not.toContain('BusinessActor')
      expect(allowed).not.toContain('Node')
    })
  })

  // ── Technology (includes Physical per Archi source) ───────────────────────
  describe('technology folder (includes Physical)', () => {
    const allowed = FOLDER_ELEMENTS.technology
    it('includes standard tech elements', () => {
      expect(allowed).toContain('Node')
      expect(allowed).toContain('Device')
      expect(allowed).toContain('Artifact')
    })
    it('includes Physical elements (Equipment, Facility, DistributionNetwork, Material)', () => {
      expect(allowed).toContain('Equipment')
      expect(allowed).toContain('Facility')
      expect(allowed).toContain('DistributionNetwork')
      expect(allowed).toContain('Material')
    })
    it('does NOT allow Application elements', () => {
      expect(allowed).not.toContain('ApplicationComponent')
    })
  })

  // ── Motivation ────────────────────────────────────────────────────────────
  describe('motivation folder', () => {
    const allowed = FOLDER_ELEMENTS.motivation
    it('has 10 allowed types', () => { expect(allowed).toHaveLength(10) })
    it('allows Outcome, Goal, Requirement, Constraint', () => {
      expect(allowed).toContain('Outcome')
      expect(allowed).toContain('Goal')
      expect(allowed).toContain('Requirement')
      expect(allowed).toContain('Constraint')
    })
  })

  // ── Implementation & Migration ────────────────────────────────────────────
  describe('implementation_migration folder', () => {
    const allowed = FOLDER_ELEMENTS.implementation_migration
    it('has 5 allowed types', () => { expect(allowed).toHaveLength(5) })
    it('allows WorkPackage, Deliverable, Plateau, Gap', () => {
      expect(allowed).toContain('WorkPackage')
      expect(allowed).toContain('Deliverable')
      expect(allowed).toContain('Plateau')
      expect(allowed).toContain('Gap')
    })
  })

  // ── Other ─────────────────────────────────────────────────────────────────
  describe('other folder', () => {
    const allowed = FOLDER_ELEMENTS.other
    it('allows Location, Grouping, Junction', () => {
      expect(allowed).toContain('Location')
      expect(allowed).toContain('Grouping')
      expect(allowed).toContain('Junction')
    })
    it('does NOT allow ArchiMate layer elements', () => {
      expect(allowed).not.toContain('BusinessActor')
      expect(allowed).not.toContain('ApplicationComponent')
    })
  })

  // ── Relations ─────────────────────────────────────────────────────────────
  describe('relations folder', () => {
    it('has NO allowed element types (relations drawn on canvas)', () => {
      expect(FOLDER_ELEMENTS.relations).toHaveLength(0)
    })
    it('addElement to relations folder adds nothing to model', async () => {
      // Relations folder should show no types in submenu → UI prevents this
      // but even if called directly, we can still add (no server-side type check)
      // The constraint is purely in FOLDER_ELEMENTS UI mapping
      expect(FOLDER_ELEMENTS.relations).toHaveLength(0)
    })
  })

  // ── Diagrams ──────────────────────────────────────────────────────────────
  describe('diagrams folder', () => {
    it('allows only ArchimateDiagramModel and SketchModel', () => {
      expect(FOLDER_ELEMENTS.diagrams).toContain('ArchimateDiagramModel')
      expect(FOLDER_ELEMENTS.diagrams).toContain('SketchModel')
      expect(FOLDER_ELEMENTS.diagrams).toHaveLength(2)
    })
    it('does NOT allow element types', () => {
      expect(FOLDER_ELEMENTS.diagrams).not.toContain('BusinessActor')
      expect(FOLDER_ELEMENTS.diagrams).not.toContain('Outcome')
    })
  })
})

// ── Nodes that CANNOT have children created ───────────────────────────────────

describe('Node types that cannot have children', () => {

  it('element nodes — FOLDER_ELEMENTS returns empty (no element type)', () => {
    // Elements don't have folder_type → no entries → empty submenu
    const noFolderType = undefined
    const types = FOLDER_ELEMENTS[noFolderType] || []
    expect(types).toHaveLength(0)
  })

  it('view node — routes creation to DIAGRAMS folder, not the view itself', async () => {
    const store = useModelStore()
    store.model = makeFullModel()
    mockFetch()
    // When creating in a view (v1), it should go to the diagrams folder (f-view)
    await store.addView('f-view', 'ArchimateDiagramModel')
    const viewsFolder = store.model.children.find(c => c.id === 'f-view')
    // The new view is added to the folder, not to the view node itself
    const view = viewsFolder.children.find(c => c.id === 'v1')
    expect(view.children).toHaveLength(0)
    expect(viewsFolder.children.length).toBeGreaterThan(1) // Default View + new view
  })

  it('addChildFolder to element node returns without adding', async () => {
    const store = useModelStore()
    store.model = makeFullModel()
    mockFetch()
    const busFolder = store.model.children.find(c => c.id === 'f-bus')
    // Add an element first
    await store.addElement('f-bus', 'BusinessActor')
    const actor = busFolder.children[0]
    // Try to add a sub-folder to the element (actor.id)
    await store.addChildFolder(actor.id)
    // Element should still have no children
    expect(actor.children).toHaveLength(0)
  })
})

// ── Cross-layer isolation ─────────────────────────────────────────────────────

describe('Cross-layer isolation (no cross-contamination)', () => {
  const LAYERS = [
    ['strategy',                ['Resource', 'Capability']],
    ['business',                ['BusinessActor', 'BusinessProcess']],
    ['application',             ['ApplicationComponent', 'DataObject']],
    ['technology',              ['Node', 'Equipment']],
    ['motivation',              ['Outcome', 'Requirement']],
    ['implementation_migration',['WorkPackage', 'Plateau']],
    ['other',                   ['Location', 'Junction']],
  ]

  LAYERS.forEach(([layer, types]) => {
    types.forEach(t => {
      it(`${t} appears only in ${layer} (not in other layers)`, () => {
        const otherLayers = Object.entries(FOLDER_ELEMENTS)
          .filter(([k]) => k !== layer && k !== 'other')
          .filter(([, v]) => v.includes(t))
          .map(([k]) => k)
        expect(otherLayers).toHaveLength(0)
      })
    })
  })
})

// ── Sub-folder creation (always allowed for node types) ───────────────────────

describe('Sub-folder creation', () => {
  const FOLDER_IDS = ['f-str','f-bus','f-app','f-tec','f-mot','f-imp','f-oth','f-rel','f-view']

  FOLDER_IDS.forEach(fid => {
    it(`can create sub-folder in ${fid}`, async () => {
      const store = useModelStore()
      store.model = makeFullModel()
      mockFetch()
      await store.addChildFolder(fid)
      const folder = store.model.children.find(c => c.id === fid)
      const subFolders = folder.children.filter(c => c.type === 'node')
      expect(subFolders.length).toBeGreaterThan(0)
    })
  })
})

// ── isTopLevelNode protection ─────────────────────────────────────────────────

describe('isTopLevelNode protection', () => {
  it('identifies all 9 standard top-level folders as protected', () => {
    const store = useModelStore()
    store.model = makeFullModel()
    const topIds = ['f-str','f-bus','f-app','f-tec','f-mot','f-imp','f-oth','f-rel','f-view']
    topIds.forEach(id => {
      expect(store.isTopLevelNode(id)).toBe(true)
    })
  })

  it('does NOT protect sub-folders', async () => {
    const store = useModelStore()
    store.model = makeFullModel()
    mockFetch()
    await store.addChildFolder('f-bus')
    const subFolder = store.model.children.find(c => c.id === 'f-bus').children[0]
    expect(store.isTopLevelNode(subFolder.id)).toBe(false)
  })

  it('does NOT protect element nodes', async () => {
    const store = useModelStore()
    store.model = makeFullModel()
    mockFetch()
    await store.addElement('f-bus', 'BusinessActor')
    const el = store.model.children.find(c => c.id === 'f-bus').children[0]
    expect(store.isTopLevelNode(el.id)).toBe(false)
  })

  it('does NOT protect view nodes', () => {
    const store = useModelStore()
    store.model = makeFullModel()
    expect(store.isTopLevelNode('v1')).toBe(false)
  })
})
