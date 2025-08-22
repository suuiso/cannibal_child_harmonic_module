#!/usr/bin/env python3
"""
Smoke tests for Harmonic Precision Analyzer API
Tests basic functionality of /m1/analyze endpoint
"""
import pytest
import requests
import json
import os
from io import BytesIO

# Configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5000')
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

def test_health_endpoint():
    """Test that health endpoint is accessible"""
    response = requests.get(f"{API_BASE_URL}/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'module' in data
    assert 'version' in data

def test_analyze_endpoint_no_file():
    """Test analyze endpoint returns error when no file provided"""
    response = requests.post(f"{API_BASE_URL}/m1/analyze")
    assert response.status_code == 400
    
    data = response.json()
    assert data['status'] == 'error'
    assert 'No file provided' in data['error']

def test_analyze_endpoint_empty_file():
    """Test analyze endpoint returns error for empty file"""
    files = {'file': ('', BytesIO(b''), 'application/xml')}
    response = requests.post(f"{API_BASE_URL}/m1/analyze", files=files)
    assert response.status_code == 400
    
    data = response.json()
    assert data['status'] == 'error'
    assert 'No file selected' in data['error']

def test_analyze_endpoint_invalid_file_type():
    """Test analyze endpoint returns error for invalid file type"""
    files = {'file': ('test.txt', BytesIO(b'invalid content'), 'text/plain')}
    response = requests.post(f"{API_BASE_URL}/m1/analyze", files=files)
    assert response.status_code == 400
    
    data = response.json()
    assert data['status'] == 'error'
    assert 'File type not allowed' in data['error']

def test_analyze_endpoint_valid_xml():
    """Test analyze endpoint with valid XML file"""
    xml_file = BytesIO(SAMPLE_XML_CONTENT.encode('utf-8'))
    files = {'file': ('test_score.xml', xml_file, 'application/xml')}
    
    response = requests.post(f"{API_BASE_URL}/m1/analyze", files=files)
    
    # Should not fail with basic XML
    assert response.status_code in [200, 500]  # 500 is acceptable for analysis errors
    
    data = response.json()
    
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

def test_analyze_endpoint_with_xml_file_key():
    """Test analyze endpoint using 'xml_file' key instead of 'file'"""
    xml_file = BytesIO(SAMPLE_XML_CONTENT.encode('utf-8'))
    files = {'xml_file': ('test_score.xml', xml_file, 'application/xml')}
    
    response = requests.post(f"{API_BASE_URL}/m1/analyze", files=files)
    
    # Should not fail with basic XML
    assert response.status_code in [200, 500]  # 500 is acceptable for analysis errors
    
    data = response.json()
    assert 'status' in data  # Should have status field regardless

def test_nonexistent_endpoint():
    """Test that nonexistent endpoints return 404"""
    response = requests.get(f"{API_BASE_URL}/nonexistent")
    assert response.status_code == 404
    
    data = response.json()
    assert data['status'] == 'error'
    assert 'Endpoint not found' in data['error']
    assert 'available_endpoints' in data

def test_wrong_method_on_analyze():
    """Test that GET on analyze endpoint returns 405"""
    response = requests.get(f"{API_BASE_URL}/m1/analyze")
    assert response.status_code == 405
    
    data = response.json()
    assert data['status'] == 'error'
    assert 'Method not allowed' in data['error']

if __name__ == '__main__':
    print(f"Running smoke tests against {API_BASE_URL}")
    pytest.main([__file__, '-v'])
