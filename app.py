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
ALLOWED_EXTENSIONS = {'xml', 'musicxml', 'midi', 'mid', 'mxl', 'gpx', 'gp'}

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
        'error': 'Payload too large',
        'max_mb': 10
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors with consistent JSON format"""
    return jsonify({
        'status': 'error',
        'error': 'Not Found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 errors with consistent JSON format"""
    return jsonify({
        'status': 'error',
        'error': 'Method Not Allowed'
    }), 405

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'module': 'harmonic_precision_analyzer_api'
    })

@app.route('/m1/health')
def health_m1():
    """Health check endpoint (alias)"""
    return jsonify({
        'status': 'healthy',
        'module': 'harmonic_precision_analyzer_api'
    })

@app.route('/m1/version')
def version():
    """Version information endpoint"""
    return jsonify({
        'version': '1.0.0',
        'module': 'harmonic_precision_analyzer_api'
    })

@app.route('/m1/analyze', methods=['POST'])
def analyze():
    """Analyze XML/MIDI file for harmonic precision"""
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '' or (file.filename and file.filename.strip() == ''):
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file is empty by reading content
        file_content = file.read()
        if len(file_content) == 0:
            return jsonify({'error': 'Empty file'}), 400
        
        # Reset file pointer for subsequent operations
        file.seek(0)
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed. Allowed extensions: xml, musicxml, midi, mid, mxl, gpx, gp'
            }), 400
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, 
                                       suffix=f".{file.filename.rsplit('.', 1)[1].lower()}") as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Initialize analyzer and process file
            analyzer = HarmonicPrecisionAnalyzer()
            result = analyzer.analyze_file(temp_file_path)
            
            return jsonify({
                'status': 'success',
                'analysis': result,
                'module': 'harmonic_precision_analyzer_api'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': f'Analysis failed: {str(e)}',
                'module': 'harmonic_precision_analyzer_api'
            }), 500
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except RequestEntityTooLarge:
        return jsonify({
            'error': 'Payload too large',
            'max_mb': 10
        }), 413
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Request processing failed: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

@app.route('/m1/schema')
def get_schema():
    """Get JSON schema for validation"""
    try:
        with open(SCHEMA_PATH, 'r') as f:
            schema_data = json.load(f)
        return jsonify({'schema': schema_data})
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'error': 'Schema file not found',
            'module': 'harmonic_precision_analyzer_api'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Failed to load schema: {str(e)}',
            'module': 'harmonic_precision_analyzer_api'
        }), 500

@app.route('/m1/validate', methods=['POST'])
def validate_json():
    """Validate JSON data against schema"""
    # Check if request contains JSON data
    if not request.is_json or request.get_json(silent=True) is None:
        return jsonify({
            'error': 'Request must contain JSON data'
        }), 400
    
    try:
        json_data = request.get_json()
        
        # Load schema
        try:
            with open(SCHEMA_PATH, 'r') as f:
                schema = json.load(f)
        except FileNotFoundError:
            return jsonify({
                'status': 'error',
                'error': 'Schema file not found',
                'module': 'harmonic_precision_analyzer_api'
            }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': f'Failed to load schema: {str(e)}',
                'module': 'harmonic_precision_analyzer_api'
            }), 500
        
        # Validate JSON against schema
        try:
            validate(instance=json_data, schema=schema)
            return jsonify({
                'status': 'success',
                'valid': True
            }), 200
        
        except jsonschema.ValidationError as ve:
            # Collect all validation errors
            validator = jsonschema.Draft7Validator(schema)
            all_errors = [str(error) for error in validator.iter_errors(json_data)]
            
            return jsonify({
                'status': 'error',
                'valid': False,
                'errors': all_errors if all_errors else [str(ve)]
            }), 422
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Validation failed: {str(e)}',
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
    print(f"")
    print(f"Running on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
