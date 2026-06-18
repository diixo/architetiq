import json
import os
import tempfile
import xml.etree.ElementTree as ET
from unittest.mock import patch
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from app_main.views import (
    _DEFAULT_MODEL, _parse_archimate,
    _parse_native_diagram, _build_elements_index,
    _read_archimate_bytes,
)


ARCHIMATE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
    ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
    ' name="Test Model" id="abc-001">'
    '<folder name="Business" type="business" id="f1">'
    '<element xsi:type="archimate:BusinessActor" id="e1" name="Customer"'
    ' documentation="Main customer"/>'
    '<element xsi:type="archimate:BusinessProcess" id="e2" name="Order Process"/>'
    '</folder>'
    '<folder name="Views" type="diagrams" id="f2">'
    '<element xsi:type="archimate:ArchimateDiagramModel" id="v1" name="Overview"/>'
    '</folder>'
    '</archimate:model>'
).encode('utf-8')

EXCHANGE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"'
    ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
    ' identifier="ex-001">'
    '<name>Exchange Model</name>'
    '<elements>'
    '<element identifier="el-1" xsi:type="BusinessActor"><name>Actor</name></element>'
    '<element identifier="el-2" xsi:type="ApplicationComponent"><name>App</name></element>'
    '</elements>'
    '<organizations>'
    '<item><label>Business</label><item identifierRef="el-1"/></item>'
    '<item><label>Application</label><item identifierRef="el-2"/></item>'
    '</organizations>'
    '</model>'
).encode('utf-8')


class ApiModelTests(TestCase):

    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)
        self._tmpdir = tempfile.mkdtemp()
        self._model_file = os.path.join(self._tmpdir, 'model.json')

    def _patch(self):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=self._model_file,
                              _GRAFICO_DIR='/nonexistent/grafico')

    # ── GET /api/model/ ────────────────────────────────────────────────────────

    def test_get_model_returns_default_when_no_file(self):
        """На чистом старте возвращает дефолтную модель с 9 папками."""
        with self._patch():
            r = self.client.get('/api/model/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['name'], '*New Model')
        self.assertEqual(len(data['children']), 9)
        names = [c['name'] for c in data['children']]
        self.assertIn('Business', names)
        self.assertIn('Views', names)

    def test_get_model_returns_saved_data(self):
        """После записи файла возвращает его содержимое."""
        saved = {'name': 'My Project', 'type': 'model', 'children': []}
        with open(self._model_file, 'w') as f:
            json.dump(saved, f)
        with self._patch():
            r = self.client.get('/api/model/')
        self.assertEqual(r.json()['name'], 'My Project')

    # ── POST /api/model/save/ ─────────────────────────────────────────────────

    def test_save_writes_to_disk(self):
        """Save записывает модель в model.json."""
        payload = {'name': 'Saved Model', 'type': 'model', 'children': []}
        with self._patch():
            r = self.client.post('/api/model/save/', json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['ok'])
        with open(self._model_file) as f:
            on_disk = json.load(f)
        self.assertEqual(on_disk['name'], 'Saved Model')

    def test_save_then_get_returns_same_data(self):
        """Сохранённые данные возвращаются при следующем GET."""
        payload = {'name': 'ASPICE', 'type': 'model',
                   'children': [{'name': 'Business', 'type': 'node', 'children': []}]}
        with self._patch():
            self.client.post('/api/model/save/', json.dumps(payload),
                             content_type='application/json')
            r = self.client.get('/api/model/')
        self.assertEqual(r.json()['name'], 'ASPICE')
        self.assertEqual(r.json()['children'][0]['name'], 'Business')

    def test_save_invalid_json_returns_400(self):
        with self._patch():
            r = self.client.post('/api/model/save/', b'not-json',
                                 content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_new_resets_model_to_default(self):
        """POST /api/model/new/ перезаписывает model.json дефолтной моделью."""
        payload = {'name': 'Precious ASPICE', 'type': 'model', 'children': []}
        with self._patch():
            self.client.post('/api/model/save/', json.dumps(payload),
                             content_type='application/json')
            r = self.client.post('/api/model/new/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['ok'])
        with open(self._model_file) as f:
            on_disk = json.load(f)
        self.assertEqual(on_disk['name'], _DEFAULT_MODEL['name'])

    def test_new_returns_405_on_get(self):
        """GET /api/model/new/ возвращает 405."""
        with self._patch():
            r = self.client.get('/api/model/new/')
        self.assertEqual(r.status_code, 405)

    def test_new_clears_diagrams_dir(self):
        """POST /api/model/new/ удаляет все .json из _DIAGRAMS_DIR."""
        tmpdir = tempfile.mkdtemp()
        diagrams_dir = os.path.join(tmpdir, 'diagrams')
        os.makedirs(diagrams_dir)
        # Write two fake diagram files
        for name in ('v1.json', 'v2.json'):
            with open(os.path.join(diagrams_dir, name), 'w') as f:
                json.dump({'id': name}, f)
        model_file = os.path.join(tmpdir, 'model.json')
        with patch.multiple('app_main.views',
                            _MODEL_FILE=model_file,
                            _DIAGRAMS_DIR=diagrams_dir,
                            _GRAFICO_DIR='/nonexistent'):
            r = self.client.post('/api/model/new/')
        self.assertEqual(r.status_code, 200)
        remaining = [f for f in os.listdir(diagrams_dir) if f.endswith('.json')]
        self.assertEqual(remaining, [], "Diagram files were not cleared by /api/model/new/")

    # ── GET /api/model/export/ ────────────────────────────────────────────────

    def test_export_returns_xml(self):
        """Export возвращает application/xml с .archimate расширением."""
        with self._patch():
            r = self.client.get('/api/model/export/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('application/xml', r['Content-Type'])
        self.assertIn('.archimate', r['Content-Disposition'])

    def test_export_contains_valid_archimate_root(self):
        """XML содержит корректный архимейт-неймспейс."""
        with self._patch():
            r = self.client.get('/api/model/export/')
        content = r.content.decode('utf-8')
        self.assertIn('<archimate:model', content)
        self.assertIn('xmlns:archimate="http://www.archimatetool.com/archimate"', content)

    def test_export_filename_from_model_name(self):
        """Имя файла формируется из названия модели."""
        payload = {'name': 'My Project', 'type': 'model', 'children': []}
        with self._patch():
            self.client.post('/api/model/save/', json.dumps(payload),
                             content_type='application/json')
            r = self.client.get('/api/model/export/')
        self.assertIn('My_Project.archimate', r['Content-Disposition'])

    def test_export_includes_folders_and_elements(self):
        """Экспортированный XML содержит папки и элементы."""
        payload = {
            'name': 'Export Test', 'type': 'model',
            'children': [{
                'name': 'Business', 'type': 'node', 'id': 'f1',
                'children': [{
                    'name': 'Actor', 'type': 'element',
                    'element_type': 'BusinessActor', 'id': 'e1',
                    'documentation': 'Test doc', 'children': []
                }]
            }]
        }
        with self._patch():
            self.client.post('/api/model/save/', json.dumps(payload),
                             content_type='application/json')
            r = self.client.get('/api/model/export/')
        content = r.content.decode('utf-8')
        self.assertIn('name="Business"', content)
        self.assertIn('name="Actor"', content)
        self.assertIn('archimate:BusinessActor', content)
        self.assertIn('Test doc', content)

    # ── POST /upload/ ─────────────────────────────────────────────────────────

    def test_upload_native_archimate(self):
        """.archimate файл парсится и сохраняется в model.json."""
        f = SimpleUploadedFile('test.archimate', ARCHIMATE_XML,
                               content_type='application/octet-stream')
        with self._patch():
            r = self.client.post('/upload/', {'file': f})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['name'], 'Test Model')

    def test_upload_creates_correct_tree(self):
        """После загрузки .archimate дерево содержит правильные папки и элементы."""
        f = SimpleUploadedFile('test.archimate', ARCHIMATE_XML,
                               content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f})
            r = self.client.get('/api/model/')
        model = r.json()
        self.assertEqual(model['name'], 'Test Model')
        business = next(c for c in model['children'] if c['name'] == 'Business')
        el_names = [e['name'] for e in business['children']]
        self.assertIn('Customer', el_names)
        self.assertIn('Order Process', el_names)
        customer = next(e for e in business['children'] if e['name'] == 'Customer')
        self.assertEqual(customer['element_type'], 'BusinessActor')
        self.assertEqual(customer['documentation'], 'Main customer')

    def test_upload_exchange_format(self):
        """Exchange Format (.xml) тоже парсится корректно."""
        f = SimpleUploadedFile('model.xml', EXCHANGE_XML,
                               content_type='application/octet-stream')
        with self._patch():
            r = self.client.post('/upload/', {'file': f})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['name'], 'Exchange Model')

    def test_upload_invalid_xml_returns_400(self):
        """Некорректный XML возвращает 400."""
        f = SimpleUploadedFile('bad.archimate', b'not xml at all',
                               content_type='application/octet-stream')
        with self._patch():
            r = self.client.post('/upload/', {'file': f})
        self.assertEqual(r.status_code, 400)

    def test_upload_no_file_returns_400(self):
        """Запрос без файла возвращает 400."""
        with self._patch():
            r = self.client.post('/upload/', {})
        self.assertEqual(r.status_code, 400)


class FolderTypeTests(TestCase):
    """folder_type сохраняется при парсинге и в дефолтной модели."""

    def test_default_model_has_folder_types(self):
        """Все папки дефолтной модели имеют folder_type."""
        expected = {
            'Strategy': 'strategy',
            'Business': 'business',
            'Application': 'application',
            'Technology & Physical': 'technology',
            'Motivation': 'motivation',
            'Implementation & Migration': 'implementation_migration',
            'Other': 'other',
            'Relations': 'relations',
            'Views': 'diagrams',
        }
        for folder in _DEFAULT_MODEL['children']:
            self.assertIn('folder_type', folder,
                          f"folder_type missing for {folder['name']}")
            self.assertEqual(folder['folder_type'], expected[folder['name']])

    def test_native_archimate_preserves_folder_type(self):
        """Парсинг .archimate сохраняет folder_type из атрибута type."""
        xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            b' name="M" id="m1">'
            b'<folder name="Business" type="business" id="f1">'
            b'<element xsi:type="archimate:BusinessActor" id="e1" name="Actor"/>'
            b'</folder>'
            b'<folder name="Strategy" type="strategy" id="f2"/>'
            b'</archimate:model>'
        )
        model = _parse_archimate(xml)
        business = next(c for c in model['children'] if c['name'] == 'Business')
        strategy = next(c for c in model['children'] if c['name'] == 'Strategy')
        self.assertEqual(business.get('folder_type'), 'business')
        self.assertEqual(strategy.get('folder_type'), 'strategy')

    def test_subfolder_without_type_has_no_folder_type(self):
        """Вложенная папка без атрибута type не получает folder_type."""
        xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            b' name="M" id="m1">'
            b'<folder name="Business" type="business" id="f1">'
            b'<folder name="SubGroup" id="f2">'
            b'<element xsi:type="archimate:BusinessActor" id="e1" name="Actor"/>'
            b'</folder>'
            b'</folder>'
            b'</archimate:model>'
        )
        model = _parse_archimate(xml)
        business = next(c for c in model['children'] if c['name'] == 'Business')
        subgroup = next(c for c in business['children'] if c['name'] == 'SubGroup')
        self.assertNotIn('folder_type', subgroup)

    def test_folder_type_survives_save_and_load(self):
        """folder_type сохраняется в model.json и загружается обратно."""
        import tempfile
        from unittest.mock import patch
        tmpdir = tempfile.mkdtemp()
        model_file = os.path.join(tmpdir, 'model.json')
        payload = {
            'name': 'Test', 'type': 'model',
            'children': [
                {'name': 'Business', 'type': 'node', 'folder_type': 'business',
                 'id': 'f1', 'children': []}
            ]
        }
        client = Client(enforce_csrf_checks=False)
        with patch.multiple('app_main.views',
                            _MODEL_FILE=model_file,
                            _GRAFICO_DIR='/nonexistent'):
            client.post('/api/model/save/', json.dumps(payload),
                        content_type='application/json')
            r = client.get('/api/model/')
        folder = r.json()['children'][0]
        self.assertEqual(folder.get('folder_type'), 'business')


