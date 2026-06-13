<template>
  <Teleport to="body">
    <div
      v-if="visible"
      ref="menuRef"
      class="tree-ctx-menu shadow"
      :style="{ top: y + 'px', left: x + 'px' }"
      @click.stop
    >
      <!-- New ▶ with inline submenu — mouse stays inside wrapper, no close on hover -->
      <div
        class="tree-ctx-item tree-ctx-has-sub"
        :class="{ 'tree-ctx-item-disabled': !hasNewItems }"
        @mouseenter="hasNewItems && (subOpen = true)"
        @mouseleave="subOpen = false"
      >
        <i class="bi bi-plus-lg me-2"></i>New
        <i class="bi bi-chevron-right ms-auto" style="font-size:0.6rem;"></i>

        <!-- Submenu: child of wrapper so mouse events don't leak out -->
        <div
          v-if="subOpen"
          class="tree-ctx-submenu shadow"
          @click.stop
        >
          <div v-if="canAddFolder" class="tree-ctx-item" @click="onAddFolder">
            <i class="bi bi-folder-fill me-2" style="color:#ffc107;"></i>Folder
          </div>

          <template v-if="elementTypes.length">
            <div class="tree-ctx-divider"></div>
            <div
              v-for="et in elementTypes"
              :key="et"
              class="tree-ctx-item tree-ctx-item-sm"
              @click="onAddElement(et)"
            >
              <img
                v-if="PALETTE_ICON[et]"
                :src="PALETTE_ICON[et]"
                width="14" height="14"
                class="me-2"
                draggable="false"
              />
              <i v-else class="bi bi-box me-2 tree-icon-element"></i>
              {{ humanizeType(et) }}
            </div>
          </template>
        </div>
      </div>

      <div class="tree-ctx-divider"></div>

      <!-- Rename / Delete — disabled for protected top-level folders -->
      <div
        class="tree-ctx-item"
        :class="{ 'tree-ctx-item-disabled': isProtected }"
        @click="!isProtected && onRename()"
      >
        <i class="bi bi-pencil me-2"></i>Rename
      </div>
      <div
        v-if="!isRoot && !isProtected"
        class="tree-ctx-item tree-ctx-item-danger"
        @click="onDelete"
      >
        <i class="bi bi-trash3 me-2"></i>Delete
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useModelStore } from '../stores/model'
import { FOLDER_ELEMENTS, humanizeType } from '../archimate-folder-elements.js'
import { PALETTE_ICON } from '../archimate-palette-icons.js'

const props = defineProps({
  node:        { type: Object,  default: null },
  isRoot:      { type: Boolean, default: false },
  isProtected: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'start-edit'])

const store   = useModelStore()
const visible = ref(false)
const subOpen = ref(false)
const x       = ref(0)
const y       = ref(0)
const menuRef = ref(null)

// Determine which folder_type to use for the New submenu.
// Archi walks UP to topMostFolder.getType() — sub-folders inherit from top-level parent.
// View nodes behave like DIAGRAMS folder.
// Element/root nodes: New is disabled.
const effectiveFolderType = computed(() => {
  const n = props.node
  if (!n) return null
  if (n.type === 'view') return 'diagrams'
  if (n.type !== 'node') return null   // element / model
  // Use own folder_type OR walk up to find topmost ancestor's folder_type
  return n.folder_type || store.getTopFolderType(n.id) || null
})

const elementTypes = computed(() =>
  effectiveFolderType.value
    ? (FOLDER_ELEMENTS[effectiveFolderType.value] || [])
    : []
)

// Sub-folder only makes sense for folder and view nodes
const canAddFolder = computed(() =>
  props.node?.type === 'node' || props.node?.type === 'view'
)

// Show New submenu if there's anything to create
const hasNewItems = computed(() =>
  canAddFolder.value || elementTypes.value.length > 0
)

function open(clientX, clientY) {
  subOpen.value = false
  x.value = clientX
  y.value = clientY
  visible.value = true
  nextTick(() => {
    const el = menuRef.value
    if (!el) return
    const rect = el.getBoundingClientRect()
    if (rect.right  > window.innerWidth)  x.value = clientX - rect.width
    if (rect.bottom > window.innerHeight) y.value = clientY - rect.height
  })
}

function close() {
  visible.value = false
  subOpen.value = false
  emit('close')
}

function targetFolderId() {
  // For view nodes: add into DIAGRAMS folder, not into the view itself
  if (props.node?.type === 'view') {
    return store.findFolderByType('diagrams')?.id || null
  }
  return props.node?.id || null
}

function onAddFolder() {
  const id = targetFolderId()
  if (id) store.addChildFolder(id)
  close()
}

function onAddElement(et) {
  const id = targetFolderId()
  if (!id) { close(); return }
  if (et === 'ArchimateDiagramModel' || et === 'SketchModel') {
    store.addView(id, et)
  } else {
    store.addElement(id, et)
  }
  close()
}

function onRename() {
  emit('start-edit')
  close()
}

function onDelete() {
  const hasKids = (props.node.children || []).length > 0
  const msg = hasKids
    ? `Delete "${props.node.name}" and all its ${props.node.children.length} children?`
    : `Delete "${props.node.name}"?`
  if (confirm(msg)) store.deleteNode(props.node.id)
  close()
}

function onOutsideClick(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) close()
}

onMounted(() => document.addEventListener('mousedown', onOutsideClick, true))
onUnmounted(() => document.removeEventListener('mousedown', onOutsideClick, true))

defineExpose({ open, close })
</script>
