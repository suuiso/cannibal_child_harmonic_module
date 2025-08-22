#!/usr/bin/env python3
"""
Unit tests for M1 JSON schema endpoints
Tests /m1/schema and /m1/validate endpoints using Flask test_client
"""
import pytest
import json
import sys
import os

# Add parent directory to path to import app module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_schema_endpoint_success(client):
    """Test that /m1/schema returns valid schema"""
    response = client.get('/m1/schema')
    assert response.status_code == 200
    
    data = response.get_json()
    
    # Check basic schema structure
    assert 'schema' in data
    assert '$schema' in data['schema']
    assert '$id' in data['schema']
    assert 'title' in data['schema']
    assert 'version' in data['schema']
    assert 'type' in data['schema']
    assert 'properties' in data['schema']
    assert 'required' in data['schema']
    
    # Check schema metadata
    assert data['schema']['title'] == 'M1 Schema'
    assert data['schema']['version'] == '1.0.0'
    assert data['schema']['type'] == 'object'
    
    # Check required properties
    assert 'version' in data['schema']['required']
    assert 'data' in data['schema']['required']

def test_validate_endpoint_valid_data(client):
    """Test /m1/validate with valid data according to schema"""
    # Load sample valid data
    sample_data = {
        "version": "1.0.0",
        "data": {
            "frequencies": [440.0, 880.0, 1320.0],
            "amplitudes": [1.0, 0.5, 0.25],
            "phases": [0.0, 1.57, 3.14]
        }
    }
    
    response = client.post('/m1/validate', 
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'validation_result' in data
    assert data['validation_result'] == 'valid'

def test_validate_endpoint_invalid_data(client):
    """Test /m1/validate with invalid data"""
    # Missing required fields
    sample_data = {
        "version": "1.0.0"
        # Missing 'data' field
    }
    
    response = client.post('/m1/validate', 
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'error' in data

def test_validate_endpoint_no_json(client):
    """Test /m1/validate with no JSON data"""
    response = client.post('/m1/validate')
    
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Request must contain JSON data' in data['error']
    assert data['module'] == 'harmonic_precision_analyzer_api'

def test_validate_endpoint_empty_json(client):
    """Test /m1/validate with empty JSON"""
    response = client.post('/m1/validate', 
                          json=None,
                          content_type='application/json')
    
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Empty or invalid JSON data' in data['error']

def test_validate_endpoint_wrong_method(client):
    """Test that GET on /m1/validate returns 405"""
    response = client.get('/m1/validate')
    
    assert response.status_code == 405
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Method not allowed' in data['error']

def test_schema_endpoint_wrong_method(client):
    """Test that POST on /m1/schema returns 405"""
    response = client.post('/m1/schema')
    
    assert response.status_code == 405
    
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Method not allowed' in data['error']

if __name__ == '__main__':
    print("Running schema endpoint tests using Flask test_client")
    pytest.main([__file__, '-v'])
