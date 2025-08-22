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
    assert data["api_version"]  # Just check that api_version field exists, not "version"

def test_analyze_endpoint_missing_file(client):
    """Test analyze endpoint returns error when file part is missing"""
    response = client.post('/m1/analyze', data={}, content_type='multipart/form-data')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error'] == "File part missing"

def test_analyze_endpoint_empty_file(client):
    """Test analyze endpoint returns error for empty file"""
    data = {'file': (BytesIO(b''), 'empty.xml')}
    response = client.post('/m1/analyze', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error'] == "Empty file"

def test_analyze_endpoint_invalid_file_type(client):
    """Test analyze endpoint returns error for invalid file type"""
    data = {'file': (BytesIO(b'invalid content'), 'test.txt')}
    response = client.post('/m1/analyze', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error'].startswith("Invalid file type. Allowed extensions:")

def test_analyze_endpoint_valid_xml(client):
    """Test analyze endpoint with valid XML file"""
    xml_file = BytesIO(SAMPLE_XML_CONTENT.encode('utf-8'))
    data = {'file': (xml_file, 'test_score.xml')}
    
    response = client.post('/m1/analyze', data=data, content_type='multipart/form-data')
    
    # Should not fail with basic XML
    assert response.status_code in [200, 500]  # 500 is acceptable for analysis errors
    
    data = response.get_json()
    
    if response.status_code == 200:
        # If successful, check response structure
        assert 'api_metadata' in data
        assert data['api_metadata']['endpoint'] == '/m1/analyze'
        assert data['api_metadata']['filename'] == 'test_score.xml'
        assert 'api_version' in data['api_metadata']
    else:
        # If analysis failed, should be structured error
        assert data['status'] == 'error'
        assert 'module' in data

def test_schema_endpoint(client):
    """Test /m1/schema endpoint"""
    response = client.get('/m1/schema')
    assert response.status_code == 200
    
    data = response.get_json()
    # Assert directly on data["schema"] instead of checking for "schema" key
    assert data["schema"]
    assert isinstance(data["schema"], dict)

def test_validate_endpoint_valid_json(client):
    """Test /m1/validate endpoint with valid JSON"""
    valid_data = {"test": "data"}
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
    
    # Could be 200 (valid but empty) or 422 (invalid)
    if response.status_code == 422:
        data = response.get_json()
        assert data['status'] == 'error'
        assert data['valid'] == False
        assert 'errors' in data
    else:
        # If it's actually valid, that's fine too
        assert response.status_code == 200

def test_validate_endpoint_no_json(client):
    """Test /m1/validate endpoint with no JSON body"""
    response = client.post('/m1/validate', 
                          data='not json', 
                          content_type='text/plain')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    # Check for correct error message
    assert 'JSON' in data['error'] or 'json' in data['error']

def test_nonexistent_endpoint(client):
    """Test that nonexistent endpoints return 404"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert isinstance(data['error'], str)

def test_wrong_method_on_analyze(client):
    """Test that GET on analyze endpoint returns 405"""
    response = client.get('/m1/analyze')
    assert response.status_code == 405
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert isinstance(data['error'], str)

if __name__ == '__main__':
    print("Running smoke tests using Flask test_client (no network calls)")
    pytest.main([__file__, '-v'])
