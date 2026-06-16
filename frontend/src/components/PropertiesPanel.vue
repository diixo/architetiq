<template>
  <div class="panel prop-panel d-flex flex-column" style="position: fixed; bottom: 0; left: 320px; right: 0; height: 250px; z-index: 100; border-top: 1px solid #ddd; border-radius: 0;">

    <!-- Title bar -->
    <div class="d-flex align-items-center px-2" style="flex-shrink: 0; height: 26px; background: #f1f3f5; border-bottom: 1px solid #dee2e6;">
      <span style="font-size: 0.75rem; font-weight: 600; color: #495057;">Properties</span>
      <button
        class="btn-close ms-auto"
        style="font-size: 0.6rem;"
        aria-label="Close"
        @click="emit('close')"
      ></button>
    </div>

    <!-- Body: vertical tabs left + content right -->
    <div class="flex-grow-1 d-flex overflow-hidden">

      <!-- Vertical tab strip -->
      <div class="d-flex flex-column" style="flex-shrink: 0; border-right: 1px solid #dee2e6; background: #f8f9fa;">
        <button
          v-for="tab in tabs" :key="tab.id"
          class="prop-tab-btn"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >{{ tab.label }}</button>
      </div>

      <!-- Content area -->
      <div class="flex-grow-1 overflow-hidden">
        <template v-if="node">

          <!-- Main tab -->
          <div v-if="activeTab === 'main'" class="h-100 d-flex flex-column p-2">
            <div class="prop-row mb-2" style="flex-shrink: 0;">
              <div class="prop-field-label">ID</div>
              <div class="text-muted" style="font-size: 0.7rem; font-family: monospace; padding-top: 5px;">{{ node.id }}</div>
            </div>
            <div class="prop-row mb-2" style="flex-shrink: 0;">
              <div class="prop-field-label">Type</div>
              <div class="text-muted" style="font-size: 0.8rem; padding-top: 5px;">{{ node.element_type || node.type }}</div>
            </div>
            <div class="prop-row mb-2" style="flex-shrink: 0;">
              <div class="prop-field-label">Name</div>
              <input
                class="form-control form-control-sm"
                v-model="editName"
                @blur="saveName"
                @keydown.enter.prevent="saveName"
              />
            </div>
            <div class="prop-row flex-grow-1" style="min-height: 0;">
              <div class="prop-field-label">Documentation</div>
              <textarea
                class="form-control h-100"
                v-model="editDoc"
                @blur="saveDoc"
                style="resize: none; font-size: 14px;"
              ></textarea>
            </div>
          </div>

          <!-- Properties tab -->
          <div v-else-if="activeTab === 'properties'" class="h-100 overflow-auto p-2">
            <table class="w-100" style="font-size: 0.8rem; border-collapse: collapse;">
              <thead>
                <tr style="border-bottom: 1px solid #dee2e6;">
                  <th class="pb-1 pe-1" style="font-weight: 600; color: #6c757d;">Key</th>
                  <th class="pb-1" style="font-weight: 600; color: #6c757d;">Value</th>
                  <th style="width: 18px;"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(prop, i) in editProps" :key="i">
                  <td class="pe-1 py-1" style="width: 40%;">
                    <input class="form-control form-control-sm" v-model="prop.key" @blur="saveProps" />
                  </td>
                  <td class="py-1">
                    <input class="form-control form-control-sm" v-model="prop.value" @blur="saveProps" />
                  </td>
                  <td>
                    <button class="btn btn-link p-0 text-danger" style="font-size: 0.75rem; line-height: 1;" @click="removeProp(i)">
                      <i class="bi bi-x-lg"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <button class="btn btn-link p-0 mt-1 text-secondary" style="font-size: 0.8rem;" @click="addProp">
              <i class="bi bi-plus me-1"></i>Add property
            </button>
          </div>

        </template>
        <div v-else class="d-flex align-items-center justify-content-center h-100">
          <p class="text-muted text-center mb-0" style="font-size: 0.8rem;">
            Select an element to show its properties
          </p>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useModelStore } from '../stores/model'

const emit = defineEmits(['close'])
const store = useModelStore()
const node  = computed(() => store.selected)

const tabs = [
  { id: 'main',       label: 'Main' },
  { id: 'properties', label: 'Properties' },
]
const activeTab = ref('main')

const editName  = ref('')
const editDoc   = ref('')
const editProps = ref([])

watch(node, (n) => {
  activeTab.value = 'main'
  editName.value  = n?.name         ?? ''
  editDoc.value   = n?.documentation ?? ''
  editProps.value = (n?.properties  ?? []).map(p => ({ ...p }))
}, { immediate: true })

function saveName() {
  if (node.value) store.renameNode(node.value.id, editName.value)
}

function saveDoc() {
  if (node.value) store.updateDocumentation(node.value.id, editDoc.value)
}

function saveProps() {
  if (node.value) store.updateProperties(node.value.id, editProps.value.filter(p => p.key))
}

function addProp() {
  editProps.value.push({ key: '', value: '' })
}

function removeProp(i) {
  editProps.value.splice(i, 1)
  saveProps()
}
</script>

<style scoped>
.prop-tab-btn {
  border: none;
  border-bottom: 1px solid #dee2e6;
  background: #f8f9fa;
  padding: 6px 12px;
  font-size: 0.78rem;
  cursor: pointer;
  color: #495057;
  text-align: left;
  white-space: nowrap;
}
.prop-tab-btn.active {
  background: #fff;
  font-weight: 600;
  color: #212529;
  border-right: 2px solid #fff;
  margin-right: -1px;
}
.prop-tab-btn:hover:not(.active) {
  background: #e9ecef;
}
.prop-row {
  display: grid;
  grid-template-columns: 100px 1fr;
  align-items: start;
  gap: 4px;
}
.prop-row.flex-grow-1 {
  align-items: stretch;
}
.prop-field-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  padding-top: 5px;
}
</style>
