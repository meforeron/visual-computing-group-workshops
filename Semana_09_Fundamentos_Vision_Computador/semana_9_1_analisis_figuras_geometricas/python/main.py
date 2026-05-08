import cv2
import numpy as np
import os

def main():
    # Create media directory if it doesn't exist
    media_dir = os.path.join(os.path.dirname(__file__), '..', 'media')
    os.makedirs(media_dir, exist_ok=True)

    # 1. Generate an image with shapes
    # Create a black image
    image = np.zeros((600, 800, 3), dtype=np.uint8)

    # Draw a circle (cyan)
    cv2.circle(image, (200, 200), 80, (255, 255, 0), -1)

    # Draw a square (magenta)
    cv2.rectangle(image, (500, 100), (650, 250), (255, 0, 255), -1)

    # Draw a triangle (green)
    pts = np.array([[400, 400], [300, 500], [500, 500]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.fillPoly(image, [pts], (0, 255, 0))

    # Save original generated image
    cv2.imwrite(os.path.join(media_dir, 'original_shapes.png'), image)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Binarize the image
    _, binary = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)

    # Save binarized image
    cv2.imwrite(os.path.join(media_dir, 'binarized_shapes.png'), binary)

    # 2. Detect contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Make a copy to draw results
    result_image = image.copy()

    # 3. Process each contour
    for cnt in contours:
        # Area
        area = cv2.contourArea(cnt)
        
        # Perimeter
        perimeter = cv2.arcLength(cnt, True)
        
        # Centroid
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            cX, cY = 0, 0
            
        # Draw contour
        cv2.drawContours(result_image, [cnt], -1, (0, 0, 255), 3)
        
        # Draw centroid
        cv2.circle(result_image, (cX, cY), 5, (255, 255, 255), -1)
        
        # Approximate polygon to classify shape
        epsilon = 0.04 * perimeter
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        
        vertices = len(approx)
        shape = "Desconocido"
        if vertices == 3:
            shape = "Triangulo"
        elif vertices == 4:
            # Check if it's a square or rectangle
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w)/h
            if 0.95 <= aspect_ratio <= 1.05:
                shape = "Cuadrado"
            else:
                shape = "Rectangulo"
        elif vertices > 4:
            shape = "Circulo"
            
        # Label the shape
        text_shape = f"{shape}"
        text_metrics1 = f"A: {area:.1f}"
        text_metrics2 = f"P: {perimeter:.1f}"
        text_metrics3 = f"C: ({cX},{cY})"
        
        cv2.putText(result_image, text_shape, (cX - 40, cY - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(result_image, text_metrics1, (cX - 40, cY - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(result_image, text_metrics2, (cX - 40, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(result_image, text_metrics3, (cX - 40, cY + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Save result image
    cv2.imwrite(os.path.join(media_dir, 'result_shapes.png'), result_image)

    print("Procesamiento completado. Las imágenes se han guardado en la carpeta 'media'.")

if __name__ == "__main__":
    main()
