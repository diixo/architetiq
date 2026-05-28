// ArchiMate layer colours — matches Archi's AbstractArchimateElementUIProvider defaults
export const LAYER_COLOR = {
  // Business (pale yellow  #ffffb5)
  BusinessActor:'#ffffb5', BusinessRole:'#ffffb5', BusinessCollaboration:'#ffffb5',
  BusinessInterface:'#ffffb5', BusinessFunction:'#ffffb5', BusinessProcess:'#ffffb5',
  BusinessInteraction:'#ffffb5', BusinessEvent:'#ffffb5', BusinessService:'#ffffb5',
  BusinessObject:'#ffffb5', Contract:'#ffffb5', Representation:'#ffffb5', Product:'#ffffb5',
  // Application (pale cyan  #b5ffff)
  ApplicationComponent:'#b5ffff', ApplicationCollaboration:'#b5ffff',
  ApplicationInterface:'#b5ffff', ApplicationFunction:'#b5ffff',
  ApplicationInteraction:'#b5ffff', ApplicationProcess:'#b5ffff',
  ApplicationEvent:'#b5ffff', ApplicationService:'#b5ffff', DataObject:'#b5ffff',
  // Technology (pale green  #b5ffb5)
  Node:'#b5ffb5', Device:'#b5ffb5', SystemSoftware:'#b5ffb5',
  TechnologyCollaboration:'#b5ffb5', TechnologyInterface:'#b5ffb5',
  TechnologyFunction:'#b5ffb5', TechnologyInteraction:'#b5ffb5',
  TechnologyProcess:'#b5ffb5', TechnologyEvent:'#b5ffb5',
  TechnologyService:'#b5ffb5', Artifact:'#b5ffb5',
  CommunicationNetwork:'#b5ffb5', Path:'#b5ffb5',
  Equipment:'#b5ffb5', Facility:'#b5ffb5', Material:'#b5ffb5',
  // Motivation (pale blue-purple  #ccccff)
  Stakeholder:'#ccccff', Driver:'#ccccff', Assessment:'#ccccff',
  Goal:'#ccccff', Outcome:'#ccccff', Principle:'#ccccff',
  Requirement:'#ccccff', Constraint:'#ccccff', Meaning:'#ccccff', Value:'#ccccff',
  // Implementation & Migration (pale pink  #ffe0e0)
  WorkPackage:'#ffe0e0', Deliverable:'#ffe0e0', ImplementationEvent:'#ffe0e0',
  Plateau:'#ffe0e0', Gap:'#ffe0e0',
  // Strategy (pale tan  #f5deaa)
  Resource:'#f5deaa', Capability:'#f5deaa', CourseOfAction:'#f5deaa', ValueStream:'#f5deaa',
  // Other
  Location:'#ffffff', Grouping:'#ffffff',
  // Physical
  DistributionNetwork:'#b5ffb5',
  // Relations (light gray background)
  AssociationRelationship:'#f8f9fa', CompositionRelationship:'#f8f9fa',
  AggregationRelationship:'#f8f9fa', AssignmentRelationship:'#f8f9fa',
  RealizationRelationship:'#f8f9fa', ServingRelationship:'#f8f9fa',
  AccessRelationship:'#f8f9fa', InfluenceRelationship:'#f8f9fa',
  TriggeringRelationship:'#f8f9fa', FlowRelationship:'#f8f9fa',
  SpecializationRelationship:'#f8f9fa', Junction:'#f8f9fa',
  // View extras
  Note:'#fffde7', DiagramGroup:'#e3f2fd',
}

export function nodeColor(elementType) {
  return LAYER_COLOR[elementType] || '#ffffff'
}
