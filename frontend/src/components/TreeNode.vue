<template>
  <li v-if="isVisible" :class="itemClass">
    <span class="tree-label" @click="handleClick">
      <i :class="caretClass"></i>
      <i v-if="node.type === 'node'" class="bi bi-folder-fill tree-icon-folder"></i>
      <i v-else-if="node.type === 'view'" class="bi bi-diagram-3 tree-icon-view"></i>
      <i v-else class="bi bi-box tree-icon-element"></i>
      <span class="tree-name" :class="{ 'fw-semibold': isSelected }">
        <span v-if="highlightedName" v-html="highlightedName"></span>
        <template v-else>{{ node.name }}</template>
      </span>
    </span>

    <ul v-if="hasChildren && effectiveOpen" class="tree-children">
      <TreeNode
        v-for="child in node.children"
        :key="child.id || child.name"
        :node="child"
      />
    </ul>
  </li>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useModelStore } from '../stores/model'

const props = defineProps({
  node: { type: Object, required: true },
})

const store  = useModelStore()
const isOpen = ref(false)

// ── Filter helpers ────────────────────────────────────────────────────────────
function treeContains(node, q) {
  if (node.name.toLowerCase().includes(q)) return true
  return (node.children || []).some(c => treeContains(c, q))
}

const isVisible = computed(() => {
  const q = store.filterQuery?.toLowerCase()
  if (!q) return true
  return treeContains(props.node, q)
})

const isMatch = computed(() => {
  const q = store.filterQuery?.toLowerCase()
  return q ? props.node.name.toLowerCase().includes(q) : false
})

// Auto-expand folders that contain a match when filtering
const effectiveOpen = computed(() => {
  const q = store.filterQuery?.toLowerCase()
  if (q && hasChildren.value) {
    return (props.node.children || []).some(c => treeContains(c, q))
  }
  return isOpen.value
})

// Highlight matched substring in node name
const highlightedName = computed(() => {
  const q = store.filterQuery
  if (!q || !isMatch.value) return null
  const lower = props.node.name.toLowerCase()
  const idx   = lower.indexOf(q.toLowerCase())
  if (idx === -1) return null
  const before = escHtml(props.node.name.slice(0, idx))
  const match  = escHtml(props.node.name.slice(idx, idx + q.length))
  const after  = escHtml(props.node.name.slice(idx + q.length))
  return `${before}<mark class="tree-highlight">${match}</mark>${after}`
})

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
}

// ── Existing logic ────────────────────────────────────────────────────────────
const hasChildren = computed(() => props.node.children?.length > 0)
const isSelected  = computed(() => store.selected?.id === props.node.id && props.node.id)

const itemClass = computed(() => ({
  'tree-folder':    props.node.type === 'node',
  'tree-element':   props.node.type === 'element',
  'tree-view-item': props.node.type === 'view',
}))

const caretClass = computed(() => [
  'bi',
  hasChildren.value ? 'bi-caret-right-fill' : 'bi-dot',
  'tree-caret',
  { 'tree-caret-open': effectiveOpen.value && hasChildren.value },
])

function handleClick() {
  if (hasChildren.value) isOpen.value = !isOpen.value
  store.selectNode(props.node)
}
</script>
