<template>
  <div class="panel overflow-auto" style="height: 250px; border-top: 1px solid #ddd; border-radius: 0;">
    <div class="panel-body h-100">
      <template v-if="node">
        <div class="p-2">
          <div class="fw-semibold mb-1" style="font-size: 0.8rem; color: #6c757d; text-transform: uppercase;">
            {{ node.element_type || node.type }}
          </div>
          <div class="fw-bold mb-2">{{ node.name }}</div>
          <div v-if="node.documentation" class="text-muted" style="font-size: 0.8rem; white-space: pre-wrap;">
            {{ node.documentation }}
          </div>
          <div v-if="node.id" class="mt-2 text-muted" style="font-size: 0.75rem; font-family: monospace;">
            {{ node.id }}
          </div>
        </div>
      </template>
      <div v-else class="d-flex align-items-center justify-content-center h-100">
        <p class="text-muted text-center mb-0" style="font-size: 0.875rem;">
          Select an element in the model tree to show its details
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useModelStore } from '../stores/model'

const store = useModelStore()
const node = computed(() => store.selected)
</script>
