<template>
  <li :class="itemClass">
    <span class="tree-label" @click="toggle">
      <i :class="caretClass"></i>
      <i v-if="node.type === 'node'" class="bi bi-folder-fill tree-icon-folder"></i>
      <i v-else-if="node.type === 'view'" class="bi bi-diagram-3 tree-icon-view"></i>
      <i v-else class="bi bi-box tree-icon-element"></i>
      <span
        class="tree-name"
        :class="{ 'text-primary fw-semibold': isSelected }"
        @click.stop="select"
      >{{ node.name }}</span>
    </span>

    <ul v-if="hasChildren && isOpen" class="tree-children">
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

const store = useModelStore()
const isOpen = ref(false)

const hasChildren = computed(() => props.node.children?.length > 0)
const isSelected = computed(() => store.selected?.id === props.node.id && props.node.id)

const itemClass = computed(() => ({
  'tree-folder': props.node.type === 'node',
  'tree-element': props.node.type === 'element',
  'tree-view-item': props.node.type === 'view',
}))

const caretClass = computed(() => [
  'bi',
  hasChildren.value ? 'bi-caret-right-fill' : 'bi-dot',
  'tree-caret',
  { 'tree-caret-open': isOpen.value && hasChildren.value },
])

function toggle() {
  if (hasChildren.value) isOpen.value = !isOpen.value
}

function select() {
  store.selectNode(props.node)
}
</script>
