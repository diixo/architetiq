<template>
  <div class="app-shell">
    <ArchimateDefs />

    <!-- Header -->
    <header class="app-header">
      <div class="px-header py-header d-flex align-items-center gap-3">
        <div class="fw-bold my-0" style="font-size: 1.25rem;">
          <span style="color: #343a40;">architet</span><span style="color: #712cf9;">IQ</span>
        </div>
        <span class="badge text-bg-light border">v0.1</span>
        <div class="flex-grow-1"></div>
      </div>
    </header>

    <!-- Horizontal menu -->
    <nav class="horizontal-menu-wrapper">
      <ul class="nav horizontal-menu flex-nowrap px-3">
        <li class="nav-item">
          <a class="nav-link active" href="#"><i class="bi bi-house-door"></i> Overview</a>
        </li>
        <li class="nav-item dropdown">
          <button class="nav-link dropdown-toggle" type="button" data-bs-toggle="dropdown">
            <i class="bi bi-three-dots"></i>
          </button>
          <ul class="dropdown-menu shadow-sm" style="font-size: 0.875rem;">
            <li><a class="dropdown-item" href="#" @click.prevent="onNew">New</a></li>
            <li><a class="dropdown-item" href="#" @click.prevent="triggerOpen">Open</a></li>
            <li><a class="dropdown-item" href="#" @click.prevent="onSave">Save</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="/api/model/export/" target="_blank">Export .archimate</a></li>
          </ul>
        </li>
        <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-list-check"></i> Requirements</a></li>
        <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-diagram-3"></i> Architecture</a></li>
        <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-kanban"></i> Scenarios</a></li>
        <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-bug"></i> Issues</a></li>
        <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-shield-check"></i> Compliance</a></li>
        <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-bar-chart"></i> Reports</a></li>
        <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-gear"></i> Settings</a></li>
      </ul>
    </nav>

    <!-- Main layout -->
    <main class="app-layout d-flex bg-dark-subtle">

      <!-- Sidebar -->
      <div class="sidebar d-flex flex-column">
        <div class="panel root-panel flex-grow-1 overflow-hidden d-flex flex-column">
          <ModelTree />
        </div>
        <PropertiesPanel />
      </div>

      <!-- Canvas area -->
      <div class="flex-grow-1 overflow-auto">
        <ArchCanvas />
      </div>

    </main>

    <!-- Toast notification -->
    <div
      v-if="toast"
      class="position-fixed bottom-0 end-0 m-3 px-3 py-2 rounded shadow-sm text-white"
      style="background:#343a40; font-size:0.875rem; z-index:9999;"
    >{{ toast }}</div>

    <!-- Hidden file input for Open -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".archimate,.xml"
      style="display: none"
      @change="onFileSelected"
    />

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useModelStore } from './stores/model'
import ModelTree from './components/ModelTree.vue'
import PropertiesPanel from './components/PropertiesPanel.vue'
import ArchCanvas from './components/ArchCanvas.vue'
import ArchimateDefs from './components/ArchimateDefs.vue'

const store = useModelStore()
const fileInputRef = ref(null)
const toast = ref('')
let toastTimer = null

function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2500)
}

function triggerOpen() {
  fileInputRef.value?.click()
}

function onNew() {
  if (!confirm('Reset to a new empty model? Unsaved changes will be lost.')) return
  store.resetModel()
  showToast('New model created — not saved yet')
}

async function onSave() {
  const result = await store.saveModel()
  if (result?.ok) showToast(`Saved: ${result.name}`)
}

async function onFileSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  const csrfMatch = document.cookie.match(/csrftoken=([^;]+)/)
  const csrfToken = csrfMatch ? csrfMatch[1] : ''
  const r = await fetch('/upload/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
    body: formData,
  })
  const data = await r.json()
  if (data.ok) await store.fetchModel()
  else alert('Error: ' + data.error)
  e.target.value = ''
}
</script>