class FolderIdMigrationTests(TestCase):
    """_migrate_folder_types додає id і folder_type до папок без них."""

    def _patch(self, model_file, grafico='/nonexistent'):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=model_file,
                              _GRAFICO_DIR=grafico)

    def test_default_model_all_folders_have_ids(self):
        """Усі папки DEFAULT_MODEL мають id."""
        from app_main.views import _DEFAULT_MODEL
        for folder in _DEFAULT_MODEL['children']:
            self.assertIn('id', folder, f"No id for {folder['name']}")
            self.assertTrue(folder['id'], f"Empty id for {folder['name']}")

    def test_migrate_adds_id_to_folder_without_id(self):
        """Міграція додає id до папки без id."""
        from app_main.views import _migrate_folder_types
        model = {
            'name': 'M', 'type': 'model',
            'children': [
                {'name': 'Business', 'type': 'node', 'folder_type': 'business', 'children': []},
                {'name': 'Strategy', 'type': 'node', 'folder_type': 'strategy', 'children': []},
            ]
        }
        result = _migrate_folder_types(model)
        for folder in result['children']:
            self.assertIn('id', folder)
            self.assertTrue(folder['id'])

    def test_migrate_preserves_existing_id(self):
        """Міграція не змінює існуючий id."""
        from app_main.views import _migrate_folder_types
        model = {
            'name': 'M', 'type': 'model',
            'children': [
                {'id': 'my-custom-uuid', 'name': 'Business', 'type': 'node',
                 'folder_type': 'business', 'children': []},
            ]
        }
        result = _migrate_folder_types(model)
        self.assertEqual(result['children'][0]['id'], 'my-custom-uuid')

    def test_migrate_adds_folder_type_by_name(self):
        """Міграція додає folder_type за іменем папки."""
        from app_main.views import _migrate_folder_types
        model = {
            'name': 'M', 'type': 'model',
            'children': [
                {'id': 'x1', 'name': 'Motivation', 'type': 'node', 'children': []},
                {'id': 'x2', 'name': 'Relations',  'type': 'node', 'children': []},
            ]
        }
        result = _migrate_folder_types(model)
        self.assertEqual(result['children'][0]['folder_type'], 'motivation')
        self.assertEqual(result['children'][1]['folder_type'], 'relations')

    def test_api_returns_folders_with_ids(self):
        """GET /api/model/ повертає папки з id."""
        import tempfile
        tmpdir = tempfile.mkdtemp()
        model_file = os.path.join(tmpdir, 'model.json')
        # Save a model without ids
        payload = {
            'name': 'Test', 'type': 'model',
            'children': [
                {'name': 'Business', 'type': 'node', 'folder_type': 'business', 'children': []},
            ]
        }
        with open(model_file, 'w') as f:
            json.dump(payload, f)
        client = Client(enforce_csrf_checks=False)
        with self._patch(model_file):
            r = client.get('/api/model/')
        data = r.json()
        business = next(c for c in data['children'] if c['name'] == 'Business')
        self.assertIn('id', business)
        self.assertTrue(business['id'])

    def test_generated_ids_are_unique_per_folder(self):
        """Згенеровані id унікальні для кожної папки."""
        from app_main.views import _migrate_folder_types
        model = {
            'name': 'M', 'type': 'model',
            'children': [
                {'name': n, 'type': 'node', 'children': []}
                for n in ['Strategy', 'Business', 'Application', 'Technology And Physical',
                          'Motivation', 'Implementation and Migration', 'Other', 'Relations', 'Views']
            ]
        }
        result = _migrate_folder_types(model)
        ids = [c['id'] for c in result['children']]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate ids generated")


# ── Native diagram parsing ─────────────────────────────────────────────────────

ARCHIMATE_WITH_DIAGRAM = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
    ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
    ' name="DiagTest" id="m1">'
    '<folder name="Business" type="business" id="f1">'
    '<element xsi:type="archimate:BusinessActor" id="e1" name="Customer"/>'
    '<element xsi:type="archimate:BusinessProcess" id="e2" name="Handle Claim"/>'
    '</folder>'
    '<folder name="Relations" type="relations" id="f2">'
    '<element xsi:type="archimate:AssignmentRelationship" id="r1"'
    ' source="e1" target="e2"/>'
    '</folder>'
    '<folder name="Views" type="diagrams" id="f3">'
    '<element xsi:type="archimate:ArchimateDiagramModel" name="Overview" id="v1">'
    '<child xsi:type="archimate:DiagramObject" id="d1" archimateElement="e1">'
    '<bounds x="100" y="200" width="120" height="55"/>'
    '</child>'
    '<child xsi:type="archimate:DiagramObject" id="d2" archimateElement="e2">'
    '<bounds x="300" y="200" width="120" height="55"/>'
    '<sourceConnection xsi:type="archimate:Connection" id="c1"'
    ' source="d2" target="d1" archimateRelationship="r1"/>'
    '</child>'
    '</element>'
    '</folder>'
    '</archimate:model>'
).encode('utf-8')


