import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useModelStore = defineStore('model', () => {
  const model = ref(null)
  const selected = ref(null)
  const loading = ref(false)
  const error = ref(null)

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

  function selectNode(node) {
    selected.value = node
  }

  return { model, selected, loading, error, fetchModel, selectNode }
})
