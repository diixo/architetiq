import { ELEMENT_ICON } from './archimate-icons.js'

const ICON_SIZE = 13

const SHAPE_TYPE = {
  BusinessObject:'passive', DataObject:'passive', Artifact:'passive',
  Contract:'passive', Representation:'passive', Material:'passive',
  Note: 'note',
  BusinessProcess:'rounded', ApplicationProcess:'rounded', TechnologyProcess:'rounded',
  BusinessService:'rounded', ApplicationService:'rounded', TechnologyService:'rounded',
  BusinessFunction:'rounded', ApplicationFunction:'rounded', TechnologyFunction:'rounded',
  BusinessInteraction:'rounded', ApplicationInteraction:'rounded', TechnologyInteraction:'rounded',
  BusinessEvent:'rounded', ApplicationEvent:'rounded', TechnologyEvent:'rounded', ImplementationEvent:'rounded',
  WorkPackage:'rounded', Capability:'rounded', CourseOfAction:'rounded', ValueStream:'rounded',
}

/**
 * Compute element body + icon + label attrs for a given size.
 * Pure function — no X6 dependency.
 */
export function computeElementAttrs(elementType, w, h) {
  const iconId     = ELEMENT_ICON[elementType] ?? null
  const shape      = SHAPE_TYPE[elementType] || 'rect'
  const foldOffset = (shape === 'passive') ? Math.min(w * 0.18, h * 0.28, 12) : 0

  return {
    iconX:       iconId ? w - ICON_SIZE - 2 : 0,
    iconY:       iconId ? foldOffset + 2    : 0,
    textWrapW:   w - (iconId ? ICON_SIZE + 6 : 8),
    textWrapH:   h - 8,
    foldOffset,
    shape,
    iconId,
  }
}
