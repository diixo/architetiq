<template>
  <div class="palette-panel" :class="{ 'palette-collapsed': collapsed }">

    <!-- Toggle button -->
    <button class="palette-toggle" @click="collapsed = !collapsed" :title="collapsed ? 'Show palette' : 'Hide palette'">
      <i :class="collapsed ? 'bi bi-chevron-left' : 'bi bi-chevron-right'"></i>
    </button>

    <div v-if="!collapsed" class="palette-content">

      <!-- ── Tools ─────────────────────────────────────────── -->
      <div class="palette-section-title">Tools</div>

      <div class="palette-tool" :class="{ active: activeTool === 'select' }" @click="setTool('select')">
        <i class="bi bi-cursor me-1"></i> Select
      </div>

      <!-- Connection type picker -->
      <div class="palette-section-title mt-2">Connection</div>
      <select
        v-model="selectedRelType"
        class="form-select form-select-sm palette-rel-select"
        @change="setTool('connect')"
      >
        <option v-for="rel in REL_TYPES" :key="rel.type" :value="rel.type">
          {{ rel.label }}
        </option>
      </select>

      <div class="palette-divider"></div>

      <!-- ── Element layers ────────────────────────────────── -->
      <div v-for="layer in LAYERS" :key="layer.folder_type" class="palette-layer">
        <div
          class="palette-section-title palette-layer-title"
          @click="layer.open = !layer.open"
          style="cursor:pointer;"
        >
          <i :class="layer.open ? 'bi bi-chevron-down' : 'bi bi-chevron-right'"
             style="font-size:0.6rem; margin-right:3px;"></i>
          {{ layer.label }}
        </div>
        <div v-if="layer.open">
          <div
            v-for="et in layer.types"
            :key="et"
            class="palette-item"
            draggable="true"
            @dragstart="onDragStart($event, et, layer.folder_type)"
          >
            <!-- Coloured mini-icon matching Archi's element colours + our SVG symbols -->
            <svg class="palette-type-icon" viewBox="0 0 20 20" width="18" height="18">
              <rect width="20" height="20" rx="2"
                    :fill="nodeColor(et)" stroke="#999" stroke-width="0.8"/>
              <use v-if="ELEMENT_ICON[et]"
                   :href="`#${ELEMENT_ICON[et]}`"
                   x="4" y="4" width="12" height="12"/>
            </svg>
            {{ humanizeType(et) }}
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { humanizeType } from '../archimate-folder-elements.js'
import { ELEMENT_ICON } from '../archimate-icons.js'
import { nodeColor } from '../archimate-styles.js'

const emit = defineEmits(['connection-type-changed'])

const collapsed      = ref(false)
const activeTool     = ref('select')
const selectedRelType = ref('AssociationRelationship')

const REL_TYPES = [
  { type: 'AssociationRelationship',    label: 'Association' },
  { type: 'RealizationRelationship',    label: 'Realization' },
  { type: 'ServingRelationship',        label: 'Serving' },
  { type: 'AccessRelationship',         label: 'Access' },
  { type: 'InfluenceRelationship',      label: 'Influence' },
  { type: 'TriggeringRelationship',     label: 'Triggering' },
  { type: 'FlowRelationship',           label: 'Flow' },
  { type: 'CompositionRelationship',    label: 'Composition' },
  { type: 'AggregationRelationship',    label: 'Aggregation' },
  { type: 'AssignmentRelationship',     label: 'Assignment' },
  { type: 'SpecializationRelationship', label: 'Specialization' },
]

const LAYERS = reactive([
  { folder_type: 'strategy',    label: 'Strategy',    open: false, types: ['Resource','Capability','ValueStream','CourseOfAction'] },
  { folder_type: 'business',    label: 'Business',    open: true,  types: ['BusinessActor','BusinessRole','BusinessProcess','BusinessFunction','BusinessService','BusinessEvent','BusinessObject','BusinessCollaboration','BusinessInterface','BusinessInteraction','Contract','Representation','Product'] },
  { folder_type: 'application', label: 'Application', open: false, types: ['ApplicationComponent','ApplicationCollaboration','ApplicationInterface','ApplicationFunction','ApplicationProcess','ApplicationInteraction','ApplicationEvent','ApplicationService','DataObject'] },
  { folder_type: 'technology',  label: 'Technology',  open: false, types: ['Node','Device','SystemSoftware','TechnologyCollaboration','TechnologyInterface','Path','CommunicationNetwork','TechnologyFunction','TechnologyProcess','TechnologyInteraction','TechnologyEvent','TechnologyService','Artifact','Equipment','Facility','DistributionNetwork','Material'] },
  { folder_type: 'motivation',  label: 'Motivation',  open: false, types: ['Stakeholder','Driver','Assessment','Goal','Outcome','Principle','Requirement','Constraint','Meaning','Value'] },
  { folder_type: 'implementation_migration', label: 'Implementation', open: false, types: ['WorkPackage','Deliverable','ImplementationEvent','Plateau','Gap'] },
  { folder_type: 'other',       label: 'Other',       open: false, types: ['Location','Grouping'] },
])

function setTool(tool) {
  activeTool.value = tool
  emit('connection-type-changed', tool === 'connect' ? selectedRelType.value : null)
}

function onDragStart(e, elementType, folderType) {
  e.dataTransfer.setData('application/archimate-element', JSON.stringify({ elementType, folderType }))
  e.dataTransfer.effectAllowed = 'copy'
}

defineExpose({ selectedRelType, activeTool })
</script>
