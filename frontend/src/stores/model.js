import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useModelStore = defineStore('model', () => {
  const model = ref(null)
  const selected = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const filterQuery = ref('')
  const editingNodeId = ref(null)

  function genId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
    })
  }

  function renameNode(id, newName) {
    const node = findById(id)
    if (node && newName.trim()) node.name = newName.trim()
    saveModel()
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
    saveModel()
  }

  function addChildFolder(parentId) {
    const parent = findById(parentId)
    if (!parent) return
    const id = genId()
    parent.children = parent.children || []
    parent.children.push({ id, name: 'New Folder', type: 'node', children: [] })
    editingNodeId.value = id
  }

  function csrfToken() {
    const m = document.cookie.match(/csrftoken=([^;]+)/)
    return m ? m[1] : ''
  }

  async function fetchModel() {
    loading.value = true
    try {
      const r = await fetch('/api/model/')
      model.value = await r.json()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  const DEFAULT_MODEL = {
    name: '*New Model',
    type: 'model',
    children: [
      { name: 'Strategy',                     type: 'node', children: [] },
      { name: 'Business',                     type: 'node', children: [] },
      { name: 'Application',                  type: 'node', children: [] },
      { name: 'Technology And Physical',      type: 'node', children: [] },
      { name: 'Motivation',                   type: 'node', children: [] },
      { name: 'Implementation and Migration', type: 'node', children: [] },
      { name: 'Other',                        type: 'node', children: [] },
      { name: 'Relations',                    type: 'node', children: [] },
      { name: 'Views',                        type: 'node', children: [] },
    ],
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

  return {
    model, selected, loading, error, filterQuery, editingNodeId,
    fetchModel, selectNode, findById, resetModel, saveModel,
    renameNode, deleteNode, addChildFolder,
  }
})