class NativeDiagramParsingTests(TestCase):
    """Tests for parsing diagram visual data from native .archimate format."""

    def _make_view_elem(self):
        root = ET.fromstring(ARCHIMATE_WITH_DIAGRAM)
        for elem in root.iter():
            if elem.get('id') == 'v1':
                return elem
        self.fail("v1 not found")

    def _make_elements_index(self):
        model = _parse_archimate(ARCHIMATE_WITH_DIAGRAM)
        return _build_elements_index(model)

    # ── Basic node parsing ────────────────────────────────────────────────────

    def test_nodes_extracted(self):
        """DiagramObject children become element nodes."""
        view = self._make_view_elem()
        idx = self._make_elements_index()
        data = _parse_native_diagram(view, idx)
        self.assertEqual(len(data['nodes']), 2)

    def test_node_has_position_and_size(self):
        """Node bounds (x, y, width, height) are parsed correctly."""
        view = self._make_view_elem()
        idx = self._make_elements_index()
        data = _parse_native_diagram(view, idx)
        d1 = next(n for n in data['nodes'] if n['id'] == 'd1')
        self.assertEqual(d1['x'], 100)
        self.assertEqual(d1['y'], 200)
        self.assertEqual(d1['width'], 120)
        self.assertEqual(d1['height'], 55)

    def test_node_resolves_element_info(self):
        """element_id and element_type are resolved from the elements index."""
        view = self._make_view_elem()
        idx = self._make_elements_index()
        data = _parse_native_diagram(view, idx)
        d1 = next(n for n in data['nodes'] if n['id'] == 'd1')
        self.assertEqual(d1['element_id'], 'e1')
        self.assertEqual(d1['element_type'], 'BusinessActor')
        self.assertEqual(d1['name'], 'Customer')

    def test_node_type_is_element(self):
        """DiagramObject nodes have type='element'."""
        view = self._make_view_elem()
        data = _parse_native_diagram(view, self._make_elements_index())
        for n in data['nodes']:
            self.assertEqual(n['type'], 'element')

    # ── Edge parsing ──────────────────────────────────────────────────────────

    def test_edges_extracted(self):
        """sourceConnection elements become edges."""
        view = self._make_view_elem()
        data = _parse_native_diagram(view, self._make_elements_index())
        self.assertEqual(len(data['edges']), 1)

    def test_edge_source_and_target(self):
        """Edge source/target reference diagram object IDs."""
        view = self._make_view_elem()
        data = _parse_native_diagram(view, self._make_elements_index())
        edge = data['edges'][0]
        self.assertEqual(edge['source'], 'd2')
        self.assertEqual(edge['target'], 'd1')

    def test_edge_type_resolved_from_relationship(self):
        """Edge type is resolved from the archimateRelationship ID in the index."""
        view = self._make_view_elem()
        data = _parse_native_diagram(view, self._make_elements_index())
        edge = data['edges'][0]
        self.assertEqual(edge['type'], 'AssignmentRelationship')

    def test_edge_vertices_empty_when_no_bendpoints(self):
        """Edges without bendpoints have empty vertices list."""
        view = self._make_view_elem()
        data = _parse_native_diagram(view, self._make_elements_index())
        self.assertEqual(data['edges'][0]['vertices'], [])

    # ── Diagram metadata ──────────────────────────────────────────────────────

    def test_diagram_id_and_name(self):
        """Parsed diagram has correct id and name."""
        view = self._make_view_elem()
        data = _parse_native_diagram(view, self._make_elements_index())
        self.assertEqual(data['id'], 'v1')
        self.assertEqual(data['name'], 'Overview')

    # ── Group rendering ───────────────────────────────────────────────────────

    def test_group_node_parsed(self):
        """archimate:Group children become type='group' nodes."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:Group" id="g1" name="MyGroup" fillColor="#ffeeaa">'
            b'<bounds x="10" y="20" width="300" height="200"/>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        data = _parse_native_diagram(view, {})
        self.assertEqual(len(data['nodes']), 1)
        g = data['nodes'][0]
        self.assertEqual(g['type'], 'group')
        self.assertEqual(g['name'], 'MyGroup')
        self.assertEqual(g['fill_color'], '#ffeeaa')
        self.assertEqual(g['x'], 10)
        self.assertEqual(g['y'], 20)

    # ── Note rendering ────────────────────────────────────────────────────────

    def test_note_node_parsed(self):
        """archimate:Note becomes type='note' node with content."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:Note" id="n1">'
            b'<bounds x="5" y="5" width="200" height="80"/>'
            b'<content>This is a note</content>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        data = _parse_native_diagram(view, {})
        self.assertEqual(len(data['nodes']), 1)
        note = data['nodes'][0]
        self.assertEqual(note['type'], 'note')
        self.assertEqual(note['name'], 'This is a note')

    # ── Bendpoints ────────────────────────────────────────────────────────────

    def test_bendpoints_resolved_to_absolute(self):
        """Relative bendpoints are converted to absolute coordinates."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:DiagramObject" id="da" archimateElement="x1">'
            b'<bounds x="0" y="0" width="120" height="55"/>'
            b'<sourceConnection xsi:type="archimate:Connection" id="ca"'
            b' source="da" target="db" archimateRelationship="r99">'
            b'<bendpoint startX="10" startY="20" endX="-10" endY="-20"/>'
            b'</sourceConnection>'
            b'</child>'
            b'<child xsi:type="archimate:DiagramObject" id="db" archimateElement="x2">'
            b'<bounds x="200" y="0" width="120" height="55"/>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        idx = {'x1': {'name': 'A', 'element_type': 'BusinessActor'},
               'x2': {'name': 'B', 'element_type': 'BusinessActor'},
               'r99': {'name': '', 'element_type': 'AssociationRelationship'}}
        data = _parse_native_diagram(view, idx)
        self.assertEqual(len(data['edges']), 1)
        # Vertices should exist (one bendpoint → one vertex)
        self.assertEqual(len(data['edges'][0]['vertices']), 1)
        v = data['edges'][0]['vertices'][0]
        self.assertIn('x', v)
        self.assertIn('y', v)


class NativeDiagramEndpointTests(TestCase):
    """Integration tests: /api/diagram/<view_id>/ serves native .archimate diagrams."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)
        self._tmpdir = tempfile.mkdtemp()
        self._model_file = os.path.join(self._tmpdir, 'model.json')
        self._diagrams_dir = os.path.join(self._tmpdir, 'diagrams')

    def _patch(self):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=self._model_file,
                              _DIAGRAMS_DIR=self._diagrams_dir,
                              _GRAFICO_DIR='/nonexistent/grafico')

    def test_upload_native_does_not_store_source(self):
        """Upload native .archimate — model.json must NOT contain _source."""
        f = SimpleUploadedFile('test.archimate', ARCHIMATE_WITH_DIAGRAM,
                               content_type='application/octet-stream')
        with self._patch():
            r = self.client.post('/upload/', {'file': f})
        self.assertEqual(r.status_code, 200)
        with open(self._model_file) as fh:
            saved_model = json.load(fh)
        self.assertNotIn('_source', saved_model)

    def test_upload_native_creates_diagram_json(self):
        """Upload native .archimate — diagram JSON is written to _DIAGRAMS_DIR."""
        f = SimpleUploadedFile('test.archimate', ARCHIMATE_WITH_DIAGRAM,
                               content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f})
        diag_file = os.path.join(self._diagrams_dir, 'v1.json')
        self.assertTrue(os.path.isfile(diag_file))

    def test_upload_exchange_does_not_record_source(self):
        """Exchange Format upload does NOT set _source in model.json."""
        f = SimpleUploadedFile('model.xml', EXCHANGE_XML,
                               content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f})
        with open(self._model_file) as fh:
            saved_model = json.load(fh)
        self.assertNotIn('_source', saved_model)

    def test_api_diagram_returns_nodes_from_native(self):
        """GET /api/diagram/v1/ returns nodes parsed from uploaded .archimate."""
        f = SimpleUploadedFile('test.archimate', ARCHIMATE_WITH_DIAGRAM,
                               content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f})
            r = self.client.get('/api/diagram/v1/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('nodes', data)
        self.assertIn('edges', data)
        self.assertEqual(len(data['nodes']), 2)
        self.assertEqual(len(data['edges']), 1)

    def test_api_diagram_node_has_element_type(self):
        """Nodes returned by /api/diagram/ have element_type resolved."""
        f = SimpleUploadedFile('test.archimate', ARCHIMATE_WITH_DIAGRAM,
                               content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f})
            r = self.client.get('/api/diagram/v1/')
        data = r.json()
        types = {n['element_type'] for n in data['nodes']}
        self.assertIn('BusinessActor', types)
        self.assertIn('BusinessProcess', types)

    def test_api_diagram_edge_type_resolved(self):
        """Edge type is AssignmentRelationship (resolved from model)."""
        f = SimpleUploadedFile('test.archimate', ARCHIMATE_WITH_DIAGRAM,
                               content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f})
            r = self.client.get('/api/diagram/v1/')
        data = r.json()
        self.assertEqual(data['edges'][0]['type'], 'AssignmentRelationship')

    def test_api_diagram_empty_for_new_view(self):
        """New view (not in native XML) returns empty nodes/edges, not 404."""
        # Save a model with a view not in any native file
        model = {
            'name': 'M', 'type': 'model', 'id': 'm1',
            'children': [{
                'name': 'Views', 'type': 'node', 'folder_type': 'diagrams',
                'id': 'fv', 'children': [
                    {'id': 'new-view-1', 'name': 'New View',
                     'type': 'view', 'element_type': 'ArchimateDiagramModel',
                     'documentation': '', 'children': []}
                ]
            }]
        }
        with open(self._model_file, 'w') as f:
            json.dump(model, f)
        with self._patch():
            r = self.client.get('/api/diagram/new-view-1/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['nodes'], [])
        self.assertEqual(data['edges'], [])


class NativeDiagramParsingEdgeCasesTests(TestCase):
    """Edge cases and advanced scenarios for native .archimate diagram parsing."""

    # ── Nested / embedded elements ────────────────────────────────────────────

    def test_nested_diagram_object_has_parent_id(self):
        """DiagramObject nested inside another DiagramObject gets parent_id set."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:DiagramObject" id="outer" archimateElement="x1">'
            b'<bounds x="100" y="100" width="300" height="200"/>'
            b'<child xsi:type="archimate:DiagramObject" id="inner" archimateElement="x2">'
            b'<bounds x="20" y="30" width="120" height="55"/>'
            b'</child>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        idx = {
            'x1': {'name': 'Container', 'element_type': 'ApplicationComponent'},
            'x2': {'name': 'Inner',     'element_type': 'DataObject'},
        }
        data = _parse_native_diagram(view, idx)
        self.assertEqual(len(data['nodes']), 2)
        inner = next(n for n in data['nodes'] if n['id'] == 'inner')
        self.assertEqual(inner['parent_id'], 'outer')

    def test_nested_element_has_absolute_coordinates(self):
        """Nested DiagramObject x/y are absolute (parent offset added)."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:DiagramObject" id="parent" archimateElement="x1">'
            b'<bounds x="100" y="200" width="300" height="200"/>'
            b'<child xsi:type="archimate:DiagramObject" id="child_el" archimateElement="x2">'
            b'<bounds x="10" y="20" width="80" height="40"/>'
            b'</child>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        idx = {
            'x1': {'name': 'P', 'element_type': 'ApplicationComponent'},
            'x2': {'name': 'C', 'element_type': 'DataObject'},
        }
        data = _parse_native_diagram(view, idx)
        child = next(n for n in data['nodes'] if n['id'] == 'child_el')
        # Absolute = parent(100,200) + relative(10,20)
        self.assertEqual(child['x'], 110)
        self.assertEqual(child['y'], 220)

    def test_top_level_element_has_no_parent_id(self):
        """Top-level DiagramObject has no parent_id key."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:DiagramObject" id="top" archimateElement="x1">'
            b'<bounds x="0" y="0" width="120" height="55"/>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        data = _parse_native_diagram(view, {'x1': {'name': 'A', 'element_type': 'BusinessActor'}})
        top = data['nodes'][0]
        self.assertNotIn('parent_id', top)

    # ── Multiple views ────────────────────────────────────────────────────────

    def test_correct_view_returned_when_multiple_views(self):
        """When file has multiple views, each parses independently."""
        xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            b' name="Multi" id="m1">'
            b'<folder name="Business" type="business" id="f1">'
            b'<element xsi:type="archimate:BusinessActor" id="e1" name="Actor"/>'
            b'<element xsi:type="archimate:BusinessProcess" id="e2" name="Process"/>'
            b'</folder>'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="View A" id="va">'
            b'<child xsi:type="archimate:DiagramObject" id="da1" archimateElement="e1">'
            b'<bounds x="10" y="10" width="120" height="55"/>'
            b'</child>'
            b'</element>'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="View B" id="vb">'
            b'<child xsi:type="archimate:DiagramObject" id="db1" archimateElement="e2">'
            b'<bounds x="50" y="50" width="120" height="55"/>'
            b'</child>'
            b'<child xsi:type="archimate:DiagramObject" id="db2" archimateElement="e1">'
            b'<bounds x="200" y="50" width="120" height="55"/>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        idx = _build_elements_index(_parse_archimate(xml))
        view_a = next(e for e in root.iter() if e.get('id') == 'va')
        view_b = next(e for e in root.iter() if e.get('id') == 'vb')
        data_a = _parse_native_diagram(view_a, idx)
        data_b = _parse_native_diagram(view_b, idx)

        self.assertEqual(data_a['name'], 'View A')
        self.assertEqual(len(data_a['nodes']), 1)
        self.assertEqual(data_b['name'], 'View B')
        self.assertEqual(len(data_b['nodes']), 2)

    # ── Unknown / missing element IDs ─────────────────────────────────────────

    def test_unknown_archimate_element_does_not_crash(self):
        """DiagramObject referencing non-existent element_id returns empty name/type."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:DiagramObject" id="d1" archimateElement="nonexistent-id">'
            b'<bounds x="0" y="0" width="120" height="55"/>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        data = _parse_native_diagram(view, {})  # empty index
        self.assertEqual(len(data['nodes']), 1)
        node = data['nodes'][0]
        self.assertEqual(node['element_id'], 'nonexistent-id')
        self.assertEqual(node['name'], '')
        self.assertEqual(node['element_type'], '')

    def test_unknown_relationship_type_defaults_to_empty(self):
        """sourceConnection with unknown archimateRelationship ID returns type=''."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:DiagramObject" id="da" archimateElement="e1">'
            b'<bounds x="0" y="0" width="120" height="55"/>'
            b'<sourceConnection xsi:type="archimate:Connection" id="ca"'
            b' source="da" target="db" archimateRelationship="UNKNOWN"/>'
            b'</child>'
            b'<child xsi:type="archimate:DiagramObject" id="db" archimateElement="e2">'
            b'<bounds x="200" y="0" width="120" height="55"/>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        idx = {
            'e1': {'name': 'A', 'element_type': 'BusinessActor'},
            'e2': {'name': 'B', 'element_type': 'BusinessActor'},
        }
        data = _parse_native_diagram(view, idx)
        self.assertEqual(data['edges'][0]['type'], '')

    # ── Missing bounds ────────────────────────────────────────────────────────

    def test_missing_bounds_uses_defaults(self):
        """DiagramObject without <bounds> defaults to x=0, y=0, w=120, h=55."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:DiagramObject" id="d1" archimateElement="e1">'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        data = _parse_native_diagram(view, {'e1': {'name': 'A', 'element_type': 'BusinessActor'}})
        node = data['nodes'][0]
        self.assertEqual(node['x'], 0)
        self.assertEqual(node['y'], 0)
        self.assertEqual(node['width'], 120)
        self.assertEqual(node['height'], 55)

    # ── Empty view ────────────────────────────────────────────────────────────

    def test_empty_view_returns_empty_nodes_and_edges(self):
        """View with no children returns nodes=[], edges=[]."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="Empty" id="ve"/>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 've')
        data = _parse_native_diagram(view, {})
        self.assertEqual(data['nodes'], [])
        self.assertEqual(data['edges'], [])

    # ── Multiple bendpoints ───────────────────────────────────────────────────

    def test_multiple_bendpoints_produce_multiple_vertices(self):
        """Two bendpoints → two absolute vertices in output."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:DiagramObject" id="da" archimateElement="e1">'
            b'<bounds x="0" y="0" width="120" height="55"/>'
            b'<sourceConnection xsi:type="archimate:Connection" id="ca"'
            b' source="da" target="db" archimateRelationship="r1">'
            b'<bendpoint startX="5" startY="10" endX="-5" endY="-10"/>'
            b'<bendpoint startX="15" startY="20" endX="-15" endY="-20"/>'
            b'</sourceConnection>'
            b'</child>'
            b'<child xsi:type="archimate:DiagramObject" id="db" archimateElement="e2">'
            b'<bounds x="300" y="0" width="120" height="55"/>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        idx = {
            'e1': {'name': 'A', 'element_type': 'BusinessActor'},
            'e2': {'name': 'B', 'element_type': 'BusinessActor'},
            'r1': {'name': '', 'element_type': 'FlowRelationship'},
        }
        data = _parse_native_diagram(view, idx)
        self.assertEqual(len(data['edges'][0]['vertices']), 2)



