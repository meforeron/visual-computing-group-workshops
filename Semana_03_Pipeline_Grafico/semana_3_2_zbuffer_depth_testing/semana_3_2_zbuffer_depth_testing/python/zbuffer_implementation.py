import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import matplotlib.patches as patches

class ZBufferRenderer:
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.image = np.zeros((height, width, 3), dtype=np.uint8)
        self.z_buffer = np.full((height, width), np.inf)
        
    def project_3d_to_2d(self, point_3d, camera_distance=8):
        """Project 3D point to 2D screen coordinates"""
        x, y, z = point_3d
        
        # Simple perspective projection with adjusted distance for larger view
        factor = camera_distance / (camera_distance - z)
        x_2d = x * factor * 60 + self.width / 2  # Scale up by 60x
        y_2d = -y * factor * 60 + self.height / 2  # Scale up by 60x
        
        return int(x_2d), int(y_2d), z
    
    def draw_triangle_no_zbuffer(self, vertices, color):
        """Draw triangle without Z-buffer (painter's algorithm)"""
        projected_vertices = [self.project_3d_to_2d(v) for v in vertices]
        
        # Simple triangle rasterization
        min_x = max(0, min(v[0] for v in projected_vertices))
        max_x = min(self.width - 1, max(v[0] for v in projected_vertices))
        min_y = max(0, min(v[1] for v in projected_vertices))
        max_y = min(self.height - 1, max(v[1] for v in projected_vertices))
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if self.point_in_triangle(x, y, projected_vertices):
                    self.image[y, x] = color
    
    def draw_triangle_with_zbuffer(self, vertices, color):
        """Draw triangle with Z-buffer for correct occlusion"""
        projected_vertices = [self.project_3d_to_2d(v) for v in vertices]
        
        # Triangle rasterization with depth testing
        min_x = max(0, min(v[0] for v in projected_vertices))
        max_x = min(self.width - 1, max(v[0] for v in projected_vertices))
        min_y = max(0, min(v[1] for v in projected_vertices))
        max_y = min(self.height - 1, max(v[1] for v in projected_vertices))
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if self.point_in_triangle(x, y, projected_vertices):
                    # Calculate interpolated Z depth
                    z_depth = self.interpolate_depth(x, y, projected_vertices)
                    
                    # Depth testing
                    if z_depth < self.z_buffer[y, x]:
                        self.z_buffer[y, x] = z_depth
                        self.image[y, x] = color
    
    def point_in_triangle(self, px, py, vertices):
        """Check if point is inside triangle using barycentric coordinates"""
        v0, v1, v2 = vertices
        
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        
        d1 = sign((px, py), v0, v1)
        d2 = sign((px, py), v1, v2)
        d3 = sign((px, py), v2, v0)
        
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        
        return not (has_neg and has_pos)
    
    def interpolate_depth(self, px, py, vertices):
        """Interpolate Z depth at pixel position"""
        v0, v1, v2 = vertices
        
        # Calculate barycentric coordinates
        denom = ((v1[1] - v2[1]) * (v0[0] - v2[0]) + (v2[0] - v1[0]) * (v0[1] - v2[1]))
        if abs(denom) < 1e-10:
            return min(v0[2], v1[2], v2[2])
        
        a = ((v1[1] - v2[1]) * (px - v2[0]) + (v2[0] - v1[0]) * (py - v2[1])) / denom
        b = ((v2[1] - v0[1]) * (px - v2[0]) + (v0[0] - v2[0]) * (py - v2[1])) / denom
        c = 1 - a - b
        
        # Interpolate Z
        return a * v0[2] + b * v1[2] + c * v2[2]
    
    def clear(self, background_color=(0, 0, 0)):
        """Clear image and Z-buffer"""
        self.image[:] = background_color
        self.z_buffer.fill(np.inf)
    
    def get_depth_visualization(self):
        """Get normalized depth buffer for visualization"""
        # Normalize depth values to [0, 1]
        valid_depths = self.z_buffer[self.z_buffer != np.inf]
        if len(valid_depths) > 0:
            min_depth = np.min(valid_depths)
            max_depth = np.max(valid_depths)
            
            normalized = np.copy(self.z_buffer)
            normalized[normalized == np.inf] = max_depth
            normalized = (normalized - min_depth) / (max_depth - min_depth + 1e-10)
            
            # Convert to grayscale
            return (normalized * 255).astype(np.uint8)
        else:
            return np.zeros((self.height, self.width), dtype=np.uint8)
    
    def save_image(self, filename):
        """Save current image"""
        img = Image.fromarray(self.image)
        img.save(filename)
    
    def save_depth_buffer(self, filename):
        """Save depth buffer visualization"""
        depth_img = self.get_depth_visualization()
        img = Image.fromarray(depth_img, mode='L')
        img.save(filename)

