<template>
  <div class="panel root-panel h-100 d-flex flex-column">
    <div class="panel-heading d-flex align-items-center gap-2">
      <b>{{ title }}</b>
      <span v-if="currentView" class="badge text-bg-light border ms-auto" style="font-size: 0.7rem;">
        {{ currentView.element_type || 'View' }}
      </span>
    </div>
    <div class="panel-body root-panel-body flex-grow-1 position-relative p-0" style="overflow: hidden;">
      <div ref="containerRef" class="w-100 h-100"></div>
      <div
        v-if="!currentView"
        class="position-absolute top-50 start-50 translate-middle text-center text-muted"
        style="pointer-events: none;"
      >
        <i class="bi bi-diagram-3" style="font-size: 2.5rem; opacity: 0.2;"></i>
        <p class="mt-2 mb-0" style="font-size: 0.875rem;">Select a view from the model tree</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Graph } from '@antv/x6'
import { useModelStore } from '../stores/model'

const store = useModelStore()
const containerRef = ref(null)
let graph = null

const currentView = computed(() =>
  store.selected?.type === 'view' ? store.selected : null
)
const title = computed(() => currentView.value?.name || store.model?.name || 'Canvas')

function initGraph() {
  if (!containerRef.value) return
  graph = new Graph({
    container: containerRef.value,
    autoResize: true,
    background: { color: '#fafafa' },
    grid: { visible: true, size: 10, type: 'dot', args: { color: '#d0d0d0' } },
    mousewheel: { enabled: true, zoomAtMousePosition: true, modifiers: 'ctrl' },
    panning: { enabled: true, modifiers: 'alt' },
    connecting: { snap: true },
  })
}

function renderView(view) {
  if (!graph || !view) return
  graph.clearCells()

  // Placeholder: draw a label node for the selected view
  graph.addNode({
    x: 60, y: 60,
    width: 320, height: 60,
    label: view.name,
    attrs: {
      body: {
        fill: '#e8f4fd',
        stroke: '#0d6efd',
        strokeWidth: 1.5,
        rx: 6, ry: 6,
      },
      label: {
        fontSize: 13,
        fill: '#0d6efd',
        fontWeight: 600,
      },
    },
  })

  if (view.documentation) {
    graph.addNode({
      x: 60, y: 150,
      width: 320, height: Math.min(200, 40 + view.documentation.length / 2),
      label: view.documentation,
      attrs: {
        body: { fill: '#fff', stroke: '#dee2e6', strokeWidth: 1, rx: 4, ry: 4 },
        label: { fontSize: 11, fill: '#495057', textWrap: { width: 300, ellipsis: true } },
      },
    })
  }

  graph.zoomToFit({ padding: 40 })
}

watch(currentView, (view) => {
  if (view) renderView(view)
  else graph?.clearCells()
})

onMounted(() => initGraph())
onUnmounted(() => graph?.dispose())
</script>
