import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useModelStore = defineStore('model', () => {
  const model = ref(null)
  const selected = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const filterQuery = ref('')

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

  return { model, selected, loading, error, filterQuery, fetchModel, selectNode, findById, resetModel, saveModel }
})
