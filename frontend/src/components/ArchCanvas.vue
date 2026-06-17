<template>
  <div class="panel root-panel h-100 d-flex flex-column">
    <div class="panel-heading d-flex align-items-center gap-2">
      <span>{{ title }}</span>
      <span v-if="loading" class="text-muted ms-1" style="font-size:0.75rem;">Loading…</span>
      <div class="ms-auto d-flex gap-1 align-items-center" v-if="diagramData">
        <!-- Save indicator + button -->
        <span v-if="isDirty" class="text-muted" style="font-size:0.7rem;">unsaved</span>
        <button
          class="btn btn-sm py-0 px-2"
          :class="isDirty ? 'btn-warning' : 'btn-light border'"
          title="Save diagram layout"
          @click="saveLayout"
        >
          <i class="bi bi-floppy" style="font-size:0.75rem;"></i>
        </button>
        <button class="btn btn-sm btn-light border py-0 px-1" title="Fit" @click="fitView">
          <i class="bi bi-fullscreen" style="font-size:0.75rem;"></i>
        </button>
        <button class="btn btn-sm btn-light border py-0 px-1" title="Reset zoom" @click="resetZoom">
          <i class="bi bi-zoom-out" style="font-size:0.75rem;"></i>
        </button>
      </div>
    </div>

    <div
      class="flex-grow-1 position-relative"
      style="overflow:hidden;"
      @dragover.prevent
      @drop="onDrop"
    >
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

    <!-- Canvas context menu — teleported to body, position here doesn't matter -->
    <Teleport to="body">
      <div
        v-if="ctxMenu.visible"
        ref="ctxMenuRef"
        class="canvas-ctx-menu"
        :style="{ top: ctxMenu.y + 'px', left: ctxMenu.x + 'px' }"
        @click.stop
      >
        <button class="canvas-ctx-item" @click="onCtxProperties">
          <span class="canvas-ctx-icon"></span>Properties
        </button>
        <hr class="canvas-ctx-divider">
        <button class="canvas-ctx-item canvas-ctx-item-danger" @click="onCtxDelete">
          <span class="canvas-ctx-icon"><i class="bi bi-trash3"></i></span>Delete
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { Graph } from '@antv/x6'
import { useModelStore } from '../stores/model'
import { ELEMENT_ICON } from '../archimate-icons.js'
import { humanizeType } from '../archimate-folder-elements.js'
import { nodeColor } from '../archimate-styles.js'

const _NHP = [[0,0],[.5,0],[1,0],[1,.5],[1,1],[.5,1],[0,1],[0,.5]]
const _NHS = 7, _NHH = 3.5
let _selHandlesEl = null

function _removeHandles() {
  if (_selHandlesEl) { _selHandlesEl.remove(); _selHandlesEl = null }
}

function _addHandles(node) {
  _removeHandles()
  const view = graph?.findViewByCell(node)
  if (!view) return
  const { width, height } = node.getSize()
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g')
  _NHP.forEach(([rx, ry]) => {
    const r = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
    r.setAttribute('x', String(rx * width - _NHH))
    r.setAttribute('y', String(ry * height - _NHH))
    r.setAttribute('width',  String(_NHS))
    r.setAttribute('height', String(_NHS))
    r.setAttribute('fill', '#0d6efd')
    r.setAttribute('stroke', '#fff')
    r.setAttribute('stroke-width', '1')
    r.setAttribute('pointer-events', 'none')
    g.appendChild(r)
  })
  const container = view.container ?? view.el
  container.appendChild(g)
  _selHandlesEl = g
}

const store            = useModelStore()
const containerRef     = ref(null)
const diagramData      = ref(null)
const loading          = ref(false)
const isDirty          = ref(false)
const currentViewId    = ref(null)
let graph = null
let resizeObserver = null
let selectedCanvasCell = null

const ctxMenuRef = ref(null)
const ctxMenu = reactive({ visible: false, x: 0, y: 0, cell: null })

