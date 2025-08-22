#!/usr/bin/env python3
"""
Flask API for Harmonic Precision Analyzer
Modulo 1 - Análisis Armónico de Cannibal Child (XML/MIDI/Partituras)
Exposes /m1/analyze endpoint for XML analysis
"""
import os
import tempfile
from flask import Flask, request, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from harmonic_precision_analyzer import HarmonicPrecisionAnalyzer

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xml', 'gp', 'gpx'}

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
            'health': ['/health', '/m1/health'],
            'version': '/m1/version',
            'analyze': '/m1/analyze'
        }
    })

@app.route('/m1/analyze', methods=['POST'])
def analyze_xml():
    """
    Analyze XML file using HarmonicPrecisionAnalyzer
    
    Expects:
    - POST request with multipart/form-data
    - File uploaded with key 'file'
    
    Returns:
    - JSON with analysis results
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'No file provided. Use key "file" in form-data',
                'module': 'harmonic_precision_analyzer_api'
            }), 400
        
        # Get file from request
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'status': 'error', 
                'error': 'No file selected',
                'module': 'harmonic_precision_analyzer_api'
            }), 400
        
        # Check if file is empty (0 bytes)
        file.seek(0)  # Reset file pointer to beginning
        first_byte = file.read(1)
        if not first_byte:
            return jsonify({
                'status': 'error',
                'error': 'Empty file (0 bytes)',
                'module': 'harmonic_precision_analyzer_api'
            }), 400
        file.seek(0)  # Reset file pointer for further processing
        
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}',
                'module': 'harmonic_precision_analyzer_api'
            }), 400
        
        # Create temporary file to save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as temp_file:
            filename = secure_filename(file.filename)
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Initialize analyzer
            analyzer = HarmonicPrecisionAnalyzer()
            
            # Perform analysis
            result = analyzer.analyze_xml_precision(temp_path)
            
            # Add API metadata
            result['api_metadata'] = {
                'endpoint': '/m1/analyze',
                'filename': filename,
                'file_size': os.path.getsize(temp_path),
                'api_version': '1.0.0'
            }
            
            return jsonify(result)
            
        except Exception as analysis_error:
            return jsonify({
                'status': 'error',
                'error': f'Analysis failed: {str(analysis_error)}',
                'module': 'harmonic_precision_analyzer_api',
                'filename': filename
            }), 500
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
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
        'available_endpoints': ['/health', '/m1/health', '/m1/version', '/m1/analyze']
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
    print(f"")
    print(f"Running on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