class RealFileTests(TestCase):
    """Tests using the actual Test-project.archimate from data/archi/."""

    REAL_FILE = os.path.join(
        os.path.dirname(__file__), '..', '..', 'data', 'archi', 'Test-project.archimate'
    )

    def setUp(self):
        if not os.path.isfile(self.REAL_FILE):
            self.skipTest('Test-project.archimate not found')

    def test_real_file_parses_model_tree(self):
        """Real .archimate file parses without error and returns a model tree."""
        with open(self.REAL_FILE, 'rb') as f:
            content = f.read()
        model = _parse_archimate(content)
        self.assertEqual(model['name'], 'TestModel')
        folder_names = [c['name'] for c in model['children']]
        self.assertIn('Business', folder_names)
        self.assertIn('Views', folder_names)

    def test_real_file_views_folder_contains_default_view(self):
        """Views folder in real file contains Default View."""
        with open(self.REAL_FILE, 'rb') as f:
            content = f.read()
        model = _parse_archimate(content)
        views = next(c for c in model['children'] if c['name'] == 'Views')
        view_names = [v['name'] for v in views['children']]
        self.assertIn('Default View', view_names)

    def test_real_file_diagram_parses_nodes(self):
        """Real file Default View diagram has 2 nodes (two BusinessActors)."""
        from app_main.views import _parse_native_diagram, _build_elements_index
        import xml.etree.ElementTree as ET
        with open(self.REAL_FILE, 'rb') as f:
            content = f.read()
        model = _parse_archimate(content)
        idx = _build_elements_index(model)
        root = ET.fromstring(content)
        # Find the Default View element
        view_elem = None
        for elem in root.iter():
            if elem.get('id') == 'id-94d17ed16bdf42bd8b890db3db0a9f65':
                view_elem = elem
                break
        self.assertIsNotNone(view_elem, "Default View element not found")
        data = _parse_native_diagram(view_elem, idx)
        self.assertEqual(len(data['nodes']), 2)
        # Both should be BusinessActor
        for node in data['nodes']:
            self.assertEqual(node['element_type'], 'BusinessActor')
            self.assertEqual(node['name'], 'Business Actor')


