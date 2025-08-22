#!/usr/bin/env python3
"""
Smoke tests for Harmonic Precision Analyzer API using Flask test_client
Tests basic functionality of all endpoints without network calls
"""
import pytest
import json
import sys
import os
from io import BytesIO

# Add parent directory to path to import app module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def load_sample_json():
    """Load sample JSON from tests/data/sample_output_ok.json"""
    data_file = os.path.join(os.path.dirname(__file__), 'data', 'sample_output_ok.json')
    with open(data_file, 'r') as f:
        return json.load(f)


SAMPLE_XML_CONTENT = '''<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work>
    <work-title>Test Score</work-title>
  </work>
  <part-list>
    <score-part id="P1">
      <part-name>Piano</part-name>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
      </attributes>
    </measure>
  </part>
</score-partwise>'''


def test_version_endpoint(client):
    """Test /m1/version endpoint"""
    response = client.get('/m1/version')
    assert response.status_code == 200
    
    data = response.get_json()
    assert "version" in data  # Check that version field exists (no api_version)


def test_analyze_endpoint_missing_file(client):
    """Test analyze endpoint returns error when file part is missing"""
    response = client.post('/m1/analyze', data={}, content_type='multipart/form-data')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'message' in data
    assert 'No file' in data['message'] or 'file' in data['message'].lower()


def test_analyze_endpoint_empty_file(client):
    """Test analyze endpoint with empty file"""
    data = {
        'musicxml_file': (BytesIO(b''), 'empty.xml')
    }
    response = client.post('/m1/analyze', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'message' in data
    assert 'empty' in data['message'].lower() or 'file' in data['message'].lower()


def test_analyze_endpoint_invalid_xml(client):
    """Test analyze endpoint with invalid XML"""
    invalid_xml = b'<invalid xml content'
    data = {
        'musicxml_file': (BytesIO(invalid_xml), 'invalid.xml')
    }
    response = client.post('/m1/analyze', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'message' in data
    assert 'XML' in data['message'] or 'xml' in data['message'] or 'parse' in data['message'].lower()


def test_analyze_endpoint_valid_xml(client):
    """Test analyze endpoint with valid XML"""
    data = {
        'musicxml_file': (BytesIO(SAMPLE_XML_CONTENT.encode('utf-8')), 'test.xml')
    }
    response = client.post('/m1/analyze', data=data, content_type='multipart/form-data')
    
    # Should return 200 for valid XML (analysis might still have issues but XML is valid)
    assert response.status_code in [200, 422]  # 422 if analysis finds issues
    
    data = response.get_json()
    if response.status_code == 200:
        assert data['status'] == 'success'
        assert 'analysis' in data
    else:
        assert data['status'] == 'error'
        assert 'message' in data


def test_schema_endpoint(client):
    """Test /m1/schema endpoint"""
    response = client.get('/m1/schema')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'schema' in data['data']  # Schema nested in data["schema"]
    assert isinstance(data['data']['schema'], dict)


def test_validate_endpoint_valid_json(client):
    """Test /m1/validate endpoint with valid JSON from sample_output_ok.json"""
    try:
        valid_data = load_sample_json()
    except FileNotFoundError:
        # Fallback if sample file doesn't exist yet
        valid_data = {
            "tempo": {
                "bpm": 120,
                "marking": "Moderato"
            },
            "key_signature": {
                "key": "C",
                "mode": "major"
            },
            "time_signature": {
                "numerator": 4,
                "denominator": 4
            }
        }
    
    response = client.post('/m1/validate', 
                          json=valid_data, 
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['valid'] == True


def test_validate_endpoint_invalid_json(client):
    """Test /m1/validate endpoint with invalid JSON against schema"""
    # This would depend on what the actual schema expects
    # For now, assume empty object might be invalid
    invalid_data = {}
    response = client.post('/m1/validate', 
                          json=invalid_data, 
                          content_type='application/json')
    
    assert response.status_code == 422
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['valid'] == False
    assert 'message' in data
    assert isinstance(data.get('errors', []), list)


def test_validate_endpoint_no_json(client):
    """Test /m1/validate endpoint with no JSON body"""
    response = client.post('/m1/validate', 
                          data='not json', 
                          content_type='text/plain')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'message' in data
    assert 'JSON' in data['message'] or 'json' in data['message']


def test_nonexistent_endpoint(client):
    """Test that nonexistent endpoints return 404"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == 'Not Found'


def test_wrong_method_on_analyze(client):
    """Test that GET on analyze endpoint returns 405"""
    response = client.get('/m1/analyze')
    assert response.status_code == 405
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == 'Method Not Allowed'


if __name__ == '__main__':
    print("Running smoke tests using Flask test_client (no network calls)")
    pytest.main([__file__, '-v'])
