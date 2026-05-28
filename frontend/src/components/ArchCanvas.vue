<template>
  <div class="panel root-panel h-100 d-flex flex-column">
    <div class="panel-heading d-flex align-items-center gap-2">
      <b>{{ title }}</b>
      <span v-if="loading" class="text-muted ms-1" style="font-size:0.75rem;">Loading…</span>
      <div class="ms-auto d-flex gap-1" v-if="diagramData">
        <button class="btn btn-sm btn-light border py-0 px-1" title="Fit" @click="fitView">
          <i class="bi bi-fullscreen" style="font-size:0.75rem;"></i>
        </button>
        <button class="btn btn-sm btn-light border py-0 px-1" title="Reset zoom" @click="resetZoom">
          <i class="bi bi-zoom-out" style="font-size:0.75rem;"></i>
        </button>
      </div>
    </div>

    <div class="flex-grow-1 position-relative" style="overflow:hidden;">
      <div ref="containerRef" class="w-100 h-100"></div>
      <div
        v-if="!diagramData && !loading"
        class="position-absolute top-50 start-50 translate-middle text-center text-muted"
        style="pointer-events:none;"
      >
        <i class="bi bi-diagram-3" style="font-size:2.5rem;opacity:0.2;"></i>
        <p class="mt-2 mb-0" style="font-size:0.875rem;">Select a view from the model tree</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Graph } from '@antv/x6'
import { useModelStore } from '../stores/model'
import { ELEMENT_ICON } from '../archimate-icons.js'

const store   = useModelStore()
const containerRef = ref(null)
const diagramData  = ref(null)
const loading      = ref(false)
let graph = null
let resizeObserver = null

const title = computed(() =>
  diagramData.value?.name || store.model?.name || 'Canvas'
)

// ── ArchiMate relationship → line style ──────────────────────────────────────
const REL_STYLE = {
  // Structural
  CompositionRelationship:    { stroke: '#444', strokeWidth: 1.5, dash: '' },
  AggregationRelationship:    { stroke: '#444', strokeWidth: 1.5, dash: '' },
  AssignmentRelationship:     { stroke: '#444', strokeWidth: 2,   dash: '' },
  RealizationRelationship:    { stroke: '#444', strokeWidth: 1,   dash: '8 4' },
  // Dependency
  AssociationRelationship:    { stroke: '#666', strokeWidth: 1,   dash: '' },
  AccessRelationship:         { stroke: '#666', strokeWidth: 1,   dash: '4 3' },
  InfluenceRelationship:      { stroke: '#666', strokeWidth: 1,   dash: '8 4' },
  // Dynamic
  TriggeringRelationship:     { stroke: '#444', strokeWidth: 1.5, dash: '' },
  FlowRelationship:           { stroke: '#444', strokeWidth: 1,   dash: '8 4' },
  // Other
  ServingRelationship:        { stroke: '#666', strokeWidth: 1,   dash: '' },
  SpecializationRelationship: { stroke: '#444', strokeWidth: 1,   dash: '' },
}

function edgeStyle(relType) {
  return REL_STYLE[relType] || { stroke: '#777', strokeWidth: 1, dash: '' }
}

