# -*- coding: utf-8 -*-

import base
import mock
import requests

from docker_registry.core import compat
json = compat.json


def mock_private_registry(adapter, request, *args, **kwargs):
    resp = requests.Response()
    resp.status_code = 200
    resp._content_consumed = True

    if request.url.endswith('4567/layer'):
        resp._content = "abcdef0123456789xxxxxx=-//"
    elif request.url.endswith('4567/json'):
        resp._content = ('{"id": "cafebabe01234567", '
                         '"created": "2014-02-03T16:47:06.615279788Z"}')
    elif request.url.endswith('4567/ancestry'):
        resp._content = '["cafebabe01234567"]'
    elif request.url.endswith('test/tags'):
        resp._content = \
            '{"latest": "cafebabe01234567", "0.1.2": "cafebabe01234567"}'
    elif request.url.endswith('test/tags/latest'):
        resp._content = 'cafebabe01234567'
    elif request.url.endswith('test/tags/0.1.2'):
        resp._content = 'cafebabe01234567'
    elif request.url.endswith('test/images'):
        resp._content = '[{"id": "cafebabe01234567"}]'
    else:
        resp.status_code = 404

    return resp


def mock_public_registry(adapter, request, *args, **kwargs):
    """branch logic for DockerHub, as their endpoints are not the same."""
    resp = requests.Response()
    resp.status_code = 200
    resp._content_consumed = True
    if request.headers and request.headers.get('X-Docker-Token') == 'true':
        resp.headers['x-docker-token'] = 'foobar'

    if request.url.endswith('deadbeef76543210/layer'):
        resp._content = "abcdef0123456789xxxxxx=-//"
    elif request.url.endswith('deadbeef76543210/json'):
        resp._content = ('{"id": "deadbeef76543210", '
                         '"created": "2014-02-03T16:47:06.615279788Z"}')
    elif request.url.endswith('deadbeef76543210/ancestry'):
        resp._content = '["deadbeef76543210"]'
    elif request.url.endswith('test/tags'):
        resp._content = ('['
                         '{"layer": "deadbeef76543210", "name": "latest"},'
                         '{"layer": "deadbeef76543210", "name": "0.1.2"}'
                         ']')
    elif request.url.endswith('test/tags/latest'):
        resp._content = '[{"pk": 1234567890, "id": "deadbeef76543210"}]'
    elif request.url.endswith('test/tags/0.1.2'):
        resp._content = '[{"pk": 1234567890, "id": "deadbeef76543210"}]'
    elif request.url.endswith('test/images'):
        resp._content = '[{"checksum": "", "id": "deadbeef76543210"}]'
    else:
        resp.status_code = 404

    return resp


