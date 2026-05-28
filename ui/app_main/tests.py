import json
import os
import tempfile
from unittest.mock import patch
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile


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
