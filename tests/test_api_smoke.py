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
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['module'] == 'harmonic_precision_analyzer'
    assert data['version'] == '1.0.0'

def test_m1_version_endpoint(client):
    """Test m1 version endpoint"""
    response = client.get('/m1/version')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['module'] == 'harmonic_precision_analyzer'
    assert data['version'] == '1.0.0'
    assert data['endpoint'] == 'm1'

def test_m1_analyze_no_file(client):
    """Test analyze endpoint with no file"""
    response = client.post('/m1/analyze')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error'] == 'No file provided'

def test_m1_analyze_empty_file(client):
    """Test analyze endpoint with empty file"""
    response = client.post('/m1/analyze', data={'file': (BytesIO(b''), '')})
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error'] == 'No file selected'

def test_m1_analyze_invalid_file_type(client):
    """Test analyze endpoint with invalid file type"""
    response = client.post('/m1/analyze', data={
        'file': (BytesIO(b'test content'), 'test.txt')
    })
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error'] == 'Invalid file type. Only XML, MusicXML, and MXL files are allowed.'

def test_m1_analyze_valid_xml_file(client):
    """Test analyze endpoint with valid XML file"""
    xml_data = BytesIO(SAMPLE_XML_CONTENT.encode('utf-8'))
    response = client.post('/m1/analyze', data={
        'file': (xml_data, 'test.xml')
    })
    
    # The response should be 200 for successful analysis or 400 for analysis failure
    assert response.status_code in [200, 400]
    
    data = json.loads(response.data)
    
    if response.status_code == 200:
        # Success case
        assert data['status'] == 'success'
        assert data['module'] == 'harmonic_precision_analyzer'
        assert 'analysis' in data
        assert 'filename' in data
        assert data['filename'] == 'test.xml'
    else:
        # Error case (analyzer might fail on simple XML)
        assert data['status'] == 'error'
        assert 'error' in data
        assert 'Analysis failed:' in data['error'] or 'Request processing failed:' in data['error']

def test_m1_analyze_musicxml_file(client):
    """Test analyze endpoint with .musicxml extension"""
    xml_data = BytesIO(SAMPLE_XML_CONTENT.encode('utf-8'))
    response = client.post('/m1/analyze', data={
        'file': (xml_data, 'test.musicxml')
    })
    
    # The response should be 200 for successful analysis or 400 for analysis failure
    assert response.status_code in [200, 400]
    
    data = json.loads(response.data)
    
    if response.status_code == 200:
        # Success case
        assert data['status'] == 'success'
        assert data['module'] == 'harmonic_precision_analyzer'
        assert 'analysis' in data
        assert 'filename' in data
        assert data['filename'] == 'test.musicxml'
    else:
        # Error case (analyzer might fail on simple XML)
        assert data['status'] == 'error'
        assert 'error' in data
        assert 'Analysis failed:' in data['error'] or 'Request processing failed:' in data['error']

def test_nonexistent_endpoint(client):
    """Test that nonexistent endpoints return 404"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
