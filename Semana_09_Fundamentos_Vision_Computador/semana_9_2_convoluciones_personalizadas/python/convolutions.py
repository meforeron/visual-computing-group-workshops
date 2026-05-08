import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def create_sample_image(filepath):
    # Create a simple geometric sample image if it doesn't exist
    img = np.zeros((300, 300), dtype=np.uint8)
    # Add some shapes
    cv2.rectangle(img, (50, 50), (150, 150), 255, -1)
    cv2.circle(img, (200, 200), 50, 200, -1)
    cv2.circle(img, (200, 50), 30, 150, -1)
    # Add a checkerboard pattern at the bottom left
    for i in range(5):
        for j in range(5):
            if (i + j) % 2 == 0:
                cv2.rectangle(img, (10 + i*20, 200 + j*20), (30 + i*20, 220 + j*20), 100, -1)
    # Add some noise to test smoothing
    noise = np.random.normal(0, 15, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    cv2.imwrite(filepath, img)

def manual_convolution2d(image, kernel):
    """
    Applies a custom 2D convolution from scratch.
    """
    # Get dimensions
    i_h, i_w = image.shape
    k_h, k_w = kernel.shape
    
    # Calculate padding
    pad_h = k_h // 2
    pad_w = k_w // 2
    
    # Pad the image
    padded_image = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='constant')
    
    # Output image
    output = np.zeros_like(image, dtype=np.float32)
    
    # Apply kernel to each pixel
    for y in range(i_h):
        for x in range(i_w):
            region = padded_image[y:y+k_h, x:x+k_w]
            output[y, x] = np.sum(region * kernel)
            
    # Clip values to valid range
    output = np.clip(output, 0, 255).astype(np.uint8)
    return output

def main():
    media_dir = '../media'
    os.makedirs(media_dir, exist_ok=True)
    sample_path = os.path.join(media_dir, 'sample.jpg')
    
    if not os.path.exists(sample_path):
        create_sample_image(sample_path)
        
    # Load image in grayscale
    image = cv2.imread(sample_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print("Error loading image.")
        return

    # Define kernels
    kernels = {
        'Sharpen': np.array([
            [ 0, -1,  0],
            [-1,  5, -1],
            [ 0, -1,  0]
        ]),
        'Blur': np.ones((5, 5), dtype=np.float32) / 25.0,
        'Edge Detection': np.array([
            [-1, -1, -1],
            [-1,  8, -1],
            [-1, -1, -1]
        ])
    }

    results = []

    for name, kernel in kernels.items():
        print(f"Applying {name} filter...")
        # Manual Convolution
        manual_res = manual_convolution2d(image, kernel)
        
        # OpenCV Convolution
        # cv2.filter2D anchors at center by default
        cv_res = cv2.filter2D(image, -1, kernel)
        
        results.append((name, manual_res, cv_res))
        
        # Plot and save comparison
        plt.figure(figsize=(15, 5))
        
        plt.subplot(1, 3, 1)
        plt.title('Original')
        plt.imshow(image, cmap='gray')
        plt.axis('off')
        
        plt.subplot(1, 3, 2)
        plt.title(f'Manual: {name}')
        plt.imshow(manual_res, cmap='gray')
        plt.axis('off')
        
        plt.subplot(1, 3, 3)
        plt.title(f'OpenCV: {name}')
        plt.imshow(cv_res, cmap='gray')
        plt.axis('off')
        
        plt.tight_layout()
        save_path = os.path.join(media_dir, f'comparison_{name.lower().replace(" ", "_")}.png')
        plt.savefig(save_path)
        plt.close()
        print(f"Saved {save_path}")

if __name__ == "__main__":
    main()
