// Maps ArchiMate element type → SVG symbol id
export const ELEMENT_ICON = {
  // Business — active structure
  BusinessActor:         'am-actor',
  BusinessRole:          'am-role',
  BusinessCollaboration: 'am-collab',
  BusinessInterface:     'am-interface',
  // Business — behavior
  BusinessProcess:       'am-process',
  BusinessFunction:      'am-function',
  BusinessInteraction:   'am-interaction',
  BusinessEvent:         'am-event',
  BusinessService:       'am-service',
  // Business — passive
  BusinessObject:        'am-object',
  Contract:              'am-contract',
  Representation:        'am-representation',
  Product:               'am-product',
  // Application — active
  ApplicationComponent:    'am-component',
  ApplicationCollaboration:'am-collab',
  ApplicationInterface:    'am-interface',
  // Application — behavior
  ApplicationFunction:    'am-function',
  ApplicationInteraction: 'am-interaction',
  ApplicationProcess:     'am-process',
  ApplicationEvent:       'am-event',
  ApplicationService:     'am-service',
  // Application — passive
  DataObject:             'am-object',
  // Technology — active
  Node:                   'am-node',
  Device:                 'am-device',
  SystemSoftware:         'am-systemsoftware',
  TechnologyCollaboration:'am-collab',
  TechnologyInterface:    'am-interface',
  CommunicationNetwork:   'am-network',
  Path:                   'am-path',
  // Technology — behavior
  TechnologyFunction:    'am-function',
  TechnologyInteraction: 'am-interaction',
  TechnologyProcess:     'am-process',
  TechnologyEvent:       'am-event',
  TechnologyService:     'am-service',
  // Technology — passive
  Artifact:     'am-artifact',
  Equipment:    'am-equipment',
  Facility:     'am-facility',
  Material:     'am-material',
  // Motivation
  Stakeholder:  'am-stakeholder',
  Driver:       'am-driver',
  Assessment:   'am-assessment',
  Goal:         'am-goal',
  Outcome:      'am-outcome',
  Principle:    'am-principle',
  Requirement:  'am-requirement',
  Constraint:   'am-constraint',
  Meaning:      'am-meaning',
  Value:        'am-value',
  // Implementation & Migration
  WorkPackage:         'am-workpackage',
  Deliverable:         'am-deliverable',
  ImplementationEvent: 'am-event',
  Plateau:             'am-plateau',
  Gap:                 'am-gap',
  // Strategy
  Resource:       'am-resource',
  Capability:     'am-capability',
  CourseOfAction: 'am-courseofaction',
  ValueStream:    'am-valuestream',
  // Other
  Location:       'am-location',
  Grouping:       'am-grouping',
  // Physical
  DistributionNetwork: 'am-distribution-network',
  // Relations (shown in palette — reuse marker-like icons)
  AssociationRelationship:    'am-path',
  CompositionRelationship:    'am-fill-dia',
  AggregationRelationship:    'am-open-dia',
  AssignmentRelationship:     'am-circle',
  RealizationRelationship:    'am-open-tri',
  ServingRelationship:        'am-open-v',
  AccessRelationship:         'am-open-v',
  InfluenceRelationship:      'am-open-v',
  TriggeringRelationship:     'am-fill-tri',
  FlowRelationship:           'am-fill-tri',
  SpecializationRelationship: 'am-open-tri',
  Junction:                   'am-junction',
  // View extras
  Note:           'am-meaning',
  // DiagramGroup has no corner icon in Archi (uses image icon system)
}
