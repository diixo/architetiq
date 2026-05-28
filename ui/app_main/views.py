import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings


_DEFAULT_MODEL = {
    "name": "*New Model",
    "type": "model",
    "children": [
        {"name": "Strategy",                     "type": "node", "folder_type": "strategy",                "children": []},
        {"name": "Business",                     "type": "node", "folder_type": "business",                "children": []},
        {"name": "Application",                  "type": "node", "folder_type": "application",             "children": []},
        {"name": "Technology And Physical",      "type": "node", "folder_type": "technology",              "children": []},
        {"name": "Motivation",                   "type": "node", "folder_type": "motivation",              "children": []},
        {"name": "Implementation and Migration", "type": "node", "folder_type": "implementation_migration","children": []},
        {"name": "Other",                        "type": "node", "folder_type": "other",                   "children": []},
        {"name": "Relations",                    "type": "node", "folder_type": "relations",               "children": []},
        {"name": "Views",                        "type": "node", "folder_type": "diagrams",                "children": []},
    ]
}

_MODEL_FILE    = os.path.join(os.path.dirname(__file__), "data", "model.json")
_DIAGRAMS_DIR  = os.path.join(os.path.dirname(__file__), "data", "diagrams")

_GRAFICO_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "aspice-archi-prj", "model")
)

_XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"

_VIEW_TYPES = {"ArchimateDiagramModel", "SketchModel", "CanvasModel"}

_SKIP_TYPES = {"Relationship", "Relation"}


def _load_model():
    if os.path.exists(_MODEL_FILE):
        with open(_MODEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
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


def _build_archimate_xml(model):
    import xml.etree.ElementTree as ET
    NS  = 'http://www.archimatetool.com/archimate'
    XSI = 'http://www.w3.org/2001/XMLSchema-instance'
    ET.register_namespace('archimate', NS)
    ET.register_namespace('xsi', XSI)

    root = ET.Element(f'{{{NS}}}model')
    root.set('name', model.get('name', ''))
    root.set('id',   model.get('id', ''))
    root.set('version', '4.6.0')
    if model.get('purpose'):
        root.set('purpose', model['purpose'])

    def build_node(parent, node):
        if node['type'] == 'node':
            folder_type = _FOLDER_TYPE.get(node['name'],
                          node['name'].lower().replace(' ', '_'))
            folder = ET.SubElement(parent, 'folder')
            folder.set('name', node['name'])
            folder.set('id',   node.get('id', ''))
            folder.set('type', folder_type)
            for child in node.get('children', []):
                build_node(folder, child)
        elif node['type'] in ('element', 'view'):
            et = node.get('element_type', 'BusinessActor')
            elem = ET.SubElement(parent, 'element')
            elem.set(f'{{{XSI}}}type', f'archimate:{et}')
            elem.set('name', node.get('name', ''))
            elem.set('id',   node.get('id', ''))
            if node.get('documentation'):
                elem.set('documentation', node['documentation'])

    for child in model.get('children', []):
        build_node(root, child)

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
    diagram_file = _find_diagram_file(view_id)
    if diagram_file:
        try:
            data = _parse_diagram_file(diagram_file, _build_elements_index(model))
            data = _apply_saved_layout(data, view_id)
            return JsonResponse(data)
        except ET.ParseError as e:
            return JsonResponse({'error': str(e)}, status=500)

    # Fallback: basic info from model tree
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
    return JsonResponse(node)


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


def upload_model(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "No file provided"}, status=400)
    try:
        model = _parse_archimate(f.read())
    except ET.ParseError as e:
        return JsonResponse({"error": f"XML parse error: {e}"}, status=400)
    os.makedirs(os.path.dirname(_MODEL_FILE), exist_ok=True)
    with open(_MODEL_FILE, "w", encoding="utf-8") as out:
        json.dump(model, out, ensure_ascii=False, indent=2)
    return JsonResponse({"ok": True, "name": model["name"]})
