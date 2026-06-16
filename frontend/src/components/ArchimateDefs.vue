<template>
  <!-- Hidden SVG: ArchiMate 3.1 notation symbols, 16×16 viewport -->
  <svg width="0" height="0" style="position:absolute;overflow:hidden;">
    <defs>

      <!-- ── Behavior ─────────────────────────────────────────────────────── -->

      <!-- Process: right-pointing horizontal arrow (from Archi ProcessFigure.java) -->
      <symbol id="am-process" viewBox="0 0 16 16">
        <polygon points="1,5 10,5 10,2 15,8 10,14 10,11 1,11" fill="#555"/>
      </symbol>

      <!-- Function: upward-pointing hex with inner notch (from Archi FunctionFigure.java)
           Java coords: (0,0),(0,-9),(6,-14),(12,-9),(12,0),(6,-6) → mapped to 16×16 -->
      <symbol id="am-function" viewBox="0 0 16 16">
        <polygon points="2,15 2,6 8,1 14,6 14,15 8,9" fill="#555"/>
      </symbol>

      <!-- Service: rounded rect (half-oval, from Archi ServiceFigure.java) -->
      <symbol id="am-service" viewBox="0 0 16 16">
        <rect x="1" y="1" width="14" height="9" rx="4.5" ry="4.5" fill="#555"/>
      </symbol>

      <!-- Event: concave left + convex right (from Archi EventFigure iconDelegate) -->
      <symbol id="am-event" viewBox="0 0 16 16">
        <path d="M2,2 Q6,8 2,14 H12 Q16,8 12,2 Z" fill="#555"/>
      </symbol>

      <!-- Interaction: two D-shapes facing outward — () (from Archi InteractionFigure iconDelegate) -->
      <symbol id="am-interaction" viewBox="0 0 16 16">
        <path d="M7,1 A6,7 0 0 0 7,15 Z" fill="#555"/>
        <path d="M9,1 A6,7 0 0 1 9,15 Z" fill="#555"/>
      </symbol>

      <!-- ── Active Structure ────────────────────────────────────────────── -->

      <!-- Actor: stick figure — head + body + arms + legs (from Archi BusinessActorFigure.java) -->
      <symbol id="am-actor" viewBox="0 0 16 16">
        <circle cx="8" cy="3" r="2.5" fill="#555"/>
        <line x1="8" y1="5.5" x2="8"  y2="11"  stroke="#555" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="3" y1="8"   x2="13" y2="8"   stroke="#555" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="8" y1="11"  x2="4"  y2="15.5" stroke="#555" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="8" y1="11"  x2="12" y2="15.5" stroke="#555" stroke-width="1.5" stroke-linecap="round"/>
      </symbol>

      <!-- Role: scroll shape — left half-ellipse + two lines + right oval cap (from Archi BusinessRoleFigure.java) -->
      <symbol id="am-role" viewBox="0 0 16 16">
        <path d="M4,2 a3,6 0 0 0 0,12"
              fill="none" stroke="#555" stroke-width="2" stroke-linecap="round"/>
        <line x1="4"  y1="2"  x2="12" y2="2"  stroke="#555" stroke-width="2"/>
        <line x1="4"  y1="14" x2="12" y2="14" stroke="#555" stroke-width="2"/>
        <ellipse cx="12" cy="8" rx="3" ry="6" fill="none" stroke="#555" stroke-width="2"/>
      </symbol>

      <!-- Collaboration: two overlapping circles (filled) -->
      <symbol id="am-collab" viewBox="0 0 16 16">
        <circle cx="5"  cy="8" r="4.5" fill="#555" opacity="0.65"/>
        <circle cx="11" cy="8" r="4.5" fill="#555" opacity="0.65"/>
      </symbol>

      <!-- Interface: horizontal lollipop — stem + circle (from Archi InterfaceFigure.java) -->
      <symbol id="am-interface" viewBox="0 0 16 16">
        <rect   x="0" y="7" width="7" height="2" fill="#555"/>
        <circle cx="12" cy="8" r="4" fill="#555"/>
      </symbol>

      <!-- ── Passive Structure ───────────────────────────────────────────── -->

      <!-- Contract: rectangle with two horizontal dividers (3 bands, from Archi ContractFigure.java) -->
      <symbol id="am-contract" viewBox="0 0 16 16">
        <rect x="1" y="2" width="14" height="12" fill="none" stroke="#555" stroke-width="1.5"/>
        <line x1="1" y1="6"  x2="15" y2="6"  stroke="#555" stroke-width="1.5"/>
        <line x1="1" y1="10" x2="15" y2="10" stroke="#555" stroke-width="1.5"/>
      </symbol>

      <!-- Representation: wavy-bottom rectangle + top divider line (from Archi RepresentationFigure.java) -->
      <symbol id="am-representation" viewBox="0 0 16 16">
        <path d="M0,0 H16 V11 Q13.5,14 11,11.5 Q8.5,9 6,11.5 Q3,14 0,11.5 Z"
              fill="none" stroke="#555" stroke-width="1.5"/>
        <line x1="0" y1="4" x2="16" y2="4" stroke="#555" stroke-width="1.5"/>
      </symbol>

      <!-- Object / DataObject / BusinessObject: rectangle with header divider at 1/3 (from Archi *ObjectFigure.java) -->
      <symbol id="am-object" viewBox="0 0 16 16">
        <rect x="1" y="2" width="14" height="12" fill="none" stroke="#555" stroke-width="1.5"/>
        <line x1="1" y1="6" x2="15" y2="6" stroke="#555" stroke-width="1.5"/>
      </symbol>

      <!-- Product: rectangle with tag notch -->
      <symbol id="am-product" viewBox="0 0 16 16">
        <rect x="0" y="2" width="13" height="12" rx="1" fill="#999"/>
        <path d="M13,5 l3,3 l-3,3" fill="#999"/>
      </symbol>

      <!-- Artifact: page with dog-ear fold top-right (from Archi ArtifactFigure.java) -->
      <symbol id="am-artifact" viewBox="0 0 16 16">
        <path d="M2,0.5 L9,0.5 L14,5.5 L14,15.5 L2,15.5 Z" fill="#555"/>
        <path d="M9,0.5 L9,5.5 L14,5.5" fill="none" stroke="#888" stroke-width="1"/>
      </symbol>

      <!-- ── Application ────────────────────────────────────────────────── -->

      <!-- Component: rectangle with two plug-like protrusions on left -->
      <symbol id="am-component" viewBox="0 0 16 16">
        <rect x="4" y="0" width="12" height="16" rx="1" fill="#555"/>
        <rect x="0" y="3"   width="7" height="3.5" rx="0.5" fill="#888"/>
        <rect x="0" y="9.5" width="7" height="3.5" rx="0.5" fill="#888"/>
      </symbol>

      <!-- ── Technology ─────────────────────────────────────────────────── -->

      <!-- Node: 3D cube -->
      <symbol id="am-node" viewBox="0 0 16 16">
        <polygon points="0,5 4,1 16,1 16,13 12,16 0,16" fill="#555"/>
        <polygon points="0,5 4,1 16,1 12,5"              fill="#777"/>
        <polygon points="12,5 16,1 16,13 12,16"          fill="#444"/>
        <polygon points="0,5 12,5 12,16 0,16"            fill="#666"/>
      </symbol>

      <!-- Device: monitor screen (rounded rect) + trapezoidal stand (from Archi DeviceFigure.java) -->
      <symbol id="am-device" viewBox="0 0 16 16">
        <rect x="2" y="1" width="12" height="8.5" rx="2" ry="2" fill="#555"/>
        <polygon points="1.5,15 4.5,9.5 11.5,9.5 14.5,15" fill="#555"/>
      </symbol>

      <!-- SystemSoftware: two diagonally offset filled circles (from Archi SystemSoftwareFigure.java) -->
      <symbol id="am-systemsoftware" viewBox="0 0 16 16">
        <circle cx="6"  cy="10" r="5" fill="#555" opacity="0.65"/>
        <circle cx="10" cy="6"  r="5" fill="#555" opacity="0.65"/>
      </symbol>

      <!-- Network: four nodes in diamond + connecting lines (from Archi CommunicationNetworkFigure.java) -->
      <symbol id="am-network" viewBox="0 0 16 16">
        <circle cx="8"    cy="1.5"  r="2" fill="#555"/>
        <circle cx="14.5" cy="8"    r="2" fill="#555"/>
        <circle cx="8"    cy="14.5" r="2" fill="#555"/>
        <circle cx="1.5"  cy="8"    r="2" fill="#555"/>
        <line x1="8"    y1="3.5"  x2="12.5" y2="6.1"  stroke="#555" stroke-width="1.2"/>
        <line x1="12.5" y1="9.9"  x2="8"    y2="12.5" stroke="#555" stroke-width="1.2"/>
        <line x1="3.5"  y1="9.9"  x2="8"    y2="12.5" stroke="#555" stroke-width="1.2"/>
        <line x1="8"    y1="3.5"  x2="3.5"  y2="6.1"  stroke="#555" stroke-width="1.2"/>
      </symbol>

      <!-- Path: left/right chevrons + dashed middle (from Archi PathFigure iconDelegate) -->
      <symbol id="am-path" viewBox="0 0 16 16">
        <polyline points="5,3 1,8 5,13"  fill="none" stroke="#555" stroke-width="1.5" stroke-linejoin="round"/>
        <line x1="6"  y1="8" x2="7.5" y2="8" stroke="#555" stroke-width="1.5"/>
        <line x1="8.5" y1="8" x2="10" y2="8" stroke="#555" stroke-width="1.5"/>
        <polyline points="11,3 15,8 11,13" fill="none" stroke="#555" stroke-width="1.5" stroke-linejoin="round"/>
      </symbol>

      <!-- Equipment: gear -->
      <symbol id="am-equipment" viewBox="0 0 16 16">
        <path d="M6,0 h4 l1,2.5 a5,5 0 0 1 2,2 l2.5,1 v4 l-2.5,1
                 a5,5 0 0 1-2,2 l-1,2.5 h-4 l-1,-2.5 a5,5 0 0 1-2,-2
                 l-2.5,-1 v-4 l2.5,-1 a5,5 0 0 1 2,-2 Z" fill="#555"/>
        <circle cx="8" cy="8" r="3" fill="white"/>
      </symbol>

      <!-- Facility: building/house -->
      <symbol id="am-facility" viewBox="0 0 16 16">
        <path d="M2,16 V7 L8,1 L14,7 V16 Z" fill="#555"/>
        <rect x="5" y="10" width="2.5" height="6" fill="white" opacity="0.4"/>
        <rect x="8.5" y="10" width="2.5" height="6" fill="white" opacity="0.4"/>
        <rect x="5.5" y="6.5" width="2" height="2" fill="white" opacity="0.4"/>
        <rect x="8.5" y="6.5" width="2" height="2" fill="white" opacity="0.4"/>
      </symbol>

      <!-- Material: flat-top hexagon with 3 faces (from Archi MaterialFigure.java) -->
      <symbol id="am-material" viewBox="0 0 16 16">
        <polygon points="4,1 12,1 8,8 0,8"   fill="#aaa"/>
        <polygon points="12,1 16,8 12,15 8,8" fill="#555"/>
        <polygon points="0,8 8,8 12,15 4,15"  fill="#777"/>
      </symbol>

      <!-- ── Motivation ─────────────────────────────────────────────────── -->

      <!-- Outcome: 4 concentric circles + arrow upper-right (from Archi OutcomeFigure iconDelegate) -->
      <symbol id="am-outcome" viewBox="0 0 20 16">
        <circle cx="7" cy="8" r="6"   fill="none" stroke="#555" stroke-width="1.2"/>
        <circle cx="7" cy="8" r="3.5" fill="none" stroke="#555" stroke-width="1.2"/>
        <circle cx="7" cy="8" r="1.5" fill="none" stroke="#555" stroke-width="1.2"/>
        <circle cx="7" cy="8" r="0.6" fill="#555"/>
        <line x1="7" y1="8" x2="17" y2="1" stroke="#555" stroke-width="1.2" stroke-linecap="round"/>
        <polygon points="14,0 19,0.5 17.5,5" fill="#555"/>
      </symbol>

      <!-- Goal: 4 concentric circles — bullseye (from Archi GoalFigure iconDelegate) -->
      <symbol id="am-goal" viewBox="0 0 16 16">
        <circle cx="8" cy="8" r="6.5" fill="none" stroke="#555" stroke-width="1.2"/>
        <circle cx="8" cy="8" r="4"   fill="none" stroke="#555" stroke-width="1.2"/>
        <circle cx="8" cy="8" r="1.5" fill="none" stroke="#555" stroke-width="1.2"/>
        <circle cx="8" cy="8" r="0.6" fill="#555"/>
      </symbol>

      <!-- Stakeholder: left D-arc + rect + right circle (from Archi StakeholderFigure iconDelegate) -->
      <symbol id="am-stakeholder" viewBox="0 0 16 16">
        <path d="M6,4 a4,4 0 0 0 0,8" fill="none" stroke="#555" stroke-width="1.5"/>
        <line x1="6" y1="4"  x2="11" y2="4"  stroke="#555" stroke-width="1.5"/>
        <line x1="6" y1="12" x2="11" y2="12" stroke="#555" stroke-width="1.5"/>
        <circle cx="13.5" cy="8" r="3.5" fill="white" stroke="#555" stroke-width="1.5"/>
      </symbol>

      <!-- Driver: circle with crossed lines + filled center (from Archi DriverFigure.java) -->
      <symbol id="am-driver" viewBox="0 0 16 16">
        <circle cx="8" cy="8" r="6.5" fill="none" stroke="#555" stroke-width="1.5"/>
        <line x1="8" y1="1.5" x2="8" y2="14.5" stroke="#555" stroke-width="1.5"/>
        <line x1="1.5" y1="8" x2="14.5" y2="8"  stroke="#555" stroke-width="1.5"/>
        <circle cx="8" cy="8" r="2" fill="#555"/>
      </symbol>

      <!-- Assessment: circle with diagonal line (from Archi AssessmentFigure.java) -->
      <symbol id="am-assessment" viewBox="0 0 16 16">
        <circle cx="8" cy="7" r="6" fill="none" stroke="#555" stroke-width="1.5"/>
        <line x1="8" y1="13" x2="2" y2="15.5" stroke="#555" stroke-width="1.5" stroke-linecap="round"/>
      </symbol>

      <!-- Principle: rounded rect + two vertical parallel lines with gap (from Archi PrincipleFigure iconDelegate) -->
      <symbol id="am-principle" viewBox="0 0 16 16">
        <rect x="2" y="1" width="12" height="14" rx="3" ry="3" fill="none" stroke="#555" stroke-width="1.5"/>
        <line x1="7"   y1="3"    x2="7"   y2="9"  stroke="#555" stroke-width="1.2"/>
        <line x1="8.5" y1="3"    x2="8.5" y2="9"  stroke="#555" stroke-width="1.2"/>
        <line x1="7"   y1="10.5" x2="7"   y2="13" stroke="#555" stroke-width="1.2"/>
        <line x1="8.5" y1="10.5" x2="8.5" y2="13" stroke="#555" stroke-width="1.2"/>
      </symbol>

      <!-- Requirement: parallelogram (from Archi RequirementFigure.java — points 0,0/12,0/8,9/-4,9) -->
      <symbol id="am-requirement" viewBox="0 0 16 16">
        <polygon points="4,2 15,2 11,14 0,14" fill="#555"/>
      </symbol>

      <!-- Constraint: same parallelogram + diagonal line (from Archi ConstraintFigure.java) -->
      <symbol id="am-constraint" viewBox="0 0 16 16">
        <polygon points="4,2 15,2 11,14 0,14" fill="#555"/>
        <line x1="4" y1="2" x2="11" y2="14" stroke="#aaa" stroke-width="1.5"/>
      </symbol>

      <!-- Meaning: cloud shape (cubic bezier, from Archi MeaningFigure.java) -->
      <symbol id="am-meaning" viewBox="0 0 16 16">
        <path d="M4,13 C1,13 1,10.5 2,9.5 C1,9 1,7 3,7
                 C3,4.5 5,3 7,3.5 C8,2 11,2 11.5,4.5
                 C13.5,4.5 15,6 14,8
                 C15.5,8.5 15.5,11 14,12
                 C14.5,13.5 12,14 11,13 Z"
              fill="#555"/>
      </symbol>

      <!-- Value: oval/ellipse (from Archi ValueFigure.java) -->
      <symbol id="am-value" viewBox="0 0 16 16">
        <ellipse cx="8" cy="8" rx="7" ry="5" fill="#555"/>
      </symbol>

      <!-- ── Implementation & Migration ────────────────────────────────── -->

      <!-- WorkPackage: open circle + line + filled arrowhead (from Archi WorkPackageFigure iconDelegate) -->
      <symbol id="am-workpackage" viewBox="0 0 16 16">
        <path d="M4.5,10 A4.5,4.5 0 1 1 8.5,9.5" fill="none" stroke="#555" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="4.5" y1="10" x2="11" y2="10" stroke="#555" stroke-width="1.5" stroke-linecap="round"/>
        <polygon points="11,7 15,10 11,13" fill="#555"/>
      </symbol>

      <!-- Deliverable: document with arrow -->
      <symbol id="am-deliverable" viewBox="0 0 16 16">
        <path d="M0,0 h10 l6,6 v10 h-16 Z" fill="#555"/>
        <path d="M10,0 v6 h6" fill="none" stroke="#888" stroke-width="1"/>
        <path d="M4,9 h6 M8,7 l2,2 l-2,2" fill="none" stroke="white"
              stroke-width="1.5" stroke-linecap="round"/>
      </symbol>

      <!-- Gap: circle + two horizontal lines below (from Archi GapFigure.java) -->
      <symbol id="am-gap" viewBox="0 0 16 16">
        <circle cx="8" cy="5" r="4" fill="none" stroke="#555" stroke-width="1.5"/>
        <line x1="1" y1="11" x2="15" y2="11" stroke="#555" stroke-width="1.5"/>
        <line x1="1" y1="14.5" x2="15" y2="14.5" stroke="#555" stroke-width="1.5"/>
      </symbol>

      <!-- Plateau: 3 staircase horizontal lines (from Archi PlateauFigure iconDelegate) -->
      <symbol id="am-plateau" viewBox="0 0 16 16">
        <line x1="0"  y1="13" x2="11" y2="13" stroke="#555" stroke-width="2" stroke-linecap="round"/>
        <line x1="2"  y1="10" x2="13" y2="10" stroke="#555" stroke-width="2" stroke-linecap="round"/>
        <line x1="4"  y1="7"  x2="15" y2="7"  stroke="#555" stroke-width="2" stroke-linecap="round"/>
      </symbol>

      <!-- ── Strategy ───────────────────────────────────────────────────── -->

      <!-- Resource: rounded rect + right nub + 3 vertical lines (from Archi ResourceFigure iconDelegate) -->
      <symbol id="am-resource" viewBox="0 0 16 16">
        <rect x="0" y="3" width="13" height="10" rx="2" fill="none" stroke="#555" stroke-width="1.5"/>
        <rect x="13" y="6" width="3" height="4" rx="1" fill="none" stroke="#555" stroke-width="1.2"/>
        <line x1="3.5" y1="5.5" x2="3.5" y2="10.5" stroke="#555" stroke-width="1.2"/>
        <line x1="6.5" y1="5.5" x2="6.5" y2="10.5" stroke="#555" stroke-width="1.2"/>
        <line x1="9.5" y1="5.5" x2="9.5" y2="10.5" stroke="#555" stroke-width="1.2"/>
      </symbol>

      <!-- Capability: staircase of 6 squares (lower-right triangle) from Archi CapabilityFigure.java -->
      <symbol id="am-capability" viewBox="0 0 16 16">
        <rect x="10" y="2"  width="4" height="4" fill="#555"/>
        <rect x="6"  y="6"  width="4" height="4" fill="#555"/>
        <rect x="10" y="6"  width="4" height="4" fill="#555"/>
        <rect x="2"  y="10" width="4" height="4" fill="#555"/>
        <rect x="6"  y="10" width="4" height="4" fill="#555"/>
        <rect x="10" y="10" width="4" height="4" fill="#555"/>
      </symbol>

      <!-- CourseOfAction: 4-ring bullseye + shortcut glyph (from Archi CourseOfActionFigure iconDelegate) -->
      <symbol id="am-courseofaction" viewBox="0 0 16 16">
        <circle cx="9" cy="7" r="5"   fill="none" stroke="#555" stroke-width="1.2"/>
        <circle cx="9" cy="7" r="3"   fill="none" stroke="#555" stroke-width="1.2"/>
        <circle cx="9" cy="7" r="1.3" fill="none" stroke="#555" stroke-width="1.2"/>
        <circle cx="9" cy="7" r="0.5" fill="#555"/>
        <path d="M1.5,14.5 A3.5,3.5 0 0 1 3.5,11" fill="none" stroke="#555" stroke-width="1.5" stroke-linecap="round"/>
        <polygon points="1,10.5 4.5,12 3,15" fill="#555"/>
      </symbol>

      <!-- ValueStream: horizontal chevron/arrow band -->
      <symbol id="am-valuestream" viewBox="0 0 16 16">
        <path d="M0,4 h10 l6,4 l-6,4 h-10 l4,-4 Z" fill="#555"/>
      </symbol>

      <!-- Location: map pin / teardrop (from Archi LocationFigure.java) -->
      <symbol id="am-location" viewBox="0 0 16 16">
        <circle cx="8" cy="6" r="5" fill="#555"/>
        <path d="M4.5,9.5 L8,15 L11.5,9.5" fill="#555"/>
        <circle cx="8" cy="6" r="2" fill="white"/>
      </symbol>

      <!-- Grouping: small tab + wider body (from Archi GroupingFigure.java) -->
      <symbol id="am-grouping" viewBox="0 0 16 16">
        <rect x="0" y="2" width="7" height="4" fill="none" stroke="#555" stroke-width="1.5"/>
        <rect x="0" y="6" width="14" height="8" fill="none" stroke="#555" stroke-width="1.5"/>
      </symbol>

      <!-- Junction: filled circle — AND junction (from Archi JunctionFigure.java) -->
      <symbol id="am-junction" viewBox="0 0 16 16">
        <circle cx="8" cy="8" r="5" fill="#555"/>
      </symbol>

      <!-- DistributionNetwork: 2 parallel lines + chevrons on both ends (from Archi DistributionNetworkFigure iconDelegate) -->
      <symbol id="am-distribution-network" viewBox="0 0 16 16">
        <line x1="2" y1="6"  x2="14" y2="6"  stroke="#555" stroke-width="1.2"/>
        <line x1="2" y1="10" x2="14" y2="10" stroke="#555" stroke-width="1.2"/>
        <polyline points="5,3 1,8 5,13"  fill="none" stroke="#555" stroke-width="1.5" stroke-linejoin="round"/>
        <polyline points="11,3 15,8 11,13" fill="none" stroke="#555" stroke-width="1.5" stroke-linejoin="round"/>
      </symbol>

    </defs>
  </svg>
</template>

<script setup></script>