def create_test_scene():
    """Create test scene with overlapping triangles"""
    # Define triangles with different depths - larger and more visible
    triangles = [
        # Background triangle (far) - much larger
        ([
            [-4, -2, 3],
            [4, -2, 3],
            [0, 3, 3]
        ], [255, 100, 100]),  # Red
        
        # Middle triangle - offset and larger
        ([
            [-2, -1, 1],
            [3, -1, 1],
            [0.5, 2.5, 1]
        ], [100, 255, 100]),  # Green
        
        # Front triangle (near) - smaller but centered
        ([
            [-1.5, -0.5, -0.5],
            [1.5, -0.5, -0.5],
            [0, 1.5, -0.5]
        ], [100, 100, 255]),  # Blue
    ]
    
    return triangles

def demonstrate_zbuffer():
    """Demonstrate Z-buffer vs no Z-buffer"""
    print("Creating Z-buffer demonstration...")
    
    # Create renderers with larger canvas
    renderer_no_z = ZBufferRenderer(800, 600)
    renderer_with_z = ZBufferRenderer(800, 600)
    
    # Get test scene
    triangles = create_test_scene()
    
    # Render without Z-buffer (wrong order)
    renderer_no_z.clear()
    for vertices, color in triangles:
        renderer_no_z.draw_triangle_no_zbuffer(vertices, color)
    
    # Render with Z-buffer (correct occlusion)
    renderer_with_z.clear()
    for vertices, color in triangles:
        renderer_with_z.draw_triangle_with_zbuffer(vertices, color)
    
    # Save results
    renderer_no_z.save_image("../media/no_zbuffer.png")
    renderer_with_z.save_image("../media/with_zbuffer.png")
    renderer_with_z.save_depth_buffer("../media/depth_buffer.png")
    
    # Create comparison visualization
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    axes[0].imshow(renderer_no_z.image)
    axes[0].set_title("Without Z-Buffer\n(Painter's Algorithm)")
    axes[0].axis('off')
    
    axes[1].imshow(renderer_with_z.image)
    axes[1].set_title("With Z-Buffer\n(Correct Occlusion)")
    axes[1].axis('off')
    
    axes[2].imshow(renderer_with_z.get_depth_visualization(), cmap='gray')
    axes[2].set_title("Depth Buffer")
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.savefig("../media/zbuffer_comparison.png", dpi=150, bbox_inches='tight')
    plt.show()
    
    print("Results saved to media/ folder")

def demonstrate_zfighting():
    """Demonstrate Z-fighting with close depth values"""
    print("Demonstrating Z-fighting...")
    
    renderer = ZBufferRenderer(800, 600)
    renderer.clear()
    
    # Create two large triangles with very similar Z values (Z-fighting scenario)
    z_fight_triangles = [
        # Triangle 1 - larger
        ([
            [-3, -2, 0.5],
            [3, -2, 0.5],
            [0, 2, 0.5]
        ], [255, 0, 0]),  # Red
        
        # Triangle 2 (very close depth) - slightly offset
        ([
            [-2.8, -1.8, 0.5001],
            [2.8, -1.8, 0.5001],
            [0.2, 1.8, 0.5001]
        ], [0, 0, 255]),  # Blue
    ]
    
    for vertices, color in z_fight_triangles:
        renderer.draw_triangle_with_zbuffer(vertices, color)
    
    # Save Z-fighting result
    renderer.save_image("../media/zfighting.png")
    
    plt.figure(figsize=(10, 8))
    plt.imshow(renderer.image)
    plt.title("Z-Fighting Demonstration\n(Two triangles with very close depth values)")
    plt.axis('off')
    plt.savefig("../media/zfighting_demo.png", dpi=150, bbox_inches='tight')
    plt.show()
    
    print("Z-fighting demonstration saved")

if __name__ == "__main__":
    print("Z-Buffer Implementation from Scratch")
    print("=" * 40)
    
    # Run demonstrations
    demonstrate_zbuffer()
    demonstrate_zfighting()
    
    print("\nAll demonstrations completed!")
    print("Check the media/ folder for results")
