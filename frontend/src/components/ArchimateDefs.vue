<template>
  <!-- Hidden SVG: ArchiMate 3.1 notation symbols, 16×16 viewport -->
  <svg width="0" height="0" style="position:absolute;overflow:hidden;">
    <defs>

      <!-- ── Behavior ─────────────────────────────────────────────────────── -->

      <!-- Process: rounded rect + right-pointing arrow tab -->
      <symbol id="am-process" viewBox="0 0 16 16">
        <path d="M0,2 Q0,0 2,0 L10,0 Q12,0 12,2 L12,5.5 L16,8 L12,10.5 L12,14
                 Q12,16 10,16 L2,16 Q0,16 0,14 Z" fill="#555"/>
      </symbol>

      <!-- Function: rounded rect + serrated/zigzag bottom -->
      <symbol id="am-function" viewBox="0 0 16 16">
        <path d="M0,1 Q0,0 1,0 L15,0 Q16,0 16,1 L16,10
                 L14,13 L12,10 L10,13 L8,10 L6,13 L4,10 L2,13 L0,10 Z"
              fill="#555"/>
      </symbol>

      <!-- Service: D-shape (flat left, curved right) -->
      <symbol id="am-service" viewBox="0 0 16 16">
        <path d="M2,0 h5 a9,9 0 0 1 0,16 h-5 Z" fill="#555"/>
      </symbol>

      <!-- Event: pentagon (tag shape, opening to left) -->
      <symbol id="am-event" viewBox="0 0 16 16">
        <path d="M4,0 h12 v16 h-12 l-4,-8 Z" fill="#555"/>
      </symbol>

      <!-- Interaction: two overlapping circles -->
      <symbol id="am-interaction" viewBox="0 0 16 16">
        <circle cx="5"  cy="8" r="5" fill="#555" opacity="0.7"/>
        <circle cx="11" cy="8" r="5" fill="#555" opacity="0.7"/>
      </symbol>

      <!-- ── Active Structure ────────────────────────────────────────────── -->

      <!-- Actor: person silhouette -->
      <symbol id="am-actor" viewBox="0 0 16 16">
        <circle cx="8" cy="4" r="3.5" fill="#555"/>
        <path d="M1,16 Q1,9 8,9 Q15,9 15,16 Z" fill="#555"/>
      </symbol>

      <!-- Role: circle outline (ring) -->
      <symbol id="am-role" viewBox="0 0 16 16">
        <path d="M8,1 a7,7 0 0 1 0,14 a7,7 0 0 1 0,-14 Z
                 M8,4 a4,4 0 0 0 0,8 a4,4 0 0 0 0,-8 Z" fill="#555" fill-rule="evenodd"/>
      </symbol>

      <!-- Collaboration: two overlapping circles (filled) -->
      <symbol id="am-collab" viewBox="0 0 16 16">
        <circle cx="5"  cy="8" r="4.5" fill="#555" opacity="0.65"/>
        <circle cx="11" cy="8" r="4.5" fill="#555" opacity="0.65"/>
      </symbol>

      <!-- Interface: lollipop — filled circle + stem + base -->
      <symbol id="am-interface" viewBox="0 0 16 16">
        <circle cx="8" cy="5" r="4" fill="#555"/>
        <rect   x="7" y="9"  width="2" height="5" fill="#555"/>
        <rect   x="4" y="14" width="8" height="2" fill="#555"/>
      </symbol>

      <!-- ── Passive Structure ───────────────────────────────────────────── -->

      <!-- Object / Contract / Representation: page with folded top-right corner -->
      <symbol id="am-object" viewBox="0 0 16 16">
        <path d="M0,0 h10 l6,6 v10 h-16 Z" fill="#999"/>
        <path d="M10,0 v6 h6" fill="none" stroke="#ccc" stroke-width="1"/>
      </symbol>

      <!-- Product: rectangle with tag notch -->
      <symbol id="am-product" viewBox="0 0 16 16">
        <rect x="0" y="2" width="13" height="12" rx="1" fill="#999"/>
        <path d="M13,5 l3,3 l-3,3" fill="#999"/>
      </symbol>

      <!-- Artifact: page with fold + two lines -->
      <symbol id="am-artifact" viewBox="0 0 16 16">
        <path d="M0,0 h10 l6,6 v10 h-16 Z" fill="#999"/>
        <path d="M10,0 v6 h6" fill="none" stroke="#ccc" stroke-width="1"/>
        <rect x="2" y="8"  width="8" height="1.5" fill="white" opacity="0.6"/>
        <rect x="2" y="11" width="5" height="1.5" fill="white" opacity="0.6"/>
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

      <!-- Device: 3D box with small notch on top -->
      <symbol id="am-device" viewBox="0 0 16 16">
        <polygon points="0,5 4,1 16,1 16,13 12,16 0,16" fill="#555"/>
        <polygon points="0,5 4,1 16,1 12,5"              fill="#777"/>
        <polygon points="12,5 16,1 16,13 12,16"          fill="#444"/>
        <polygon points="0,5 12,5 12,16 0,16"            fill="#666"/>
        <rect x="4" y="2" width="4" height="2" fill="#999"/>
      </symbol>

      <!-- SystemSoftware: window-like frame -->
      <symbol id="am-systemsoftware" viewBox="0 0 16 16">
        <rect x="0" y="0" width="16" height="16" rx="1" fill="#555"/>
        <rect x="1" y="4" width="14" height="11" fill="#888" rx="0.5"/>
        <circle cx="3" cy="2" r="1" fill="#aaa"/>
        <circle cx="7" cy="2" r="1" fill="#aaa"/>
      </symbol>

      <!-- Network: three nodes connected -->
      <symbol id="am-network" viewBox="0 0 16 16">
        <circle cx="8"  cy="2"  r="2.5" fill="#555"/>
        <circle cx="2"  cy="13" r="2.5" fill="#555"/>
        <circle cx="14" cy="13" r="2.5" fill="#555"/>
        <path d="M8,4.5 L2,10.5 M8,4.5 L14,10.5 M4.5,13 L11.5,13"
              stroke="#555" stroke-width="1.5" fill="none"/>
      </symbol>

      <!-- Path: two endpoints + dashed line -->
      <symbol id="am-path" viewBox="0 0 16 16">
        <circle cx="2" cy="8" r="2.5" fill="#555"/>
        <circle cx="14" cy="8" r="2.5" fill="#555"/>
        <path d="M4.5,8 L11.5,8" stroke="#555" stroke-width="2"
              stroke-dasharray="2.5 2" fill="none"/>
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

      <!-- Material: 3D box/package -->
      <symbol id="am-material" viewBox="0 0 16 16">
        <polygon points="8,0 16,4 16,12 8,16 0,12 0,4"  fill="#777"/>
        <polygon points="8,0 16,4 8,8 0,4"              fill="#aaa"/>
        <polygon points="16,4 16,12 8,16 8,8"           fill="#555"/>
      </symbol>

      <!-- ── Motivation ─────────────────────────────────────────────────── -->

      <!-- Outcome: filled circle -->
      <symbol id="am-outcome" viewBox="0 0 16 16">
        <circle cx="8" cy="8" r="7" fill="#555"/>
      </symbol>

      <!-- Goal: empty circle (ring) -->
      <symbol id="am-goal" viewBox="0 0 16 16">
        <path d="M8,1 a7,7 0 0 1 0,14 a7,7 0 0 1 0,-14 Z
                 M8,4 a4,4 0 0 0 0,8 a4,4 0 0 0 0,-8 Z"
              fill="#555" fill-rule="evenodd"/>
      </symbol>

      <!-- Stakeholder: person inside circle -->
      <symbol id="am-stakeholder" viewBox="0 0 16 16">
        <path d="M8,1 a7,7 0 0 1 0,14 a7,7 0 0 1 0,-14 Z
                 M8,4 a4,4 0 0 0 0,8 a4,4 0 0 0 0,-8 Z"
              fill="#555" fill-rule="evenodd"/>
        <circle cx="8" cy="5.5" r="2" fill="#555"/>
        <path d="M4,13 Q4,9.5 8,9.5 Q12,9.5 12,13" fill="#555"/>
      </symbol>

      <!-- Driver: upward arrow / cloud-arrow -->
      <symbol id="am-driver" viewBox="0 0 16 16">
        <path d="M8,1 L13,8 H10 V15 H6 V8 H3 Z" fill="#555"/>
      </symbol>

      <!-- Assessment: balance/scale -->
      <symbol id="am-assessment" viewBox="0 0 16 16">
        <rect x="7" y="0" width="2" height="16" fill="#555"/>
        <rect x="3" y="13" width="10" height="2" fill="#555"/>
        <path d="M1,4 h5 L3,9 Z"  fill="#555"/>
        <path d="M10,4 h5 L13,9 Z" fill="#555"/>
        <line x1="1" y1="4" x2="15" y2="4" stroke="#555" stroke-width="1.5"/>
      </symbol>

      <!-- Principle: scroll/document with ribbon bottom -->
      <symbol id="am-principle" viewBox="0 0 16 16">
        <path d="M2,0 h12 v13 Q8,17 2,13 Z" fill="#555"/>
        <rect x="4" y="3"  width="8" height="1.5" fill="white" opacity="0.5"/>
        <rect x="4" y="6"  width="8" height="1.5" fill="white" opacity="0.5"/>
        <rect x="4" y="9"  width="5" height="1.5" fill="white" opacity="0.5"/>
      </symbol>

      <!-- Requirement: rectangle with lines -->
      <symbol id="am-requirement" viewBox="0 0 16 16">
        <rect x="1" y="0" width="14" height="16" rx="1" fill="#555"/>
        <rect x="3" y="4"  width="10" height="1.5" fill="white" opacity="0.6"/>
        <rect x="3" y="7.5" width="10" height="1.5" fill="white" opacity="0.6"/>
        <rect x="3" y="11" width="6"  height="1.5" fill="white" opacity="0.6"/>
      </symbol>

      <!-- Constraint: padlock -->
      <symbol id="am-constraint" viewBox="0 0 16 16">
        <rect x="2" y="7" width="12" height="9" rx="1.5" fill="#555"/>
        <path d="M5,7 Q5,1 8,1 Q11,1 11,7" fill="none" stroke="#555" stroke-width="2.5"/>
        <circle cx="8" cy="12" r="1.5" fill="white"/>
        <rect   x="7.2" y="12" width="1.6" height="2.5" fill="white"/>
      </symbol>

      <!-- Meaning: speech bubble -->
      <symbol id="am-meaning" viewBox="0 0 16 16">
        <path d="M1,0 h14 a1,1 0 0 1 1,1 v9 a1,1 0 0 1-1,1
                 h-7 l-5,5 v-5 h-2 a1,1 0 0 1-1,-1 v-9 a1,1 0 0 1 1,-1 Z"
              fill="#555"/>
      </symbol>

      <!-- Value: diamond -->
      <symbol id="am-value" viewBox="0 0 16 16">
        <polygon points="8,0 16,8 8,16 0,8" fill="#555"/>
      </symbol>

      <!-- ── Implementation & Migration ────────────────────────────────── -->

      <!-- WorkPackage: document + checkmark -->
      <symbol id="am-workpackage" viewBox="0 0 16 16">
        <path d="M0,0 h10 l6,6 v10 h-16 Z" fill="#555"/>
        <path d="M10,0 v6 h6" fill="none" stroke="#888" stroke-width="1"/>
        <path d="M3,9 L6,12 L13,5" fill="none" stroke="white"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </symbol>

      <!-- Deliverable: document with arrow -->
      <symbol id="am-deliverable" viewBox="0 0 16 16">
        <path d="M0,0 h10 l6,6 v10 h-16 Z" fill="#555"/>
        <path d="M10,0 v6 h6" fill="none" stroke="#888" stroke-width="1"/>
        <path d="M4,9 h6 M8,7 l2,2 l-2,2" fill="none" stroke="white"
              stroke-width="1.5" stroke-linecap="round"/>
      </symbol>

      <!-- Gap: two zigzag rows -->
      <symbol id="am-gap" viewBox="0 0 16 16">
        <path d="M0,6 L3,3 L6,6 L9,3 L12,6 L15,3"
              fill="none" stroke="#555" stroke-width="2" stroke-linecap="round"/>
        <path d="M0,12 L3,9 L6,12 L9,9 L12,12 L15,9"
              fill="none" stroke="#555" stroke-width="2" stroke-linecap="round"/>
      </symbol>

      <!-- Plateau: layered rectangles -->
      <symbol id="am-plateau" viewBox="0 0 16 16">
        <rect x="3" y="12" width="10" height="4" rx="0.5" fill="#555"/>
        <rect x="5" y="7"  width="6"  height="4" rx="0.5" fill="#777"/>
        <rect x="6" y="2"  width="4"  height="4" rx="0.5" fill="#999"/>
      </symbol>

      <!-- ── Strategy ───────────────────────────────────────────────────── -->

      <!-- Resource: box with right-arrow inside -->
      <symbol id="am-resource" viewBox="0 0 16 16">
        <rect x="0" y="0" width="16" height="16" rx="1.5" fill="#555"/>
        <path d="M4,8 h7 M8,5 l3,3 l-3,3" fill="none" stroke="white"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </symbol>

      <!-- Capability: bullseye / concentric circles -->
      <symbol id="am-capability" viewBox="0 0 16 16">
        <path d="M8,1 a7,7 0 0 1 0,14 a7,7 0 0 1 0,-14 Z
                 M8,4.5 a3.5,3.5 0 0 0 0,7 a3.5,3.5 0 0 0 0,-7 Z"
              fill="#555" fill-rule="evenodd"/>
        <circle cx="8" cy="8" r="1.5" fill="#555"/>
      </symbol>

      <!-- CourseOfAction: curved path with arrowhead -->
      <symbol id="am-courseofaction" viewBox="0 0 16 16">
        <path d="M2,14 Q2,3 9,3" fill="none" stroke="#555" stroke-width="2.5"
              stroke-linecap="round"/>
        <path d="M6,1 L11,3 L9,8" fill="#555"/>
      </symbol>

      <!-- ValueStream: horizontal chevron/arrow band -->
      <symbol id="am-valuestream" viewBox="0 0 16 16">
        <path d="M0,4 h10 l6,4 l-6,4 h-10 l4,-4 Z" fill="#555"/>
      </symbol>

    </defs>
  </svg>
</template>

<script setup></script>
