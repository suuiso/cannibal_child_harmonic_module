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
        "error": message,
        "module": "harmonic_precision_analyzer_api"
    }
    response.update(kwargs)
    return jsonify(response), code

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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
    return json_error('Archivo demasiado grande. Máximo permitido: 16MB', 413, max_mb=16)

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors with consistent JSON format"""
    return json_error('Endpoint no encontrado', 404)

@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 errors with consistent JSON format"""
    return json_error('Método HTTP no permitido', 405)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return json_success({"health": "ok", "service": "harmonic_precision_analyzer_api"})

@app.route('/m1/health', methods=['GET'])
def m1_health_check():
    """Module 1 health check endpoint"""
    return json_success({"health": "ok", "module": "m1", "service": "harmonic_precision_analyzer_api"})

@app.route('/m1/version', methods=['GET'])
def m1_version():
    """Module 1 version endpoint"""
    try:
        analyzer = HarmonicPrecisionAnalyzer()
        version = analyzer.get_version()
        return json_success({"version": version, "module": "m1"})
    except Exception as e:
        return json_error(f'Error obteniendo versión: {str(e)}', 500)

@app.route('/m1/analyze', methods=['POST'])
def m1_analyze():
    """Main XML analysis endpoint for Module 1"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return json_error('No se encontró archivo en la petición', 400)
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return json_error('No se seleccionó archivo', 400)
        
        # Validate file extension
        if not allowed_file(file.filename):
            return json_error(f'Tipo de archivo no permitido. Extensiones válidas: {", ".join(ALLOWED_EXTENSIONS)}', 400)
        
        # Check file size manually if needed (Flask should handle this via MAX_CONTENT_LENGTH)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size = 16 * 1024 * 1024  # 16MB
        if file_size > max_size:
            return json_error(f'Archivo demasiado grande. Tamaño: {file_size} bytes, máximo: {max_size} bytes', 413)
        
        # Create secure filename and temporary file
        filename = secure_filename(file.filename)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}') as temp_file:
            try:
                file.save(temp_file.name)
                
                # Initialize analyzer and perform analysis
                analyzer = HarmonicPrecisionAnalyzer()
                result = analyzer.analyze_file(temp_file.name)
                
                return json_success(result)
                
            except FileNotFoundError:
                return json_error('Archivo temporal no encontrado', 500)
            except PermissionError:
                return json_error('Permisos insuficientes para procesar archivo', 500)
            except ValueError as ve:
                return json_error(f'Error de formato en archivo: {str(ve)}', 422)
            except Exception as e:
                return json_error(f'Error procesando archivo: {str(e)}', 500)
            finally:
                # Clean up temp file
                try:
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                except Exception:
                    pass  # Ignore cleanup errors
    
    except RequestEntityTooLarge:
        return json_error('Archivo demasiado grande. Máximo permitido: 16MB', 413, max_mb=16)
    except Exception as e:
        return json_error(f'Error interno del servidor: {str(e)}', 500)

@app.route('/m1/schema', methods=['GET'])
def m1_get_schema():
    """Get JSON schema for Module 1"""
    try:
        if not SCHEMA_PATH.exists():
            return json_error('Archivo de schema no encontrado', 500)
        
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as schema_file:
            schema = json.load(schema_file)
            return json_success(schema)
    
    except FileNotFoundError:
        return json_error('Archivo de schema no encontrado', 500)
    except json.JSONDecodeError as e:
        return json_error(f'Error parseando schema JSON: {str(e)}', 500)
    except Exception as e:
        return json_error(f'Error cargando schema: {str(e)}', 500)

@app.route('/m1/validate', methods=['POST'])
def m1_validate_json():
    """Validate JSON data against Module 1 schema"""
    try:
        # Check if JSON data is provided
        if not request.is_json:
            return json_error('Petición debe contener JSON válido', 400)
        
        json_data = request.get_json()
        if json_data is None:
            return json_error('No se pudo parsear JSON', 400)
        
        # Load schema
        try:
            if not SCHEMA_PATH.exists():
                return json_error('Archivo de schema no encontrado', 500)
                
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as schema_file:
                schema = json.load(schema_file)
        
        except FileNotFoundError:
            return json_error('Archivo de schema no encontrado', 500)
        except json.JSONDecodeError as e:
            return json_error(f'Error parseando schema JSON: {str(e)}', 500)
        except Exception as e:
            return json_error(f'Error cargando schema: {str(e)}', 500)
        
        # Validate JSON against schema
        try:
            validate(instance=json_data, schema=schema)
            return json_success({"valid": True, "message": "JSON válido según schema"})
        
        except jsonschema.ValidationError as ve:
            # Collect all validation errors
            validator = jsonschema.Draft7Validator(schema)
            all_errors = [str(error) for error in validator.iter_errors(json_data)]
            
            return json_error('JSON no válido según schema', 422, valid=False, validation_errors=all_errors if all_errors else [str(ve)])
    
    except Exception as e:
        return json_error(f'Error durante validación: {str(e)}', 500)

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
