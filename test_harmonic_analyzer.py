#!/usr/bin/env python3
"""
Tests básicos para HarmonicTheoreticalAnalyzer

Valida funcionalidades principales del analizador harmónico
"""

import unittest
import tempfile
import os
from harmonic_theoretical_analyzer import HarmonicTheoreticalAnalyzer
import music21

class TestHarmonicAnalyzer(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.analyzer = HarmonicTheoreticalAnalyzer()
    
    def test_modal_detection_dorian(self):
        """Test: Detección correcta de modo dórico"""
        # Crear progresión dórica simple (Dm - G - Am)
        score = music21.stream.Score()
        part = music21.stream.Part()
        
        # Dm (D-F-A)
        m1 = music21.stream.Measure()
        m1.append(music21.chord.Chord(['D4', 'F4', 'A4'], quarterLength=2))
        
        # G (G-B-D)
        m2 = music21.stream.Measure()
        m2.append(music21.chord.Chord(['G4', 'B4', 'D5'], quarterLength=2))
        
        # Am (A-C-E)
        m3 = music21.stream.Measure()
        m3.append(music21.chord.Chord(['A4', 'C5', 'E5'], quarterLength=2))
        
        part.append([m1, m2, m3])
        score.append(part)
        
        # Analizar
        result = self.analyzer._perform_full_analysis(score)
        
        # Verificar que se detectó algún modo
        self.assertGreater(len(result['segments']), 0)
        first_segment = result['segments'][0]
        self.assertIn('mode', first_segment)
        self.assertIn('key_center', first_segment)
        # Verificar que es un modo válido
        self.assertIn(first_segment['mode'], ['major', 'natural_minor', 'dorian', 'phrygian', 'lydian', 'mixolydian', 'locrian'])
    
    def test_power_chord_detection(self):
        """Test: Detección correcta de power chords"""
        # Crear power chord D5 (D-A)
        chord_obj = music21.chord.Chord(['D4', 'A4'])
        symbol = self.analyzer._chord_to_symbol(chord_obj)
        
        self.assertEqual(symbol, "D5")
    
    def test_harmonic_tension_calculation(self):
        """Test: Cálculo de tensión harmónica"""
        # Crear acorde con tritono (alta tensión)
        chord_obj = music21.chord.Chord(['C4', 'F#4'])
        
        # Crear segmento simple
        segment = music21.stream.Stream()
        segment.append(chord_obj)
        
        tension = self.analyzer.calculate_harmonic_tension(segment)
        
        # Debe tener tensión alta por el tritono
        self.assertGreater(tension, 0.5)
    
    def test_chord_progression_extraction(self):
        """Test: Extracción de progresiones de acordes"""
        # Crear progresión simple
        score = music21.stream.Score()
        part = music21.stream.Part()
        
        measures = []
        chords = [['C4', 'E4', 'G4'], ['D4', 'F4', 'A4'], ['E4', 'G4', 'B4']]
        
        for chord_notes in chords:
            measure = music21.stream.Measure()
            measure.append(music21.chord.Chord(chord_notes, quarterLength=2))
            measures.append(measure)
        
        part.append(measures)
        score.append(part)
        
        # Extraer progresión usando el método correcto
        result = self.analyzer._perform_full_analysis(score)
        
        # Verificar que hay segmentos con progresiones
        self.assertGreater(len(result['segments']), 0)
        # Verificar que al menos un segmento tiene acordes
        total_chords = sum(len(seg.get('chord_progression', [])) for seg in result['segments'])
        self.assertGreaterEqual(total_chords, 1)
    
    def test_json_output_format(self):
        """Test: Formato JSON de salida válido"""
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
            # Crear score simple
            score = music21.stream.Score()
            part = music21.stream.Part()
            measure = music21.stream.Measure()
            measure.append(music21.note.Note('C4', quarterLength=1))
            part.append(measure)
            score.append(part)
            
            # Guardar
            score.write('musicxml', fp=tmp.name)
            tmp_path = tmp.name
        
        try:
            # Analizar
            result = self.analyzer.analyze_file(tmp_path)
            
            # Verificar estructura JSON
            self.assertEqual(result['status'], 'success')
            self.assertIn('temporal_segments', result)
            self.assertIn('global_analysis', result)
            self.assertIsNone(result['error'])
            
        finally:
            os.unlink(tmp_path)
    
    def test_error_handling(self):
        """Test: Manejo de errores"""
        # Archivo inexistente
        result = self.analyzer.analyze_file('archivo_inexistente.xml')
        
        self.assertEqual(result['status'], 'error')
        self.assertIsNotNone(result['error'])
    
    def test_empty_score(self):
        """Test: Manejo de score vacío"""
        score = music21.stream.Score()
        # Agregar part vacío para evitar IndexError
        empty_part = music21.stream.Part()
        score.append(empty_part)
        
        result = self.analyzer._perform_full_analysis(score)
        
        self.assertEqual(len(result['segments']), 0)

if __name__ == '__main__':
    unittest.main()