function showCtxMenu(cell, e) {
  e.preventDefault()
  ctxMenu.cell    = cell
  ctxMenu.x       = e.clientX
  ctxMenu.y       = e.clientY
  ctxMenu.visible = true
}
function hideCtxMenu() {
  ctxMenu.visible = false
  ctxMenu.cell    = null
}
function onCtxProperties() {
  const cell = ctxMenu.cell
  if (cell?.isNode()) {
    selectNode(cell)
    const d = cell.getData()
    if (d?.element_id) store.selectNode(store.findById(d.element_id) || d)
    else store.selectNode(d)
  } else if (cell?.isEdge()) {
    selectEdge(cell)
  }
  store.propertiesPanelVisible = true
  hideCtxMenu()
}
function onCtxDelete() {
  if (ctxMenu.cell) {
    graph.removeCell(ctxMenu.cell)
    if (selectedCanvasCell === ctxMenu.cell) selectedCanvasCell = null
  }
  hideCtxMenu()
}
function onCtxOutside(e) {
  if (ctxMenuRef.value && !ctxMenuRef.value.contains(e.target)) hideCtxMenu()
}

// ── Node selection ────────────────────────────────────────────────────────────
function _strokeSel(node) {
  return node?.getData?.()?.type === 'group' ? 'outline' : 'body'
}

function _nodeDefaultStroke(d) {
  if (d?.type === 'group') return '#999'
  if (d?.type === 'note')  return '#ccc'
  if (d?.type === 'view')  return '#1565c0'
  return '#888'
}

function deselectNode() {
  if (!selectedCanvasCell?.isNode?.()) return
  const sel = _strokeSel(selectedCanvasCell)
  selectedCanvasCell.attr(`${sel}/stroke`, _nodeDefaultStroke(selectedCanvasCell.getData()))
  selectedCanvasCell.attr(`${sel}/strokeWidth`, 1)
  _removeHandles()
}

function selectNode(node) {
  if (selectedCanvasCell === node) return
  deselectEdge()
  deselectNode()
  selectedCanvasCell = node
  const sel = _strokeSel(node)
  node.attr(`${sel}/stroke`, '#0d6efd')
  node.attr(`${sel}/strokeWidth`, 2)
  _addHandles(node)
}

// ── Edge selection ────────────────────────────────────────────────────────────
const ENDPOINT_HANDLE_ATTRS = {
  d: 'M -3 0 a 3,3 0 1,0 6,0 a 3,3 0 1,0 -6,0',
  fill: '#0d6efd', stroke: '#fff', 'stroke-width': 1.5, cursor: 'move',
}

function deselectEdge() {
  if (!selectedCanvasCell?.isEdge?.()) return
  const s = edgeStyle(selectedCanvasCell.getData()?.type)
  selectedCanvasCell.attr('line/stroke', s.stroke)
  selectedCanvasCell.attr('line/strokeWidth', s.strokeWidth)
  selectedCanvasCell.removeTools()
}

function selectEdge(edge) {
  if (selectedCanvasCell === edge) return
  deselectEdge()
  deselectNode()
  selectedCanvasCell = edge
  edge.attr('line/stroke', '#0d6efd')
  edge.attr('line/strokeWidth', Math.max(edge.attr('line/strokeWidth') || 1, 1.5))
  edge.addTools([
    { name: 'source-arrowhead', args: { attrs: ENDPOINT_HANDLE_ATTRS } },
    { name: 'target-arrowhead', args: { attrs: ENDPOINT_HANDLE_ATTRS } },
    { name: 'vertices', args: { snapRadius: 10, attrs: { circle: { r: 2, fill: '#0d6efd', stroke: '#fff', strokeWidth: 1.5 } } } },
    { name: 'segments',  args: { snapRadius: 10 } },
  ])
}

// CSRF token helper
function csrfToken() {
  const m = document.cookie.match(/csrftoken=([^;]+)/)
  return m ? m[1] : ''
}

const title = computed(() => {
  const model = store.model?.name
  const view  = diagramData.value?.name
  if (model && view) return `${model}: ${view}`
  return view || model || 'Canvas'
})

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


