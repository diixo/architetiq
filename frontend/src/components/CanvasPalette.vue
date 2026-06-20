<template>
  <div class="palette-panel" :class="{ 'palette-collapsed': collapsed }">

    <!-- Toggle button -->
    <button class="palette-toggle" @click="collapsed = !collapsed" :title="collapsed ? 'Show palette' : 'Hide palette'">
      <i :class="collapsed ? 'bi bi-chevron-left' : 'bi bi-chevron-right'"></i>
    </button>

    <div v-if="!collapsed" class="palette-content">
      <!-- Pointer / normal mode button -->
      <div class="palette-pointer-row">
        <div
          class="palette-type-icon palette-icon-relation"
          :class="{ 'palette-icon-active': !store.activePaletteItem }"
          title="Select (normal mode)"
          @click="store.resetPaletteSelection()"
        >
          <i class="fa-solid fa-arrow-pointer" style="font-size:13px; color:#495057;"></i>
        </div>
      </div>
      <div class="palette-divider"></div>

      <!-- ── Element layers — 3 icons per row, no labels ─── -->
      <template v-for="(layer, idx) in LAYERS" :key="layer.folder_type">
        <div class="palette-divider" v-if="idx > 0"></div>
        <div class="palette-grid">
          <div
            v-for="et in layer.types"
            :key="et"
            class="palette-type-icon"
            :class="{
              'palette-icon-relation': true,
              'palette-icon-active': store.activePaletteItem?.value === et,
            }"
            :draggable="!layer.isRelations && !layer.connTypes?.has(et)"
            :title="humanizeType(et)"
            @click="store.selectPaletteItem((layer.isRelations || layer.connTypes?.has(et)) ? 'conn' : 'elem', et)"
            @dragstart="!layer.isRelations && !layer.connTypes?.has(et) && onDragStart($event, et, layer.folder_type)"
          >
            <img
              v-if="PALETTE_ICON[et]"
              :src="PALETTE_ICON[et]"
              width="16" height="16"
              :alt="humanizeType(et)"
              draggable="false"
            />
            <span v-else style="font-size:0.5rem;color:#999;">?</span>
          </div>
        </div>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { humanizeType } from '../archimate-folder-elements.js'
import { nodeColor } from '../archimate-styles.js'
import { PALETTE_ICON } from '../archimate-palette-icons.js'
import { useModelStore } from '../stores/model'

const store = useModelStore()

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

// Special relation types for the Relations group
const REL_TYPES_PALETTE = [
  'AssociationRelationship','CompositionRelationship','AggregationRelationship',
  'AssignmentRelationship','RealizationRelationship','ServingRelationship',
  'AccessRelationship','InfluenceRelationship','TriggeringRelationship',
  'FlowRelationship','SpecializationRelationship','Junction',
]

const LAYERS = reactive([
  // 1. Relations
  { folder_type: 'relations', label: 'Relations',       open: true, types: REL_TYPES_PALETTE, isRelations: true },
  // 2. View extras
  { folder_type: 'diagrams',  label: 'View',            open: true, types: ['Note','Connection'], connTypes: new Set(['Connection']) },
  // 3–10. ArchiMate layers
  { folder_type: 'other',       label: 'Other',         open: true, types: ['Location','Grouping','DiagramGroup'] },
  { folder_type: 'strategy',    label: 'Strategy',      open: true, types: ['Resource','Capability','ValueStream','CourseOfAction'] },
  { folder_type: 'business',    label: 'Business',      open: true, types: ['BusinessActor','BusinessRole','BusinessCollaboration','BusinessInterface','BusinessProcess','BusinessFunction','BusinessInteraction','BusinessEvent','BusinessService','BusinessObject','Contract','Representation','Product'] },
  { folder_type: 'application', label: 'Application',   open: true, types: ['ApplicationComponent','ApplicationCollaboration','ApplicationInterface','ApplicationFunction','ApplicationInteraction','ApplicationProcess','ApplicationEvent','ApplicationService','DataObject'] },
  { folder_type: 'technology',  label: 'Technology',    open: true, types: ['Node','Device','SystemSoftware','TechnologyCollaboration','TechnologyInterface','Path','CommunicationNetwork','TechnologyFunction','TechnologyProcess','TechnologyInteraction','TechnologyEvent','TechnologyService','Artifact'] },
  { folder_type: 'technology',  label: 'Physical',      open: true, types: ['Equipment','Facility','DistributionNetwork','Material'] },
  { folder_type: 'motivation',  label: 'Motivation',    open: true, types: ['Stakeholder','Driver','Assessment','Goal','Outcome','Principle','Requirement','Constraint','Meaning','Value'] },
  { folder_type: 'implementation_migration', label: 'Implementation', open: true, types: ['WorkPackage','Deliverable','ImplementationEvent','Plateau','Gap'] },
])

function setTool(tool) {
  activeTool.value = tool
  emit('connection-type-changed', tool === 'connect' ? selectedRelType.value : null)
}

const TREE_FOLDER_OVERRIDE = { Note: 'other' }

function onDragStart(e, elementType, folderType) {
  const treeFolderType = TREE_FOLDER_OVERRIDE[elementType] ?? folderType
  e.dataTransfer.setData('application/archimate-element', JSON.stringify({ elementType, folderType: treeFolderType }))
  e.dataTransfer.effectAllowed = 'copy'
}

defineExpose({ selectedRelType, activeTool })
</script>
