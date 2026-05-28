import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useModelStore = defineStore('model', () => {
  const model = ref(null)
  const selected = ref(null)
  const loading = ref(false)
  const error = ref(null)

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

  async function resetModel() {
    const r = await fetch('/api/model/new/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken() },
    })
    if (r.ok) {
      selected.value = null
      await fetchModel()
    }
  }

  async function saveModel() {
    const r = await fetch('/api/model/save/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken() },
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

  return { model, selected, loading, error, fetchModel, selectNode, findById, resetModel, saveModel }
})
