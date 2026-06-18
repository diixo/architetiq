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
        <span v-if="store.isDirty" title="Unsaved changes" style="color:#e67700; font-size:1rem; line-height:1;">●</span>
        <div class="flex-grow-1"></div>
        <!-- Burger button — mobile only -->
        <button
          class="btn btn-light border d-md-none"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mobileMenu"
          aria-controls="mobileMenu"
          aria-expanded="false"
          aria-label="Toggle menu"
        >
          <i class="bi bi-list" style="font-size:1.25rem; -webkit-text-stroke:0.5px;"></i>
        </button>
      </div>
    </header>

    <!-- Mobile dropdown menu — visible only on small screens -->
    <div class="collapse d-md-none border-bottom" id="mobileMenu">
      <nav class="px-3 py-2 bg-white">
        <ul class="nav flex-column" style="font-size:0.875rem;">
          <li class="nav-item">
            <a class="nav-link active" href="#"><i class="bi bi-house-door me-2"></i>Overview</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/processes/"><i class="bi bi-diagram-3 me-2"></i>Processes</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#" @click.prevent="onNew"><i class="bi bi-file me-2"></i>New</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#" @click.prevent="triggerOpen"><i class="bi bi-folder2-open me-2"></i>Open</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#" @click.prevent="onSave"><i class="bi bi-save me-2"></i>Save</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/api/model/export/" target="_blank"><i class="bi bi-box-arrow-up me-2"></i>Export .archimate</a>
          </li>
          <li><hr class="my-1"></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-list-check me-2"></i>Requirements</a></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-diagram-3 me-2"></i>Architecture</a></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-kanban me-2"></i>Scenarios</a></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-bug me-2"></i>Issues</a></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-shield-check me-2"></i>Compliance</a></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-bar-chart me-2"></i>Reports</a></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-gear me-2"></i>Settings</a></li>
        </ul>
      </nav>
    </div>

    <!-- Horizontal menu — desktop only -->
    <nav class="horizontal-menu-wrapper d-none d-md-block">
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
            <li><a class="dropdown-item" href="#" @click.prevent="triggerOpen">Open…</a></li>
            <li><a class="dropdown-item" href="#" @click.prevent="onLoadAspice">
              <i class="bi bi-box-seam me-1"></i>Open ASPICE
            </a></li>
            <li><a class="dropdown-item" href="#" @click.prevent="onSave">Save</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="/api/model/export/" target="_blank">Export .archimate</a></li>
          </ul>
        </li>
        <li class="nav-item"><a class="nav-link" href="/processes/"><i class="bi bi-diagram-3"></i> Processes</a></li>
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
      </div>

      <!-- Canvas area + Palette + Properties -->
      <div class="flex-grow-1 overflow-hidden" style="display: grid; grid-template-rows: 1fr auto; min-height: 0;">
        <div class="d-flex overflow-hidden" style="min-height: 0;">
          <ArchCanvas ref="canvasRef" class="flex-grow-1" />
          <CanvasPalette />
        </div>
        <PropertiesPanel v-if="store.propertiesPanelVisible" @close="store.propertiesPanelVisible = false" />
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useModelStore } from './stores/model'
import ModelTree from './components/ModelTree.vue'
import PropertiesPanel from './components/PropertiesPanel.vue'
import ArchCanvas from './components/ArchCanvas.vue'
import ArchimateDefs from './components/ArchimateDefs.vue'
import CanvasPalette from './components/CanvasPalette.vue'

const store = useModelStore()
const fileInputRef = ref(null)
const canvasRef = ref(null)
const toast = ref('')
let toastTimer = null

function handleBeforeUnload(e) {
  if (store.isDirty) {
    e.preventDefault()
    e.returnValue = ''
  }
}
onMounted(() => window.addEventListener('beforeunload', handleBeforeUnload))
onUnmounted(() => window.removeEventListener('beforeunload', handleBeforeUnload))

function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2500)
}

function triggerOpen() {
  fileInputRef.value?.click()
}

async function onNew() {
  if (!confirm('Reset to a new empty model? Unsaved changes will be lost.')) return
  const csrfMatch = document.cookie.match(/csrftoken=([^;]+)/)
  const csrfToken = csrfMatch ? csrfMatch[1] : ''
  await fetch('/api/model/new/', { method: 'POST', headers: { 'X-CSRFToken': csrfToken } })
  store.selected = null
  store.filterQuery = ''
  canvasRef.value?.clearDiagram()
  await store.fetchModel()
  showToast('New model created')
}

async function onLoadAspice() {
  const ok = await store.loadAspice()
  if (ok) showToast('ASPICE project loaded')
  else showToast('ASPICE project not found')
}

async function onSave() {
  await canvasRef.value?.saveCurrentDiagram()
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
