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
    assert 'version' in data
    assert 'module' in data  # Cambiado de 'api' a 'module'

def test_health_endpoint(client):
    """Test /m1/health endpoint"""
    response = client.get('/m1/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_schema_endpoint(client):
    """Test /m1/schema endpoint"""
    response = client.get('/m1/schema')
    assert response.status_code == 200
    data = response.get_json()
    # Schema should be directly under data['schema'], not data['data']['schema']
    assert 'schema' in data
    assert isinstance(data['schema'], (dict, list))  # Permite dict o list (fallback)

def test_analyze_endpoint_success(client):
    """Test /m1/analyze endpoint with valid XML file"""
    xml_file = (BytesIO(SAMPLE_XML_CONTENT.encode('utf-8')), 'test.xml')
    response = client.post('/m1/analyze',
                          data={'file': xml_file},
                          content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'analysis' in data

def test_analyze_endpoint_no_file(client):
    """Test /m1/analyze endpoint without file"""
    response = client.post('/m1/analyze',
                          data={},
                          content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'error' in data  # Cambiado de 'message' a 'error'

def test_analyze_endpoint_invalid_file(client):
    """Test /m1/analyze endpoint with invalid file content"""
    invalid_file = (BytesIO(b'not valid xml'), 'invalid.xml')
    response = client.post('/m1/analyze',
                          data={'file': invalid_file},
                          content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'error' in data  # Cambiado de 'message' a 'error'

def test_analyze_endpoint_wrong_extension(client):
    """Test /m1/analyze endpoint with wrong file extension"""
    txt_file = (BytesIO(b'some content'), 'test.txt')
    response = client.post('/m1/analyze',
                          data={'file': txt_file},
                          content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'error' in data  # Cambiado de 'message' a 'error'

def test_validate_endpoint_success(client):
    """Test /m1/validate endpoint with valid JSON data"""
    sample_data = load_sample_json()
    
    response = client.post('/m1/validate',
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['valid'] == True

def test_validate_endpoint_invalid_json(client):
    """Test /m1/validate endpoint with invalid JSON against schema"""
    invalid_data = {}
    response = client.post('/m1/validate',
                          json=invalid_data,
                          content_type='application/json')
    
    assert response.status_code == 422
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['valid'] == False
    assert 'error' in data  # Cambiado de 'message' a 'error'
    assert isinstance(data.get('validation_errors', []), list)

def test_validate_endpoint_no_json(client):
    """Test /m1/validate endpoint with no JSON body"""
    response = client.post('/m1/validate',
                          data='not json',
                          content_type='text/plain')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'error' in data  # Cambiado de 'message' a 'error'
    assert 'JSON' in data['error'] or 'json' in data['error']

def test_nonexistent_endpoint(client):
    """Test that nonexistent endpoints return 404"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'error' in data  # Cambiado de 'message' a 'error'

def test_wrong_method_on_analyze(client):
    """Test that GET on analyze endpoint returns 405"""
    response = client.get('/m1/analyze')
    assert response.status_code == 405
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'error' in data  # Cambiado de 'message' a 'error'

if __name__ == '__main__':
    print("Running smoke tests using Flask test_client (no network calls)")
    pytest.main([__file__, '-v'])
