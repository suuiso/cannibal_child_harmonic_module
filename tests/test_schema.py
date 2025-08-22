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

def load_sample_json():
    """Load sample JSON from tests/data/sample_output_ok.json"""
    data_file = os.path.join(os.path.dirname(__file__), 'data', 'sample_output_ok.json')
    with open(data_file, 'r') as f:
        return json.load(f)

def test_schema_endpoint_success(client):
    """Test that /m1/schema returns valid schema"""
    response = client.get('/m1/schema')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'success'
    
    # Schema should be directly under data['schema'], not data['data']['schema']
    assert 'schema' in data
    assert isinstance(data['schema'], dict)
    
    schema = data['schema']
    
    # Check basic schema structure
    assert '$schema' in schema
    assert '$id' in schema or 'id' in schema  # Allow both formats
    assert 'title' in schema
    assert 'type' in schema
    assert 'properties' in schema
    
    # Check schema metadata
    assert schema['type'] == 'object'

def test_validate_endpoint_success(client):
    """Test /m1/validate with valid JSON data"""
    # Success tests should use and check sample_output_ok.json for validation
    sample_data = load_sample_json()
    
    response = client.post('/m1/validate',
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['valid'] == True

def test_validate_endpoint_invalid_json(client):
    """Test /m1/validate with JSON that doesn't match schema"""
    # This should fail validation
    invalid_data = {
        "invalid_field": "should not be here",
        "missing_required": "fields"
    }
    
    response = client.post('/m1/validate',
                          json=invalid_data,
                          content_type='application/json')
    
    # Should be 422 for validation error
    assert response.status_code == 422
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['valid'] == False
    # Error assertions should check 'status' == 'error' and 'error' in payload, never 'message'
    assert 'error' in data
    assert isinstance(data.get('errors', []), list)

def test_validate_endpoint_no_json(client):
    """Test /m1/validate with no JSON data"""
    response = client.post('/m1/validate',
                          data='not json',
                          content_type='text/plain')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    # Error assertions should check 'status' == 'error' and 'error' in payload, never 'message'
    assert 'error' in data
    # Check for correct error message about JSON
    assert ('JSON' in data['error'] or 'json' in data['error'] or
            'Empty' in data['error'] or 'invalid' in data['error'])

def test_validate_endpoint_empty_json(client):
    """Test /m1/validate with empty JSON"""
    response = client.post('/m1/validate',
                          json={},
                          content_type='application/json')
    
    # Empty JSON should be invalid against schema (missing required fields)
    assert response.status_code == 422
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['valid'] == False
    # Error assertions should check 'status' == 'error' and 'error' in payload, never 'message'
    assert 'error' in data
    assert isinstance(data.get('errors', []), list)

def test_validate_endpoint_wrong_method(client):
    """Test that GET on /m1/validate returns 405"""
    response = client.get('/m1/validate')
    
    assert response.status_code == 405
    data = response.get_json()
    assert data['status'] == 'error'
    # Error assertions should check 'status' == 'error' and 'error' in payload, never 'message'
    assert 'error' in data

def test_schema_endpoint_wrong_method(client):
    """Test that POST on /m1/schema returns 405"""
    response = client.post('/m1/schema')
    
    assert response.status_code == 405
    data = response.get_json()
    assert data['status'] == 'error'
    # Error assertions should check 'status' == 'error' and 'error' in payload, never 'message'
    assert 'error' in data

if __name__ == '__main__':
    print("Running schema endpoint tests using Flask test_client")
    pytest.main([__file__, '-v'])
