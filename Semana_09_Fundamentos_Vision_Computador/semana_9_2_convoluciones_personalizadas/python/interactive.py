import cv2
import numpy as np
import os

original_image = None

def update_kernel(*args):
    # Retrieve slider values
    k11 = cv2.getTrackbarPos('k11', 'Interactive Filter') - 10
    k12 = cv2.getTrackbarPos('k12', 'Interactive Filter') - 10
    k13 = cv2.getTrackbarPos('k13', 'Interactive Filter') - 10
    
    k21 = cv2.getTrackbarPos('k21', 'Interactive Filter') - 10
    k22 = cv2.getTrackbarPos('k22', 'Interactive Filter') - 10
    k23 = cv2.getTrackbarPos('k23', 'Interactive Filter') - 10
    
    k31 = cv2.getTrackbarPos('k31', 'Interactive Filter') - 10
    k32 = cv2.getTrackbarPos('k32', 'Interactive Filter') - 10
    k33 = cv2.getTrackbarPos('k33', 'Interactive Filter') - 10
    
    # Construct kernel
    kernel = np.array([
        [k11, k12, k13],
        [k21, k22, k23],
        [k31, k32, k33]
    ], dtype=np.float32)
    
    # Normalize if requested
    normalize = cv2.getTrackbarPos('Normalize', 'Interactive Filter')
    if normalize == 1:
        k_sum = np.sum(kernel)
        if k_sum != 0:
            kernel = kernel / k_sum
            
    # Apply filter using OpenCV for realtime performance
    global original_image
    filtered = cv2.filter2D(original_image, -1, kernel)
    
    # Show results
    cv2.imshow('Interactive Filter', filtered)

def main():
    global original_image
    
    media_dir = '../media'
    sample_path = os.path.join(media_dir, 'sample.jpg')
    
    if not os.path.exists(sample_path):
        print("Please run convolutions.py first to generate the sample image.")
        return
        
    original_image = cv2.imread(sample_path, cv2.IMREAD_GRAYSCALE)
    if original_image is None:
        print("Error loading image.")
        return
        
    cv2.namedWindow('Interactive Filter', cv2.WINDOW_NORMAL)
    
    # Create trackbars
    # Offset by 10 so we can have negative values (-10 to 10)
    # The default value in createTrackbar cannot be negative, so we use 0-20 mapped to -10 to 10
    cv2.createTrackbar('k11', 'Interactive Filter', 10, 20, update_kernel)
    cv2.createTrackbar('k12', 'Interactive Filter', 9, 20, update_kernel)  # -1
    cv2.createTrackbar('k13', 'Interactive Filter', 10, 20, update_kernel)
    
    cv2.createTrackbar('k21', 'Interactive Filter', 9, 20, update_kernel)  # -1
    cv2.createTrackbar('k22', 'Interactive Filter', 15, 20, update_kernel) # 5
    cv2.createTrackbar('k23', 'Interactive Filter', 9, 20, update_kernel)  # -1
    
    cv2.createTrackbar('k31', 'Interactive Filter', 10, 20, update_kernel)
    cv2.createTrackbar('k32', 'Interactive Filter', 9, 20, update_kernel)  # -1
    cv2.createTrackbar('k33', 'Interactive Filter', 10, 20, update_kernel)
    
    cv2.createTrackbar('Normalize', 'Interactive Filter', 0, 1, update_kernel)
    
    # Show initial state
    update_kernel()
    
    print("Press 'q' or 'ESC' to exit.")
    print("Press 's' to save the current filter result.")
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('s'):
            # Save the current result
            filtered = cv2.filter2D(original_image, -1, update_kernel_silent())
            save_path = os.path.join(media_dir, 'interactive_result.png')
            cv2.imwrite(save_path, filtered)
            print(f"Saved result to {save_path}")
            
    cv2.destroyAllWindows()

def update_kernel_silent():
    k11 = cv2.getTrackbarPos('k11', 'Interactive Filter') - 10
    k12 = cv2.getTrackbarPos('k12', 'Interactive Filter') - 10
    k13 = cv2.getTrackbarPos('k13', 'Interactive Filter') - 10
    k21 = cv2.getTrackbarPos('k21', 'Interactive Filter') - 10
    k22 = cv2.getTrackbarPos('k22', 'Interactive Filter') - 10
    k23 = cv2.getTrackbarPos('k23', 'Interactive Filter') - 10
    k31 = cv2.getTrackbarPos('k31', 'Interactive Filter') - 10
    k32 = cv2.getTrackbarPos('k32', 'Interactive Filter') - 10
    k33 = cv2.getTrackbarPos('k33', 'Interactive Filter') - 10
    
    kernel = np.array([
        [k11, k12, k13],
        [k21, k22, k23],
        [k31, k32, k33]
    ], dtype=np.float32)
    
    normalize = cv2.getTrackbarPos('Normalize', 'Interactive Filter')
    if normalize == 1:
        k_sum = np.sum(kernel)
        if k_sum != 0:
            kernel = kernel / k_sum
    return kernel

if __name__ == "__main__":
    main()
