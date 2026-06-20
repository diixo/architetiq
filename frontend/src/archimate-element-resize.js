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

export const TAB_H = 18  // GroupFigure.java TOPBAR_HEIGHT = 18

// Matches GroupFigure.java: base = width/2, expand to textWidth+8 if needed, cap at full width
export function groupTabWidth(name, groupWidth) {
  const base = Math.floor(groupWidth / 2)
  const textW = Math.round((name || '').length * 6)
  return Math.min(Math.max(base, textW + 8), groupWidth)
}

/**
 * Compute DiagramGroup attrs for a given size.
 * Pure function — no X6 dependency.
 */
export function computeGroupAttrs(name, w, h) {
  const tabW = groupTabWidth(name, w)
  return {
    tabW,
    bodyFillW:  w,
    bodyFillH:  Math.max(0, h - TAB_H),
    outlineD:   `M 0,${TAB_H} L 0,0 H ${tabW} V ${TAB_H} M 0,${TAB_H} H ${w} V ${h} H 0 Z`,
  }
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
