<template>
  <div class="panel root-panel h-100 d-flex flex-column">
    <div class="panel-heading"><b>{{ title }}</b></div>
    <div class="panel-body root-panel-body flex-grow-1 position-relative">
      <div ref="containerRef" class="w-100 h-100"></div>
      <div v-if="!hasContent" class="position-absolute top-50 start-50 translate-middle text-center text-muted" style="pointer-events: none;">
        <i class="bi bi-diagram-3" style="font-size: 2rem; opacity: 0.3;"></i>
        <p class="mt-2 mb-0" style="font-size: 0.875rem;">Select a view from the model tree to display it here</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useModelStore } from '../stores/model'

const store = useModelStore()
const containerRef = ref(null)

const title = computed(() => store.selected?.name || store.model?.name || 'Canvas')
const hasContent = computed(() => store.selected?.type === 'view')
</script>
