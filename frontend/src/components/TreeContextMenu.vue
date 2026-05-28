<template>
  <Teleport to="body">
    <div
      v-if="visible"
      ref="menuRef"
      class="tree-ctx-menu shadow"
      :style="{ top: y + 'px', left: x + 'px' }"
      @click.stop
    >
      <!-- Add sub-folder -->
      <div class="tree-ctx-item" @click="onAddFolder">
        <i class="bi bi-folder-plus me-2"></i>New Sub-folder
      </div>

      <!-- Add elements for this folder type -->
      <template v-if="elementTypes.length">
        <div class="tree-ctx-divider"></div>
        <div class="tree-ctx-section">Add element</div>
        <div
          v-for="et in elementTypes"
          :key="et"
          class="tree-ctx-item tree-ctx-item-sm"
          @click="onAddElement(et)"
        >
          <i class="bi bi-box me-2 tree-icon-element"></i>{{ humanizeType(et) }}
        </div>
      </template>

      <div class="tree-ctx-divider"></div>

      <!-- Rename / Delete -->
      <div class="tree-ctx-item" @click="onRename">
        <i class="bi bi-pencil me-2"></i>Rename
      </div>
      <div v-if="!isRoot" class="tree-ctx-item tree-ctx-item-danger" @click="onDelete">
        <i class="bi bi-trash3 me-2"></i>Delete
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useModelStore } from '../stores/model'
import { FOLDER_ELEMENTS, humanizeType } from '../archimate-folder-elements.js'

const props = defineProps({
  node:   { type: Object,  default: null },
  isRoot: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'start-edit'])

const store   = useModelStore()
const visible = ref(false)
const x       = ref(0)
const y       = ref(0)
const menuRef = ref(null)

const elementTypes = computed(() => {
  const ft = props.node?.folder_type
  return ft ? (FOLDER_ELEMENTS[ft] || []) : []
})

function open(clientX, clientY) {
  x.value = clientX
  y.value = clientY
  visible.value = true
  nextTick(() => {
    // Keep menu inside viewport
    const el = menuRef.value
    if (!el) return
    const rect = el.getBoundingClientRect()
    if (rect.right  > window.innerWidth)  x.value = clientX - rect.width
    if (rect.bottom > window.innerHeight) y.value = clientY - rect.height
  })
}

function close() {
  visible.value = false
  emit('close')
}

function onAddFolder() {
  store.addChildFolder(props.node.id)
  close()
}

function onAddElement(et) {
  store.addElement(props.node.id, et)
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