class DiagramSaveTests(TestCase):
    """Tests for POST /api/diagram/<view_id>/save/ — merge semantics."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)
        self._tmpdir = tempfile.mkdtemp()
        self._model_file = os.path.join(self._tmpdir, 'model.json')
        self._diagrams_dir = os.path.join(self._tmpdir, 'diagrams')
        os.makedirs(self._diagrams_dir)

    def _patch(self):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=self._model_file,
                              _DIAGRAMS_DIR=self._diagrams_dir,
                              _GRAFICO_DIR='/nonexistent')

    def _diag(self, view_id):
        with open(os.path.join(self._diagrams_dir, f'{view_id}.json')) as f:
            return json.load(f)

    def test_save_creates_diagram_file_when_none_exists(self):
        """POST to a new view creates the diagram JSON file."""
        payload = {'view_id': 'new-view', 'nodes': [
            {'id': 'n1', 'x': 10, 'y': 20, 'width': 120, 'height': 55,
             'node_type': 'element', 'element_id': 'e1', 'name': 'Actor'},
        ], 'user_edges': []}
        with self._patch():
            r = self.client.post('/api/diagram/new-view/save/',
                                 json.dumps(payload), content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['ok'])
        self.assertTrue(os.path.isfile(os.path.join(self._diagrams_dir, 'new-view.json')))

    def test_save_updates_existing_node_positions(self):
        """Save updates positions; edges whose endpoints are still present are kept."""
        initial = {
            'id': 'v1', 'name': 'V', 'documentation': '',
            'nodes': [
                {'id': 'n1', 'type': 'element', 'element_id': 'e1',
                 'element_type': 'BusinessActor', 'name': 'Actor',
                 'x': 0, 'y': 0, 'width': 120, 'height': 55},
                {'id': 'n2', 'type': 'element', 'element_id': 'e2',
                 'element_type': 'BusinessProcess', 'name': 'Process',
                 'x': 200, 'y': 0, 'width': 120, 'height': 55},
            ],
            'edges': [
                {'id': 'c1', 'source': 'n1', 'target': 'n2',
                 'type': 'AssignmentRelationship', 'relation_id': 'r1', 'vertices': []},
            ],
            'user_edges': [],
        }
        with open(os.path.join(self._diagrams_dir, 'v1.json'), 'w') as f:
            json.dump(initial, f)

        payload = {'view_id': 'v1', 'nodes': [
            {'id': 'n1', 'x': 100, 'y': 200, 'width': 150, 'height': 70},
            {'id': 'n2', 'x': 300, 'y': 200, 'width': 150, 'height': 70},
        ], 'user_edges': []}
        with self._patch():
            self.client.post('/api/diagram/v1/save/',
                             json.dumps(payload), content_type='application/json')

        saved = self._diag('v1')
        n1 = next(n for n in saved['nodes'] if n['id'] == 'n1')
        self.assertEqual(n1['x'], 100)
        self.assertEqual(n1['y'], 200)
        # edge preserved — both endpoints still present
        self.assertEqual(len(saved['edges']), 1)
        self.assertEqual(saved['edges'][0]['relation_id'], 'r1')

    def test_save_drops_edge_when_node_deleted(self):
        """Edge whose source or target is absent from canvas is dropped on save."""
        initial = {
            'id': 'v1', 'name': 'V', 'documentation': '',
            'nodes': [
                {'id': 'n1', 'type': 'element', 'element_id': 'e1',
                 'element_type': 'BusinessActor', 'name': 'A',
                 'x': 0, 'y': 0, 'width': 120, 'height': 55},
                {'id': 'n2', 'type': 'element', 'element_id': 'e2',
                 'element_type': 'BusinessProcess', 'name': 'B',
                 'x': 200, 'y': 0, 'width': 120, 'height': 55},
            ],
            'edges': [
                {'id': 'c1', 'source': 'n1', 'target': 'n2',
                 'type': 'AssignmentRelationship', 'relation_id': 'r1', 'vertices': []},
            ],
            'user_edges': [],
        }
        with open(os.path.join(self._diagrams_dir, 'v1.json'), 'w') as f:
            json.dump(initial, f)

        # Canvas only has n1 — n2 was deleted
        payload = {'view_id': 'v1',
                   'nodes': [{'id': 'n1', 'x': 0, 'y': 0, 'width': 120, 'height': 55}],
                   'user_edges': []}
        with self._patch():
            self.client.post('/api/diagram/v1/save/',
                             json.dumps(payload), content_type='application/json')

        saved = self._diag('v1')
        self.assertEqual(len(saved['nodes']), 1)
        self.assertEqual(len(saved['edges']), 0)

    def test_save_canvas_is_source_of_truth_for_nodes(self):
        """Nodes absent from canvas payload are removed from diagram JSON."""
        initial = {
            'id': 'v1', 'name': 'V', 'documentation': '',
            'nodes': [
                {'id': 'n1', 'type': 'element', 'element_id': 'e1',
                 'element_type': 'BusinessActor', 'name': 'Old',
                 'x': 0, 'y': 0, 'width': 120, 'height': 55},
            ],
            'edges': [], 'user_edges': [],
        }
        with open(os.path.join(self._diagrams_dir, 'v1.json'), 'w') as f:
            json.dump(initial, f)

        # Canvas has n1 (existing) + new-node (added from palette)
        payload = {'view_id': 'v1', 'nodes': [
            {'id': 'n1', 'x': 0, 'y': 0, 'width': 120, 'height': 55},
            {'id': 'new-node', 'x': 50, 'y': 60, 'width': 120, 'height': 55,
             'node_type': 'element', 'element_id': 'e2',
             'element_type': 'BusinessProcess', 'name': 'New'},
        ], 'user_edges': []}
        with self._patch():
            self.client.post('/api/diagram/v1/save/',
                             json.dumps(payload), content_type='application/json')

        ids = {n['id'] for n in self._diag('v1')['nodes']}
        self.assertIn('n1', ids)
        self.assertIn('new-node', ids)

    def test_save_preserves_archimate_fields_from_existing_diagram(self):
        """element_id / element_type / parent_id are kept from diagram JSON
        even when canvas payload omits them (loaded nodes don't resend metadata)."""
        initial = {
            'id': 'v1', 'name': 'V', 'documentation': '',
            'nodes': [
                {'id': 'n1', 'type': 'element', 'element_id': 'e1',
                 'element_type': 'BusinessActor', 'name': 'Actor',
                 'parent_id': 'grp1',
                 'x': 0, 'y': 0, 'width': 120, 'height': 55},
            ],
            'edges': [], 'user_edges': [],
        }
        with open(os.path.join(self._diagrams_dir, 'v1.json'), 'w') as f:
            json.dump(initial, f)

        # Canvas sends only geometry — no element_id / element_type / parent_id
        payload = {'view_id': 'v1',
                   'nodes': [{'id': 'n1', 'x': 50, 'y': 50, 'width': 120, 'height': 55}],
                   'user_edges': []}
        with self._patch():
            self.client.post('/api/diagram/v1/save/',
                             json.dumps(payload), content_type='application/json')

        saved_node = self._diag('v1')['nodes'][0]
        self.assertEqual(saved_node['element_id'],   'e1')
        self.assertEqual(saved_node['element_type'], 'BusinessActor')
        self.assertEqual(saved_node['name'],         'Actor')
        self.assertEqual(saved_node.get('parent_id'), 'grp1')

    def test_save_replaces_user_edges(self):
        """user_edges is replaced entirely on each save."""
        initial = {
            'id': 'v1', 'name': 'V', 'documentation': '',
            'nodes': [], 'edges': [],
            'user_edges': [
                {'id': 'old', 'source_cell': 'a', 'target_cell': 'b',
                 'type': 'AssociationRelationship', 'vertices': []},
            ],
        }
        with open(os.path.join(self._diagrams_dir, 'v1.json'), 'w') as f:
            json.dump(initial, f)

        payload = {'view_id': 'v1', 'nodes': [], 'user_edges': [
            {'id': 'new', 'source_cell': 'x', 'target_cell': 'y',
             'type': 'FlowRelationship', 'vertices': []},
        ]}
        with self._patch():
            self.client.post('/api/diagram/v1/save/',
                             json.dumps(payload), content_type='application/json')

        saved = self._diag('v1')
        self.assertEqual(len(saved['user_edges']), 1)
        self.assertEqual(saved['user_edges'][0]['id'], 'new')

    def test_save_requires_post(self):
        """GET to /api/diagram/<id>/save/ returns 405."""
        with self._patch():
            r = self.client.get('/api/diagram/v1/save/')
        self.assertEqual(r.status_code, 405)

    def test_save_invalid_json_returns_400(self):
        """POST with invalid JSON body returns 400."""
        with self._patch():
            r = self.client.post('/api/diagram/v1/save/', b'not-json',
                                 content_type='application/json')
        self.assertEqual(r.status_code, 400)


class RelationIdTests(TestCase):
    """relation_id is parsed from archimateRelationship and preserved in diagram JSON."""

    def test_edge_has_relation_id(self):
        """_parse_native_diagram sets relation_id from archimateRelationship attr."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:DiagramObject" id="da" archimateElement="e1">'
            b'<bounds x="0" y="0" width="120" height="55"/>'
            b'<sourceConnection xsi:type="archimate:Connection" id="ca"'
            b' source="da" target="db" archimateRelationship="rel-42"/>'
            b'</child>'
            b'<child xsi:type="archimate:DiagramObject" id="db" archimateElement="e2">'
            b'<bounds x="200" y="0" width="120" height="55"/>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        data = _parse_native_diagram(view, {})
        self.assertEqual(data['edges'][0]['relation_id'], 'rel-42')

    def test_edge_relation_id_empty_when_no_archimate_relationship(self):
        """Connection without archimateRelationship gets relation_id=''."""
        xml = (
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="M" id="m1">'
            b'<folder name="Views" type="diagrams" id="fv">'
            b'<element xsi:type="archimate:ArchimateDiagramModel" name="V" id="vx">'
            b'<child xsi:type="archimate:DiagramObject" id="da" archimateElement="e1">'
            b'<bounds x="0" y="0" width="120" height="55"/>'
            b'<sourceConnection xsi:type="archimate:Connection" id="ca"'
            b' source="da" target="db"/>'
            b'</child>'
            b'<child xsi:type="archimate:DiagramObject" id="db" archimateElement="e2">'
            b'<bounds x="200" y="0" width="120" height="55"/>'
            b'</child>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        root = ET.fromstring(xml)
        view = next(e for e in root.iter() if e.get('id') == 'vx')
        data = _parse_native_diagram(view, {})
        self.assertEqual(data['edges'][0]['relation_id'], '')

    def test_upload_diagram_json_preserves_relation_id(self):
        """Diagram JSON created on upload keeps relation_id in edges."""
        client = Client(enforce_csrf_checks=False)
        tmpdir = tempfile.mkdtemp()
        diagrams_dir = os.path.join(tmpdir, 'diagrams')
        f = SimpleUploadedFile('test.archimate', ARCHIMATE_WITH_DIAGRAM,
                               content_type='application/octet-stream')
        with patch.multiple('app_main.views',
                            _MODEL_FILE=os.path.join(tmpdir, 'model.json'),
                            _DIAGRAMS_DIR=diagrams_dir,
                            _GRAFICO_DIR='/nonexistent'):
            client.post('/upload/', {'file': f})
        with open(os.path.join(diagrams_dir, 'v1.json')) as fh:
            diag = json.load(fh)
        self.assertEqual(len(diag['edges']), 1)
        self.assertEqual(diag['edges'][0]['relation_id'], 'r1')


class ExportWithDiagramDataTests(TestCase):
    """Export generates <child> and <sourceConnection> from diagram JSON files."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)
        self._tmpdir = tempfile.mkdtemp()
        self._model_file = os.path.join(self._tmpdir, 'model.json')
        self._diagrams_dir = os.path.join(self._tmpdir, 'diagrams')
        os.makedirs(self._diagrams_dir)

    def _patch(self):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=self._model_file,
                              _DIAGRAMS_DIR=self._diagrams_dir,
                              _GRAFICO_DIR='/nonexistent')

    def _write_model(self):
        model = {
            'name': 'ExportTest', 'type': 'model', 'id': 'mod1',
            'children': [
                {'name': 'Business', 'type': 'node', 'id': 'fb',
                 'folder_type': 'business', 'children': [
                    {'id': 'e1', 'name': 'Actor', 'type': 'element',
                     'element_type': 'BusinessActor', 'children': []},
                    {'id': 'e2', 'name': 'Process', 'type': 'element',
                     'element_type': 'BusinessProcess', 'children': []},
                ]},
                {'name': 'Relations', 'type': 'node', 'id': 'fr',
                 'folder_type': 'relations', 'children': [
                    {'id': 'r1', 'name': '', 'type': 'element',
                     'element_type': 'AssignmentRelationship', 'children': []},
                ]},
                {'name': 'Views', 'type': 'node', 'id': 'fv',
                 'folder_type': 'diagrams', 'children': [
                    {'id': 'v1', 'name': 'Overview', 'type': 'view',
                     'element_type': 'ArchimateDiagramModel',
                     'documentation': '', 'children': []},
                ]},
            ]
        }
        with open(self._model_file, 'w') as f:
            json.dump(model, f)

    def _write_diagram(self, view_id, diagram):
        with open(os.path.join(self._diagrams_dir, f'{view_id}.json'), 'w') as f:
            json.dump(diagram, f)

    def test_export_includes_child_elements(self):
        """Exported XML contains <child> elements from diagram JSON."""
        self._write_model()
        self._write_diagram('v1', {
            'id': 'v1', 'name': 'Overview', 'documentation': '',
            'nodes': [
                {'id': 'd1', 'type': 'element', 'element_id': 'e1',
                 'element_type': 'BusinessActor', 'name': 'Actor',
                 'x': 100, 'y': 100, 'width': 120, 'height': 55},
            ],
            'edges': [], 'user_edges': [],
        })
        with self._patch():
            r = self.client.get('/api/model/export/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('archimateElement="e1"', r.content.decode())

    def test_export_child_has_correct_bounds(self):
        """Exported <child> has <bounds> matching saved positions."""
        self._write_model()
        self._write_diagram('v1', {
            'id': 'v1', 'name': 'Overview', 'documentation': '',
            'nodes': [
                {'id': 'd1', 'type': 'element', 'element_id': 'e1',
                 'element_type': 'BusinessActor', 'name': 'Actor',
                 'x': 150, 'y': 250, 'width': 130, 'height': 60},
            ],
            'edges': [], 'user_edges': [],
        })
        with self._patch():
            xml = self.client.get('/api/model/export/').content.decode()
        self.assertIn('x="150"', xml)
        self.assertIn('y="250"', xml)
        self.assertIn('width="130"', xml)
        self.assertIn('height="60"', xml)

    def test_export_includes_source_connection_with_relation_id(self):
        """Exported <sourceConnection> carries archimateRelationship from relation_id."""
        self._write_model()
        self._write_diagram('v1', {
            'id': 'v1', 'name': 'Overview', 'documentation': '',
            'nodes': [
                {'id': 'd1', 'type': 'element', 'element_id': 'e1',
                 'element_type': 'BusinessActor', 'name': 'Actor',
                 'x': 0, 'y': 0, 'width': 120, 'height': 55},
                {'id': 'd2', 'type': 'element', 'element_id': 'e2',
                 'element_type': 'BusinessProcess', 'name': 'Process',
                 'x': 200, 'y': 0, 'width': 120, 'height': 55},
            ],
            'edges': [
                {'id': 'c1', 'source': 'd1', 'target': 'd2',
                 'type': 'AssignmentRelationship', 'relation_id': 'r1', 'vertices': []},
            ],
            'user_edges': [],
        })
        with self._patch():
            xml = self.client.get('/api/model/export/').content.decode()
        self.assertIn('sourceConnection', xml)
        self.assertIn('archimateRelationship="r1"', xml)

    def test_export_note_uses_archimate_note_type(self):
        """Note nodes export with xsi:type='archimate:Note', not DiagramModelNote."""
        self._write_model()
        self._write_diagram('v1', {
            'id': 'v1', 'name': 'Overview', 'documentation': '',
            'nodes': [
                {'id': 'n1', 'type': 'note', 'name': 'Some note text',
                 'x': 10, 'y': 10, 'width': 100, 'height': 40},
            ],
            'edges': [], 'user_edges': [],
        })
        with self._patch():
            xml = self.client.get('/api/model/export/').content.decode()
        self.assertIn('archimate:Note', xml)
        self.assertNotIn('archimate:DiagramModelNote', xml)

    def test_export_note_content_present(self):
        """Exported note has <content> child element with the note text."""
        self._write_model()
        self._write_diagram('v1', {
            'id': 'v1', 'name': 'Overview', 'documentation': '',
            'nodes': [
                {'id': 'n1', 'type': 'note', 'name': 'Hello note',
                 'x': 0, 'y': 0, 'width': 100, 'height': 40},
            ],
            'edges': [], 'user_edges': [],
        })
        with self._patch():
            xml = self.client.get('/api/model/export/').content.decode()
        self.assertIn('<content>Hello note</content>', xml)

    def test_export_nested_element_uses_relative_bounds(self):
        """Element nested inside a group exports bounds relative to the group, not absolute."""
        import xml.etree.ElementTree as ET
        self._write_model()
        self._write_diagram('v1', {
            'id': 'v1', 'name': 'Overview', 'documentation': '',
            'nodes': [
                {'id': 'g1', 'type': 'group', 'name': 'My Group',
                 'x': 100, 'y': 100, 'width': 300, 'height': 200},
                {'id': 'd1', 'type': 'element', 'element_id': 'e1',
                 'element_type': 'BusinessActor', 'name': 'Actor',
                 'x': 150, 'y': 130, 'width': 120, 'height': 55,
                 'parent_id': 'g1'},
            ],
            'edges': [], 'user_edges': [],
        })
        with self._patch():
            raw = self.client.get('/api/model/export/').content
        root = ET.fromstring(raw)
        # Find the group child
        group_child = next(
            (e for e in root.iter()
             if e.get('{http://www.w3.org/2001/XMLSchema-instance}type') == 'archimate:Group'),
            None
        )
        self.assertIsNotNone(group_child, "Group <child> not found in export")
        # Element must be nested inside the group, not a sibling
        nested = next(
            (e for e in group_child.iter()
             if e.get('{http://www.w3.org/2001/XMLSchema-instance}type') == 'archimate:DiagramObject'),
            None
        )
        self.assertIsNotNone(nested, "Element not nested inside group")
        # Bounds must be relative: (150-100, 130-100) = (50, 30)
        bounds = nested.find('bounds')
        self.assertIsNotNone(bounds)
        self.assertEqual(bounds.get('x'), '50', "x should be relative to group (150-100=50)")
        self.assertEqual(bounds.get('y'), '30', "y should be relative to group (130-100=30)")

    def test_export_relation_with_source_target(self):
        """Relation element with source/target in model exports those attributes."""
        import json
        model = {
            'name': 'RelTest', 'type': 'model', 'id': 'mod2',
            'children': [
                {'name': 'Business', 'type': 'node', 'id': 'fb',
                 'folder_type': 'business', 'children': [
                    {'id': 'e1', 'name': 'A', 'type': 'element',
                     'element_type': 'BusinessActor', 'children': []},
                    {'id': 'e2', 'name': 'B', 'type': 'element',
                     'element_type': 'BusinessProcess', 'children': []},
                ]},
                {'name': 'Relations', 'type': 'node', 'id': 'fr',
                 'folder_type': 'relations', 'children': [
                    {'id': 'rel1', 'name': '', 'type': 'element',
                     'element_type': 'AssociationRelationship',
                     'source': 'e1', 'target': 'e2', 'children': []},
                ]},
                {'name': 'Views', 'type': 'node', 'id': 'fv',
                 'folder_type': 'diagrams', 'children': []},
            ]
        }
        with open(self._model_file, 'w') as f:
            json.dump(model, f)
        with self._patch():
            xml = self.client.get('/api/model/export/').content.decode()
        self.assertIn('archimate:AssociationRelationship', xml)
        self.assertIn('source="e1"', xml)
        self.assertIn('target="e2"', xml)

    def test_export_view_without_diagram_json_has_no_children(self):
        """View with no diagram JSON exports as an empty view element."""
        self._write_model()
        # No diagram JSON for v1
        with self._patch():
            xml = self.client.get('/api/model/export/').content.decode()
        self.assertIn('name="Overview"', xml)
        self.assertNotIn('archimateElement=', xml)

    def test_api_diagram_returns_404_for_unknown_view(self):
        """GET /api/diagram/<id>/ → 404 when not in model and no diagram file."""
        model = {'name': 'M', 'type': 'model', 'id': 'm1', 'children': []}
        with open(self._model_file, 'w') as f:
            json.dump(model, f)
        with self._patch():
            r = self.client.get('/api/diagram/totally-unknown-id/')
        self.assertEqual(r.status_code, 404)

    def test_upload_diagram_json_has_empty_user_edges(self):
        """Diagram JSON created on upload has user_edges=[]."""
        f = SimpleUploadedFile('test.archimate', ARCHIMATE_WITH_DIAGRAM,
                               content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f})
        with open(os.path.join(self._diagrams_dir, 'v1.json')) as fh:
            diag = json.load(fh)
        self.assertEqual(diag['user_edges'], [])


