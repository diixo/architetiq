<template>
  <div class="model-tree h-100 d-flex flex-column">

    <!-- Header: toggles between title and search input -->
    <div class="panel-heading d-flex align-items-center gap-1 pe-1">
      <template v-if="!searching">
        <b class="flex-grow-1" style="font-size:0.875rem;">Model Tree</b>
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
        <b v-if="!store.filterQuery">
          <a href="#" class="text-decoration-none text-dark"
             @click.prevent="store.selectNode(store.model)">
            {{ store.model.name }}
          </a>
        </b>
        <ul class="tree ms-2 mt-1">
          <TreeNode
            v-for="child in store.model.children"
            :key="child.id || child.name"
            :node="child"
          />
        </ul>
      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useModelStore } from '../stores/model'
import TreeNode from './TreeNode.vue'

const store    = useModelStore()
const searching = ref(false)
const inputRef  = ref(null)

async function startSearch() {
  searching.value = true
  await nextTick()
  inputRef.value?.focus()
}

function stopSearch() {
  store.filterQuery = ''
  searching.value = false
}

import { onMounted } from 'vue'
onMounted(() => store.fetchModel())
</script>
