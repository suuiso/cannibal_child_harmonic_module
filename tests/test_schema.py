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
    assert '$schema' in data
    assert '$id' in data
    assert 'title' in data
    assert 'version' in data
    assert 'type' in data
    assert 'properties' in data
    assert 'required' in data
    
    # Check schema metadata
    assert data['title'] == 'M1 Schema'
    assert data['version'] == '1.0.0'
    assert data['type'] == 'object'
    
    # Check required properties
    assert 'version' in data['required']
    assert 'data' in data['required']


def test_validate_endpoint_valid_data(client):
    """Test /m1/validate with valid data according to schema"""
    # Load sample valid data
    sample_data = {
        "version": "1.0.0",
        "data": {
            "id": "test-123",
            "name": "Test Item"
        }
    }
    
    response = client.post('/m1/validate', 
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'valid'
    assert 'message' in data
    assert 'module' in data
    assert data['module'] == 'harmonic_precision_analyzer_api'


def test_validate_endpoint_invalid_data_missing_version(client):
    """Test /m1/validate with invalid data (missing version)"""
    sample_data = {
        "data": {
            "id": "test-123",
            "name": "Test Item"
        }
    }
    
    response = client.post('/m1/validate', 
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'invalid'
    assert 'validation_error' in data
    assert 'module' in data


def test_validate_endpoint_invalid_data_missing_data(client):
    """Test /m1/validate with invalid data (missing data object)"""
    sample_data = {
        "version": "1.0.0"
    }
    
    response = client.post('/m1/validate', 
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'invalid'
    assert 'validation_error' in data


def test_validate_endpoint_invalid_data_wrong_version(client):
    """Test /m1/validate with invalid version"""
    sample_data = {
        "version": "2.0.0",  # Wrong version, schema expects 1.0.0
        "data": {
            "id": "test-123",
            "name": "Test Item"
        }
    }
    
    response = client.post('/m1/validate', 
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'invalid'
    assert 'validation_error' in data


def test_validate_endpoint_invalid_data_missing_id(client):
    """Test /m1/validate with missing required field in data object"""
    sample_data = {
        "version": "1.0.0",
        "data": {
            "name": "Test Item"  # Missing required 'id' field
        }
    }
    
    response = client.post('/m1/validate', 
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'invalid'
    assert 'validation_error' in data


def test_validate_endpoint_invalid_data_empty_name(client):
    """Test /m1/validate with empty name (violates minLength: 1)"""
    sample_data = {
        "version": "1.0.0",
        "data": {
            "id": "test-123",
            "name": ""  # Empty name violates minLength: 1
        }
    }
    
    response = client.post('/m1/validate', 
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'invalid'
    assert 'validation_error' in data


def test_validate_endpoint_invalid_data_additional_properties(client):
    """Test /m1/validate with additional properties (not allowed)"""
    sample_data = {
        "version": "1.0.0",
        "data": {
            "id": "test-123",
            "name": "Test Item",
            "extra_field": "not allowed"  # Additional property not allowed
        }
    }
    
    response = client.post('/m1/validate', 
                          json=sample_data,
                          content_type='application/json')
    
    assert response.status_code == 400
    
    data = response.get_json()
    assert data['status'] == 'invalid'
    assert 'validation_error' in data


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
