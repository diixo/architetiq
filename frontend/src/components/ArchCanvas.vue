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

// ── ArchiMate marker definitions (from Archi Java source) ────────────────────
// tagName:'path' required in X6 v3 for custom SVG markers
// Tip at (0,0), body extends to positive x
const MK_FILL_TRI  = { name: 'block', width: 10, height: 8 }
const MK_OPEN_TRI  = { tagName: 'path', d: 'M 10 -5 L 0 0 L 10 5 Z',  fill: '#ffffff', stroke: '#444', strokeWidth: 1.5 }
const MK_OPEN_V    = { tagName: 'path', d: 'M 8 -5 L 0 0 L 8 5',       fill: 'none',    stroke: '#666', strokeWidth: 1.5 }
const MK_FILL_DIA  = { tagName: 'path', d: 'M 0 0 L 7 -4 L 14 0 L 7 4 Z', fill: '#444', stroke: '#444', strokeWidth: 1 }
const MK_OPEN_DIA  = { tagName: 'path', d: 'M 0 0 L 7 -4 L 14 0 L 7 4 Z', fill: '#fff', stroke: '#444', strokeWidth: 1.5 }
const MK_CIRCLE    = { name: 'circle', r: 4, fill: '#444' }
const MK_NONE      = null

// ── ArchiMate relationship → line style ──────────────────────────────────────
const REL_STYLE = {
  CompositionRelationship:    { stroke: '#444', strokeWidth: 1.5, dash: '',    src: MK_FILL_DIA, tgt: MK_NONE    },
  AggregationRelationship:    { stroke: '#444', strokeWidth: 1.5, dash: '',    src: MK_OPEN_DIA, tgt: MK_NONE    },
  AssignmentRelationship:     { stroke: '#444', strokeWidth: 1.5, dash: '',    src: MK_CIRCLE,   tgt: MK_FILL_TRI },
  RealizationRelationship:    { stroke: '#444', strokeWidth: 1,   dash: '8 4', src: MK_NONE,     tgt: MK_OPEN_TRI },
  SpecializationRelationship: { stroke: '#444', strokeWidth: 1,   dash: '',    src: MK_NONE,     tgt: MK_OPEN_TRI },
  AssociationRelationship:    { stroke: '#666', strokeWidth: 1,   dash: '',    src: MK_NONE,     tgt: MK_OPEN_V  },
  ServingRelationship:        { stroke: '#666', strokeWidth: 1,   dash: '',    src: MK_NONE,     tgt: MK_OPEN_V  },
  AccessRelationship:         { stroke: '#666', strokeWidth: 1,   dash: '4 3', src: MK_NONE,     tgt: MK_OPEN_V  },
  InfluenceRelationship:      { stroke: '#666', strokeWidth: 1,   dash: '8 4', src: MK_NONE,     tgt: MK_OPEN_V  },
  TriggeringRelationship:     { stroke: '#444', strokeWidth: 1.5, dash: '',    src: MK_NONE,     tgt: MK_FILL_TRI },
  FlowRelationship:           { stroke: '#444', strokeWidth: 1,   dash: '8 4', src: MK_NONE,     tgt: MK_FILL_TRI },
}

function edgeStyle(relType) {
  return REL_STYLE[relType] || { stroke: '#777', strokeWidth: 1, dash: '', src: MK_NONE, tgt: MK_FILL_TRI }
}

// ── OrthogonalAnchor — точки входу/виходу стрілок (як в Archi OrthogonalAnchor.java) ──
function clamp(v, min, max) { return Math.max(min, Math.min(max, v)) }