class ZipArchimateTests(TestCase):
    """Tests for ZIP-wrapped .archimate files (contain images)."""

    def test_read_plain_xml_unchanged(self):
        """Plain XML bytes pass through unchanged."""
        xml = b'<?xml version="1.0"?><root/>'
        result = _read_archimate_bytes(xml)
        self.assertEqual(result, xml)

    def test_read_zip_with_model_xml(self):
        """ZIP archive with model.xml returns the inner XML."""
        import io, zipfile
        inner_xml = b'<?xml version="1.0"?><archimate:model name="Zipped"/>'
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('model.xml', inner_xml)
            z.writestr('images/icon.png', b'\x89PNG\r\n')
        zip_bytes = buf.getvalue()

        result = _read_archimate_bytes(zip_bytes)
        self.assertEqual(result, inner_xml)

    def test_upload_zipped_archimate(self):
        """Uploading a ZIP .archimate file parses the model correctly."""
        import io, zipfile
        inner_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            b' name="ZippedModel" id="z1">'
            b'<folder name="Business" type="business" id="f1">'
            b'<element xsi:type="archimate:BusinessActor" id="e1" name="Actor"/>'
            b'</folder>'
            b'</archimate:model>'
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('model.xml', inner_xml)
        zip_bytes = buf.getvalue()

        tmpdir = tempfile.mkdtemp()
        model_file = os.path.join(tmpdir, 'model.json')
        client = Client(enforce_csrf_checks=False)
        f = SimpleUploadedFile('model.archimate', zip_bytes,
                               content_type='application/octet-stream')
        with patch.multiple('app_main.views',
                            _MODEL_FILE=model_file,
                            _DIAGRAMS_DIR=os.path.join(tmpdir, 'diagrams'),
                            _GRAFICO_DIR='/nonexistent'):
            r = client.post('/upload/', {'file': f})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['name'], 'ZippedModel')


