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
SCHEMA_PATH = Path(__file__).resolve().parent / 'docs' / 'schema_m1.json'

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
        'status': 'success',
        'module': 'harmonic_precision_analyzer_api',
        'version': '1.0.0',
        'description': 'Harmonic Precision Analyzer - Modulo 1',
        'endpoints': [
            '/health',
            '/m1/health',
            '/m1/version',
            '/m1/analyze',
            '/m1/schema',
            '/m1/validate'
        ]
    })

@app.route('/m1/schema', methods=['GET'])
def m1_schema():
    """Return the JSON schema for M1 requests"""
    try:
        if not SCHEMA_PATH.exists():
            return jsonify({
                'status': 'error',
                'error': f'Schema file not found: {SCHEMA_PATH}',
                'module': 'harmonic_precision_analyzer_api'
            }), 404
        
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        return jsonify({
            'status': 'success',
            'schema': schema,
            'module': 'harmonic_precision_analyzer_api'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Failed to load schema: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

@app.route('/m1/validate', methods=['POST'])
def m1_validate():
    """Validate JSON against M1 schema"""
    try:
        # Load schema
        if not SCHEMA_PATH.exists():
            return jsonify({
                'status': 'error',
                'error': f'Schema file not found: {SCHEMA_PATH}',
                'module': 'harmonic_precision_analyzer_api'
            }), 404
        
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Get JSON data from request
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'error': 'Request must be JSON',
                'module': 'harmonic_precision_analyzer_api'
            }), 400
        
        data = request.get_json()
        
        # Validate against schema
        validate(instance=data, schema=schema)
        
        return jsonify({
            'status': 'success',
            'message': 'JSON is valid according to M1 schema',
            'module': 'harmonic_precision_analyzer_api'
        })
    
    except jsonschema.exceptions.ValidationError as e:
        return jsonify({
            'status': 'error',
            'error': f'JSON validation failed: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 400
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Validation failed: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

@app.route('/m1/analyze', methods=['POST'])
def m1_analyze():
    """Main endpoint for XML harmonic analysis"""
    
    # Check if file is present in request
    if 'file' not in request.files:
        return jsonify({
            'status': 'error',
            'error': 'No file provided in request',
            'module': 'harmonic_precision_analyzer_api'
        }), 400
    
    file = request.files['file']
    
    # Check if filename is empty
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
            'error': f'File type not allowed. Accepted types: {", ".join(ALLOWED_EXTENSIONS)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 400
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file.filename.rsplit(".", 1)[1].lower()}') as temp_file:
            filename = secure_filename(file.filename)
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        # Initialize analyzer
        analyzer = HarmonicPrecisionAnalyzer()
        
        # Perform analysis
        result = analyzer.analyze_file(temp_file_path)
        
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass
        
        # Return result
        return jsonify({
            'status': 'success',
            'filename': filename,
            'analysis': result,
            'module': 'harmonic_precision_analyzer_api'
        })
    
    except Exception as e:
        # Clean up temporary file if it exists
        try:
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        except OSError:
            pass
        
        return jsonify({
            'status': 'error',
            'error': f'Analysis failed: {str(e)}',
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

@app.get('/debug/ls')
def debug_ls():
    """Debug endpoint to list contents of base directory and docs directory"""
    try:
        base_path = Path(__file__).resolve().parent
        docs_path = base_path / 'docs'
        
        base_contents = []
        docs_contents = []
        
        # List base directory contents
        if base_path.exists():
            for item in sorted(base_path.iterdir()):
                item_info = {
                    'name': item.name,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None
                }
                base_contents.append(item_info)
        
        # List docs directory contents
        if docs_path.exists():
            for item in sorted(docs_path.iterdir()):
                item_info = {
                    'name': item.name,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None
                }
                docs_contents.append(item_info)
        
        return jsonify({
            'status': 'success',
            'base_path': str(base_path),
            'base_contents': base_contents,
            'docs_path': str(docs_path),
            'docs_exists': docs_path.exists(),
            'docs_contents': docs_contents,
            'schema_path': str(Path(__file__).resolve().parent / 'docs' / 'schema_m1.json'),
            'schema_exists': (Path(__file__).resolve().parent / 'docs' / 'schema_m1.json').exists(),
            'module': 'harmonic_precision_analyzer_api'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Debug listing failed: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

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
    print(f"  GET  /debug/ls - Debug directory listing")
    print(f"")
    print(f"Running on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
