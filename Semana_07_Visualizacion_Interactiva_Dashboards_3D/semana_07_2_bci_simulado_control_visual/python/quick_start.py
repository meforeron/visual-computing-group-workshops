#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧠 BCI Simulado - Script de Inicio Rápido
==========================================

Este script verifica que todas las dependencias estén instaladas
y ejecuta una demostración rápida del sistema BCI simulado.

Uso:
    python quick_start.py
"""

import sys
import subprocess

def check_dependencies():
    """Verificar que todas las librerías están instaladas."""
    dependencies = {
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'matplotlib': 'Matplotlib',
        'scipy': 'SciPy',
    }
    
    missing = []
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name} instalado correctamente")
        except ImportError:
            print(f"❌ {name} NO está instalado")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Instala las librerías faltantes con:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def run_quick_demo():
    """Ejecutar demostración rápida."""
    print("\n" + "="*60)
    print("🚀 DEMOSTRACIÓN RÁPIDA DE BCI SIMULADO")
    print("="*60)
    
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from scipy import signal
    
    print("\n📊 Generando datos EEG simulados...")
    
    # Parámetros
    fs = 250
    duration = 5
    t = np.arange(fs * duration) / fs
    
    # Generar señal
    noise = np.random.normal(0, 10, len(t))
    alpha = 15 * np.sin(2 * np.pi * 10 * t)
    eeg = noise + alpha
    
    print(f"✅ Datos generados: {len(eeg)} muestras")
    print(f"   Rango: [{eeg.min():.2f}, {eeg.max():.2f}] μV")
    print(f"   Media: {eeg.mean():.2f} μV")
    print(f"   Desv. Est: {eeg.std():.2f} μV")
    
    # Filtrado
    print("\n🔧 Aplicando filtro pasa banda Alpha (8-12 Hz)...")
    nyquist = fs / 2
    b, a = signal.butter(4, [8/nyquist, 12/nyquist], btype='band')
    eeg_filtered = signal.lfilter(b, a, eeg)
    
    print(f"✅ Señal filtrada")
    print(f"   Rango: [{eeg_filtered.min():.2f}, {eeg_filtered.max():.2f}] μV")
    
    # Extracción de características
    print("\n📈 Extrayendo características...")
    window_size = int(fs * 1)  # 1 segundo
    power = []
    for i in range(0, len(eeg_filtered) - window_size, window_size):
        window = eeg_filtered[i:i+window_size]
        rms = np.sqrt(np.mean(window**2))
        power.append(rms)
    
    power = np.array(power)
    threshold = power.mean()
    
    print(f"✅ Características extraídas: {len(power)} ventanas")
    print(f"   Potencia media: {power.mean():.2f} μV²")
    print(f"   Umbral: {threshold:.2f} μV²")
    
    # Detección de eventos
    events = power > threshold
    num_events = events.sum()
    
    print(f"\n🎯 Detección de eventos:")
    print(f"   Eventos detectados: {num_events}/{len(power)}")
    print(f"   Porcentaje de actividad: {(num_events/len(power)*100):.1f}%")
    
    print("\n✅ Demostración completada exitosamente!")
    print("\n📝 Próximos pasos:")
    print("   1. Abre el notebook: bci_simulado_control_visual.ipynb")
    print("   2. Ejecuta cada sección paso a paso")
    print("   3. Modifica parámetros y experimenta")
    print("   4. Completa los ejercicios prácticos")

if __name__ == "__main__":
    print("🧠 BCI SIMULADO - VERIFICACIÓN DE INSTALACIÓN")
    print("=" * 60)
    
    if not check_dependencies():
        sys.exit(1)
    
    try:
        run_quick_demo()
    except Exception as e:
        print(f"\n❌ Error durante la demostración: {e}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🎉 ¡Todo listo para comenzar el taller!")
    print("="*60)
