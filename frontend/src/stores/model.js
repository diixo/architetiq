import { defineStore } from 'pinia'
import { ref, nextTick } from 'vue'

export const useModelStore = defineStore('model', () => {
  const model = ref(null)
  const selected = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const filterQuery = ref('')
  const editingNodeId = ref(null)
  const activeConnType  = ref('AssociationRelationship')
  const propertiesPanelVisible = ref(false)
  const pendingOpenId   = ref(null)  // folder to expand before editing new child
  const isDirty = ref(false)
  const diagramRenameSignal = ref(null)  // { id, name } — replaced on each canvas-node rename
  const diagramDeleteSignal = ref(null)  // { id } — canvas node to remove when tree node is deleted
  // Currently selected palette icon (type + value), null = normal pointer mode
  const activePaletteItem = ref(null)  // { kind: 'conn'|'elem', value: 'TypeName' }

  function markDirty() { isDirty.value = true }

  function selectPaletteItem(kind, value) {
    activePaletteItem.value = { kind, value }
    if (kind === 'conn') activeConnType.value = value
  }

  function resetPaletteSelection() {
    activePaletteItem.value = null
    activeConnType.value = 'AssociationRelationship'
  }

  function genId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
    })
  }

  function renameNode(id, newName) {
    const node = findById(id)
    if (node && newName.trim()) {
      node.name = newName.trim()
      if (node.element_type === 'DiagramGroup') {
        diagramRenameSignal.value = { id, name: newName.trim() }
      }
      markDirty()
    } else if (newName.trim()) {
      // Canvas-level node not in model tree — signal watcher in ArchCanvas
      diagramRenameSignal.value = { id, name: newName.trim() }
      markDirty()
    }
  }

  function updateDocumentation(id, doc) {
    const node = findById(id)
    if (node) { node.documentation = doc; markDirty() }
  }

  function updateProperties(id, props) {
    const node = findById(id)
    if (node) { node.properties = props; markDirty() }
  }

  function deleteNode(id) {
    function removeFrom(parent) {
      if (!parent.children) return false
      const idx = parent.children.findIndex(c => c.id === id)
      if (idx !== -1) { parent.children.splice(idx, 1); return true }
      return parent.children.some(c => removeFrom(c))
    }
    if (model.value) removeFrom(model.value)
    if (selected.value?.id === id) selected.value = null
    markDirty()
    diagramDeleteSignal.value = { id }
  }

  async function _addChild(parentId, newNode) {
    const parent = findById(parentId)
    // Only folder nodes (type: 'node') can have children
    if (!parent || parent.type !== 'node') return
    parent.children = parent.children || []
    parent.children.push(newNode)
    // Step 1: expand parent so children render
    pendingOpenId.value = parentId
    await nextTick()
    pendingOpenId.value = null
    // Step 2: now the new child's TreeNode is mounted → trigger edit
    await nextTick()
    editingNodeId.value = newNode.id
  }

  async function addChildFolder(parentId) {
    await _addChild(parentId, { id: genId(), name: 'New Folder', type: 'node', children: [] })
    markDirty()
  }

  async function addView(parentId, viewType = 'ArchimateDiagramModel') {
    const id = genId()
    const label = viewType === 'SketchModel' ? 'New Sketch' : 'New View'
    await _addChild(parentId, { id, name: label, type: 'view',
      element_type: viewType, documentation: '', children: [] })
    markDirty()
  }

  async function addElement(parentId, elementType, opts = {}) {
    const id   = opts.id   ?? genId()
    const name = opts.name ?? elementType.replace(/([A-Z])/g, ' $1').trim()
    await _addChild(parentId, {
      id, name, type: 'element', element_type: elementType,
      documentation: '', children: [],
    })
    markDirty()
  }

  function csrfToken() {
    const m = document.cookie.match(/csrftoken=([^;]+)/)
    return m ? m[1] : ''
  }

  const TOP_FOLDER_TYPES = {
    'Strategy': 'strategy', 'Business': 'business', 'Application': 'application',
    'Technology & Physical': 'technology', 'Technology And Physical': 'technology',
    'Motivation': 'motivation',
    'Implementation & Migration': 'implementation_migration',
    'Implementation and Migration': 'implementation_migration',
    'Other': 'other', 'Relations': 'relations', 'Views': 'diagrams',
  }

  function migrateFolderTypes(m) {
    ;(m.children || []).forEach((child, i) => {
      if (child.type !== 'node') return
      if (!child.folder_type && TOP_FOLDER_TYPES[child.name])
        child.folder_type = TOP_FOLDER_TYPES[child.name]
      if (!child.id)
        child.id = `00000000-0000-0000-0001-${String(i + 1).padStart(12, '0')}`
    })
    return m
  }

  async function fetchModel() {
    loading.value = true
    try {
      const r = await fetch('/api/model/')
      model.value = migrateFolderTypes(await r.json())
      isDirty.value = false
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  const DEFAULT_MODEL = {
    name: '*New Model', type: 'model', id: '00000000-0000-0000-0000-000000000000',
    children: [
      { id: '00000000-0000-0000-0001-000000000001', name: 'Strategy',                    type: 'node', folder_type: 'strategy',                children: [] },
      { id: '00000000-0000-0000-0001-000000000002', name: 'Business',                    type: 'node', folder_type: 'business',                children: [] },
      { id: '00000000-0000-0000-0001-000000000003', name: 'Application',                 type: 'node', folder_type: 'application',             children: [] },
      { id: '00000000-0000-0000-0001-000000000004', name: 'Technology & Physical',       type: 'node', folder_type: 'technology',              children: [] },
      { id: '00000000-0000-0000-0001-000000000005', name: 'Motivation',                  type: 'node', folder_type: 'motivation',              children: [] },
      { id: '00000000-0000-0000-0001-000000000006', name: 'Implementation & Migration',  type: 'node', folder_type: 'implementation_migration', children: [] },
      { id: '00000000-0000-0000-0001-000000000007', name: 'Other',                       type: 'node', folder_type: 'other',                   children: [] },
      { id: '00000000-0000-0000-0001-000000000008', name: 'Relations',                   type: 'node', folder_type: 'relations',               children: [] },
      { id: '00000000-0000-0000-0001-000000000009', name: 'Views',                       type: 'node', folder_type: 'diagrams',                children: [
        { id: '00000000-0000-0000-0000-000000000001', name: 'Default View',
          type: 'view', element_type: 'ArchimateDiagramModel',
          documentation: '', children: [] },
      ]},
    ],
  }

  async function loadAspice() {
    const r = await fetch('/api/model/load-aspice/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken() },
    })
    if (r.ok) {
      selected.value = null
      filterQuery.value = ''
      await fetchModel()
    }
    return r.ok
  }

  function resetModel() {
    model.value = JSON.parse(JSON.stringify(DEFAULT_MODEL))
    selected.value = null
  }

  async function saveModel() {
    const r = await fetch('/api/model/save/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(model.value),
    })
    if (r.ok) isDirty.value = false
    return r.ok ? (await r.json()) : null
  }

  function selectNode(node) {
    selected.value = node
  }

  function findById(id) {
    if (!model.value || !id) return null
    function walk(node) {
      if (node.id === id) return node
      for (const child of (node.children || [])) {
        const found = walk(child)
        if (found) return found
      }
      return null
    }
    return walk(model.value)
  }

  function isTopLevelNode(id) {
    return model.value?.children?.some(c => c.id === id) ?? false
  }

  // Walk up the tree to find the topmost folder_type ancestor
  // (matches Archi's topMostFolder.getType() logic)
  function getTopFolderType(nodeId) {
    if (!model.value) return null
    function findPath(node, target, path) {
      if (node.id === target) return path
      for (const c of (node.children || [])) {
        const r = findPath(c, target, [...path, node])
        if (r) return r
      }
      return null
    }
    const ancestors = findPath(model.value, nodeId, [])
    if (!ancestors) return null
    // Return folder_type of the first ancestor that has one (topmost = first in path after root)
    for (const anc of ancestors) {
      if (anc.folder_type && anc.type === 'node') return anc.folder_type
    }
    return null
  }

  function findFolderByType(folderType) {
    if (!model.value || !folderType) return null
    function walk(node) {
      if (node.folder_type === folderType) return node
      for (const c of (node.children || [])) {
        const r = walk(c)
        if (r) return r
      }
      return null
    }
    return walk(model.value)
  }

  function getNodePath(id) {
    if (!model.value || !id) return []
    function find(node, target, path) {
      const p = [...path, node.name]
      if (node.id === target) return p
      for (const c of (node.children || [])) {
        const r = find(c, target, p)
        if (r) return r
      }
      return null
    }
    const full = find(model.value, id, []) || []
    return full.slice(1) // skip root model name
  }

  return {
    model, selected, loading, error, filterQuery, editingNodeId, diagramRenameSignal, diagramDeleteSignal,
    fetchModel, selectNode, findById, getNodePath, findFolderByType, isTopLevelNode, getTopFolderType,
    activeConnType, activePaletteItem, selectPaletteItem, resetPaletteSelection,
    pendingOpenId,
    loadAspice, resetModel, saveModel, renameNode, deleteNode, addChildFolder, addElement, addView,
    updateDocumentation, updateProperties,
    propertiesPanelVisible,
    isDirty, markDirty,
  }
})
