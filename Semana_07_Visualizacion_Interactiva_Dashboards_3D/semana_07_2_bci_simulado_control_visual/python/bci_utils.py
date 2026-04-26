"""
🧠 Utilidades para BCI Simulado
===============================

Este módulo contiene funciones reutilizables para procesamiento de señales EEG
y análisis BCI. Puede importarse para extender la funcionalidad del taller.

Módulos:
    - signal_processing: Filtrado y procesamiento de señales
    - feature_extraction: Extracción de características
    - event_detection: Detección de eventos y clasificación
    - visualization: Funciones de visualización
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
from scipy.signal import butter, lfilter, welch


# ==================== PROCESAMIENTO DE SEÑALES ====================

def bandpass_filter(signal_data, lowcut, highcut, fs, order=4):
    """
    Aplicar filtro pasa banda Butterworth.
    
    Parámetros:
    -----------
    signal_data : array-like
        Señal a filtrar
    lowcut : float
        Frecuencia de corte inferior (Hz)
    highcut : float
        Frecuencia de corte superior (Hz)
    fs : float
        Frecuencia de muestreo (Hz)
    order : int
        Orden del filtro (default: 4)
    
    Retorna:
    --------
    filtered_signal : ndarray
        Señal filtrada
    """
    nyquist_freq = fs / 2
    low = lowcut / nyquist_freq
    high = highcut / nyquist_freq
    
    if low <= 0 or high >= 1:
        raise ValueError(f"Frecuencias de corte inválidas para Nyquist={nyquist_freq} Hz")
    
    b, a = butter(order, [low, high], btype='band')
    filtered_signal = lfilter(b, a, signal_data)
    
    return filtered_signal


def notch_filter(signal_data, freq, fs, width=2):
    """
    Aplicar filtro notch para eliminar frecuencias específicas (ej: 50/60 Hz).
    
    Parámetros:
    -----------
    signal_data : array-like
        Señal a filtrar
    freq : float
        Frecuencia a eliminar (Hz)
    fs : float
        Frecuencia de muestreo (Hz)
    width : float
        Ancho del notch (Hz)
    
    Retorna:
    --------
    filtered_signal : ndarray
        Señal filtrada
    """
    nyquist_freq = fs / 2
    low = (freq - width/2) / nyquist_freq
    high = (freq + width/2) / nyquist_freq
    
    b, a = butter(4, [low, high], btype='bandstop')
    filtered_signal = lfilter(b, a, signal_data)
    
    return filtered_signal


def normalize_signal(signal_data, method='zscore'):
    """
    Normalizar una señal.
    
    Parámetros:
    -----------
    signal_data : array-like
        Señal a normalizar
    method : str
        'zscore': (x - mean) / std
        'minmax': (x - min) / (max - min)
        'mean': x / mean
    
    Retorna:
    --------
    normalized : ndarray
        Señal normalizada
    """
    if method == 'zscore':
        return (signal_data - np.mean(signal_data)) / np.std(signal_data)
    elif method == 'minmax':
        return (signal_data - np.min(signal_data)) / (np.max(signal_data) - np.min(signal_data))
    elif method == 'mean':
        return signal_data / np.mean(signal_data)
    else:
        raise ValueError(f"Método desconocido: {method}")


# ==================== EXTRACCIÓN DE CARACTERÍSTICAS ====================

def extract_power_features(signal_data, fs, window_size_sec=1, method='rms'):
    """
    Extraer características de potencia usando ventanas deslizantes.
    
    Parámetros:
    -----------
    signal_data : array-like
        Señal a procesar
    fs : float
        Frecuencia de muestreo (Hz)
    window_size_sec : float
        Tamaño de ventana en segundos
    method : str
        'rms': Root Mean Square
        'welch': Densidad Espectral de Potencia
        'energy': Energía de la señal
    
    Retorna:
    --------
    power : ndarray
        Valores de potencia por ventana
    time_windows : ndarray
        Tiempos correspondientes
    """
    window_size = int(fs * window_size_sec)
    num_windows = len(signal_data) // window_size
    
    power = []
    time_windows = []
    
    for i in range(num_windows):
        start_idx = i * window_size
        end_idx = (i + 1) * window_size
        window = signal_data[start_idx:end_idx]
        
        if method == 'rms':
            power_val = np.sqrt(np.mean(window**2))
        elif method == 'energy':
            power_val = np.sum(window**2)
        elif method == 'welch':
            freq, psd = welch(window, fs=fs, nperseg=min(256, len(window)))
            power_val = np.mean(psd)
        else:
            raise ValueError(f"Método desconocido: {method}")
        
        power.append(power_val)
        time_window = (start_idx + end_idx) / (2 * fs)
        time_windows.append(time_window)
    
    return np.array(power), np.array(time_windows)


def compute_spectral_features(signal_data, fs, freq_bands=None):
    """
    Calcular características espectrales en bandas de frecuencia.
    
    Parámetros:
    -----------
    signal_data : array-like
        Señal a procesar
    fs : float
        Frecuencia de muestreo (Hz)
    freq_bands : dict
        Diccionario con bandas: {'alpha': (8, 12), 'beta': (12, 30)}
    
    Retorna:
    --------
    features : dict
        Potencia en cada banda
    """
    if freq_bands is None:
        freq_bands = {
            'delta': (0.5, 4),
            'theta': (4, 7),
            'alpha': (8, 12),
            'beta': (12, 30),
            'gamma': (30, 100)
        }
    
    freqs, psd = welch(signal_data, fs=fs, nperseg=min(1024, len(signal_data)))
    features = {}
    
    for band_name, (low_freq, high_freq) in freq_bands.items():
        mask = (freqs >= low_freq) & (freqs <= high_freq)
        band_power = np.mean(psd[mask])
        features[band_name] = band_power
    
    return features


# ==================== DETECCIÓN DE EVENTOS ====================

def detect_events_threshold(features, threshold, method='simple'):
    """
    Detectar eventos usando umbralización.
    
    Parámetros:
    -----------
    features : array-like
        Características a analizar
    threshold : float
        Valor umbral
    method : str
        'simple': x > threshold
        'above_mean': x > mean + threshold*std
        'zscore': z-score > threshold
    
    Retorna:
    --------
    events : ndarray
        Array de eventos (0/1)
    """
    if method == 'simple':
        events = (features > threshold).astype(int)
    elif method == 'above_mean':
        threshold_val = np.mean(features) + threshold * np.std(features)
        events = (features > threshold_val).astype(int)
    elif method == 'zscore':
        z_scores = (features - np.mean(features)) / np.std(features)
        events = (z_scores > threshold).astype(int)
    else:
        raise ValueError(f"Método desconocido: {method}")
    
    return events


def classify_state(alpha_power, beta_power, attention_level, thresholds):
    """
    Clasificar estado cerebral en categorías.
    
    Parámetros:
    -----------
    alpha_power : float
        Potencia de banda Alpha
    beta_power : float
        Potencia de banda Beta
    attention_level : float
        Nivel de atención normalizado
    thresholds : dict
        {'alpha': th_alpha, 'beta': th_beta, 'attention': th_attn}
    
    Retorna:
    --------
    state : int
        0: Inactivo, 1: Relajado, 2: Concentrado, 3: Muy Activo
    state_label : str
        Descripción del estado
    """
    labels = {
        0: "INACTIVO",
        1: "RELAJADO",
        2: "CONCENTRADO",
        3: "MUY ACTIVO"
    }
    
    if attention_level > thresholds.get('attention', 0.5):
        state = 3
    elif beta_power > thresholds.get('beta', 0):
        state = 2
    elif alpha_power > thresholds.get('alpha', 0):
        state = 1
    else:
        state = 0
    
    return state, labels[state]


# ==================== VISUALIZACIÓN ====================

def plot_signal_with_events(time, signal_data, events=None, title="Señal con Eventos"):
    """
    Graficar señal con eventos superpuestos.
    
    Parámetros:
    -----------
    time : array-like
        Vector de tiempo
    signal_data : array-like
        Datos de la señal
    events : array-like, optional
        Índices o tiempos de eventos
    title : str
        Título del gráfico
    """
    fig, ax = plt.subplots(figsize=(14, 5))
    
    ax.plot(time, signal_data, color='#2E86AB', linewidth=1.5, label='Señal')
    
    if events is not None:
        for event_time in events:
            ax.axvline(x=event_time, color='red', alpha=0.5, linestyle='--')
    
    ax.set_xlabel('Tiempo (segundos)', fontweight='bold')
    ax.set_ylabel('Amplitud (μV)', fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    return fig, ax


def plot_spectrum(signal_data, fs, title="Espectro de Potencia"):
    """
    Graficar espectro de potencia.
    
    Parámetros:
    -----------
    signal_data : array-like
        Señal a analizar
    fs : float
        Frecuencia de muestreo
    title : str
        Título del gráfico
    """
    freqs, psd = welch(signal_data, fs=fs, nperseg=1024)
    
    fig, ax = plt.subplots(figsize=(12, 5))
    
    ax.semilogy(freqs, psd, color='#06A77D', linewidth=2)
    
    # Marcar bandas
    ax.axvspan(8, 12, alpha=0.2, color='blue', label='Alpha')
    ax.axvspan(12, 30, alpha=0.2, color='red', label='Beta')
    
    ax.set_xlabel('Frecuencia (Hz)', fontweight='bold')
    ax.set_ylabel('PSD (V²/Hz)', fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlim(0, 50)
    ax.grid(True, alpha=0.3, which='both')
    ax.legend()
    
    plt.tight_layout()
    return fig, ax


def plot_features_timeline(time, alpha, beta, attention, thresholds=None):
    """
    Graficar características en línea de tiempo.
    
    Parámetros:
    -----------
    time : array-like
        Vector de tiempo
    alpha : array-like
        Potencia Alpha
    beta : array-like
        Potencia Beta
    attention : array-like
        Nivel de atención
    thresholds : dict, optional
        Umbrales para visualizar
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    # Alpha
    axes[0].plot(time, alpha, color='#0066FF', marker='o', markersize=4, linewidth=2)
    if thresholds and 'alpha' in thresholds:
        axes[0].axhline(y=thresholds['alpha'], color='#0066FF', linestyle='--', alpha=0.7)
    axes[0].fill_between(time, alpha, alpha=0.3, color='#0066FF')
    axes[0].set_ylabel('Potencia Alpha', fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # Beta
    axes[1].plot(time, beta, color='#FF0033', marker='s', markersize=4, linewidth=2)
    if thresholds and 'beta' in thresholds:
        axes[1].axhline(y=thresholds['beta'], color='#FF0033', linestyle='--', alpha=0.7)
    axes[1].fill_between(time, beta, alpha=0.3, color='#FF0033')
    axes[1].set_ylabel('Potencia Beta', fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    # Atención
    colors = ['#00AA00' if x > 0 else '#FF8800' for x in attention]
    axes[2].bar(time, attention, color=colors, alpha=0.7, width=0.7)
    if thresholds and 'attention' in thresholds:
        axes[2].axhline(y=thresholds['attention'], color='red', linestyle='--', linewidth=2)
    axes[2].set_xlabel('Tiempo (segundos)', fontweight='bold')
    axes[2].set_ylabel('Atención', fontweight='bold')
    axes[2].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    return fig, axes


# ==================== UTILIDADES ====================

def calculate_statistics(signal_data):
    """Calcular estadísticas básicas de una señal."""
    stats = {
        'mean': np.mean(signal_data),
        'std': np.std(signal_data),
        'min': np.min(signal_data),
        'max': np.max(signal_data),
        'median': np.median(signal_data),
        'rms': np.sqrt(np.mean(signal_data**2))
    }
    return stats


def sliding_window(data, window_size, step=1):
    """Generar ventanas deslizantes de un array."""
    windows = []
    for i in range(0, len(data) - window_size + 1, step):
        windows.append(data[i:i+window_size])
    return np.array(windows)


if __name__ == "__main__":
    print("🧠 Módulo de utilidades para BCI Simulado")
    print("Importa este módulo para usar las funciones")
    print("\nEjemplo:")
    print("  from bci_utils import bandpass_filter, extract_power_features")
    print("  filtered = bandpass_filter(signal, 8, 12, fs=250)")
