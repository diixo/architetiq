# ArchiMate Model Tree — Types and Rules

Source: Archi `TreeModelViewActionFactory.java`, `ArchimateModelUtils.java`

---

## Node Types

| `type`    | Description                          | Example                          |
|-----------|--------------------------------------|----------------------------------|
| `model`   | Root of the model                    | `*New Model`, `ASPICE`           |
| `node`    | Folder — groups elements by layer    | `Business`, `Views`, `Strategy`  |
| `element` | ArchiMate concept element            | `BusinessActor`, `Outcome`       |
| `view`    | Diagram / view                       | `Default View`, `Overview - SWE.3` |

---

## Folder Types (`folder_type`)

Each `node` has a `folder_type` that determines which element types can be created inside it.

| `folder_type`             | Folder Name                   | Can Create                                  |
|---------------------------|-------------------------------|---------------------------------------------|
| `strategy`                | Strategy                      | Resource, Capability, ValueStream, CourseOfAction |
| `business`                | Business                      | BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface, BusinessProcess, BusinessFunction, BusinessInteraction, BusinessEvent, BusinessService, BusinessObject, Contract, Representation, Product |
| `application`             | Application                   | ApplicationComponent, ApplicationCollaboration, ApplicationInterface, ApplicationFunction, ApplicationInteraction, ApplicationProcess, ApplicationEvent, ApplicationService, DataObject |
| `technology`              | Technology + Physical         | Node, Device, SystemSoftware, TechnologyCollaboration, TechnologyInterface, Path, CommunicationNetwork, TechnologyFunction, TechnologyProcess, TechnologyInteraction, TechnologyEvent, TechnologyService, Artifact, Equipment, Facility, DistributionNetwork, Material |
| `motivation`              | Motivation                    | Stakeholder, Driver, Assessment, Goal, Outcome, Principle, Requirement, Constraint, Meaning, Value |
| `implementation_migration`| Implementation and Migration  | WorkPackage, Deliverable, ImplementationEvent, Plateau, Gap |
| `other`                   | Other                         | Location, Grouping, Junction |
| `relations`               | Relations                     | *(nothing — relations created by drawing on canvas)* |
| `diagrams`                | Views                         | ArchimateDiagramModel, SketchModel |

> **Note:** Physical layer elements (Equipment, Facility, DistributionNetwork, Material) are stored in the Technology folder — they are NOT a separate folder type in Archi.

---

## Top-Level Folder Restrictions

The 9 standard top-level folders (direct children of the model root) are **protected**:

| Folder | `folder_type` | Can Rename | Can Delete |
|--------|---------------|------------|------------|
| Strategy | `strategy` | ❌ No | ❌ No |
| Business | `business` | ❌ No | ❌ No |
| Application | `application` | ❌ No | ❌ No |
| Technology And Physical | `technology` | ❌ No | ❌ No |
| Motivation | `motivation` | ❌ No | ❌ No |
| Implementation and Migration | `implementation_migration` | ❌ No | ❌ No |
| Other | `other` | ❌ No | ❌ No |
| Relations | `relations` | ❌ No | ❌ No |
| Views | `diagrams` | ❌ No | ❌ No |

Sub-folders created by the user inside these folders CAN be renamed and deleted.

---

## Right-Click Context Menu — "New" Submenu Rules

| Node type | `folder_type` | New submenu shows |
|-----------|---------------|-------------------|
| `node`    | `strategy`    | Folder + Strategy elements |
| `node`    | `business`    | Folder + Business elements |
| `node`    | `application` | Folder + Application elements |
| `node`    | `technology`  | Folder + Technology + Physical elements |
| `node`    | `motivation`  | Folder + Motivation elements |
| `node`    | `implementation_migration` | Folder + Implementation elements |
| `node`    | `other`       | Folder + Location, Grouping, Junction |
| `node`    | `relations`   | Folder only |
| `node`    | `diagrams`    | Folder + ArchiMate View + Sketch View |
| `node`    | *(none)*      | Folder only |
| `view`    | —             | Same as `diagrams` folder (Folder + ArchiMate View + Sketch View). New items are added to the parent DIAGRAMS folder. |
| `element` | —             | **Disabled** — New is greyed out |
| `model`   | —             | **Disabled** — New is greyed out |

---

## ArchiMate Layers and Colors

| Layer | `folder_type` | Fill Color | Hex |
|-------|---------------|------------|-----|
| Strategy | `strategy` | Pale tan | `#f5deaa` |
| Business | `business` | Pale yellow | `#ffffb5` |
| Application | `application` | Pale cyan | `#b5ffff` |
| Technology + Physical | `technology` | Pale green | `#b5ffb5` |
| Motivation | `motivation` | Pale blue-purple | `#ccccff` |
| Implementation & Migration | `implementation_migration` | Pale pink | `#ffe0e0` |
| Other | `other` | White | `#ffffff` |

---

## Element Type Aspects

ArchiMate 3.1 classifies elements by **aspect**:

### Active Structure (actors, components — WHO)
Business: Actor, Role, Collaboration, Interface  
Application: Component, Collaboration, Interface  
Technology: Node, Device, SystemSoftware, Collaboration, Interface, Path, Network  
Physical: Equipment, Facility, DistributionNetwork  

### Behavior (processes, functions — WHAT)
Business: Process, Function, Interaction, Event, Service  
Application: Function, Interaction, Process, Event, Service  
Technology: Function, Process, Interaction, Event, Service  

### Passive Structure (data, objects — WITH WHAT)
Business: Object, Contract, Representation, Product  
Application: DataObject  
Technology: Artifact  
Physical: Material  

---

## Relationship Types

| Type | Direction | Line Style | Arrowhead |
|------|-----------|------------|-----------|
| AssociationRelationship | — | Solid | Open V |
| CompositionRelationship | source→ | Solid | Filled diamond (source) |
| AggregationRelationship | source→ | Solid | Open diamond (source) |
| AssignmentRelationship | source→target | Solid | Circle (source) + Filled triangle |
| RealizationRelationship | →target | Dashed `8 4` | Open triangle |
| ServingRelationship | →target | Solid | Open V |
| AccessRelationship | →target | Dashed `4 3` | Open V |
| InfluenceRelationship | →target | Dashed `8 4` | Open V |
| TriggeringRelationship | →target | Solid | Filled triangle |
| FlowRelationship | →target | Dashed `8 4` | Filled triangle |
| SpecializationRelationship | →target | Solid | Open triangle |
| Junction | — | — | Circle (AND/OR) |

> Relations are **not created via the tree context menu** — they are drawn directly on the canvas by dragging from source to target element.

---

## View / Diagram Types

| `element_type` | Name | Description |
|----------------|------|-------------|
| `ArchimateDiagramModel` | ArchiMate View | Standard ArchiMate diagram |
| `SketchModel` | Sketch View | Freehand sketch view |

---

## Model JSON Structure

```json
{
  "name": "Model Name",
  "type": "model",
  "id": "uuid",
  "children": [
    {
      "name": "Business",
      "type": "node",
      "folder_type": "business",
      "id": "uuid",
      "children": [
        {
          "name": "My Actor",
          "type": "element",
          "element_type": "BusinessActor",
          "id": "uuid",
          "documentation": "...",
          "children": []
        }
      ]
    },
    {
      "name": "Views",
      "type": "node",
      "folder_type": "diagrams",
      "id": "uuid",
      "children": [
        {
          "name": "Default View",
          "type": "view",
          "element_type": "ArchimateDiagramModel",
          "id": "uuid",
          "documentation": "",
          "children": []
        }
      ]
    }
  ]
}
```