// ── ArchiMate shape categories ────────────────────────────────────────────────
// Per Archi source: most figures use RoundedRectangleFigureDelegate for type=0 (default).
// Custom shapes (process arrow, function polygon, etc.) are user-selectable alternatives.
// Only truly standardized shape differences are kept here:
const SHAPE_TYPE = {
  // Passive structure: folded top-right corner (standard ArchiMate notation)
  BusinessObject:'passive', DataObject:'passive', Artifact:'passive',
  Contract:'passive', Representation:'passive', Material:'passive',
}

function roundedRect(w, h, r = 3) {
  r = Math.min(r, w / 2, h / 2)
  return `M ${r},0 H ${w-r} Q ${w},0 ${w},${r} V ${h-r} Q ${w},${h} ${w-r},${h} H ${r} Q 0,${h} 0,${h-r} V ${r} Q 0,0 ${r},0 Z`
}

function getElementPath(et, w, h) {
  const s = SHAPE_TYPE[et] || 'rect'
  switch (s) {
    case 'passive': {
      const f = Math.min(w * 0.18, h * 0.28, 12)
      return `M 0,0 H ${w-f} L ${w},${f} V ${h} H 0 Z`
    }
    default:
      return roundedRect(w, h, 3)
  }
}


const ELEMENT_MARKUP = [
  { tagName: 'path', selector: 'body' },
  { tagName: 'text', selector: 'label' },
  { tagName: 'use',  selector: 'icon' },
]

// ── Group rendering helpers ───────────────────────────────────────────────────
const TAB_H = 18  // GroupFigure.java TOPBAR_HEIGHT = 18

function darkenColor(hex) {
  if (!hex || hex.length < 7) return '#cccccc'
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  const d = (v) => Math.max(0, Math.floor(v * 0.78)).toString(16).padStart(2, '0')
  return `#${d(r)}${d(g)}${d(b)}`
}

