<template>
  <li v-if="isVisible" :class="itemClass">
    <span
      class="tree-label"
      @click="handleClick"
      @dblclick.stop="startEdit"
      @contextmenu.prevent="openCtx"
      @mouseenter="hovered = true"
      @mouseleave="hovered = false"
    >
      <i :class="caretClass"></i>
      <i v-if="node.type === 'node'" class="bi bi-folder-fill tree-icon-folder"></i>
      <i v-else-if="node.type === 'view'" class="bi bi-diagram-3 tree-icon-view"></i>
      <i v-else class="bi bi-box tree-icon-element"></i>

      <!-- Inline edit input -->
      <input
        v-if="isEditing"
        ref="editInputRef"
        v-model="editValue"
        class="tree-edit-input"
        @blur="confirmEdit"
        @keyup.enter="confirmEdit"
        @keyup.escape="cancelEdit"
        @click.stop
      />

      <!-- Normal name display -->
      <span v-else class="tree-name" :class="{ 'fw-semibold': isSelected }">
        <span v-if="highlightedName" v-html="highlightedName"></span>
        <template v-else>{{ node.name }}</template>
      </span>

      <!-- Hover action buttons -->
      <span
        v-if="hovered && !isEditing && !store.filterQuery"
        class="tree-actions"
        @click.stop
      >
        <button
          v-if="node.type === 'node'"
          class="tree-action-btn"
          title="Add folder"
          @click.stop="onAdd"
        ><i class="bi bi-plus"></i></button>
        <button
          class="tree-action-btn"
          title="Rename"
          @click.stop="startEdit"
        ><i class="bi bi-pencil"></i></button>
        <button
          v-if="!isRoot"
          class="tree-action-btn tree-action-delete"
          title="Delete"
          @click.stop="onDelete"
        ><i class="bi bi-trash3"></i></button>
      </span>
    </span>

    <ul v-if="hasChildren && effectiveOpen" class="tree-children">
      <TreeNode
        v-for="child in node.children"
        :key="child.id || child.name"
        :node="child"
      />
    </ul>

    <!-- Context menu -->
    <TreeContextMenu
      ref="ctxRef"
      :node="node"
      :is-root="isRoot"
      @start-edit="startEdit"
    />
  </li>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useModelStore } from '../stores/model'
import TreeContextMenu from './TreeContextMenu.vue'

const props = defineProps({
  node:   { type: Object,  required: true },
  isRoot: { type: Boolean, default: false },
})

const store        = useModelStore()
const hovered      = ref(false)
const isEditing    = ref(false)
const editValue    = ref('')
const editInputRef = ref(null)
const isOpen       = ref(false)
const ctxRef       = ref(null)

function openCtx(e) {
  ctxRef.value?.open(e.clientX, e.clientY)
}

// Start editing when store.editingNodeId matches this node
watch(() => store.editingNodeId, async (id) => {
  if (id === props.node.id) {
    isOpen.value = true
    await nextTick()
    startEdit()
    store.editingNodeId = null
  }
})

async function startEdit() {
  editValue.value = props.node.name
  isEditing.value = true
  await nextTick()
  editInputRef.value?.focus()
  editInputRef.value?.select()
}

function confirmEdit() {
  if (editValue.value.trim()) {
    store.renameNode(props.node.id, editValue.value)
  }
  isEditing.value = false
}

function cancelEdit() {
  // If name is empty (newly created folder), delete it
  if (!props.node.name.trim()) {
    store.deleteNode(props.node.id)
  }
  isEditing.value = false
}

function onAdd() {
  isOpen.value = true
  store.addChildFolder(props.node.id)
}

function onDelete() {
  const label = props.node.name || 'this item'
  const hasKids = (props.node.children || []).length > 0
  const msg = hasKids
    ? `Delete "${label}" and all its ${props.node.children.length} children?`
    : `Delete "${label}"?`
  if (confirm(msg)) store.deleteNode(props.node.id)
}

// ── Filter helpers ────────────────────────────────────────────────────────────
function treeContains(node, q) {
  if (node.name.toLowerCase().includes(q)) return true
  return (node.children || []).some(c => treeContains(c, q))
}

const isVisible = computed(() => {
  const q = store.filterQuery?.toLowerCase()
  return !q || treeContains(props.node, q)
})

const isMatch = computed(() => {
  const q = store.filterQuery?.toLowerCase()
  return q ? props.node.name.toLowerCase().includes(q) : false
})

const effectiveOpen = computed(() => {
  const q = store.filterQuery?.toLowerCase()
  if (q && hasChildren.value) return (props.node.children || []).some(c => treeContains(c, q))
  return isOpen.value
})

const highlightedName = computed(() => {
  const q = store.filterQuery
  if (!q || !isMatch.value) return null
  const lower = props.node.name.toLowerCase()
  const idx = lower.indexOf(q.toLowerCase())
  if (idx === -1) return null
  const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  return esc(props.node.name.slice(0, idx))
    + `<mark class="tree-highlight">${esc(props.node.name.slice(idx, idx + q.length))}</mark>`
    + esc(props.node.name.slice(idx + q.length))
})

// ── Standard tree logic ───────────────────────────────────────────────────────
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
