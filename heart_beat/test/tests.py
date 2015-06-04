"""
This file will run automated tests to see if heart_beat is still running as
expected.

You can also choose to manually test heart_beat using:

curl --request POST 'http://localhost:5000/ping' --data-binary @test/test_data.json --header "Content-Type:application/json"
"""
import os
import tempfile
import uuid
import unittest
import json
import datetime
from unittest import mock

from heart_beat.views import insert_ping_data
from heart_beat.models import DiagnosticPingData
import heart_beat

class TestURLMapping(unittest.TestCase):
    """
    Ensure that we have the correct get and post end points.
    """
    def setUp(self):
        # Putting things in tmp couples this project to Unix.
        db_uri = 'sqlite:////tmp/{}'.format(uuid.uuid1())
        heart_beat.app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        heart_beat.app.config['TESTING'] = True
        self.test_app = heart_beat.app.test_client()
        heart_beat.setup_db()

    def tearDown(self):
        heart_beat.teardown_db()
        heart_beat.load_configs()

    def test_version_get_request(self):
        response = self.test_app.get('/version', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    def test_version_returns_configured_version(self):
        heart_beat.app.config['VERSION'] = b'Testing'
        response = self.test_app.get('/version', content_type='html/text')
        self.assertEqual(response.data, heart_beat.app.config['VERSION'])

    def test_ping_fails_on_get_request(self):
        response = self.test_app.get('/ping', content_type='html/text')
        self.assertEqual(response.status_code, 405)

    def test_ping_post_request_bad_content_type(self):
        response = self.test_app.post('/ping', content_type='html/text')
        self.assertEqual(response.status_code, 406)

    def test_ping_post_request_correct_content_type_no_json(self):
        response = self.test_app.post('/ping', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_ping_post_valid_content_type_valid_data(self):
        example_json_data = {
            "client_start_time":"1429572087",
            "logset_gather_time":"1429572066",
            "onefs_version":"7.2.0.0",
            "esrs_enabled":"False",
            "tool_version":"0.0.0.1",
            "sr_number":"12345678910"}
        example_json_data = json.dumps(example_json_data)
        response = self.test_app.post(
            '/ping',
            content_type='application/json',
            data=example_json_data)
        self.assertEqual(response.data, b"success")
        self.assertEqual(response.status_code, 200)

class TestDBOperations(unittest.TestCase):
    """
    Test all code which modifies or selects from the database.
    """
    maxDiff = None

    def setUp(self):
        db_uri = 'sqlite:////tmp/{}'.format(uuid.uuid1())
        heart_beat.app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        heart_beat.app.config['TESTING'] = True
        self.test_app = heart_beat.app.test_client()
        heart_beat.setup_db()

    def tearDown(self):
        heart_beat.teardown_db()
        heart_beat.load_configs()
    
    def test_valid_dict_insertion(self):
        example_json_data = {
            "client_start_time":"1429572087",
            "logset_gather_time":"1429572066",
            "onefs_version":"7.2.0.0",
            "esrs_enabled":"False",
            "tool_version":"0.0.0.1",
            "sr_number":"12345678910"}
        insert_ping_data(example_json_data)
        actual_data = DiagnosticPingData.query.filter_by(ping_id=1).first()
        expected_data = {
            "ping_id": 1,
            "client_start_time":"2015-04-20 23:21:27",
            "logset_gather_time":"2015-04-20 23:21:06",
            "onefs_version":"7.2.0.0",
            "esrs_enabled": False,
            "tool_version":"0.0.0.1",
            "sr_number": 12345678910}
        actual_data = actual_data.get_dict()
        del actual_data["db_insert_time"] # going to be different every time.
        self.assertEqual(expected_data, actual_data)

if __name__ == '__main__':
    unittest.main()