class DocumentationFormatTests(TestCase):
    """Export writes documentation/purpose as child XML elements (Archi ecore requires kind=element)."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)
        self._tmpdir = tempfile.mkdtemp()
        self._model_file = os.path.join(self._tmpdir, 'model.json')
        self._diagrams_dir = os.path.join(self._tmpdir, 'diagrams')
        os.makedirs(self._diagrams_dir)

    def _patch(self):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=self._model_file,
                              _DIAGRAMS_DIR=self._diagrams_dir,
                              _GRAFICO_DIR='/nonexistent')

    def test_export_documentation_as_child_element(self):
        """documentation is exported as <documentation> child, not as XML attribute."""
        payload = {
            'name': 'Doc Test', 'type': 'model', 'id': 'm1',
            'children': [{
                'name': 'Business', 'type': 'node', 'id': 'f1',
                'folder_type': 'business', 'children': [{
                    'id': 'e1', 'name': 'Actor', 'type': 'element',
                    'element_type': 'BusinessActor',
                    'documentation': 'Detailed description here.',
                    'children': [],
                }]
            }]
        }
        with self._patch():
            self.client.post('/api/model/save/', json.dumps(payload),
                             content_type='application/json')
            r = self.client.get('/api/model/export/')
        xml = r.content.decode('utf-8')
        # Must be a child element, NOT an attribute
        self.assertIn('<documentation>Detailed description here.</documentation>', xml)
        self.assertNotIn('documentation="Detailed description here."', xml)

    def test_export_purpose_as_child_element(self):
        """purpose is exported as <purpose> child element, not as XML attribute."""
        payload = {
            'name': 'Purpose Test', 'type': 'model', 'id': 'm1',
            'purpose': 'This is the model purpose.',
            'children': [],
        }
        with self._patch():
            self.client.post('/api/model/save/', json.dumps(payload),
                             content_type='application/json')
            r = self.client.get('/api/model/export/')
        xml = r.content.decode('utf-8')
        self.assertIn('<purpose>This is the model purpose.</purpose>', xml)
        self.assertNotIn('purpose="This is the model purpose."', xml)

    def test_import_reads_documentation_from_child_element(self):
        """Import reads <documentation> child element (Archi native format)."""
        xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            b' name="DocModel" id="m1">'
            b'<folder name="Business" type="business" id="f1">'
            b'<element xsi:type="archimate:BusinessActor" id="e1" name="Actor">'
            b'<documentation>Actor description from child element.</documentation>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        model = _parse_archimate(xml)
        business = next(c for c in model['children'] if c['name'] == 'Business')
        actor = next(e for e in business['children'] if e['name'] == 'Actor')
        self.assertEqual(actor['documentation'], 'Actor description from child element.')

    def test_import_reads_purpose_from_child_element(self):
        """Import reads <purpose> child element (Archi native format)."""
        xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            b' name="PurposeModel" id="m1">'
            b'<purpose>Model purpose text.</purpose>'
            b'<folder name="Business" type="business" id="f1"/>'
            b'</archimate:model>'
        )
        model = _parse_archimate(xml)
        self.assertEqual(model.get('purpose'), 'Model purpose text.')

    def test_export_documentation_roundtrip(self):
        """documentation survives upload → export round-trip as child element."""
        xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<archimate:model xmlns:archimate="http://www.archimatetool.com/archimate"'
            b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            b' name="RoundTrip" id="m1">'
            b'<folder name="Business" type="business" id="f1">'
            b'<element xsi:type="archimate:BusinessActor" id="e1" name="Actor">'
            b'<documentation>Round-trip documentation.</documentation>'
            b'</element>'
            b'</folder>'
            b'</archimate:model>'
        )
        f = SimpleUploadedFile('test.archimate', xml,
                               content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f})
            r = self.client.get('/api/model/export/')
        exported = r.content.decode('utf-8')
        self.assertIn('<documentation>Round-trip documentation.</documentation>', exported)
        self.assertNotIn('documentation="Round-trip documentation."', exported)


class AspiceExportTests(TestCase):
    """Export tests using the real ASPICE grafico project from data/aspice-archi-prj/model/."""

    GRAFICO_DIR = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'aspice-archi-prj', 'model')
    )

    def setUp(self):
        if not os.path.isdir(self.GRAFICO_DIR):
            self.skipTest('ASPICE grafico project not found')
        self.client = Client(enforce_csrf_checks=False)
        self._tmpdir = tempfile.mkdtemp()
        self._model_file = os.path.join(self._tmpdir, 'model.json')
        self._diagrams_dir = os.path.join(self._tmpdir, 'diagrams')
        os.makedirs(self._diagrams_dir)

    def _patch(self):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=self._model_file,
                              _DIAGRAMS_DIR=self._diagrams_dir,
                              _GRAFICO_DIR=self.GRAFICO_DIR)

    def _load_and_export(self):
        with self._patch():
            r_load = self.client.post('/api/model/load-aspice/')
            r_export = self.client.get('/api/model/export/')
        return r_load, r_export

    # ── Load ─────────────────────────────────────────────────────────────────

    def test_aspice_loads_successfully(self):
        """api_model_load_aspice returns 200 and ASPICE model name."""
        with self._patch():
            r = self.client.post('/api/model/load-aspice/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['ok'])
        self.assertEqual(r.json()['name'], 'ASPICE')

    def test_aspice_model_has_expected_folders(self):
        """Loaded ASPICE model contains standard ArchiMate folders."""
        with self._patch():
            self.client.post('/api/model/load-aspice/')
            r = self.client.get('/api/model/')
        model = r.json()
        folder_names = {c['name'] for c in model['children']}
        for expected in ('Business', 'Relations', 'Views'):
            self.assertIn(expected, folder_names, f"Folder '{expected}' missing from ASPICE model")

    def test_aspice_business_folder_has_elements(self):
        """Business folder contains elements after loading ASPICE."""
        with self._patch():
            self.client.post('/api/model/load-aspice/')
            r = self.client.get('/api/model/')
        model = r.json()
        business = next(c for c in model['children'] if c['name'] == 'Business')
        self.assertGreater(len(business['children']), 0, "Business folder is empty")

    def test_aspice_elements_have_documentation(self):
        """ASPICE elements preserve documentation text after loading."""
        with self._patch():
            self.client.post('/api/model/load-aspice/')
            r = self.client.get('/api/model/')
        model = r.json()
        business = next(c for c in model['children'] if c['name'] == 'Business')
        elements_with_docs = [e for e in business['children'] if e.get('documentation')]
        self.assertGreater(len(elements_with_docs), 0, "No elements have documentation")

    def test_aspice_views_folder_has_views(self):
        """Views folder contains view entries after loading ASPICE."""
        with self._patch():
            self.client.post('/api/model/load-aspice/')
            r = self.client.get('/api/model/')
        model = r.json()
        def count_views(node):
            count = 0
            if node.get('type') == 'view':
                count += 1
            for ch in node.get('children', []):
                count += count_views(ch)
            return count
        views_folder = next(c for c in model['children'] if c['name'] == 'Views')
        total_views = count_views(views_folder)
        self.assertGreater(total_views, 0, "Views folder has no views")

    # ── Export structure ──────────────────────────────────────────────────────

    def test_aspice_export_returns_200(self):
        """ASPICE export returns HTTP 200 with XML content type."""
        r_load, r_export = self._load_and_export()
        self.assertEqual(r_export.status_code, 200)
        self.assertIn('application/xml', r_export['Content-Type'])

    def test_aspice_export_is_valid_xml(self):
        """Exported ASPICE archimate file is well-formed XML."""
        import xml.etree.ElementTree as ET
        _, r_export = self._load_and_export()
        try:
            ET.fromstring(r_export.content)
        except ET.ParseError as e:
            self.fail(f"Exported XML is not well-formed: {e}")

    def test_aspice_export_has_archimate_root(self):
        """Exported XML has <archimate:model> root with correct namespace."""
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        self.assertIn('<archimate:model', xml)
        self.assertIn('xmlns:archimate="http://www.archimatetool.com/archimate"', xml)

    def test_aspice_export_model_name(self):
        """Exported XML carries the ASPICE model name."""
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        self.assertIn('name="ASPICE"', xml)

    def test_aspice_export_has_business_folder(self):
        """Exported XML contains a Business folder."""
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        self.assertIn('name="Business"', xml)
        self.assertIn('type="business"', xml)

    def test_aspice_export_has_views_folder(self):
        """Exported XML contains a Views folder."""
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        self.assertIn('type="diagrams"', xml)

    def test_aspice_export_documentation_as_child_element(self):
        """Exported ASPICE XML uses <documentation> child elements, not attributes."""
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        self.assertIn('<documentation>', xml,
                      "documentation should be a child element in exported XML")
        self.assertNotIn('documentation="', xml,
                         "documentation must NOT be an XML attribute")

    def test_aspice_export_purpose_as_child_element(self):
        """Exported ASPICE XML uses <purpose> child element, not attribute."""
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        # ASPICE has a purpose — verify it's a child element if present
        if 'purpose' in xml.lower():
            self.assertNotIn('purpose="', xml,
                             "purpose must NOT be an XML attribute")

    def test_aspice_export_has_elements(self):
        """Exported XML contains ArchiMate elements (BusinessFunction etc.)."""
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        self.assertIn('archimate:BusinessFunction', xml)

    def test_aspice_export_has_relations(self):
        """Exported XML contains relation elements in Relations folder."""
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        self.assertIn('type="relations"', xml)

    def test_aspice_export_views_have_diagram_children(self):
        """ASPICE views contain <child> diagram objects after grafico diagram parsing."""
        import xml.etree.ElementTree as ET
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        self.assertIn('<child ', xml, "No <child> elements found — grafico diagram parsing may have failed")

    def test_aspice_export_child_has_bounds(self):
        """Exported <child> elements contain <bounds> with position data."""
        import xml.etree.ElementTree as ET
        _, r_export = self._load_and_export()
        root = ET.fromstring(r_export.content)
        children_with_bounds = 0
        for elem in root.iter():
            tag = elem.tag.split('}')[-1]
            if tag == 'child':
                for sub in elem:
                    if sub.tag.split('}')[-1] == 'bounds':
                        children_with_bounds += 1
                        break
        self.assertGreater(children_with_bounds, 0, "No <child> with <bounds> found in export")

    def test_aspice_relations_have_source_and_target(self):
        """Exported relation elements carry source and target attributes."""
        import xml.etree.ElementTree as ET
        _, r_export = self._load_and_export()
        root = ET.fromstring(r_export.content)
        relations_with_src_tgt = [
            e for e in root.iter()
            if e.get('source') and e.get('target')
            and 'Relationship' in (e.get(
                '{http://www.w3.org/2001/XMLSchema-instance}type', '') or '')
        ]
        self.assertGreater(
            len(relations_with_src_tgt), 0,
            "No relation elements with source+target found — "
            "grafico relations may still be skipped during parse"
        )

    def test_aspice_no_diagram_model_note_type(self):
        """Notes must not be exported with the abstract DiagramModelNote class."""
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        self.assertNotIn(
            'archimate:DiagramModelNote', xml,
            "DiagramModelNote is abstract in Archi — use archimate:Note instead"
        )

    def test_aspice_archimate_relationship_ids_resolved(self):
        """Every archimateRelationship ID in the export exists as an element."""
        import xml.etree.ElementTree as ET, re
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        root = ET.fromstring(r_export.content)

        # Collect all element ids in the model
        element_ids = {e.get('id') for e in root.iter() if e.get('id')}

        # Collect all archimateRelationship refs from sourceConnections
        refs = re.findall(r'archimateRelationship="([^"]+)"', xml)
        unresolved = [rid for rid in refs if rid not in element_ids]
        self.assertEqual(
            unresolved, [],
            f"Unresolved archimateRelationship IDs: {unresolved[:5]}..."
        )

    def test_aspice_views_subfolders_have_diagrams_type(self):
        """All folders nested inside the Views (diagrams) folder must have type='diagrams'.

        Regression test: subfolders without an explicit folder_type used to get
        a generated slug like 'spl_supply_process_group' instead of 'diagrams',
        which prevented Archi from recognising views inside them and caused
        every model element to appear as 'Unused element' in the validator.
        """
        import xml.etree.ElementTree as ET
        _, r_export = self._load_and_export()
        root = ET.fromstring(r_export.content)

        diagrams_folder = next(
            (f for f in root.iter('folder') if f.get('type') == 'diagrams'),
            None,
        )
        self.assertIsNotNone(diagrams_folder, "No folder with type='diagrams' in export")

        wrong = []
        def check(elem):
            for child in elem:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if tag == 'folder':
                    if child.get('type') != 'diagrams':
                        wrong.append((child.get('name', ''), child.get('type', '')))
                    check(child)
        check(diagrams_folder)

        self.assertEqual(
            wrong, [],
            f"Subfolders inside Views with wrong type: {wrong[:5]}"
        )

    def test_aspice_archimate_element_refs_resolved(self):
        """Every archimateElement ID in diagram children resolves to a model element."""
        import xml.etree.ElementTree as ET, re
        _, r_export = self._load_and_export()
        xml = r_export.content.decode('utf-8')
        root = ET.fromstring(r_export.content)

        XSI = 'http://www.w3.org/2001/XMLSchema-instance'
        view_types = {'ArchimateDiagramModel', 'SketchModel', 'CanvasModel'}

        # Collect IDs of model concept elements (not views, not folders)
        model_element_ids = set()
        for elem in root.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag != 'element':
                continue
            xsi = elem.get(f'{{{XSI}}}type', '').split(':')[-1]
            if xsi and xsi not in view_types:
                eid = elem.get('id')
                if eid:
                    model_element_ids.add(eid)

        refs = re.findall(r'archimateElement="([^"]+)"', xml)
        unresolved = [rid for rid in refs if rid not in model_element_ids]
        self.assertEqual(
            unresolved, [],
            f"Unresolved archimateElement IDs ({len(unresolved)} total): {unresolved[:5]}..."
        )


class SubfolderTypeExportTests(TestCase):
    """Unit tests for folder type inheritance in _build_archimate_xml."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)
        self._tmpdir = tempfile.mkdtemp()
        self._model_file = os.path.join(self._tmpdir, 'model.json')
        self._diagrams_dir = os.path.join(self._tmpdir, 'diagrams')
        os.makedirs(self._diagrams_dir)

    def _patch(self):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=self._model_file,
                              _DIAGRAMS_DIR=self._diagrams_dir,
                              _GRAFICO_DIR='/nonexistent')

    def _export_model(self, model):
        with open(self._model_file, 'w') as f:
            json.dump(model, f)
        with self._patch():
            return self.client.get('/api/model/export/').content.decode()

    def test_views_subfolder_without_folder_type_gets_diagrams_type(self):
        """A subfolder inside Views with no folder_type must export as type='diagrams'.

        Regression: previously generated 'process_group' slug, preventing Archi
        from loading views nested inside the subfolder.
        """
        import xml.etree.ElementTree as ET
        model = {
            'name': 'T', 'type': 'model', 'id': 'm1',
            'children': [{
                'name': 'Views', 'type': 'node', 'id': 'fv',
                'folder_type': 'diagrams', 'children': [{
                    # Subfolder with no folder_type — simulates Grafico import
                    'name': 'Process Group', 'type': 'node', 'id': 'fsub',
                    'children': [{
                        'id': 'v1', 'name': 'My View', 'type': 'view',
                        'element_type': 'ArchimateDiagramModel', 'children': [],
                    }],
                }],
            }],
        }
        xml = self._export_model(model)
        root = ET.fromstring(xml.encode())
        subfolder = next(
            (f for f in root.iter('folder') if f.get('name') == 'Process Group'),
            None,
        )
        self.assertIsNotNone(subfolder, "Subfolder 'Process Group' not found in export")
        self.assertEqual(
            subfolder.get('type'), 'diagrams',
            f"Subfolder type should be 'diagrams', got {subfolder.get('type')!r}"
        )

    def test_business_subfolder_without_folder_type_gets_business_type(self):
        """A subfolder inside Business with no folder_type inherits 'business' type."""
        import xml.etree.ElementTree as ET
        model = {
            'name': 'T', 'type': 'model', 'id': 'm1',
            'children': [{
                'name': 'Business', 'type': 'node', 'id': 'fb',
                'folder_type': 'business', 'children': [{
                    'name': 'Sub', 'type': 'node', 'id': 'fsub',
                    'children': [{
                        'id': 'e1', 'name': 'Actor', 'type': 'element',
                        'element_type': 'BusinessActor', 'children': [],
                    }],
                }],
            }],
        }
        xml = self._export_model(model)
        root = ET.fromstring(xml.encode())
        subfolder = next(
            (f for f in root.iter('folder') if f.get('name') == 'Sub'),
            None,
        )
        self.assertIsNotNone(subfolder, "Subfolder 'Sub' not found in export")
        self.assertEqual(
            subfolder.get('type'), 'business',
            f"Subfolder type should be 'business', got {subfolder.get('type')!r}"
        )

    def test_top_level_folder_with_explicit_folder_type_not_overridden(self):
        """Explicit folder_type on a top-level node is never overridden by inheritance."""
        import xml.etree.ElementTree as ET
        model = {
            'name': 'T', 'type': 'model', 'id': 'm1',
            'children': [{
                'name': 'Motivation', 'type': 'node', 'id': 'fm',
                'folder_type': 'motivation', 'children': [],
            }],
        }
        xml = self._export_model(model)
        root = ET.fromstring(xml.encode())
        folder = next(
            (f for f in root.iter('folder') if f.get('name') == 'Motivation'),
            None,
        )
        self.assertIsNotNone(folder)
        self.assertEqual(folder.get('type'), 'motivation')


