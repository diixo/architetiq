import { describe, it, expect } from 'vitest'
import { computeElementAttrs, computeGroupAttrs, groupTabWidth, TAB_H } from './archimate-element-resize.js'

const ICON_SIZE = 13

describe('computeElementAttrs — icon position', () => {
  it('places icon at right edge for standard element with icon', () => {
    const { iconX, iconY } = computeElementAttrs('BusinessActor', 120, 55)
    expect(iconX).toBe(120 - ICON_SIZE - 2)  // 105
    expect(iconY).toBe(2)
  })

  it('icon x tracks width when element is resized wider', () => {
    const { iconX } = computeElementAttrs('BusinessActor', 200, 55)
    expect(iconX).toBe(200 - ICON_SIZE - 2)  // 185
  })

  it('icon x tracks width when element is resized narrower', () => {
    const { iconX } = computeElementAttrs('BusinessActor', 80, 55)
    expect(iconX).toBe(80 - ICON_SIZE - 2)   // 65
  })

  it('passive shape: iconY = foldOffset + 2', () => {
    const w = 120, h = 55
    const expectedFold = Math.min(w * 0.18, h * 0.28, 12)  // 12
    const { iconY, foldOffset } = computeElementAttrs('BusinessObject', w, h)
    expect(foldOffset).toBe(expectedFold)
    expect(iconY).toBe(foldOffset + 2)
  })

  it('passive foldOffset capped at 12 for large elements', () => {
    const { foldOffset } = computeElementAttrs('Artifact', 300, 200)
    expect(foldOffset).toBe(12)
  })

  it('passive foldOffset scales with small elements', () => {
    const w = 50, h = 40
    const { foldOffset } = computeElementAttrs('Artifact', w, h)
    expect(foldOffset).toBe(Math.min(w * 0.18, h * 0.28, 12))
  })
})

describe('computeElementAttrs — label textWrap', () => {
  it('textWrap reserves space for icon when icon present', () => {
    const { textWrapW } = computeElementAttrs('BusinessActor', 120, 55)
    expect(textWrapW).toBe(120 - ICON_SIZE - 6)  // 101
  })

  it('textWrap uses full width (minus padding) when no icon', () => {
    const { textWrapW, iconId } = computeElementAttrs('DiagramGroup', 120, 55)
    expect(iconId).toBeNull()
    expect(textWrapW).toBe(120 - 8)  // 112
  })

  it('textWrapH = h - 8', () => {
    const { textWrapH } = computeElementAttrs('Node', 120, 80)
    expect(textWrapH).toBe(72)
  })

  it('textWrap width updates when resized', () => {
    const { textWrapW: w1 } = computeElementAttrs('Node', 120, 55)
    const { textWrapW: w2 } = computeElementAttrs('Node', 200, 55)
    expect(w2 - w1).toBe(80)
  })
})

describe('computeGroupAttrs — tab_fill width on resize', () => {
  it('tabW = half of groupWidth when name is short', () => {
    const { tabW } = computeGroupAttrs('G', 400, 140)
    expect(tabW).toBe(Math.floor(400 / 2))  // 200 — base wins over short name
  })

  it('tabW grows with long name but caps at groupWidth', () => {
    const longName = 'A very long group name here'
    const { tabW } = computeGroupAttrs(longName, 400, 140)
    const textW = Math.round(longName.length * 6)
    expect(tabW).toBe(Math.min(Math.max(200, textW + 8), 400))
  })

  it('tabW caps at groupWidth so tab never overflows', () => {
    const { tabW } = computeGroupAttrs('X'.repeat(100), 400, 140)
    expect(tabW).toBe(400)
  })

  it('tabW tracks new width after resize', () => {
    const { tabW: tabW1 } = computeGroupAttrs('Group', 400, 140)
    const { tabW: tabW2 } = computeGroupAttrs('Group', 200, 140)
    expect(tabW2).toBeLessThan(tabW1)
    expect(tabW2).toBe(Math.floor(200 / 2))  // 100
  })

  it('bodyFillH = h - TAB_H', () => {
    const { bodyFillH } = computeGroupAttrs('Group', 400, 140)
    expect(bodyFillH).toBe(140 - TAB_H)
  })

  it('bodyFillH never goes below 0', () => {
    const { bodyFillH } = computeGroupAttrs('Group', 400, TAB_H - 5)
    expect(bodyFillH).toBe(0)
  })

  it('outlineD contains new width and height', () => {
    const w = 300, h = 100
    const { outlineD } = computeGroupAttrs('Group', w, h)
    expect(outlineD).toContain(`H ${w}`)
    expect(outlineD).toContain(`V ${h}`)
  })
})

describe('computeElementAttrs — element without icon', () => {
  it('returns iconX=0, iconY=0 for element without icon', () => {
    const { iconX, iconY, iconId } = computeElementAttrs('DiagramGroup', 120, 55)
    expect(iconId).toBeNull()
    expect(iconX).toBe(0)
    expect(iconY).toBe(0)
  })
})