function labelColor(bgHex) {
  if (!bgHex || bgHex.length < 7) return '#333'
  const r = parseInt(bgHex.slice(1, 3), 16)
  const g = parseInt(bgHex.slice(3, 5), 16)
  const b = parseInt(bgHex.slice(5, 7), 16)
  return (0.299 * r + 0.587 * g + 0.114 * b) > 128 ? '#333' : '#fff'
}

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
    // ── Enable editing ────────────────────────────────────────────────────────
    interacting: { nodeMovable: true, edgeLabelMovable: false, vertexAddable: false, arrowheadMovable: true },
    magnetThreshold: 4,
    connecting: {
      snap:             { radius: 50 },
      allowBlank:       false,
      allowLoop:        false,
      highlight:        true,
      connector:        { name: 'normal' },
      connectionPoint:  'boundary',
      validateConnection: ({ sourceCell, targetCell }) =>
        sourceCell !== targetCell,
    },
  })

  // Selection / PropertiesPanel
  graph.on('node:click', ({ node }) => {
    selectNode(node)
    const d = node.getData()
    if (!d) return
    if (d.element_id) {
      store.selectNode(store.findById(d.element_id) || d)
    } else if (d.type === 'view' && d.id) {
      store.selectNode(store.findById(d.id) || d)
    } else {
      store.selectNode(d)
    }
  })
  graph.on('edge:click', ({ edge }) => selectEdge(edge))
  graph.on('blank:click', () => {
    deselectEdge()
    deselectNode()
    selectedCanvasCell = null
    hideCtxMenu()
  })
  graph.on('node:contextmenu', ({ node, e }) => showCtxMenu(node, e))
  graph.on('edge:contextmenu', ({ edge, e }) => showCtxMenu(edge, e))

  // Mark dirty on any structural change
  graph.on('node:moved',         () => { isDirty.value = true })
  graph.on('node:resized',       () => { isDirty.value = true })
  graph.on('node:removed',       () => { isDirty.value = true })
  graph.on('edge:connected',     ({ edge }) => applyConnTypeToEdge(edge))
  graph.on('edge:added',         ({ edge }) => {
    if (!edge.getData()?.isLoaded) isDirty.value = true
  })
  graph.on('edge:removed',       ({ edge }) => {
    if (!edge.getData()?.isLoaded) isDirty.value = true
  })
  graph.on('edge:change:vertices', () => { isDirty.value = true })

  resizeObserver = new ResizeObserver(() => {
    if (containerRef.value)
      graph.resize(containerRef.value.clientWidth, containerRef.value.clientHeight)
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
      const fillColor = n.fill_color || '#f0f0f0'
      const tabW = Math.floor(n.width / 2)
      graph.addNode({
        id: n.id, x: n.x, y: n.y, width: n.width, height: n.height,
        zIndex: 0,
        markup: [
          { tagName: 'rect',  selector: 'body_fill' },
          { tagName: 'rect',  selector: 'tab_fill'  },
          { tagName: 'path',  selector: 'outline'   },
          { tagName: 'text',  selector: 'label'     },
        ],
        data: { type: 'group', name: n.name, id: n.id },
        attrs: {
          body_fill: {
            x: 0, y: TAB_H, width: n.width, height: Math.max(0, n.height - TAB_H),
            fill: fillColor, stroke: 'none',
          },
          tab_fill: {
            x: 0, y: 0, width: tabW, height: TAB_H,
            fill: darkenColor(fillColor), stroke: 'none',
          },
          outline: {
            d: `M 0,${TAB_H} L 0,0 H ${tabW} V ${TAB_H} H ${n.width} V ${n.height} H 0 Z`,
            fill: 'none', stroke: '#999', strokeWidth: 1,
          },
          label: {
            text: n.name,
            x: 6, y: TAB_H / 2,
            textAnchor: 'start',
            textVerticalAnchor: 'middle',
            fontSize: 11, fontWeight: 600,
            fill: labelColor(fillColor),
            textWrap: { text: n.name, width: tabW - 12, ellipsis: true },
          },
        },
      })
    } else if (n.type === 'element') {
      const zIdx     = n.parent_id ? 2 : 1
      const iconId   = ELEMENT_ICON[n.element_type]
      const iconSize = 13
      const shape    = SHAPE_TYPE[n.element_type] || 'rect'
      const bodyPath = getElementPath(n.element_type, n.width, n.height)
      const foldOffset = (shape === 'passive') ? Math.min(n.width * 0.18, n.height * 0.28, 12) : 0
      const iconX    = n.width - iconSize - 2
      const iconY    = (shape === 'passive') ? foldOffset + 2 : 2
      const textAreaW = n.width - (iconId ? iconSize + 6 : 8)

      graph.addNode({
        id: n.id, x: n.x, y: n.y, width: n.width, height: n.height,
        zIndex: zIdx, markup: ELEMENT_MARKUP,
        data: { type: 'element', element_id: n.element_id, element_type: n.element_type, name: n.name, id: n.element_id },
        attrs: {
          body: {
            d: bodyPath, fill: nodeColor(n.element_type),
            stroke: '#888', strokeWidth: 1, magnet: true,
            ...(n.element_type === 'Grouping' ? { strokeDasharray: '8 4' } : {}),
          },
          label: {
            text: n.name, fontSize: 10, fill: '#222',
            refX: '50%', refY: '50%',
            textAnchor: 'middle', textVerticalAnchor: 'middle',
            textWrap: { text: n.name, width: textAreaW, height: n.height - 8, ellipsis: true },
          },
          icon: iconId && iconX > 0 ? {
            href: `#${iconId}`, x: iconX, y: iconY, width: iconSize, height: iconSize,
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
        source: srcPt,
        target: tgtPt,
        data: { isLoaded: true, type: e.type },
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
          wrap: { strokeWidth: 10 },
        },
      })
    } catch (_) { /* skip invalid */ }
  }

  for (const ue of (diagramData.value.user_edges || [])) {
    if (!nodeIds.has(ue.source_cell) || !nodeIds.has(ue.target_cell)) continue
    const s = edgeStyle(ue.type)
    try {
      graph.addEdge({
        id: ue.id || undefined,
        source: { cell: ue.source_cell },
        target: { cell: ue.target_cell },
        data: { isLoaded: true, type: ue.type },
        ...(ue.vertices?.length ? { vertices: ue.vertices } : {}),
        connector: { name: 'normal' },
        attrs: {
          line: {
            stroke: s.stroke,
            strokeWidth: s.strokeWidth,
            ...(s.dash ? { strokeDasharray: s.dash } : {}),
            sourceMarker: s.src,
            targetMarker: s.tgt,
          },
          wrap: { strokeWidth: 10 },
        },
      })
    } catch (_) { /* skip invalid */ }
  }

  graph.zoomToFit({ padding: 24, maxScale: 1 })
}

