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
        {"name": "Strategy", "type": "node", "children": []},
        {"name": "Business", "type": "node", "children": []},
        {"name": "Application", "type": "node", "children": []},
        {"name": "Technology And Physical", "type": "node", "children": []},
        {"name": "Motivation", "type": "node", "children": []},
        {"name": "Implementation and Migration", "type": "node", "children": []},
        {"name": "Other", "type": "node", "children": []},
        {"name": "Relations", "type": "node", "children": []},
        {"name": "Views", "type": "node", "children": []},
    ]
}

_MODEL_FILE = os.path.join(os.path.dirname(__file__), "data", "model.json")

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
    # First run: try Grafico folder, fall back to default
    grafico_root = os.path.join(_GRAFICO_DIR, "folder.xml")
    if os.path.isfile(grafico_root):
        model = _parse_grafico(_GRAFICO_DIR)
    else:
        model = _DEFAULT_MODEL
    os.makedirs(os.path.dirname(_MODEL_FILE), exist_ok=True)
    with open(_MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    return model


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
        return {
            "name": elem.get("name", ""),
            "type": "node",
            "id": elem.get("id", ""),
            "children": children,
        }

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
        folder_id = folder_elem.get("id", "")

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

        return {
            "name": folder_name,
            "type": "node",
            "id": folder_id,
            "children": children,
        }

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
