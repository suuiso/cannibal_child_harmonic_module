# Cannibal Child Harmonic Analysis Module

[![Python Tests](https://github.com/suuiso/cannibal_child_harmonic_module/actions/workflows/python-tests.yml/badge.svg)](https://github.com/suuiso/cannibal_child_harmonic_module/actions/workflows/python-tests.yml)

## Overview

Módulo 1 – Análisis Armónico de Cannibal Child (XML/MIDI/Partituras).

## File Limits

- **Maximum file size**: 10 MB
- **Valid extensions**: `.xml`, `.musicxml`, `.mxl`

## Endpoints

### 1. Health Check

**GET** `/health`

Verifies that the service is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-22T12:08:00Z"
}
```

**Example:**
```bash
curl -X GET <TU_HOST>/health
```

### 2. Upload Music File

**POST** `/upload`

Uploads and processes a music file for harmonic analysis.

**Parameters:**
- `file`: Music file (.xml, .musicxml, .mxl) - max 10MB

**Response:**
```json
{
  "file_id": "abc123def456",
  "filename": "cannibal_child.xml",
  "size": 2048576,
  "status": "uploaded",
  "processed_at": "2025-08-22T12:08:15Z"
}
```

**Example:**
```bash
curl -X POST <TU_HOST>/upload \
  -F "file=@cannibal_child.xml"
```

### 3. Analyze Harmony

**POST** `/analyze/{file_id}`

Performs harmonic analysis on the uploaded file.

**Parameters:**
- `file_id`: String - ID of previously uploaded file

**Response:**
```json
{
  "file_id": "abc123def456",
  "analysis": {
    "key_signature": "C major",
    "chord_progressions": [
      {
        "measure": 1,
        "chord": "C",
        "quality": "major",
        "inversion": "root"
      },
      {
        "measure": 2,
        "chord": "Am",
        "quality": "minor",
        "inversion": "root"
      }
    ],
    "harmonic_complexity": 0.65,
    "modulations": []
  },
  "processed_at": "2025-08-22T12:08:30Z"
}
```

**Example:**
```bash
curl -X POST <TU_HOST>/analyze/abc123def456
```

### 4. Get Analysis Results

**GET** `/results/{file_id}`

Retrieves the harmonic analysis results for a specific file.

**Parameters:**
- `file_id`: String - ID of analyzed file

**Response:**
```json
{
  "file_id": "abc123def456",
  "filename": "cannibal_child.xml",
  "analysis": {
    "key_signature": "C major",
    "chord_progressions": [
      {
        "measure": 1,
        "chord": "C",
        "quality": "major",
        "inversion": "root"
      },
      {
        "measure": 2,
        "chord": "Am",
        "quality": "minor",
        "inversion": "root"
      }
    ],
    "harmonic_complexity": 0.65,
    "modulations": []
  },
  "status": "completed",
  "created_at": "2025-08-22T12:08:15Z",
  "analyzed_at": "2025-08-22T12:08:30Z"
}
```

**Example:**
```bash
curl -X GET <TU_HOST>/results/abc123def456
```

### 5. List Processed Files

**GET** `/files`

Returns a list of all processed files.

**Response:**
```json
{
  "files": [
    {
      "file_id": "abc123def456",
      "filename": "cannibal_child.xml",
      "status": "completed",
      "created_at": "2025-08-22T12:08:15Z"
    }
  ],
  "total": 1
}
```

**Example:**
```bash
curl -X GET <TU_HOST>/files
```

### 6. Delete File

**DELETE** `/files/{file_id}`

Deletes a processed file and its analysis results.

**Parameters:**
- `file_id`: String - ID of file to delete

**Response:**
```json
{
  "file_id": "abc123def456",
  "status": "deleted",
  "deleted_at": "2025-08-22T12:08:45Z"
}
```

**Example:**
```bash
curl -X DELETE <TU_HOST>/files/abc123def456
```

## Usage Examples

All curl examples are copy-paste friendly. Simply replace `<TU_HOST>` with your actual host URL (e.g., `http://localhost:8000` or `https://your-domain.com`).

## Development

For development and testing, refer to the test files for exact expected responses and behavior.
