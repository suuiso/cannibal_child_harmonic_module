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

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xml', 'gp', 'gpx'}

# Get absolute path to schema file
SCHEMA_PATH = Path(__file__).parent / 'docs' / 'schema_m1.json'

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'module': 'harmonic_precision_analyzer_api',
        'version': '1.0.0'
    })

@app.route('/m1/health', methods=['GET'])
def m1_health_check():
    """M1 Health check endpoint (alias for /health)"""
    return jsonify({
        'status': 'healthy',
        'module': 'harmonic_precision_analyzer_api',
        'version': '1.0.0'
    })

@app.route('/m1/version', methods=['GET'])
def m1_version():
    """M1 Version endpoint"""
    return jsonify({
        'version': '1.0.0',
        'module': 'harmonic_precision_analyzer_api',
        'endpoints': {
            'health': '/health',
            'm1_health': '/m1/health',
            'm1_version': '/m1/version',
            'm1_analyze': '/m1/analyze',
            'm1_schema': '/m1/schema',
            'm1_validate': '/m1/validate'
        }
    })

@app.route('/m1/schema', methods=['GET'])
def m1_schema():
    """Return the JSON schema for M1 analysis results"""
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        return jsonify(schema)
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'error': 'Schema file not found',
            'module': 'harmonic_precision_analyzer_api'
        }), 404
    except json.JSONDecodeError as e:
        return jsonify({
            'status': 'error',
            'error': f'Invalid JSON in schema file: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

@app.route('/m1/validate', methods=['POST'])
def m1_validate():
    """Validate JSON data against the M1 schema"""
    try:
        # Get JSON data from request
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'error': 'Request must contain JSON data',
                'module': 'harmonic_precision_analyzer_api'
            }), 400
        
        data = request.get_json()
        
        # Load schema
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Validate data against schema
        validate(instance=data, schema=schema)
        
        return jsonify({
            'status': 'success',
            'message': 'Data is valid according to M1 schema',
            'module': 'harmonic_precision_analyzer_api'
        })
        
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'error': 'Schema file not found',
            'module': 'harmonic_precision_analyzer_api'
        }), 404
    except json.JSONDecodeError as e:
        return jsonify({
            'status': 'error',
            'error': f'Invalid JSON in schema file: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500
    except jsonschema.ValidationError as e:
        return jsonify({
            'status': 'error',
            'error': f'Validation failed: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 400
    except jsonschema.SchemaError as e:
        return jsonify({
            'status': 'error',
            'error': f'Invalid schema: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

@app.route('/m1/analyze', methods=['POST'])
def m1_analyze():
    """Main analysis endpoint for Modulo 1"""
    temp_file_path = None
    
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'No file provided. Use key "file" in form-data.',
                'module': 'harmonic_precision_analyzer_api'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'error': 'No file selected',
                'module': 'harmonic_precision_analyzer_api'
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'error': f'File type not allowed. Allowed types: {list(ALLOWED_EXTENSIONS)}',
                'module': 'harmonic_precision_analyzer_api'
            }), 400
        
        # Save file temporarily with secure filename
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, filename)
        file.save(temp_file_path)
        
        # Initialize analyzer
        analyzer = HarmonicPrecisionAnalyzer()
        
        # Perform analysis
        result = analyzer.analyze_file(temp_file_path)
        
        # Validate result against schema if available
        try:
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            validate(instance=result, schema=schema)
        except (FileNotFoundError, json.JSONDecodeError, jsonschema.ValidationError):
            # Schema validation failed, but continue with result
            pass
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Analysis failed: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                # Also try to remove the temporary directory
                os.rmdir(os.path.dirname(temp_file_path))
            except OSError:
                pass
                
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Request processing failed: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

@app.errorhandler(RequestEntityTooLarge)
@app.errorhandler(413)
def request_entity_too_large(e):
    """Handle file too large error (413)"""
    return jsonify({
        'status': 'error',
        'error': 'File too large. Maximum size: 10MB',
        'module': 'harmonic_precision_analyzer_api'
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'error': 'Endpoint not found',
        'module': 'harmonic_precision_analyzer_api',
        'available_endpoints': ['/health', '/m1/health', '/m1/version', '/m1/analyze', '/m1/schema', '/m1/validate']
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    """Handle method not allowed errors"""
    return jsonify({
        'status': 'error',
        'error': 'Method not allowed',
        'module': 'harmonic_precision_analyzer_api'
    }), 405

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
