import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings


_DEFAULT_MODEL = {
    "name": "*New Model", "type": "model", "id": "00000000-0000-0000-0000-000000000000",
    "children": [
        {"id": "00000000-0000-0000-0001-000000000001", "name": "Strategy",                     "type": "node", "folder_type": "strategy",                "children": []},
        {"id": "00000000-0000-0000-0001-000000000002", "name": "Business",                     "type": "node", "folder_type": "business",                "children": []},
        {"id": "00000000-0000-0000-0001-000000000003", "name": "Application",                  "type": "node", "folder_type": "application",             "children": []},
        {"id": "00000000-0000-0000-0001-000000000004", "name": "Technology And Physical",      "type": "node", "folder_type": "technology",              "children": []},
        {"id": "00000000-0000-0000-0001-000000000005", "name": "Motivation",                   "type": "node", "folder_type": "motivation",              "children": []},
        {"id": "00000000-0000-0000-0001-000000000006", "name": "Implementation and Migration", "type": "node", "folder_type": "implementation_migration", "children": []},
        {"id": "00000000-0000-0000-0001-000000000007", "name": "Other",                        "type": "node", "folder_type": "other",                   "children": []},
        {"id": "00000000-0000-0000-0001-000000000008", "name": "Relations",                    "type": "node", "folder_type": "relations",               "children": []},
        {"id": "00000000-0000-0000-0001-000000000009", "name": "Views",                        "type": "node", "folder_type": "diagrams",                "children": [
            {"id": "00000000-0000-0000-0000-000000000001", "name": "Default View",
             "type": "view", "element_type": "ArchimateDiagramModel",
             "documentation": "", "children": []},
        ]},
    ]
}

_MODEL_FILE   = os.path.join(os.path.dirname(__file__), "data", "model.json")
_UPLOADS_DIR  = os.path.join(os.path.dirname(__file__), "data", "uploads")
_DIAGRAMS_DIR = os.path.join(os.path.dirname(__file__), "data", "diagrams")

_GRAFICO_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "aspice-archi-prj", "model")
)

_XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"

_VIEW_TYPES = {"ArchimateDiagramModel", "SketchModel", "CanvasModel"}

_SKIP_TYPES = {"Relationship", "Relation"}


_FOLDER_TYPE_BY_NAME = {
    "Strategy":                     "strategy",
    "Business":                     "business",
    "Application":                  "application",
    "Technology And Physical":      "technology",
    "Motivation":                   "motivation",
    "Implementation and Migration": "implementation_migration",
    "Other":                        "other",
    "Relations":                    "relations",
    "Views":                        "diagrams",
}


def _migrate_folder_types(model):
    """Add folder_type and id to top-level folders missing them."""
    import uuid as _uuid
    for i, child in enumerate(model.get("children", [])):
        if child.get("type") != "node":
            continue
        if not child.get("folder_type"):
            ft = _FOLDER_TYPE_BY_NAME.get(child.get("name", ""))
            if ft:
                child["folder_type"] = ft
        if not child.get("id"):
            # Deterministic id based on position so it stays stable across reloads
            child["id"] = f"00000000-0000-0000-0001-{(i+1):012d}"
    return model


def _load_model():
    if os.path.exists(_MODEL_FILE):
        with open(_MODEL_FILE, "r", encoding="utf-8") as f:
            model = json.load(f)
        return _migrate_folder_types(model)
    # First run: start with empty default model
    return _DEFAULT_MODEL


def _local(tag):
    return tag.split("}")[-1] if "}" in tag else tag


def _el_type(xsi_type):
    return xsi_type.split(":")[-1] if ":" in xsi_type else xsi_type


# ── Native Archi format (.archimate) ──────────────────────────────────────────

def _parse_native(root):
    def parse_folder(elem):
        children = []
        for child in elem:
            tag = _local(child.tag)
            if tag == "folder":
                children.append(parse_folder(child))
            elif tag == "element":
                et = _el_type(child.get(_XSI_TYPE, ""))
                children.append({
                    "name": child.get("name", ""),
                    "type": "view" if et in _VIEW_TYPES else "element",
                    "element_type": et,
                    "id": child.get("id", ""),
                    "documentation": child.get("documentation", ""),
                    "children": [],
                })
        node = {
            "name": elem.get("name", ""),
            "type": "node",
            "id": elem.get("id", ""),
            "children": children,
        }
        ft = elem.get("type", "")   # e.g. "business", "strategy"
        if ft:
            node["folder_type"] = ft
        return node

    return {
        "name": root.get("name", "*New Model"),
        "type": "model",
        "id": root.get("id", ""),
        "children": [
            parse_folder(child)
            for child in root
            if _local(child.tag) == "folder"
        ],
    }