// ── Load ──────────────────────────────────────────────────────────────────────
function extractLayout() {
  if (!graph || !currentViewId.value) return null
  const nodes = graph.getNodes().map(n => {
    const { x, y } = n.getPosition()
    const { width, height } = n.getSize()
    const data = n.getData() || {}
    const node = { id: n.id, x, y, width, height }
    if (data.type) node.node_type = data.type
    if (data.element_id) node.element_id = data.element_id
    if (data.element_type) node.element_type = data.element_type
    if (data.name != null) node.name = data.name
    return node
  })
  const userEdges = graph.getEdges()
    .filter(e => !e.getData()?.isLoaded)
    .map(e => {
      const src = e.getSource()
      const tgt = e.getTarget()
      return {
        id: e.id,
        source_cell: src?.cell ?? null,
        target_cell: tgt?.cell ?? null,
        type: e.getData()?.type || '',
        vertices: e.getVertices() || [],
      }
    })
  return { view_id: currentViewId.value, nodes, user_edges: userEdges }
}

async function saveLayout() {
  const layout = extractLayout()
  if (!layout) return
  try {
    const r = await fetch(`/api/diagram/${layout.view_id}/save/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify(layout),
    })
    if (!r.ok) {
      console.error('Save layout HTTP error:', r.status, await r.text())
      return
    }
    if ((await r.json()).ok) isDirty.value = false
  } catch (e) {
    console.error('Save layout failed:', e)
  }
}

async function loadDiagram(viewId) {
  isDirty.value = false
  currentViewId.value = viewId
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

// ── Drag-and-drop from palette ────────────────────────────────────────────────
function onDrop(e) {
  if (!graph || !diagramData.value) return
  const raw = e.dataTransfer?.getData('application/archimate-element')
  if (!raw) return

  const { elementType, folderType } = JSON.parse(raw)
  // Convert screen coords → canvas local coords
  const rect = containerRef.value.getBoundingClientRect()
  const scale = graph.zoom()
  const trs   = graph.translate()
  const x = (e.clientX - rect.left - trs.tx) / scale
  const y = (e.clientY - rect.top  - trs.ty) / scale

  const id   = crypto.randomUUID ? crypto.randomUUID()
    : `new-${Date.now()}-${Math.random().toString(36).slice(2)}`
  const name = humanizeType(elementType)
  const w = 120, h = 55

  if (elementType === 'DiagramGroup') {
    const fillColor = nodeColor('DiagramGroup')
    const tabW = Math.floor(w / 2)
    graph.addNode({
      id, x: x - w/2, y: y - h/2, width: w, height: h,
      zIndex: 0,
      markup: [
        { tagName: 'rect',  selector: 'body_fill' },
        { tagName: 'rect',  selector: 'tab_fill'  },
        { tagName: 'path',  selector: 'outline'   },
        { tagName: 'text',  selector: 'label'     },
      ],
      data: { type: 'group', name, id },
      attrs: {
        body_fill: { x: 0, y: TAB_H, width: w, height: Math.max(0, h - TAB_H),
                     fill: fillColor, stroke: 'none' },
        tab_fill:  { x: 0, y: 0, width: tabW, height: TAB_H,
                     fill: darkenColor(fillColor), stroke: 'none' },
        outline:   { d: `M 0,${TAB_H} L 0,0 H ${tabW} V ${TAB_H} H ${w} V ${h} H 0 Z`,
                     fill: 'none', stroke: '#999', strokeWidth: 1 },
        label:     { text: name, x: 6, y: TAB_H / 2,
                     textAnchor: 'start', textVerticalAnchor: 'middle',
                     fontSize: 11, fontWeight: 600, fill: labelColor(fillColor),
                     textWrap: { text: name, width: tabW - 12, ellipsis: true } },
      },
    })
  } else {
    const bodyPath = getElementPath(elementType, w, h)
    const iconId   = ELEMENT_ICON[elementType]
    const iconSize = 13
    graph.addNode({
      id, x: x - w/2, y: y - h/2, width: w, height: h,
      zIndex: 1, markup: ELEMENT_MARKUP,
      data: { type: 'element', element_id: id, element_type: elementType, name, id },
      attrs: {
        body:  { d: bodyPath, fill: nodeColor(elementType), stroke: '#888', strokeWidth: 1, magnet: true,
                 ...(elementType === 'Grouping' ? { strokeDasharray: '8 4' } : {}) },
        label: { text: name, fontSize: 10, fill: '#222',
                 refX: '50%', refY: '50%', textAnchor: 'middle', textVerticalAnchor: 'middle',
                 textWrap: { text: name, width: w - (iconId ? iconSize + 6 : 8), height: h - 8, ellipsis: true } },
        icon: iconId ? { href: `#${iconId}`, x: w - iconSize - 2, y: 2, width: iconSize, height: iconSize }
                     : { width: 0, height: 0 },
      },
    })
  }

  // Add to model tree
  store.addElement(store.findFolderByType(folderType)?.id, elementType)
  isDirty.value = true
}

