import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def process_image(image_path):
    if not os.path.exists(image_path):
        print(f"Error: no se encontró la imagen '{image_path}'.")
        print("Por favor asegúrate de tener una imagen en la misma carpeta o cambiar la ruta.")
        return

    # Cargar la imagen a color
    img_color = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB)
    
    # Convertir a escala de grises
    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    
    # Aplicar filtros convolucionales simples
    # Blur (Filtro Gaussiano)
    img_blur = cv2.GaussianBlur(img_gray, (5, 5), 0)
    
    # Sharpening (Filtro de enfoque)
    kernel_sharpening = np.array([[-1,-1,-1], 
                                  [-1, 9,-1], 
                                  [-1,-1,-1]])
    img_sharpen = cv2.filter2D(img_gray, -1, kernel_sharpening)
    
    # Implementar detección de bordes
    # Filtro Sobel en X
    sobel_x = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0, ksize=3)
    sobel_x = cv2.convertScaleAbs(sobel_x)
    
    # Filtro Sobel en Y
    sobel_y = cv2.Sobel(img_gray, cv2.CV_64F, 0, 1, ksize=3)
    sobel_y = cv2.convertScaleAbs(sobel_y)
    
    # Filtro Laplaciano
    laplacian = cv2.Laplacian(img_gray, cv2.CV_64F)
    laplacian = cv2.convertScaleAbs(laplacian)
    
    # Visualizar resultados y comparacion con matplotlib
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    
    images = [
        ("Imagen Original", img_rgb, None),
        ("Escala de Grises", img_gray, 'gray'),
        ("Blur (Desenfocado)", img_blur, 'gray'),
        ("Sharpening (Enfocado)", img_sharpen, 'gray'),
        ("Bordes Sobel X", sobel_x, 'gray'),
        ("Bordes Sobel Y", sobel_y, 'gray'),
        ("Bordes Laplaciano", laplacian, 'gray')
    ]
    
    for i, (title, img, cmap) in enumerate(images):
        if cmap:
            axes[i].imshow(img, cmap=cmap)
        else:
            axes[i].imshow(img)
        axes[i].set_title(title)
        axes[i].axis('off')
        
    # Ocultar el último cuadro que sobra
    axes[7].axis('off')
    
    plt.tight_layout()
    
    # Crear carpeta media si no existe y guardar resultado
    media_dir = os.path.join(os.path.dirname(image_path), "..", "media")
    os.makedirs(media_dir, exist_ok=True)
    plt.savefig(os.path.join(media_dir, "resultados.png"))
    print("Resultados guardados en la carpeta 'media'.")
    
    plt.show()

if __name__ == "__main__":
    # Nombre de la imagen de prueba, cambiar según corresponda
    script_dir = os.path.dirname(os.path.abspath(__file__))
    process_image(os.path.join(script_dir, "test.jpg"))
