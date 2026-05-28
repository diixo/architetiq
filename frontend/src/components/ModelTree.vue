<template>
  <div class="model-tree h-100 d-flex flex-column">
    <div class="panel-heading"><b>Model Tree</b></div>
    <div class="panel-body root-panel-body p-2 flex-grow-1 overflow-auto">
      <div v-if="store.loading" class="text-muted p-2">Loading...</div>
      <div v-else-if="store.error" class="text-danger p-2">{{ store.error }}</div>
      <template v-else-if="store.model">
        <b>
          <a href="#" class="text-decoration-none text-dark" @click.prevent="store.selectNode(store.model)">
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
import { onMounted } from 'vue'
import { useModelStore } from '../stores/model'
import TreeNode from './TreeNode.vue'

const store = useModelStore()
onMounted(() => store.fetchModel())
</script>