// ── Apply active connection type to newly drawn edges ─────────────────────────
function applyConnTypeToEdge(edge) {
  const relType = store.activeConnType
  edge.setData({ type: relType })
  const s = edgeStyle(relType)
  // Use attr() path setters — setAttrs() deep-merges and won't clear X6 default blue markers
  edge.attr('line/stroke', s.stroke)
  edge.attr('line/strokeWidth', s.strokeWidth)
  edge.attr('line/strokeDasharray', s.dash || null)
  edge.attr('line/sourceMarker', s.src ?? false)
  edge.attr('line/targetMarker', s.tgt ?? false)
  edge.attr('wrap/strokeWidth', 10)
  isDirty.value = true
}

// ── Auto-save layout on any change ────────────────────────────────────────────
watch(isDirty, (dirty) => { if (dirty) saveLayout() })

// ── Watchers ──────────────────────────────────────────────────────────────────
watch(() => store.selected, node => {
  if (node?.type === 'view') loadDiagram(node.id)
  // Non-view selection (element, group, note) — only updates PropertiesPanel,
  // canvas stays showing the current diagram
})

watch(() => store.activePaletteItem, item => {
  if (containerRef.value)
    containerRef.value.style.cursor = item?.kind === 'conn' ? 'crosshair' : ''
})

async function clearDiagram() {
  if (currentViewId.value) {
    try {
      await fetch(`/api/diagram/${currentViewId.value}/save/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
        body: JSON.stringify({ view_id: currentViewId.value, nodes: [], user_edges: [] }),
      })
    } catch (e) { /* ignore */ }
  }
  diagramData.value = null
  currentViewId.value = null
  isDirty.value = false
  graph?.clearCells()
}

function onKeyDown(e) {
  if (e.key !== 'Delete' && e.key !== 'Backspace') return
  const tag = e.target.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || e.target.isContentEditable) return
  if (!graph || !selectedCanvasCell) return
  graph.removeCell(selectedCanvasCell)
  selectedCanvasCell = null
}

defineExpose({ clearDiagram })

onMounted(() => {
  initGraph()
  document.addEventListener('keydown', onKeyDown)
  document.addEventListener('mousedown', onCtxOutside, true)
})
onUnmounted(() => {
  resizeObserver?.disconnect()
  graph?.dispose()
  document.removeEventListener('keydown', onKeyDown)
  document.removeEventListener('mousedown', onCtxOutside, true)
})
</script>
