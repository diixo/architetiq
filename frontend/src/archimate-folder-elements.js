// Maps folder_type → list of ArchiMate element types that can be created there
// Source: Archi TreeModelViewActionFactory.java
// Source: Archi TreeModelViewActionFactory.java
export const FOLDER_ELEMENTS = {
  strategy: [
    'Resource', 'Capability', 'ValueStream', 'CourseOfAction',
  ],
  business: [
    'BusinessActor', 'BusinessRole', 'BusinessCollaboration', 'BusinessInterface',
    'BusinessProcess', 'BusinessFunction', 'BusinessInteraction', 'BusinessEvent',
    'BusinessService', 'BusinessObject', 'Contract', 'Representation', 'Product',
  ],
  application: [
    'ApplicationComponent', 'ApplicationCollaboration', 'ApplicationInterface',
    'ApplicationFunction', 'ApplicationInteraction', 'ApplicationProcess',
    'ApplicationEvent', 'ApplicationService', 'DataObject',
  ],
  // Physical is merged into Technology (per Archi source)
  technology: [
    'Node', 'Device', 'SystemSoftware', 'TechnologyCollaboration', 'TechnologyInterface',
    'Path', 'CommunicationNetwork', 'TechnologyFunction', 'TechnologyProcess',
    'TechnologyInteraction', 'TechnologyEvent', 'TechnologyService', 'Artifact',
    'Equipment', 'Facility', 'DistributionNetwork', 'Material',
  ],
  motivation: [
    'Stakeholder', 'Driver', 'Assessment', 'Goal', 'Outcome',
    'Principle', 'Requirement', 'Constraint', 'Meaning', 'Value',
  ],
  implementation_migration: [
    'WorkPackage', 'Deliverable', 'ImplementationEvent', 'Plateau', 'Gap',
  ],
  other: [
    'Location', 'Grouping', 'Junction', 'Note', 'DiagramGroup',
  ],
  // Relations are created by drawing on canvas, not via New menu
  relations: [],
  // Diagrams: ArchimateDiagramModel and SketchModel
  diagrams: ['ArchimateDiagramModel', 'SketchModel'],
}

// Human-readable name from CamelCase type
export function humanizeType(type) {
  return type.replace(/([A-Z])/g, ' $1').trim()
}
