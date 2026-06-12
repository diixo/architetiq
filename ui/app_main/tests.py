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
    _read_archimate_bytes, _find_model_view,
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

    def test_new_does_not_overwrite_disk(self):
        """New — это клиентская операция: сервер не имеет /api/model/new/."""
        payload = {'name': 'Precious ASPICE', 'type': 'model', 'children': []}
        with self._patch():
            self.client.post('/api/model/save/', json.dumps(payload),
                             content_type='application/json')
            # /api/model/new/ не существует — сервер возвращает 404
            r = self.client.post('/api/model/new/')
        self.assertEqual(r.status_code, 404)
        # model.json на диске не тронут
        with open(self._model_file) as f:
            on_disk = json.load(f)
        self.assertEqual(on_disk['name'], 'Precious ASPICE')

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
            'Technology And Physical': 'technology',
            'Motivation': 'motivation',
            'Implementation and Migration': 'implementation_migration',
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
        self._uploads_dir = os.path.join(self._tmpdir, 'uploads')
        self._diagrams_dir = os.path.join(self._tmpdir, 'diagrams')

    def _patch(self):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=self._model_file,
                              _UPLOADS_DIR=self._uploads_dir,
                              _DIAGRAMS_DIR=self._diagrams_dir,
                              _GRAFICO_DIR='/nonexistent/grafico')

    def test_upload_saves_original_file_in_uploads(self):
        """Upload saves original .archimate file under uploads/<filename>."""
        f = SimpleUploadedFile('test.archimate', ARCHIMATE_WITH_DIAGRAM,
                               content_type='application/octet-stream')
        with self._patch():
            r = self.client.post('/upload/', {'file': f})
        self.assertEqual(r.status_code, 200)
        saved = os.path.join(self._uploads_dir, 'test.archimate')
        self.assertTrue(os.path.isfile(saved))

    def test_upload_records_source_path_in_model(self):
        """model.json contains _source pointing to the uploaded file."""
        f = SimpleUploadedFile('mymodel.archimate', ARCHIMATE_WITH_DIAGRAM,
                               content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f})
        with open(self._model_file) as fh:
            saved_model = json.load(fh)
        self.assertIn('_source', saved_model)
        self.assertTrue(saved_model['_source'].endswith('mymodel.archimate'))

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
        """When file has multiple views, /api/diagram/ returns the requested one."""
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
        from app_main.views import _find_model_view, _parse_native_diagram, _parse_archimate, _build_elements_index
        import tempfile, os
        tmpdir = tempfile.mkdtemp()
        src_file = os.path.join(tmpdir, 'multi.archimate')
        model_file = os.path.join(tmpdir, 'model.json')
        with open(src_file, 'wb') as f:
            f.write(xml)
        with open(model_file, 'w') as f:
            json.dump({'name': 'M', 'type': 'model', 'id': 'm1',
                       'children': [], '_source': src_file}, f)

        with patch('app_main.views._MODEL_FILE', model_file):
            _, view_a = _find_model_view('va')
            _, view_b = _find_model_view('vb')

        idx = _build_elements_index(_parse_archimate(xml))
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


class NativeDiagramLifecycleTests(TestCase):
    """Tests for _source lifecycle and _find_model_view behaviour."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)
        self._tmpdir = tempfile.mkdtemp()
        self._model_file = os.path.join(self._tmpdir, 'model.json')
        self._uploads_dir = os.path.join(self._tmpdir, 'uploads')
        self._diagrams_dir = os.path.join(self._tmpdir, 'diagrams')

    def _patch(self):
        return patch.multiple('app_main.views',
                              _MODEL_FILE=self._model_file,
                              _UPLOADS_DIR=self._uploads_dir,
                              _DIAGRAMS_DIR=self._diagrams_dir,
                              _GRAFICO_DIR='/nonexistent/grafico')

    def test_find_model_view_returns_none_when_no_source(self):
        """_find_model_view returns (None, None) when model has no _source."""
        model = {'name': 'M', 'type': 'model', 'id': 'm1', 'children': []}
        with open(self._model_file, 'w') as f:
            json.dump(model, f)
        with patch('app_main.views._MODEL_FILE', self._model_file):
            root, view = _find_model_view('any-id')
        self.assertIsNone(root)
        self.assertIsNone(view)

    def test_find_model_view_returns_none_when_source_missing(self):
        """_find_model_view returns (None, None) when _source file is gone."""
        model = {'name': 'M', 'type': 'model', 'id': 'm1', 'children': [],
                 '_source': '/nonexistent/path.archimate'}
        with open(self._model_file, 'w') as f:
            json.dump(model, f)
        with patch('app_main.views._MODEL_FILE', self._model_file):
            root, view = _find_model_view('any-id')
        self.assertIsNone(root)
        self.assertIsNone(view)

    def test_find_model_view_returns_none_for_unknown_id(self):
        """_find_model_view returns (None, None) when view_id not in file."""
        # Write real archimate file as the source
        src = os.path.join(self._tmpdir, 'src.archimate')
        with open(src, 'wb') as f:
            f.write(ARCHIMATE_WITH_DIAGRAM)
        model = {'name': 'M', 'type': 'model', 'id': 'm1', 'children': [],
                 '_source': src}
        with open(self._model_file, 'w') as f:
            json.dump(model, f)
        with patch('app_main.views._MODEL_FILE', self._model_file):
            root, view = _find_model_view('no-such-view-id')
        self.assertIsNone(root)
        self.assertIsNone(view)

    def test_find_model_view_finds_correct_view(self):
        """_find_model_view returns correct element when _source is set."""
        src = os.path.join(self._tmpdir, 'src.archimate')
        with open(src, 'wb') as f:
            f.write(ARCHIMATE_WITH_DIAGRAM)
        model = {'name': 'M', 'type': 'model', 'id': 'm1', 'children': [],
                 '_source': src}
        with open(self._model_file, 'w') as f:
            json.dump(model, f)
        with patch('app_main.views._MODEL_FILE', self._model_file):
            root, view = _find_model_view('v1')
        self.assertIsNotNone(view)
        self.assertEqual(view.get('id'), 'v1')

    def test_api_diagram_404_for_completely_unknown_view(self):
        """View not in model tree or source file → 404."""
        model = {'name': 'M', 'type': 'model', 'id': 'm1', 'children': []}
        with open(self._model_file, 'w') as f:
            json.dump(model, f)
        with self._patch():
            r = self.client.get('/api/diagram/totally-unknown-id/')
        self.assertEqual(r.status_code, 404)

    def test_upload_native_then_exchange_clears_source(self):
        """After uploading Exchange Format, _source is removed from model.json."""
        # First upload native
        f1 = SimpleUploadedFile('proj.archimate', ARCHIMATE_WITH_DIAGRAM,
                                content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f1})
        with open(self._model_file) as fh:
            self.assertIn('_source', json.load(fh))

        # Then upload Exchange — _source should be gone
        f2 = SimpleUploadedFile('model.xml', EXCHANGE_XML,
                                content_type='application/octet-stream')
        with self._patch():
            self.client.post('/upload/', {'file': f2})
        with open(self._model_file) as fh:
            self.assertNotIn('_source', json.load(fh))


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
                            _UPLOADS_DIR=os.path.join(tmpdir, 'uploads'),
                            _DIAGRAMS_DIR=os.path.join(tmpdir, 'diagrams'),
                            _GRAFICO_DIR='/nonexistent'):
            r = client.post('/upload/', {'file': f})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['name'], 'ZippedModel')