# ── ArchiMate Exchange Format (.xml) ─────────────────────────────────────────

def _parse_exchange(root, ns):
    def t(tag):
        return f"{{{ns}}}{tag}"

    name_el = root.find(t("name"))
    model_name = name_el.text if name_el is not None and name_el.text else "*New Model"

    # Build flat elements index
    elements = {}
    for elem in root.findall(f".//{t('element')}"):
        ident = elem.get("identifier", "")
        n = elem.find(t("name"))
        d = elem.find(t("documentation"))
        et = _el_type(elem.get(_XSI_TYPE, ""))
        elements[ident] = {
            "name": n.text if n is not None else "",
            "type": "view" if et in _VIEW_TYPES else "element",
            "element_type": et,
            "id": ident,
            "documentation": d.text if d is not None else "",
            "children": [],
        }

    def parse_item(item):
        ref = item.get("identifierRef")
        if ref:
            return elements.get(ref, {
                "name": ref, "type": "element",
                "element_type": "", "id": ref,
                "documentation": "", "children": [],
            })
        label = item.find(t("label"))
        return {
            "name": label.text if label is not None else "",
            "type": "node",
            "id": "",
            "children": [parse_item(c) for c in item.findall(t("item"))],
        }

    orgs = root.find(t("organizations"))
    if orgs is not None:
        children = [parse_item(item) for item in orgs.findall(t("item"))]
    else:
        children = list(elements.values())

    # Append views if present and not already in organizations
    views_root = root.find(t("views"))
    if views_root is not None:
        view_items = []
        for view in views_root.findall(f".//{t('view')}"):
            n = view.find(t("name"))
            view_items.append({
                "name": n.text if n is not None else "",
                "type": "view",
                "element_type": "ArchimateDiagramModel",
                "id": view.get("identifier", ""),
                "documentation": "",
                "children": [],
            })
        if view_items:
            children.append({
                "name": "Views",
                "type": "node",
                "id": "",
                "children": view_items,
            })

    return {
        "name": model_name,
        "type": "model",
        "id": root.get("identifier", ""),
        "children": children,
    }


# ── Grafico multi-file format (folder of XML files) ──────────────────────────

def _parse_grafico(model_dir):
    root_elem = ET.parse(os.path.join(model_dir, "folder.xml")).getroot()
    model_name = root_elem.get("name", "*New Model")
    model_id = root_elem.get("id", "")
    purpose = root_elem.get("purpose", "")

    def parse_dir(dirpath):
        folder_xml = os.path.join(dirpath, "folder.xml")
        folder_elem = ET.parse(folder_xml).getroot()
        folder_name = folder_elem.get("name", os.path.basename(dirpath))
        folder_id   = folder_elem.get("id", "")
        folder_type = folder_elem.get("type", "")   # e.g. "business", "strategy"

        children = []
        for entry in sorted(os.scandir(dirpath), key=lambda e: e.name):
            if entry.name == "folder.xml":
                continue
            if entry.is_dir():
                sub = parse_dir(entry.path)
                if sub:
                    children.append(sub)
            elif entry.name.endswith(".xml"):
                try:
                    elem = ET.parse(entry.path).getroot()
                except ET.ParseError:
                    continue
                tag = _local(elem.tag)
                if any(skip in tag for skip in _SKIP_TYPES):
                    continue
                is_view = tag in _VIEW_TYPES
                children.append({
                    "name": elem.get("name", ""),
                    "type": "view" if is_view else "element",
                    "element_type": tag,
                    "id": elem.get("id", ""),
                    "documentation": elem.get("documentation", ""),
                    "children": [],
                })

        node = {
            "name": folder_name,
            "type": "node",
            "id": folder_id,
            "children": children,
        }
        if folder_type:
            node["folder_type"] = folder_type
        return node

    children = [
        parse_dir(e.path)
        for e in sorted(os.scandir(model_dir), key=lambda e: e.name)
        if e.is_dir()
    ]

    return {
        "name": model_name,
        "type": "model",
        "id": model_id,
        "purpose": purpose,
        "children": children,
    }


# ── Dispatcher ────────────────────────────────────────────────────────────────

def _parse_archimate(content):
    root = ET.fromstring(content)
    tag = root.tag
    if "opengroup.org" in tag:
        ns = tag[1:tag.index("}")]
        return _parse_exchange(root, ns)
    return _parse_native(root)


# ── Views ─────────────────────────────────────────────────────────────────────

