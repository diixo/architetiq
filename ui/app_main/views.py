import os
import json
from django.shortcuts import render, redirect


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


def _load_model():
    if os.path.exists(_MODEL_FILE):
        with open(_MODEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    os.makedirs(os.path.dirname(_MODEL_FILE), exist_ok=True)
    with open(_MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(_DEFAULT_MODEL, f, ensure_ascii=False, indent=2)
    return _DEFAULT_MODEL


def main(request):
    model = _load_model()
    return render(request, "app_main/main.html", context={
        "title": "ArchitetIQ",
        "description": "ArchitetIQ description",
        "model": model,
    })
