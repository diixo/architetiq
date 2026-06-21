<template>
  <div class="model-tree h-100 d-flex flex-column">

    <!-- Header: toggles between title and search input -->
    <div class="panel-heading d-flex align-items-center gap-1 pe-1">
      <template v-if="!searching">
        <span class="flex-grow-1" style="font-size:0.875rem;">Model Tree</span>
        <button class="btn btn-link p-0 text-muted tree-search-btn" title="Filter" @click="startSearch">
          <i class="bi bi-search" style="font-size:0.7rem;"></i>
        </button>
      </template>
      <template v-else>
        <input
          ref="inputRef"
          v-model="store.filterQuery"
          type="text"
          class="form-control form-control-sm flex-grow-1 tree-filter-input"
          placeholder="Filter elements…"
        />
        <button class="btn btn-link p-0 text-muted tree-search-btn ms-1" title="Clear" @click="stopSearch">
          <i class="bi bi-x-lg" style="font-size:0.7rem;"></i>
        </button>
      </template>
    </div>

    <div class="panel-body root-panel-body p-2 flex-grow-1 overflow-auto">
      <div v-if="store.loading" class="text-muted p-2">Loading...</div>
      <div v-else-if="store.error" class="text-danger p-2">{{ store.error }}</div>
      <template v-else-if="store.model">
        <div
          v-if="!store.filterQuery"
          class="tree-label"
          :class="{ 'fw-semibold': store.selected?.id === store.model?.id }"
          @click="store.selectNode(store.model)"
          @contextmenu.prevent="openModelMenu"
          @mouseenter="rootHovered = true"
          @mouseleave="rootHovered = false"
        >
          <i class="bi bi-dot tree-caret" style="color: transparent;"></i>
          <i class="bi bi-diagram-3-fill" style="color:#0091da;font-size:14px;flex-shrink:0;"></i>
          <span class="tree-name">{{ store.model.name }}</span>
          <span v-if="rootHovered" class="tree-actions" @click.stop>
            <button class="tree-action-btn" title="Properties" @click.stop="onModelProperties">
              <i class="bi bi-sliders"></i>
            </button>
          </span>
        </div>

        <Teleport to="body">
          <div v-if="modelMenu.visible" ref="modelMenuRef" class="tree-ctx-menu shadow"
               :style="{ top: modelMenu.y + 'px', left: modelMenu.x + 'px' }" @click.stop>
            <div class="tree-ctx-item" @click="onModelProperties">
              <span class="me-2" style="width:1em;flex-shrink:0;"></span>Properties
            </div>
          </div>
        </Teleport>
        <ul class="tree ms-2 mt-1">
          <TreeNode
            v-for="child in store.model.children.filter(c => c.folder_type !== 'relations')"
            :key="child.id || child.name"
            :node="child"
          />
        </ul>
      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted, onUnmounted } from 'vue'
import { useModelStore } from '../stores/model'
import TreeNode from './TreeNode.vue'

const store      = useModelStore()
const searching  = ref(false)
const inputRef   = ref(null)
const rootHovered = ref(false)

const modelMenuRef = ref(null)
const modelMenu = reactive({ visible: false, x: 0, y: 0 })

function openModelMenu(e) {
  modelMenu.x = e.clientX
  modelMenu.y = e.clientY
  modelMenu.visible = true
}
function closeModelMenu() { modelMenu.visible = false }
function onModelProperties() {
  store.selectNode(store.model)
  store.propertiesPanelVisible = true
  closeModelMenu()
}
function onModelMenuOutside(e) {
  if (modelMenuRef.value && !modelMenuRef.value.contains(e.target)) closeModelMenu()
}

async function startSearch() {
  searching.value = true
  await nextTick()
  inputRef.value?.focus()
}

function stopSearch() {
  store.filterQuery = ''
  searching.value = false
}

onMounted(() => {
  store.fetchModel()
  document.addEventListener('mousedown', onModelMenuOutside, true)
})
onUnmounted(() => document.removeEventListener('mousedown', onModelMenuOutside, true))
</script>