function orthogonalPoints(src, tgt) {
  const srcR = src.x + src.width
  const srcB = src.y + src.height
  const tgtR = tgt.x + tgt.width
  const tgtB = tgt.y + tgt.height
  const sCX  = src.x + src.width  / 2
  const sCY  = src.y + src.height / 2
  const tCX  = tgt.x + tgt.width  / 2
  const tCY  = tgt.y + tgt.height / 2

  // Gap between bounding boxes (0 if overlapping in that axis)
  // Correct approach: compare GAPS, not center distances
  // Wide/tall elements have far-offset centers which misleads center-based dx/dy
  const hGap = Math.max(0, tgt.x - srcR, src.x - tgtR)
  const vGap = Math.max(0, tgt.y - srcB, src.y - tgtB)

  if (vGap >= hGap) {
    // Vertical dominant: arrows exit/enter top or bottom
    // Both points share source-center X → parallel vertical arrows
    const sx = clamp(sCX, src.x, srcR)
    const tx = clamp(sCX, tgt.x, tgtR)
    return tgt.y >= src.y
      ? { srcPt: { x: sx, y: srcB  }, tgtPt: { x: tx, y: tgt.y } }  // tgt below
      : { srcPt: { x: sx, y: src.y }, tgtPt: { x: tx, y: tgtB  } }  // tgt above
  } else {
    // Horizontal dominant: arrows exit/enter left or right
    // Both points share target-center Y → parallel horizontal arrows
    const sy = clamp(tCY, src.y, srcB)
    const ty = clamp(tCY, tgt.y, tgtB)
    return tgt.x >= src.x
      ? { srcPt: { x: srcR,  y: sy }, tgtPt: { x: tgt.x, y: ty } }  // tgt right
      : { srcPt: { x: src.x, y: sy }, tgtPt: { x: tgtR,  y: ty } }  // tgt left
  }
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

// ── ArchiMate shape categories ────────────────────────────────────────────────
// Per Archi source: most figures use RoundedRectangleFigureDelegate for type=0 (default).
// Custom shapes (process arrow, function polygon, etc.) are user-selectable alternatives.
// Only truly standardized shape differences are kept here:
const SHAPE_TYPE = {
  // Passive structure: folded top-right corner (standard ArchiMate notation)
  BusinessObject:'passive', DataObject:'passive', Artifact:'passive',
  Contract:'passive', Representation:'passive', Material:'passive',
  // ApplicationComponent: rect with two nubs on left (standard IT notation)
  ApplicationComponent:'component',
}

function roundedRect(w, h, r = 3) {
  r = Math.min(r, w / 2, h / 2)
  return `M ${r},0 H ${w-r} Q ${w},0 ${w},${r} V ${h-r} Q ${w},${h} ${w-r},${h} H ${r} Q 0,${h} 0,${h-r} V ${r} Q 0,0 ${r},0 Z`
}

function getElementPath(et, w, h) {
  const s = SHAPE_TYPE[et] || 'rect'
  switch (s) {
    case 'passive': {
      // Folded top-right corner (ArchiMate passive structure notation)
      const f = Math.min(w * 0.18, h * 0.28, 12)
      return `M 0,0 H ${w-f} L ${w},${f} V ${h} H 0 Z`
    }
    case 'component': {
      // ApplicationComponent: rect with two nubs on left side
      const nb = Math.min(w * 0.12, 12), nh = Math.min(h * 0.22, 12)
      const g1 = h * 0.2, g2 = h * 0.52
      return `M ${nb},0 H ${w} V ${h} H ${nb} V ${g2+nh} H 0 V ${g2} H ${nb} V ${g1+nh} H 0 V ${g1} H ${nb} Z`
    }
    default:
      return roundedRect(w, h, 3)
  }
}

// Passive structure elements — dashed border in ArchiMate notation
const PASSIVE_TYPES = new Set([
  'BusinessObject','Contract','Representation','Product',
  'DataObject','Artifact','Material','Equipment','Facility',
])

const ELEMENT_MARKUP = [
  { tagName: 'path', selector: 'body' },   // path instead of rect for custom shapes
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
      const iconId  = ELEMENT_ICON[n.element_type]
      const dashed  = PASSIVE_TYPES.has(n.element_type)
      const iconSize = 13
      const zIdx    = n.parent_id ? 2 : 1
      const shape    = SHAPE_TYPE[n.element_type] || 'rect'
      const bodyPath = getElementPath(n.element_type, n.width, n.height)

      // Shift label/icon for shapes with non-rectangular areas
      const nubOffset  = (shape === 'component') ? Math.min(n.width * 0.12, 12) : 0
      const foldOffset = (shape === 'passive')   ? Math.min(n.width * 0.18, n.height * 0.28, 12) : 0

      const textAreaW = n.width - nubOffset - (iconId ? iconSize + 6 : 8)
      const iconX     = n.width - iconSize - 2
      const iconY     = (shape === 'passive') ? foldOffset + 2 : 2
      const labelCX   = (shape === 'component')
        ? `${Math.round(nubOffset + (n.width - nubOffset) / 2)}`
        : '50%'

      graph.addNode({
        id: n.id,
        x: n.x, y: n.y,
        width: n.width, height: n.height,
        zIndex: zIdx,
        markup: ELEMENT_MARKUP,
        data: { type: 'element', element_id: n.element_id,
                element_type: n.element_type, name: n.name, id: n.element_id },
        attrs: {
          body: {
            d: bodyPath,
            fill: nodeColor(n.element_type),
            stroke: '#888', strokeWidth: 1,
            ...(dashed ? { strokeDasharray: '5 3' } : {}),
          },
          label: {
            text: n.name,
            fontSize: 10, fill: '#222',
            refX: labelCX, refY: '50%',
            textAnchor: 'middle', textVerticalAnchor: 'middle',
            textWrap: { text: n.name, width: textAreaW, height: n.height - 8, ellipsis: true },
          },
          icon: iconId && iconX > 0 ? {
            href: `#${iconId}`,
            x: iconX, y: iconY,
            width: iconSize, height: iconSize,
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
    const srcNode = nodeMap[e.source]
    const tgtNode = nodeMap[e.target]

    // Use OrthogonalAnchor: connection enters/exits at border aligned with target/source center
    const { srcPt, tgtPt } = orthogonalPoints(srcNode, tgtNode)

    try {
      graph.addEdge({
        id: e.id || undefined,
        source: srcPt,          // absolute point on source border
        target: tgtPt,          // absolute point on target border
        ...(e.vertices?.length ? { vertices: e.vertices } : {}),
        connector: { name: 'normal' },
        attrs: {
          line: {
            stroke: s.stroke,
            strokeWidth: s.strokeWidth,
            ...(s.dash ? { strokeDasharray: s.dash } : {}),
            sourceMarker: s.src,
            targetMarker: s.tgt,
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
  // Non-view selection (element, group, note) — only updates PropertiesPanel,
  // canvas stays showing the current diagram
})

onMounted(initGraph)
onUnmounted(() => {
  resizeObserver?.disconnect()
  graph?.dispose()
})
</script>
