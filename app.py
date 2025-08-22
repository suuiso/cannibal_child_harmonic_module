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

@app.errorhandler(413)
def payload_too_large(e):
    """Handle payload too large errors with consistent JSON format"""
    return jsonify({
        'status': 'error',
        'error': 'Payload too large',
        'max_mb': 10
    }), 413

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
    try:
        from harmonic_precision_analyzer import __version__
        analyzer_version = __version__
    except ImportError:
        analyzer_version = 'unknown'
    
    return jsonify({
        'status': 'success',
        'api_version': '1.0.0',
        'analyzer_version': analyzer_version,
        'module': 'harmonic_precision_analyzer_api'
    })

@app.route('/m1/analyze', methods=['POST'])
def m1_analyze():
    """M1 XML Analysis endpoint with robust error handling"""
    try:
        # Check if file part is present in request
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'File part missing'
            }), 400
        
        file = request.files['file']
        
        # Check if file was actually selected
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'error': 'No file selected'
            }), 400
        
        # Check if file is empty (0 bytes)
        if file.content_length == 0:
            # For cases where content_length might not be set, read and check
            file_content = file.read()
            if len(file_content) == 0:
                return jsonify({
                    'status': 'error',
                    'error': 'Empty file'
                }), 400
            # Reset file pointer after reading
            file.seek(0)
        
        # Validate file extension
        if not file.filename or not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'error': f'Invalid file type. Allowed extensions: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}') as tmp_file:
            file.save(tmp_file.name)
            temp_filepath = tmp_file.name
        
        try:
            # Initialize analyzer and process file
            analyzer = HarmonicPrecisionAnalyzer()
            result = analyzer.analyze_xml(temp_filepath)
            
            # Clean up temp file
            os.unlink(temp_filepath)
            
            return jsonify({
                'status': 'success',
                'filename': filename,
                'analysis': result,
                'module': 'harmonic_precision_analyzer_api'
            })
            
        except Exception as analysis_error:
            # Clean up temp file on error
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)
            
            return jsonify({
                'status': 'error',
                'error': f'Analysis failed: {str(analysis_error)}',
                'module': 'harmonic_precision_analyzer_api'
            }), 500
    
    except RequestEntityTooLarge:
        # This should be handled by the errorhandler, but include as fallback
        return jsonify({
            'status': 'error',
            'error': 'Payload too large',
            'max_mb': 10
        }), 413
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Unexpected error: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

@app.route('/m1/schema', methods=['GET'])
def m1_schema():
    """M1 JSON Schema endpoint"""
    try:
        if not SCHEMA_PATH.exists():
            return jsonify({
                'status': 'error',
                'error': f'Schema file not found at {SCHEMA_PATH}',
                'module': 'harmonic_precision_analyzer_api'
            }), 404
        
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        return jsonify({
            'status': 'success',
            'schema': schema,
            'module': 'harmonic_precision_analyzer_api'
        })
    
    except json.JSONDecodeError as e:
        return jsonify({
            'status': 'error',
            'error': f'Invalid JSON in schema file: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Schema loading failed: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

@app.route('/m1/validate', methods=['POST'])
def m1_validate():
    """M1 JSON Validation endpoint with robust error handling"""
    try:
        # Check Content-Type and request.is_json
        if not request.is_json or request.content_type != 'application/json':
            return jsonify({
                'status': 'error',
                'error': 'Request must contain JSON data'
            }), 400
        
        # Get JSON data
        json_data = request.get_json()
        
        # Check for None or empty JSON
        if json_data is None or json_data == {}:
            return jsonify({
                'status': 'error',
                'error': 'Empty or invalid JSON data'
            }), 400
        
        # Load schema
        if not SCHEMA_PATH.exists():
            return jsonify({
                'status': 'error',
                'error': f'Schema file not found at {SCHEMA_PATH}',
                'module': 'harmonic_precision_analyzer_api'
            }), 500
        
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Validate JSON against schema
        try:
            validate(instance=json_data, schema=schema)
            return jsonify({
                'status': 'success',
                'valid': True
            }), 200
        
        except jsonschema.ValidationError as ve:
            errors = [str(ve)]
            # Collect all validation errors if possible
            validator = jsonschema.Draft7Validator(schema)
            all_errors = [str(error) for error in validator.iter_errors(json_data)]
            
            return jsonify({
                'status': 'error',
                'valid': False,
                'errors': all_errors if all_errors else errors
            }), 422
    
    except json.JSONDecodeError:
        return jsonify({
            'status': 'error',
            'error': 'Empty or invalid JSON data'
        }), 400
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Validation failed: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

@app.route('/debug/ls', methods=['GET'])
def debug_ls():
    """Debug endpoint to list directory contents"""
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