class TargetConnectionsExportTests(TestCase):
    """Regression tests: exported <child> target elements must have targetConnections attribute.

    Without this attribute Archi cannot resolve arrow endpoints and all connections
    converge to a single point in the diagram.
    """

    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)
        self._tmpdir = tempfile.mkdtemp()
        self._model_file = os.path.join(self._tmpdir, 'model.json')
        self._diagrams_dir = os.path.join(self._tmpdir, 'diagrams')
        os.makedirs(self._diagrams_dir)

    def _patch(self):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=self._model_file,
                              _DIAGRAMS_DIR=self._diagrams_dir,
                              _GRAFICO_DIR='/nonexistent')

    def _export(self, model, layout):
        """Write model + diagram layout, run export, return parsed XML root."""
        with open(self._model_file, 'w') as f:
            json.dump(model, f)
        view_id = layout['view_id']
        diag_file = os.path.join(self._diagrams_dir, f'{view_id}.json')
        with open(diag_file, 'w') as f:
            json.dump(layout, f)
        with self._patch():
            resp = self.client.get('/api/model/export/')
        self.assertEqual(resp.status_code, 200)
        return ET.fromstring(resp.content)

    def test_target_child_gets_targetConnections_attribute(self):
        """Target <child> element must have targetConnections listing the connection ID.

        Regression: previously the attribute was never set, causing Archi to render
        all arrows converging to one point.
        """
        model = {
            'name': 'T', 'type': 'model', 'id': 'm1',
            'children': [{
                'name': 'Views', 'type': 'node', 'id': 'fv',
                'folder_type': 'diagrams', 'children': [{
                    'id': 'v1', 'name': 'V', 'type': 'view',
                    'element_type': 'ArchimateDiagramModel', 'children': [],
                }],
            }],
        }
        layout = {
            'view_id': 'v1',
            'nodes': [
                {'id': 'n1', 'type': 'element', 'element_id': 'e1',
                 'x': 0, 'y': 0, 'width': 120, 'height': 55, 'parent_id': None},
                {'id': 'n2', 'type': 'element', 'element_id': 'e2',
                 'x': 200, 'y': 0, 'width': 120, 'height': 55, 'parent_id': None},
            ],
            'edges': [
                {'id': 'c1', 'source': 'n1', 'target': 'n2',
                 'relation_id': 'r1', 'vertices': []},
            ],
            'user_edges': [],
        }
        root = self._export(model, layout)
        n2 = next((c for c in root.iter('child') if c.get('id') == 'n2'), None)
        self.assertIsNotNone(n2, "<child id='n2'> not found in export")
        tc = n2.get('targetConnections')
        self.assertIsNotNone(tc,
            "Target <child> is missing 'targetConnections' attribute — "
            "Archi will render all arrows converging to one point")
        self.assertIn('c1', tc.split(),
            f"Connection 'c1' not listed in targetConnections={tc!r}")

    def test_multiple_incoming_connections_all_listed(self):
        """When two connections target the same element, both IDs appear in targetConnections."""
        model = {
            'name': 'T', 'type': 'model', 'id': 'm1',
            'children': [{
                'name': 'Views', 'type': 'node', 'id': 'fv',
                'folder_type': 'diagrams', 'children': [{
                    'id': 'v1', 'name': 'V', 'type': 'view',
                    'element_type': 'ArchimateDiagramModel', 'children': [],
                }],
            }],
        }
        layout = {
            'view_id': 'v1',
            'nodes': [
                {'id': 'n1', 'type': 'element', 'element_id': 'e1',
                 'x': 0, 'y': 0, 'width': 120, 'height': 55, 'parent_id': None},
                {'id': 'n2', 'type': 'element', 'element_id': 'e2',
                 'x': 200, 'y': 0, 'width': 120, 'height': 55, 'parent_id': None},
                {'id': 'n3', 'type': 'element', 'element_id': 'e3',
                 'x': 400, 'y': 0, 'width': 120, 'height': 55, 'parent_id': None},
            ],
            'edges': [
                {'id': 'c1', 'source': 'n1', 'target': 'n3',
                 'relation_id': 'r1', 'vertices': []},
                {'id': 'c2', 'source': 'n2', 'target': 'n3',
                 'relation_id': 'r2', 'vertices': []},
            ],
            'user_edges': [],
        }
        root = self._export(model, layout)
        n3 = next((c for c in root.iter('child') if c.get('id') == 'n3'), None)
        self.assertIsNotNone(n3, "<child id='n3'> not found in export")
        tc_ids = n3.get('targetConnections', '').split()
        self.assertIn('c1', tc_ids,
            f"Connection 'c1' not in targetConnections={n3.get('targetConnections')!r}")
        self.assertIn('c2', tc_ids,
            f"Connection 'c2' not in targetConnections={n3.get('targetConnections')!r}")
