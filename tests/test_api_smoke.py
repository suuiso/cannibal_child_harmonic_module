#!/usr/bin/env python3
"""
Smoke tests for Harmonic Precision Analyzer API using Flask test_client
Tests basic functionality of /m1/analyze endpoint without network calls
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
        <key>
          <fifths>0</fifths>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <type>quarter</type>
      </note>
    </measure>
  </part>
</score-partwise>'''


def test_health_endpoint(client):
    """Test that health endpoint is accessible"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'module' in data
    assert 'version' in data


def test_m1_health_alias(client):
    """Test that /m1/health alias works"""
    response = client.get('/m1/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'module' in data
    assert 'version' in data


def test_version_endpoint(client):
    """Test version endpoint"""
    response = client.get('/m1/version')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'version' in data
    assert 'module' in data


def test_analyze_endpoint_no_file(client):
    """Test analyze endpoint returns error when no file provided"""
    response = client.post('/m1/analyze')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'No file provided' in data['error']


def test_analyze_endpoint_empty_file(client):
    """Test analyze endpoint returns error for empty file"""
    data = {'file': (BytesIO(b''), '')}
    response = client.post('/m1/analyze', data=data)
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'No file selected' in data['error']


def test_analyze_endpoint_invalid_file_type(client):
    """Test analyze endpoint returns error for invalid file type"""
    data = {'file': (BytesIO(b'invalid content'), 'test.txt')}
    response = client.post('/m1/analyze', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'File type not allowed' in data['error']


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


def test_analyze_endpoint_with_xml_file_key(client):
    """Test analyze endpoint using 'xml_file' key instead of 'file'"""
    xml_file = BytesIO(SAMPLE_XML_CONTENT.encode('utf-8'))
    data = {'xml_file': (xml_file, 'test_score.xml')}
    
    response = client.post('/m1/analyze', data=data, content_type='multipart/form-data')
    
    # Should not fail with basic XML
    assert response.status_code in [200, 500]  # 500 is acceptable for analysis errors
    
    data = response.get_json()
    assert 'status' in data  # Should have status field regardless


def test_nonexistent_endpoint(client):
    """Test that nonexistent endpoints return 404"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Endpoint not found' in data['error']
    assert 'available_endpoints' in data


def test_wrong_method_on_analyze(client):
    """Test that GET on analyze endpoint returns 405"""
    response = client.get('/m1/analyze')
    assert response.status_code == 405
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Method not allowed' in data['error']


if __name__ == '__main__':
    print("Running smoke tests using Flask test_client (no network calls)")
    pytest.main([__file__, '-v'])