// ── ArchiMate layer colours (Archi defaults) ─────────────────────────────────
const LAYER_COLOR = {
  // Business
  BusinessActor:'#ffffb5', BusinessRole:'#ffffb5', BusinessCollaboration:'#ffffb5',
  BusinessInterface:'#ffffb5', BusinessFunction:'#ffffb5', BusinessProcess:'#ffffb5',
  BusinessInteraction:'#ffffb5', BusinessEvent:'#ffffb5', BusinessService:'#ffffb5',
  BusinessObject:'#ffffb5', Contract:'#ffffb5', Representation:'#ffffb5',
  Product:'#ffffb5',
  // Application
  ApplicationComponent:'#b5ffff', ApplicationCollaboration:'#b5ffff',
  ApplicationInterface:'#b5ffff', ApplicationFunction:'#b5ffff',
  ApplicationInteraction:'#b5ffff', ApplicationProcess:'#b5ffff',
  ApplicationEvent:'#b5ffff', ApplicationService:'#b5ffff', DataObject:'#b5ffff',
  // Technology
  Node:'#b5ffb5', Device:'#b5ffb5', SystemSoftware:'#b5ffb5',
  TechnologyCollaboration:'#b5ffb5', TechnologyInterface:'#b5ffb5',
  TechnologyFunction:'#b5ffb5', TechnologyInteraction:'#b5ffb5',
  TechnologyProcess:'#b5ffb5', TechnologyEvent:'#b5ffb5',
  TechnologyService:'#b5ffb5', Artifact:'#b5ffb5',
  CommunicationNetwork:'#b5ffb5', Path:'#b5ffb5',
  Equipment:'#b5ffb5', Facility:'#b5ffb5', Material:'#b5ffb5',
  // Motivation
  Stakeholder:'#ccccff', Driver:'#ccccff', Assessment:'#ccccff',
  Goal:'#ccccff', Outcome:'#ccccff', Principle:'#ccccff',
  Requirement:'#ccccff', Constraint:'#ccccff', Meaning:'#ccccff', Value:'#ccccff',
  // Implementation & Migration
  WorkPackage:'#ffe0e0', Deliverable:'#ffe0e0', ImplementationEvent:'#ffe0e0',
  Plateau:'#ffe0e0', Gap:'#ffe0e0',
  // Strategy
  Resource:'#f5deaa', Capability:'#f5deaa',
  CourseOfAction:'#f5deaa', ValueStream:'#f5deaa',
}

function nodeColor(elementType) {
  return LAYER_COLOR[elementType] || '#ffffff'
}

// Passive structure elements — dashed border in ArchiMate notation
const PASSIVE_TYPES = new Set([
  'BusinessObject','Contract','Representation','Product',
  'DataObject','Artifact','Material','Equipment','Facility',
])

const ELEMENT_MARKUP = [
  { tagName: 'rect', selector: 'body' },
  { tagName: 'text', selector: 'label' },
  { tagName: 'use',  selector: 'icon' },
]

