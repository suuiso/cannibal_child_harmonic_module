#!/usr/bin/env python3
"""
Flask API for Harmonic Precision Analyzer
Modulo 1 - Análisis Armónico de Cannibal Child (XML/MIDI/Partituras)
Exposes /m1/analyze endpoint for XML analysis
"""
import os
import tempfile
import json
from pathlib import Path
from flask import Flask, request, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from harmonic_precision_analyzer import HarmonicPrecisionAnalyzer
import jsonschema
from jsonschema import validate

# JSON response helpers
def json_success(data=None, message=None, **kwargs):
    """Standard JSON success response"""
    response = {"status": "success"}
    if data is not None:
        response.update(data)
    if message:
        response["message"] = message
    response.update(kwargs)
    return jsonify(response)

def json_error(message, code=400, **kwargs):
    """Standard JSON error response"""
    response = {
        "status": "error",
        "error": message
    }
    response.update(kwargs)
    return jsonify(response), code

# Flask app setup
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure paths
BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "schemas" / "cannibal_child_schema.json"

# Initialize analyzer
analyzer = HarmonicPrecisionAnalyzer()

# Error handlers for standard HTTP errors
@app.errorhandler(404)
def not_found(error):
    return json_error("Endpoint not found", 404)

@app.errorhandler(405)
def method_not_allowed(error):
    return json_error("Method not allowed", 405)

@app.errorhandler(413)
@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return json_error("File too large", 413)

# Routes
@app.route('/health', methods=['GET'])
@app.route('/m1/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status":"success","health":"healthy","module":"harmonic_precision_analyzer","version":"1.0.0"})

@app.route('/m1/version', methods=['GET'])
def version():
    """Version endpoint - hardened to never return 500"""
    try:
        return jsonify({"status":"success","version":"1.0.0","module":"harmonic_precision_analyzer","endpoint":"m1"})
    except Exception:
        # Hardened fallback - should never fail
        return jsonify({
            "status": "success",
            "version": "1.0.0",
            "module": "harmonic_precision_analyzer",
            "endpoint": "m1"
        }), 200

@app.route('/m1/analyze', methods=['POST'])
def analyze():
    """Analyze XML file for harmonic precision"""
    try:
        # Check content type for multipart/form-data
        if not request.content_type or not request.content_type.startswith('multipart/form-data'):
            return json_error("Content-Type must be multipart/form-data")
        
        # Check if file is present
        if 'file' not in request.files:
            return json_error("No file provided")
        
        file = request.files['file']
        if file.filename == '' or not file.filename:
            return json_error("No file provided")
        
        if not file:
            return json_error("No file provided")
        
        # Validate file extension - accept XML, MusicXML, and MXL files
        filename_lower = file.filename.lower()
        valid_extensions = ('.xml', '.musicxml', '.mxl')
        if not filename_lower.endswith(valid_extensions):
            return json_error("Invalid file type. Only XML, MusicXML, and MXL files are allowed.")
        
        # Create secure temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as temp_file:
            file.save(temp_file.name)
            temp_path = Path(temp_file.name)
        
        try:
            # Analyze the file using analyze_xml_precision
            result = analyzer.analyze_xml_precision(temp_path)
            
            return json_success({
                "analysis": result,
                "filename": secure_filename(file.filename),
                "module": "harmonic_precision_analyzer"
            })
        
        except Exception as e:
            return json_error(f"Analysis error: {str(e)}")
        
        finally:
            # Clean up temporary file
            if temp_path.exists():
                temp_path.unlink()
    
    except Exception as e:
        return json_error(f"File processing error: {str(e)}")

@app.route('/m1/schema', methods=['GET'])
def get_schema():
    """Get JSON schema for validation"""
    try:
        if not SCHEMA_PATH.exists():
            # Fallback si el schema no existe
            fallback_schema = {
                "type": "object",
                "properties": {
                    "version": {"type": "string"},
                    "data": {"type": "object"}
                }
            }
            return json_success({"schema": fallback_schema})
        
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as schema_file:
            content = schema_file.read().strip()
            if not content:
                # Fallback si el schema está vacío
                fallback_schema = {
                    "type": "object",
                    "properties": {
                        "version": {"type": "string"},
                        "data": {"type": "object"}
                    }
                }
                return json_success({"schema": fallback_schema})
            
            schema = json.loads(content)
        
        return json_success({"schema": schema})
    
    except json.JSONDecodeError as e:
        # Fallback si hay error parseando JSON
        fallback_schema = {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "data": {"type": "object"}
            }
        }
        return json_success({"schema": fallback_schema})
    except Exception as e:
        # Fallback para cualquier otro error
        fallback_schema = {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "data": {"type": "object"}
            }
        }
        return json_success({"schema": fallback_schema})

@app.route('/m1/validate', methods=['POST'])
def validate_json():
    """Validate JSON against schema"""
    try:
        # Check if JSON data is provided
        if not request.is_json:
            return json_error('Request must contain valid JSON')
        
        json_data = request.get_json()
        if json_data is None:
            return json_error('Request must contain valid JSON')
        
        # Load schema with fallbacks
        try:
            if not SCHEMA_PATH.exists():
                fallback_schema = {
                    "type": "object",
                    "properties": {
                        "version": {"type": "string"},
                        "data": {"type": "object"}
                    }
                }
                schema = fallback_schema
            else:
                with open(SCHEMA_PATH, 'r', encoding='utf-8') as schema_file:
                    content = schema_file.read().strip()
                    if not content:
                        fallback_schema = {
                            "type": "object",
                            "properties": {
                                "version": {"type": "string"},
                                "data": {"type": "object"}
                            }
                        }
                        schema = fallback_schema
                    else:
                        schema = json.loads(content)
        
        except (json.JSONDecodeError, FileNotFoundError):
            fallback_schema = {
                "type": "object",
                "properties": {
                    "version": {"type": "string"},
                    "data": {"type": "object"}
                }
            }
            schema = fallback_schema
        
        # Validate JSON against schema
        try:
            validate(instance=json_data, schema=schema)
            return json_success({"valid": True, "message": "Valid JSON according to schema"})
        
        except jsonschema.ValidationError as ve:
            # Collect all validation errors
            validator = jsonschema.Draft7Validator(schema)
            all_errors = [str(error) for error in validator.iter_errors(json_data)]
            
            return json_error('Invalid JSON according to schema', 422, valid=False, validation_errors=all_errors if all_errors else [str(ve)])
    
    except Exception as e:
        return json_error(f'Validation error: {str(e)}', 500)

if __name__ == '__main__':
    # Development server configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Harmonic Precision Analyzer API...")
    print(f"Available endpoints:")
    print(f"  GET  /health - Health check")
    print(f"  GET  /m1/health - Health check (alias)")
    print(f"  GET  /m1/version - Version info")
    print(f"  POST /m1/analyze - XML analysis")
    print(f"  GET  /m1/schema - JSON Schema")
    print(f"  POST /m1/validate - JSON validation")
    print(f"")
    print(f"Running on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