@ensure_csrf_cookie
def spa(request):
    index = Path(settings.FRONTEND_DIST) / 'index.html'
    if index.exists():
        return HttpResponse(index.read_text(encoding='utf-8'), content_type='text/html')
    return HttpResponse('Frontend not built. Run: cd frontend && npm run build', status=503)


@ensure_csrf_cookie
def main(request):
    model = _load_model()
    return render(request, "app_main/main.html", context={
        "title": "ArchitetIQ",
        "description": "ArchitetIQ description",
        "model": model,
    })


def api_model(request):
    return JsonResponse(_load_model())


def api_model_load_aspice(request):
    """Load the built-in ASPICE Grafico project."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    grafico_root = os.path.join(_GRAFICO_DIR, "folder.xml")
    if not os.path.isfile(grafico_root):
        return JsonResponse({'error': 'ASPICE project not found'}, status=404)
    model = _parse_grafico(_GRAFICO_DIR)
    os.makedirs(os.path.dirname(_MODEL_FILE), exist_ok=True)
    with open(_MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    return JsonResponse({'ok': True, 'name': model.get('name', '')})


def api_model_new(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    os.makedirs(os.path.dirname(_MODEL_FILE), exist_ok=True)
    with open(_MODEL_FILE, 'w', encoding='utf-8') as f:
        json.dump(_DEFAULT_MODEL, f, ensure_ascii=False, indent=2)
    return JsonResponse({'ok': True})


def api_model_save(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    os.makedirs(os.path.dirname(_MODEL_FILE), exist_ok=True)
    with open(_MODEL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return JsonResponse({'ok': True, 'name': data.get('name', '')})


_FOLDER_TYPE = {
    'Strategy':                      'strategy',
    'Business':                      'business',
    'Application':                   'application',
    'Technology And Physical':       'technology',
    'Motivation':                    'motivation',
    'Implementation and Migration':  'implementation_migration',
    'Other':                         'other',
    'Relations':                     'relations',
    'Views':                         'diagrams',
}


def _load_layout(view_id):
    """Load saved canvas layout for a view; returns {} if not found."""
    lp = _layout_path(view_id)
    if not os.path.isfile(lp):
        return {}
    try:
        with open(lp, encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _export_collect(model):
    """Walk model tree, return {view_id: layout} for all views that have saved layouts."""
    result = {}
    def walk(node):
        if node.get('type') == 'view':
            layout = _load_layout(node['id'])
            if layout:
                result[node['id']] = layout
        for ch in node.get('children', []):
            walk(ch)
    walk(model)
    return result


def _make_child_element(node, XSI):
    """Build a <child> ET.Element from a layout node dict (enhanced format)."""
    ntype = node.get('node_type', 'element')
    nid   = node.get('id', '')
    child = ET.Element('child')
    if ntype == 'element' and node.get('element_id'):
        child.set(f'{{{XSI}}}type', 'archimate:DiagramObject')
        child.set('id', nid)
        child.set('archimateElement', node['element_id'])
    elif ntype == 'group':
        child.set(f'{{{XSI}}}type', 'archimate:Group')
        child.set('id', nid)
        if node.get('name'):
            child.set('name', node['name'])
    elif ntype == 'note':
        child.set(f'{{{XSI}}}type', 'archimate:DiagramModelNote')
        child.set('id', nid)
        if node.get('name'):
            c = ET.SubElement(child, 'content')
            c.text = node['name']
    else:
        return None
    b = ET.SubElement(child, 'bounds')
    b.set('x', str(int(node.get('x', 0))))
    b.set('y', str(int(node.get('y', 0))))
    b.set('width', str(int(node.get('width', 120))))
    b.set('height', str(int(node.get('height', 55))))
    return child


def _add_source_connection(src_xml, edge, rel_id, XSI):
    """Append a <sourceConnection> to src_xml element."""
    conn = ET.SubElement(src_xml, 'sourceConnection')
    conn.set(f'{{{XSI}}}type', 'archimate:Connection')
    conn.set('id', edge.get('id', ''))
    conn.set('source', edge.get('source_cell', ''))
    conn.set('target', edge.get('target_cell', ''))
    conn.set('archimateRelationship', rel_id)
    for v in edge.get('vertices', []):
        bp = ET.SubElement(conn, 'bendpoint')
        bp.set('startX', str(int(v.get('x', 0))))
        bp.set('startY', str(int(v.get('y', 0))))


def _copy_children_with_overrides(parent_out, parent_src, pos_override, abs_x, abs_y, built):
    """Recursively copy <child> elements from source XML, updating <bounds> from pos_override.
    Tracks copied elements in `built` {id → xml_elem} for later sourceConnection injection."""
    import copy
    for child in parent_src:
        if _local(child.tag) != 'child':
            continue
        cid = child.get('id', '')
        # Original relative bounds
        ox, oy, ow, oh = 0, 0, 120, 55
        for sub in child:
            if _local(sub.tag) == 'bounds':
                ox, oy = int(sub.get('x', 0)), int(sub.get('y', 0))
                ow, oh = int(sub.get('width', 120)), int(sub.get('height', 55))
                break
        child_abs_x = abs_x + ox
        child_abs_y = abs_y + oy
        if cid in pos_override:
            ov = pos_override[cid]
            new_ax, new_ay = int(ov['x']), int(ov['y'])
            rx, ry = new_ax - abs_x, new_ay - abs_y
            rw, rh = int(ov['width']), int(ov['height'])
            child_abs_x, child_abs_y = new_ax, new_ay
        else:
            rx, ry, rw, rh = ox, oy, ow, oh
        new_child = ET.Element(child.tag, dict(child.attrib))
        b = ET.SubElement(new_child, 'bounds')
        b.set('x', str(rx)); b.set('y', str(ry))
        b.set('width', str(rw)); b.set('height', str(rh))
        for sub in child:
            stag = _local(sub.tag)
            if stag not in ('bounds', 'child'):
                new_child.append(copy.deepcopy(sub))
        if cid:
            built[cid] = new_child
        _copy_children_with_overrides(new_child, child, pos_override, child_abs_x, child_abs_y, built)
        parent_out.append(new_child)


def _append_diagram_children(view_xml, view_id, layout, source_root, XSI, user_edges_with_rel):
    """Add <child> and <sourceConnection> elements to a view XML element for export."""
    nodes = layout.get('nodes', [])
    pos_override = {n['id']: n for n in nodes}
    has_rich_data = any(n.get('element_id') or n.get('node_type') for n in nodes)

    built = {}  # id → xml element (for attaching user connections)

    if has_rich_data:
        for node in nodes:
            child_xml = _make_child_element(node, XSI)
            if child_xml is not None:
                view_xml.append(child_xml)
                built[node['id']] = child_xml
    elif source_root is not None:
        source_view = None
        for elem in source_root.iter():
            if elem.get('id') == view_id and _el_type(elem.get(_XSI_TYPE, '')) in _VIEW_TYPES:
                source_view = elem
                break
        if source_view is not None:
            _copy_children_with_overrides(view_xml, source_view, pos_override, 0, 0, built)

    for edge, rel_id in user_edges_with_rel:
        src_xml = built.get(edge.get('source_cell', ''))
        if src_xml is not None:
            _add_source_connection(src_xml, edge, rel_id, XSI)


def _build_archimate_xml(model):
    import uuid as _uuid
    NS  = 'http://www.archimatetool.com/archimate'
    XSI = 'http://www.w3.org/2001/XMLSchema-instance'
    ET.register_namespace('archimate', NS)
    ET.register_namespace('xsi', XSI)

    # Load original source XML (for diagrams not yet saved from canvas)
    source_root = None
    source_path = model.get('_source', '')
    if source_path and os.path.isfile(source_path):
        try:
            source_root = ET.parse(source_path).getroot()
        except ET.ParseError:
            pass

    # Load all saved layouts and build node_id → element_id lookup
    layouts = _export_collect(model)
    node_to_elem = {}
    for layout in layouts.values():
        for n in layout.get('nodes', []):
            if n.get('element_id'):
                node_to_elem[n['id']] = n['element_id']

    # Pre-generate relation IDs for user-drawn edges
    # user_edges_by_view: view_id → [(edge_dict, rel_id)]
    user_edges_by_view = {}
    new_relations = []  # (rel_id, rel_type, src_elem_id, tgt_elem_id)
    for vid, layout in layouts.items():
        pairs = []
        for edge in layout.get('user_edges', []):
            rel_id = str(_uuid.uuid4())
            pairs.append((edge, rel_id))
            src_eid = node_to_elem.get(edge.get('source_cell', ''), '')
            tgt_eid = node_to_elem.get(edge.get('target_cell', ''), '')
            if src_eid and tgt_eid:
                new_relations.append((rel_id, edge.get('type', 'AssociationRelationship'), src_eid, tgt_eid))
        if pairs:
            user_edges_by_view[vid] = pairs

    root = ET.Element(f'{{{NS}}}model')
    root.set('name', model.get('name', ''))
    root.set('id',   model.get('id', ''))
    root.set('version', '4.6.0')
    if model.get('purpose'):
        root.set('purpose', model['purpose'])

    def build_node(parent, node):
        if node['type'] == 'node':
            ft = node.get('folder_type') or _FOLDER_TYPE.get(node['name'],
                          node['name'].lower().replace(' ', '_'))
            folder = ET.SubElement(parent, 'folder')
            folder.set('name', node['name'])
            folder.set('id',   node.get('id', ''))
            folder.set('type', ft)
            for ch in node.get('children', []):
                build_node(folder, ch)
            if ft == 'relations':
                for rel_id, rel_type, src_eid, tgt_eid in new_relations:
                    rel = ET.SubElement(folder, 'element')
                    rel.set(f'{{{XSI}}}type', f'archimate:{rel_type}')
                    rel.set('id', rel_id)
                    rel.set('name', '')
                    rel.set('source', src_eid)
                    rel.set('target', tgt_eid)
        elif node['type'] in ('element', 'view'):
            et = node.get('element_type', 'BusinessActor')
            elem = ET.SubElement(parent, 'element')
            elem.set(f'{{{XSI}}}type', f'archimate:{et}')
            elem.set('name', node.get('name', ''))
            elem.set('id',   node.get('id', ''))
            if node.get('documentation'):
                elem.set('documentation', node['documentation'])
            if node['type'] == 'view':
                vid = node['id']
                _append_diagram_children(
                    elem, vid,
                    layouts.get(vid, {}),
                    source_root, XSI,
                    user_edges_by_view.get(vid, []),
                )

    for ch in model.get('children', []):
        build_node(root, ch)

    ET.indent(root, space='  ')
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode').encode('utf-8')


def api_model_export(request):
    model = _load_model()
    xml_bytes = _build_archimate_xml(model)
    safe_name = model.get('name', 'model').replace(' ', '_')
    response = HttpResponse(xml_bytes, content_type='application/xml; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}.archimate"'
    return response


# ── Diagram visual data ───────────────────────────────────────────────────────

def _build_elements_index(model):
    """Flat id → {name, element_type} for all elements/views in the model tree."""
    index = {}
    def walk(node):
        nid = node.get('id')
        if nid and node.get('type') in ('element', 'view'):
            index[nid] = {
                'name': node.get('name', ''),
                'element_type': node.get('element_type', ''),
            }
        for child in node.get('children', []):
            walk(child)
    walk(model)
    return index


def _find_diagram_file(view_id):
    diagrams_dir = os.path.join(_GRAFICO_DIR, 'diagrams')
    if not os.path.isdir(diagrams_dir):
        return None
    for dirpath, _, filenames in os.walk(diagrams_dir):
        for fname in filenames:
            if view_id in fname and fname.endswith('.xml') and fname != 'folder.xml':
                return os.path.join(dirpath, fname)
    return None


def _parse_diagram_file(xml_path, elements_index):
    root = ET.parse(xml_path).getroot()
    nodes, edges = [], []
    node_bounds = {}  # visual_id → (ax, ay, w, h) for bendpoint calculation

    def get_bounds(elem):
        for child in elem:
            if _local(child.tag) == 'bounds':
                return (
                    int(child.get('x', 0)), int(child.get('y', 0)),
                    int(child.get('width', 120)), int(child.get('height', 55)),
                )
        return 0, 0, 120, 55

    def resolve_href(href):
        eid = href.split('#')[-1] if '#' in href else ''
        info = elements_index.get(eid, {})
        return eid, info.get('name', eid), info.get('element_type', '')

    def parse_child(elem, px=0, py=0, emb_parent=None):
        xsi_type = elem.get(_XSI_TYPE, '')
        obj_type = xsi_type.split(':')[-1] if ':' in xsi_type else xsi_type
        oid = elem.get('id', '')
        bx, by, bw, bh = get_bounds(elem)
        ax, ay = px + bx, py + by

        for sub in elem:
            stag = _local(sub.tag)
            if stag in ('sourceConnection', 'sourceConnections'):
                # Collect raw relative bendpoints + resolve ArchiMate relation type
                raw_bps = []
                rel_type = ''
                for bp in sub:
                    bp_tag = _local(bp.tag)
                    if bp_tag == 'bendpoint':
                        raw_bps.append({
                            'startX': int(bp.get('startX', 0)),
                            'startY': int(bp.get('startY', 0)),
                            'endX':   int(bp.get('endX', 0)),
                            'endY':   int(bp.get('endY', 0)),
                        })
                    elif bp_tag == 'archimateRelationship':
                        # e.g. xsi:type="archimate:RealizationRelationship"
                        rel_type = _el_type(bp.get(_XSI_TYPE, ''))
                edges.append({
                    'id':     sub.get('id', ''),
                    'type':   rel_type,
                    'source': sub.get('source', ''),
                    'target': sub.get('target', ''),
                    '_raw_bps': raw_bps,
                })

        if obj_type == 'DiagramModelGroup':
            for sub in elem:
                if _local(sub.tag) == 'children':
                    parse_child(sub, ax, ay)
            node_bounds[oid] = (ax, ay, bw, bh)
            nodes.append({
                'id': oid, 'type': 'group',
                'name': elem.get('name', ''),
                'x': ax, 'y': ay, 'width': bw, 'height': bh,
                'fill_color': elem.get('fillColor', '#f5f5f5'),
            })

        elif obj_type == 'DiagramModelArchimateObject':
            eid, ename, etype = '', '', ''
            embedded = []
            for sub in elem:
                stag2 = _local(sub.tag)
                if stag2 == 'archimateElement':
                    eid, ename, etype = resolve_href(sub.get('href', ''))
                elif stag2 == 'children':
                    embedded.append(sub)
            node_bounds[oid] = (ax, ay, bw, bh)
            node_entry = {
                'id': oid, 'type': 'element',
                'name': ename, 'element_id': eid, 'element_type': etype,
                'x': ax, 'y': ay, 'width': bw, 'height': bh,
            }
            if emb_parent:
                node_entry['parent_id'] = emb_parent
            nodes.append(node_entry)
            # Recurse embedded children — pass this node as their parent
            for sub in embedded:
                parse_child(sub, ax, ay, emb_parent=oid)

        elif obj_type == 'DiagramModelNote':
            node_bounds[oid] = (ax, ay, bw, bh)
            nodes.append({
                'id': oid, 'type': 'note',
                'name': elem.get('content', ''),
                'x': ax, 'y': ay, 'width': bw, 'height': bh,
            })

        elif obj_type == 'DiagramModelReference':
            ref_id = ''
            for sub in elem:
                if _local(sub.tag) == 'referencedModel':
                    ref_id = sub.get('href', '').split('#')[-1]
            node_bounds[oid] = (ax, ay, bw, bh)
            nodes.append({
                'id': oid, 'type': 'view_ref',
                'name': '', 'ref_id': ref_id,
                'x': ax, 'y': ay, 'width': bw, 'height': bh,
            })


    for child in root:
        if _local(child.tag) == 'children':
            parse_child(child)

    # Calculate absolute bendpoint vertices (Archi relative → absolute)
    for edge in edges:
        raw_bps = edge.pop('_raw_bps', [])
        if not raw_bps:
            edge['vertices'] = []
            continue
        sx, sy, sw, sh = node_bounds.get(edge['source'], (0, 0, 120, 55))
        tx, ty, tw, th = node_bounds.get(edge['target'], (0, 0, 120, 55))
        src_cx, src_cy = sx + sw / 2, sy + sh / 2
        tgt_cx, tgt_cy = tx + tw / 2, ty + th / 2
        n = len(raw_bps)
        vertices = []
        for i, bp in enumerate(raw_bps):
            w = (i + 1) / (n + 1)
            abs_x = round((1 - w) * (src_cx + bp['startX']) + w * (tgt_cx + bp['endX']))
            abs_y = round((1 - w) * (src_cy + bp['startY']) + w * (tgt_cy + bp['endY']))
            vertices.append({'x': abs_x, 'y': abs_y})
        edge['vertices'] = vertices

    return {
        'id': root.get('id', ''),
        'name': root.get('name', ''),
        'documentation': root.get('documentation', ''),
        'nodes': nodes,
        'edges': edges,
    }


def _collect_bps(conn_elem):
    """Extract raw bendpoints from a sourceConnection element."""
    bps = []
    for child in conn_elem:
        if _local(child.tag) == 'bendpoint':
            bps.append({
                'startX': int(child.get('startX', 0)),
                'startY': int(child.get('startY', 0)),
                'endX':   int(child.get('endX', 0)),
                'endY':   int(child.get('endY', 0)),
            })
    return bps


def _parse_native_diagram(view_elem, elements_index):
    """Parse diagram visual data from a native .archimate view element.

    Native format uses:
      <child xsi:type="archimate:DiagramObject" archimateElement="elem-id">
      <child xsi:type="archimate:Group" name="...">
      <sourceConnection xsi:type="archimate:Connection" archimateRelationship="rel-id">
    """
    nodes, edges = [], []
    node_bounds = {}

    def get_bounds(elem):
        for child in elem:
            if _local(child.tag) == 'bounds':
                return (
                    int(child.get('x', 0)), int(child.get('y', 0)),
                    int(child.get('width', 120)), int(child.get('height', 55)),
                )
        return 0, 0, 120, 55

    def parse_child(elem, px=0, py=0, parent_id=None):
        xsi_type = _el_type(elem.get(_XSI_TYPE, ''))
        oid = elem.get('id', '')
        bx, by, bw, bh = get_bounds(elem)
        ax, ay = px + bx, py + by
        node_bounds[oid] = (ax, ay, bw, bh)

        # Collect outgoing connections from this element
        for sub in elem:
            stag = _local(sub.tag)
            if stag == 'sourceConnection':
                rel_id = sub.get('archimateRelationship', '')
                rel_info = elements_index.get(rel_id, {})
                edges.append({
                    'id':     sub.get('id', ''),
                    'type':   rel_info.get('element_type', ''),
                    'source': sub.get('source', oid),
                    'target': sub.get('target', ''),
                    '_raw_bps': _collect_bps(sub),
                })

        if xsi_type in ('DiagramObject', 'DiagramModelArchimateObject'):
            # ArchiMate element rendered on canvas
            el_id = elem.get('archimateElement', '')
            # Grafico compat: may be a child element with href
            if not el_id:
                for sub in elem:
                    if _local(sub.tag) == 'archimateElement':
                        href = sub.get('href', '')
                        el_id = href.split('#')[-1] if '#' in href else href
                        break
            info = elements_index.get(el_id, {})
            entry = {
                'id': oid, 'type': 'element',
                'name': info.get('name', ''),
                'element_id': el_id,
                'element_type': info.get('element_type', ''),
                'x': ax, 'y': ay, 'width': bw, 'height': bh,
            }
            if parent_id:
                entry['parent_id'] = parent_id
            nodes.append(entry)
            # Recurse embedded children
            for sub in elem:
                if _local(sub.tag) == 'child':
                    parse_child(sub, ax, ay, parent_id=oid)

        elif xsi_type in ('Group', 'DiagramModelGroup'):
            fill = elem.get('fillColor', '#f5f5f5')
            nodes.append({
                'id': oid, 'type': 'group',
                'name': elem.get('name', ''),
                'x': ax, 'y': ay, 'width': bw, 'height': bh,
                'fill_color': fill,
            })
            for sub in elem:
                if _local(sub.tag) in ('child', 'children'):
                    parse_child(sub, ax, ay)

        elif xsi_type in ('Note', 'DiagramModelNote'):
            content = ''
            for sub in elem:
                if _local(sub.tag) == 'content':
                    content = sub.text or ''
            nodes.append({
                'id': oid, 'type': 'note',
                'name': content or elem.get('name', ''),
                'x': ax, 'y': ay, 'width': bw, 'height': bh,
            })

        elif xsi_type in ('DiagramModelReference',):
            ref_id = elem.get('model', '')
            # Grafico compat: may be a child element with href
            if not ref_id:
                for sub in elem:
                    if _local(sub.tag) == 'referencedModel':
                        href = sub.get('href', '')
                        ref_id = href.split('#')[-1] if '#' in href else href
                        break
            nodes.append({
                'id': oid, 'type': 'view_ref',
                'name': '', 'ref_id': ref_id,
                'x': ax, 'y': ay, 'width': bw, 'height': bh,
            })

    for child in view_elem:
        if _local(child.tag) == 'child':
            parse_child(child)

    # Resolve relative bendpoints to absolute coordinates
    for edge in edges:
        raw_bps = edge.pop('_raw_bps', [])
        if not raw_bps:
            edge['vertices'] = []
            continue
        sx, sy, sw, sh = node_bounds.get(edge['source'], (0, 0, 120, 55))
        tx, ty, tw, th = node_bounds.get(edge['target'], (0, 0, 120, 55))
        src_cx, src_cy = sx + sw / 2, sy + sh / 2
        tgt_cx, tgt_cy = tx + tw / 2, ty + th / 2
        n = len(raw_bps)
        vertices = []
        for i, bp in enumerate(raw_bps):
            w = (i + 1) / (n + 1)
            abs_x = round((1 - w) * (src_cx + bp['startX']) + w * (tgt_cx + bp['endX']))
            abs_y = round((1 - w) * (src_cy + bp['startY']) + w * (tgt_cy + bp['endY']))
            vertices.append({'x': abs_x, 'y': abs_y})
        edge['vertices'] = vertices

    return {
        'id':            view_elem.get('id', ''),
        'name':          view_elem.get('name', ''),
        'documentation': view_elem.get('documentation', ''),
        'nodes': nodes,
        'edges': edges,
    }


def _find_model_view(view_id):
    """Return (root, view_elem) from the uploaded .archimate file, or (None, None).

    The path to the uploaded file is stored in model.json under '_source'.
    """
    model = _load_model()
    source = model.get('_source', '')
    if not source or not os.path.isfile(source):
        return None, None
    try:
        root = ET.parse(source).getroot()
    except ET.ParseError:
        return None, None
    for elem in root.iter():
        if elem.get('id') == view_id:
            et = _el_type(elem.get(_XSI_TYPE, ''))
            if et in _VIEW_TYPES:
                return root, elem
    return None, None


def _layout_path(view_id):
    return os.path.join(_DIAGRAMS_DIR, f"{view_id}.json")


def _apply_saved_layout(data, view_id):
    """Merge saved node positions and user edges into parsed diagram data."""
    path = _layout_path(view_id)
    if not os.path.isfile(path):
        return data
    with open(path, encoding='utf-8') as f:
        layout = json.load(f)
    # Override node positions with saved values
    pos = {n['id']: n for n in layout.get('nodes', [])}
    for node in data['nodes']:
        if node['id'] in pos:
            s = pos[node['id']]
            node.update({k: s[k] for k in ('x', 'y', 'width', 'height') if k in s})
    # Append user-created edges (not from Archi XML)
    existing_ids = {e['id'] for e in data['edges']}
    for edge in layout.get('user_edges', []):
        if edge.get('id') not in existing_ids:
            data['edges'].append(edge)
    return data


def api_diagram(request, view_id):
    model = _load_model()
    elements_index = _build_elements_index(model)

    # 1. Try Grafico multi-file diagram
    diagram_file = _find_diagram_file(view_id)
    if diagram_file:
        try:
            data = _parse_diagram_file(diagram_file, elements_index)
            data = _apply_saved_layout(data, view_id)
            return JsonResponse(data)
        except ET.ParseError as e:
            return JsonResponse({'error': str(e)}, status=500)

    # 2. Try model.archimate diagram
    _, view_elem = _find_model_view(view_id)
    if view_elem is not None:
        data = _parse_native_diagram(view_elem, elements_index)
        data = _apply_saved_layout(data, view_id)
        return JsonResponse(data)

    # 3. Fallback: return empty diagram (blank canvas for user-created views)
    def find_node(node, tid):
        if node.get('id') == tid:
            return node
        for child in node.get('children', []):
            found = find_node(child, tid)
            if found:
                return found
        return None

    node = find_node(model, view_id)
    if node is None:
        return JsonResponse({'error': 'Not found'}, status=404)
    return JsonResponse({
        'id': view_id,
        'name': node.get('name', ''),
        'documentation': node.get('documentation', ''),
        'nodes': [], 'edges': [],
    })


def api_diagram_save(request, view_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        layout = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    os.makedirs(_DIAGRAMS_DIR, exist_ok=True)
    with open(_layout_path(view_id), 'w', encoding='utf-8') as f:
        json.dump(layout, f, ensure_ascii=False, indent=2)
    return JsonResponse({'ok': True})


def _read_archimate_bytes(raw):
    """Return XML bytes from .archimate (plain XML or ZIP archive with model.xml)."""
    stripped = raw.lstrip()
    if stripped.startswith(b'<?xml') or stripped.startswith(b'<'):
        return raw
    try:
        import zipfile, io
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if 'model.xml' in z.namelist():
                return z.read('model.xml')
    except Exception:
        pass
    return raw


def upload_model(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "No file provided"}, status=400)
    try:
        raw = _read_archimate_bytes(f.read())
        model = _parse_archimate(raw)
    except ET.ParseError as e:
        return JsonResponse({"error": f"XML parse error: {e}"}, status=400)

    # Save original file to uploads/ and record its path in the model
    try:
        root_tag = ET.fromstring(raw).tag
        is_native = "opengroup.org" not in root_tag
    except ET.ParseError:
        is_native = False

    if is_native:
        os.makedirs(_UPLOADS_DIR, exist_ok=True)
        filename = os.path.basename(f.name) or "model.archimate"
        upload_path = os.path.join(_UPLOADS_DIR, filename)
        with open(upload_path, "wb") as out:
            out.write(raw)
        model["_source"] = upload_path
    else:
        model.pop("_source", None)

    os.makedirs(os.path.dirname(_MODEL_FILE), exist_ok=True)
    with open(_MODEL_FILE, "w", encoding="utf-8") as out:
        json.dump(model, out, ensure_ascii=False, indent=2)

    return JsonResponse({"ok": True, "name": model["name"]})