class TestTags(base.TestCase):

    def test_simple(self, repos_name=None):
        if repos_name is None:
            repos_name = self.gen_random_string()
        image_id = self.gen_hex_string()
        layer_data = self.gen_random_string(1024)
        self.upload_image(image_id, parent_id=None, layer=layer_data)

        # test tags create
        url = '/v1/repositories/foo/{0}/tags/latest'.format(repos_name)
        headers = {'User-Agent':
                   'docker/0.7.2-dev go/go1.2 os/ostest arch/archtest'}
        resp = self.http_client.put(url,
                                    headers=headers,
                                    data=json.dumps(image_id))
        self.assertEqual(resp.status_code, 200, resp.data)
        url = '/v1/repositories/foo/{0}/tags/test'.format(repos_name)
        resp = self.http_client.put(url,
                                    data=json.dumps(image_id))
        self.assertEqual(resp.status_code, 200, resp.data)

        # test tags read
        url = '/v1/repositories/foo/{0}/tags/latest'.format(repos_name)
        resp = self.http_client.get(url)
        self.assertEqual(resp.status_code, 200, resp.data)
        # Note(dmp): unicode patch XXX not applied assume requests does the job
        self.assertEqual(json.loads(resp.data), image_id, resp.data)

        # test repository json
        url = '/v1/repositories/foo/{0}/json'.format(repos_name)
        resp = self.http_client.get(url)
        self.assertEqual(resp.status_code, 200, resp.data)
        # Note(dmp): unicode patch XXX not applied assume requests does the job
        props = json.loads(resp.data)
        self.assertEqual(props['docker_version'], '0.7.2-dev')
        self.assertEqual(props['docker_go_version'], 'go1.2')
        self.assertEqual(props['os'], 'ostest')
        self.assertEqual(props['arch'], 'archtest')

        # test repository tags json
        url = '/v1/repositories/foo/{0}/tags/latest/json'.format(repos_name)
        resp = self.http_client.get(url)
        self.assertEqual(resp.status_code, 200, resp.data)
        # Note(dmp): unicode patch XXX not applied assume requests does the job
        props = json.loads(resp.data)
        self.assertEqual(props['docker_version'], '0.7.2-dev')
        self.assertEqual(props['docker_go_version'], 'go1.2')
        self.assertEqual(props['os'], 'ostest')
        self.assertEqual(props['arch'], 'archtest')

        # test tags update
        url = '/v1/repositories/foo/{0}/tags/latest'.format(repos_name)
        headers = {'User-Agent':
                   'docker/0.7.2-dev go/go1.2 os/ostest arch/changedarch'}
        resp = self.http_client.put(url,
                                    headers=headers,
                                    data=json.dumps(image_id))
        self.assertEqual(resp.status_code, 200, resp.data)
        url = '/v1/repositories/foo/{0}/tags/test'.format(repos_name)
        resp = self.http_client.put(url,
                                    headers=headers,
                                    data=json.dumps(image_id))
        self.assertEqual(resp.status_code, 200, resp.data)

        # test repository latest tag json update
        url = '/v1/repositories/foo/{0}/tags/latest/json'.format(repos_name)
        resp = self.http_client.get(url)
        self.assertEqual(resp.status_code, 200, resp.data)
        # Note(dmp): unicode patch XXX not applied assume requests does the job
        props = json.loads(resp.data)
        self.assertEqual(props['docker_version'], '0.7.2-dev')
        self.assertEqual(props['docker_go_version'], 'go1.2')
        self.assertEqual(props['os'], 'ostest')
        self.assertEqual(props['arch'], 'changedarch')

        # test repository test tag json update
        url = '/v1/repositories/foo/{0}/tags/test/json'.format(repos_name)
        resp = self.http_client.get(url)
        self.assertEqual(resp.status_code, 200, resp.data)
        # Note(dmp): unicode patch XXX not applied assume requests does the job
        props = json.loads(resp.data)
        self.assertEqual(props['docker_version'], '0.7.2-dev')
        self.assertEqual(props['docker_go_version'], 'go1.2')
        self.assertEqual(props['os'], 'ostest')
        self.assertEqual(props['arch'], 'changedarch')

        # test tags list
        url = '/v1/repositories/foo/{0}/tags'.format(repos_name)
        resp = self.http_client.get(url)
        self.assertEqual(resp.status_code, 200, resp.data)
        # Note(dmp): unicode patch XXX not applied assume requests does the job
        self.assertEqual(len(json.loads(resp.data)), 2, resp.data)

        # test tag delete
        url = '/v1/repositories/foo/{0}/tags/latest'.format(repos_name)
        resp = self.http_client.delete(url)
        self.assertEqual(resp.status_code, 200, resp.data)
        url = '/v1/repositories/foo/{0}/tags'.format(repos_name)
        resp = self.http_client.get(url)
        self.assertEqual(resp.status_code, 200, resp.data)
        url = '/v1/repositories/foo/{0}/tags/latest'.format(repos_name)
        resp = self.http_client.get(url)
        self.assertEqual(resp.status_code, 404, resp.data)

        # test whole delete
        url = '/v1/repositories/foo/{0}/'.format(repos_name)
        resp = self.http_client.delete(url)
        self.assertEqual(resp.status_code, 200, resp.data)
        url = '/v1/repositories/foo/{0}/tags'.format(repos_name)
        resp = self.http_client.get(url)
        self.assertEqual(resp.status_code, 404, resp.data)

    def test_notfound(self):
        notexist = self.gen_random_string()
        url = '/v1/repositories/{0}/bar/tags'.format(notexist)
        resp = self.http_client.get(url)
        self.assertEqual(resp.status_code, 404, resp.data)

    def test_special_chars(self):
        repos_name = '{0}%$_-test'.format(self.gen_random_string(5))
        self.test_simple(repos_name)

    def test_tag_name_validation(self):
        repos_name = self.gen_random_string()
        image_id = self.gen_hex_string()
        layer_data = self.gen_random_string(1024)
        self.upload_image(image_id, parent_id=None, layer=layer_data)

        headers = {'User-Agent':
                   'docker/0.7.2-dev go/go1.2 os/ostest arch/archtest'}
        url = lambda tag: '/v1/repositories/foo/{0}/tags/{1}'.format(
            repos_name, tag
        )

        tag_name = '$<invalid>'
        resp = self.http_client.put(
            url(tag_name), headers=headers, data=json.dumps(image_id)
        )
        self.assertEqual(resp.status_code, 400)

        tag_name = '.invalid'
        resp = self.http_client.put(
            url(tag_name), headers=headers, data=json.dumps(image_id)
        )
        self.assertEqual(resp.status_code, 400)

        tag_name = '-invalid'
        resp = self.http_client.put(
            url(tag_name), headers=headers, data=json.dumps(image_id)
        )
        self.assertEqual(resp.status_code, 400)

        tag_name = '_valid'
        resp = self.http_client.put(
            url(tag_name), headers=headers, data=json.dumps(image_id)
        )
        self.assertEqual(resp.status_code, 200, resp.data)

    @mock.patch('requests.adapters.HTTPAdapter.send', mock_private_registry)
    def test_import_repository_from_private_registry(self):
        data = {
            'src': 'example.com/othernamespace/test',
        }
        resp = self.http_client.post('/v1/repositories/testing2/test/tags',
                                     data=data)
        self.assertEqual(resp.status_code, 200)
        # test that the images were imported
        resp = self.http_client.get('/v1/images/cafebabe01234567/layer')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            "abcdef0123456789xxxxxx=-//"
        )
        resp = self.http_client.get('/v1/images/cafebabe01234567/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            '{"id": "cafebabe01234567", '
            '"created": "2014-02-03T16:47:06.615279788Z"}'
        )
        resp = self.http_client.get('/v1/images/cafebabe01234567/ancestry')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            '["cafebabe01234567"]'
        )
        # test that the tags were imported
        resp = self.http_client.get('/v1/repositories/testing2/test/tags')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            json.loads(resp.data),
            {"latest": "cafebabe01234567", "0.1.2": "cafebabe01234567"}
        )
        # test that index images were imported
        resp = self.http_client.get('/v1/repositories/testing2/test/images')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            json.loads(resp.data),
            [{"id": "cafebabe01234567"}]
        )

    @mock.patch('requests.adapters.HTTPAdapter.send', mock_private_registry)
    def test_import_repository_tag_from_private_registry(self):
        data = {
            'src': 'example.com/othernamespace/test:latest',
        }
        resp = self.http_client.post('/v1/repositories/testing3/test/tags',
                                     data=data)
        self.assertEqual(resp.status_code, 200)
        # test that the images were imported
        resp = self.http_client.get('/v1/images/cafebabe01234567/layer')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            "abcdef0123456789xxxxxx=-//"
        )
        resp = self.http_client.get('/v1/images/cafebabe01234567/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            '{"id": "cafebabe01234567", '
            '"created": "2014-02-03T16:47:06.615279788Z"}'
        )
        resp = self.http_client.get('/v1/images/cafebabe01234567/ancestry')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            '["cafebabe01234567"]'
        )
        # test that the tags were imported
        resp = self.http_client.get('/v1/repositories/testing3/test/tags')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            json.loads(resp.data),
            {"latest": "cafebabe01234567"}
        )
        # test that index images were imported
        resp = self.http_client.get('/v1/repositories/testing3/test/images')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            json.loads(resp.data),
            [{"id": "cafebabe01234567"}]
        )

    @mock.patch('requests.adapters.HTTPAdapter.send', mock_public_registry)
    def test_import_repository_from_public_index(self):
        data = {
            'src': 'testing3/test',
        }
        resp = self.http_client.post('/v1/repositories/testing4/test/tags',
                                     data=data)
        self.assertEqual(resp.status_code, 200)
        # test that the images were imported
        resp = self.http_client.get('/v1/images/deadbeef76543210/layer')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            "abcdef0123456789xxxxxx=-//"
        )
        resp = self.http_client.get('/v1/images/deadbeef76543210/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            '{"id": "deadbeef76543210", '
            '"created": "2014-02-03T16:47:06.615279788Z"}'
        )
        resp = self.http_client.get('/v1/images/deadbeef76543210/ancestry')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            '["deadbeef76543210"]'
        )
        # test that the tags were imported
        resp = self.http_client.get('/v1/repositories/testing4/test/tags')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            json.loads(resp.data),
            {"latest": "deadbeef76543210", "0.1.2": "deadbeef76543210"}
        )
        # test that index images were imported
        resp = self.http_client.get('/v1/repositories/testing4/test/images')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            json.loads(resp.data),
            [{"id": "deadbeef76543210"}]
        )

    @mock.patch('requests.adapters.HTTPAdapter.send', mock_public_registry)
    def test_import_repository_tag_from_public_index(self):
        data = {
            'src': 'testing3/test:latest',
        }
        resp = self.http_client.post('/v1/repositories/testing5/test/tags',
                                     data=data)
        self.assertEqual(resp.status_code, 200)
        # test that the images were imported
        resp = self.http_client.get('/v1/images/deadbeef76543210/layer')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            "abcdef0123456789xxxxxx=-//"
        )
        resp = self.http_client.get('/v1/images/deadbeef76543210/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            '{"id": "deadbeef76543210", '
            '"created": "2014-02-03T16:47:06.615279788Z"}'
        )
        resp = self.http_client.get('/v1/images/deadbeef76543210/ancestry')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            '["deadbeef76543210"]'
        )
        # test that the tags were imported
        resp = self.http_client.get('/v1/repositories/testing5/test/tags')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            json.loads(resp.data),
            {"latest": "deadbeef76543210"}
        )
        # test that index images were imported
        resp = self.http_client.get('/v1/repositories/testing5/test/images')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            json.loads(resp.data),
            [{"id": "deadbeef76543210"}]
        )