// ── Graph init ────────────────────────────────────────────────────────────────
function initGraph() {
  if (!containerRef.value) return
  graph = new Graph({
    container: containerRef.value,
    background: { color: '#fafafa' },
    grid: { visible: true, size: 10, type: 'dot',
            args: [{ color: '#d0d0d0', thickness: 1 }] },
    mousewheel: { enabled: true, modifiers: 'ctrl', zoomAtMousePosition: true },
    panning:    { enabled: true, modifiers: 'alt' },
    interacting: false,
  })

  graph.on('node:click', ({ node }) => {
    const d = node.getData()
    if (!d) return
    if (d.element_id) {
      const full = store.findById(d.element_id)
      store.selectNode(full || d)
    } else if (d.type === 'view' && d.id) {
      // view_ref: resolve full view node so watch triggers loadDiagram
      const full = store.findById(d.id)
      store.selectNode(full || d)
    } else {
      store.selectNode(d)
    }
  })

  resizeObserver = new ResizeObserver(() => {
    if (containerRef.value) {
      graph.resize(containerRef.value.clientWidth, containerRef.value.clientHeight)
    }
  })
  resizeObserver.observe(containerRef.value)
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderDiagram() {
  if (!graph || !diagramData.value) return
  graph.clearCells()

  const { nodes, edges } = diagramData.value
  const nodeIds = new Set(nodes.map(n => n.id))
  // Index for looking up parent absolute positions (for relative coord calc)
  const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]))
  // Index: child_id → parent_id  (for hiding containment connections)
  const parentOf = Object.fromEntries(
    nodes.filter(n => n.parent_id).map(n => [n.id, n.parent_id])
  )

  for (const n of nodes) {
    const wrap = { width: n.width - 8, height: n.height - 6, ellipsis: true }

    if (n.type === 'group') {
      graph.addNode({
        id: n.id, x: n.x, y: n.y, width: n.width, height: n.height,
        zIndex: 0,
        label: n.name,
        data: { type: 'group', name: n.name, id: n.id },
        attrs: {
          body:  { fill: n.fill_color || '#f0f0f0', stroke:'#aaa',
                   strokeWidth:1, rx:4, ry:4 },
          label: { fontSize:11, fontWeight:600, fill:'#333',
                   textAnchor:'middle', textVerticalAnchor:'top',
                   refX:'50%', refY:6 },
        },
      })
    } else if (n.type === 'element') {
      const iconId = ELEMENT_ICON[n.element_type]
      const dashed = PASSIVE_TYPES.has(n.element_type)
      const iconSize = 13
      // Embedded elements drawn ON TOP of parent (zIndex: 2), like Archi's Draw2D layer order
      const zIdx = n.parent_id ? 2 : 1
      graph.addNode({
        id: n.id,
        x: n.x, y: n.y,           // always absolute coordinates
        width: n.width, height: n.height,
        zIndex: zIdx,
        markup: ELEMENT_MARKUP,
        data: { type: 'element', element_id: n.element_id,
                element_type: n.element_type, name: n.name, id: n.element_id },
        attrs: {
          body: {
            fill: nodeColor(n.element_type),
            stroke: '#888', strokeWidth: 1, rx: 2, ry: 2,
            ...(dashed ? { strokeDasharray: '5 3' } : {}),
          },
          label: {
            text: n.name,
            fontSize: 10, fill: '#222',
            refX: '50%', refY: '50%',
            textAnchor: 'middle', textVerticalAnchor: 'middle',
            textWrap: {
              text: n.name,
              width: n.width - (iconId ? iconSize + 6 : 8),
              height: n.height - 8,
              ellipsis: true,
            },
          },
          icon: iconId ? {
            href: `#${iconId}`,
            x: n.width - iconSize - 2,
            y: 2,
            width: iconSize,
            height: iconSize,
          } : { width: 0, height: 0 },
        },
      })
    } else if (n.type === 'note') {
      graph.addNode({
        id: n.id, x: n.x, y: n.y, width: n.width, height: n.height,
        zIndex: 1,
        label: n.name,
        data: { type: 'note', name: n.name, id: n.id },
        attrs: {
          body:  { fill:'#fffde7', stroke:'#ccc', strokeWidth:1 },
          label: { fontSize:10, fill:'#555', textWrap: wrap,
                   textVerticalAnchor:'top', refY:4 },
        },
      })
    } else if (n.type === 'view_ref') {
      const refView = n.ref_id ? store.findById(n.ref_id) : null
      const refLabel = refView ? `→ ${refView.name}` : '→ View'
      graph.addNode({
        id: n.id, x: n.x, y: n.y, width: n.width, height: n.height,
        zIndex: 1,
        label: refLabel,
        data: { type: 'view', id: n.ref_id, name: refView?.name || refLabel },
        attrs: {
          body:  { fill:'#e3f2fd', stroke:'#1565c0', strokeWidth:1, rx:4 },
          label: { fontSize:10, fill:'#1565c0',
                   textWrap: { width: n.width - 8, ellipsis: true } },
        },
      })
    }
  }

  for (const e of edges) {
    if (!e.source || !e.target) continue
    if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) continue
    // Hide connections where containment is already shown visually (Archi behavior)
    if (parentOf[e.target] === e.source || parentOf[e.source] === e.target) continue
    const s = edgeStyle(e.type)
    try {
      graph.addEdge({
        id: e.id || undefined,
        source: e.source,
        target: e.target,
        ...(e.vertices?.length ? { vertices: e.vertices } : {}),
        connector: { name: 'normal' },
        attrs: {
          line: {
            stroke: s.stroke,
            strokeWidth: s.strokeWidth,
            ...(s.dash ? { strokeDasharray: s.dash } : {}),
            targetMarker: { name: 'block', width: 8, height: 5 },
          },
        },
      })
    } catch (_) { /* skip invalid */ }
  }

  graph.zoomToFit({ padding: 24 })
}

// ── Load ──────────────────────────────────────────────────────────────────────
async function loadDiagram(viewId) {
  loading.value = true
  diagramData.value = null
  try {
    const r = await fetch(`/api/diagram/${viewId}/`)
    if (r.ok) {
      diagramData.value = await r.json()
      renderDiagram()
    }
  } finally {
    loading.value = false
  }
}

function fitView()   { graph?.zoomToFit({ padding: 24 }) }
function resetZoom() { graph?.zoomTo(1); graph?.centerContent() }

// ── Watchers ──────────────────────────────────────────────────────────────────
watch(() => store.selected, node => {
  if (node?.type === 'view') loadDiagram(node.id)
  else { diagramData.value = null; graph?.clearCells() }
})

onMounted(initGraph)
onUnmounted(() => {
  resizeObserver?.disconnect()
  graph?.dispose()
})
</script>
