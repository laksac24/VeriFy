# # certificate_detection/detector.py
# import cv2
# import numpy as np
# from PIL import Image
# import os
# from ultralytics import YOLO

# class CertificateDetector:
#     def __init__(self, model_path="./certificate_detection/yolov8/best.pt", confidence_threshold=0.5):
#         """
#         Initialize the certificate detector with your trained model
        
#         Args:
#             model_path: Path to your trained best.pt model
#             confidence_threshold: Minimum confidence for detections
#         """
#         self.confidence_threshold = confidence_threshold
#         self.model_path = model_path
#         self.model = None
        
#         # Load the model
#         if os.path.exists(self.model_path):
#             self.load_model()
#         else:
#             print(f"Model not found at {self.model_path}")
#             print("Please make sure your best.pt file is in the certificate_detection folder")
    
#     def load_model(self):
#         """Load your trained YOLO model"""
#         try:
#             self.model = YOLO(self.model_path)
#             print(f"Certificate detection model loaded from {self.model_path}")
#             return True
#         except Exception as e:
#             print(f"Error loading model: {e}")
#             return False
    
#     def detect_and_crop_certificates(self, image_path, output_folder="./processed_certificates", padding=10):
#         """
#         Detect certificates in image and crop them
        
#         Args:
#             image_path: Path to input image
#             output_folder: Folder to save cropped certificates
#             padding: Padding around detected certificate
            
#         Returns:
#             List of paths to cropped certificate images
#         """
#         if self.model is None:
#             print("Model not loaded. Cannot perform detection.")
#             return []
        
#         try:
#             # Run inference
#             results = self.model(image_path, conf=self.confidence_threshold)
            
#             # Load original image
#             image = cv2.imread(image_path)
#             if image is None:
#                 print(f"Could not load image: {image_path}")
#                 return []
            
#             os.makedirs(output_folder, exist_ok=True)
            
#             cropped_paths = []
#             base_filename = os.path.splitext(os.path.basename(image_path))[0]
            
#             # Process detections
#             for result in results:
#                 boxes = result.boxes
#                 if boxes is not None:
#                     for i, box in enumerate(boxes):
#                         # Get bounding box coordinates
#                         x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
#                         confidence = box.conf[0].cpu().numpy()
                        
#                         print(f"Detected certificate with confidence: {confidence:.2f}")
                        
#                         # Add padding
#                         h, w = image.shape[:2]
#                         x1 = max(0, x1 - padding)
#                         y1 = max(0, y1 - padding)
#                         x2 = min(w, x2 + padding)
#                         y2 = min(h, y2 + padding)
                        
#                         # Crop certificate
#                         cropped_cert = image[y1:y2, x1:x2]
                        
#                         # Save cropped certificate
#                         output_filename = f"{base_filename}_detected_{i+1}.png"
#                         output_path = os.path.join(output_folder, output_filename)
                        
#                         cv2.imwrite(output_path, cropped_cert)
#                         cropped_paths.append(output_filename)  # Just return filename for consistency
                        
#                         print(f"Cropped certificate saved: {output_path}")
            
#             return cropped_paths
        
#         except Exception as e:
#             print(f"Error during detection and cropping: {e}")
#             return []



# # certificate_detection/detector.py
# import cv2
# import numpy as np
# from PIL import Image
# import os
# from ultralytics import YOLO
# import time

# class CertificateDetector:
#     def __init__(self, model_path="./certificate_detection/yolov8/best.pt", confidence_threshold=0.5):
#         """
#         Initialize the certificate detector with your trained model
#         """
#         self.confidence_threshold = confidence_threshold
#         self.model_path = model_path
#         self.model = None
        
#         # Load the model once at startup
#         if os.path.exists(self.model_path):
#             self.load_model()
#         else:
#             print(f"Model not found at {self.model_path}")
    
#     def load_model(self):
#         """Load your trained YOLO model with optimizations"""
#         try:
#             self.model = YOLO(self.model_path)
            
#             # Optimize for speed on CPU
#             self.model.overrides['device'] = 'cpu'
#             self.model.overrides['half'] = False  # Disable FP16 for CPU
#             self.model.overrides['verbose'] = False  # Reduce logging
            
#             print(f"Certificate detection model loaded from {self.model_path}")
#             return True
#         except Exception as e:
#             print(f"Error loading model: {e}")
#             return False
    
#     def preprocess_image_for_detection(self, image_path, max_size=(640, 640)):
#         """Preprocess image to reduce inference time"""
#         try:
#             # Load and resize image to reduce processing time
#             image = cv2.imread(image_path)
#             if image is None:
#                 return None, None
                
#             original_shape = image.shape[:2]
            
#             # Resize if image is too large
#             h, w = original_shape
#             if h > max_size[0] or w > max_size[1]:
#                 # Calculate scale to maintain aspect ratio
#                 scale = min(max_size[0]/h, max_size[1]/w)
#                 new_h, new_w = int(h * scale), int(w * scale)
#                 image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
#                 print(f"Resized image from {original_shape} to {(new_h, new_w)} for faster processing")
            
#             return image, original_shape
#         except Exception as e:
#             print(f"Error preprocessing image: {e}")
#             return None, None
    
#     def detect_and_crop_certificates(self, image_path, output_folder="./processed_certificates", padding=10, timeout=30):
#         """
#         Detect certificates in image and crop them with timeout protection
#         """
#         if self.model is None:
#             print("Model not loaded. Cannot perform detection.")
#             return []
        
#         start_time = time.time()
        
#         try:
#             print(f"Starting object detection for: {os.path.basename(image_path)}")
            
#             # Preprocess image for faster inference
#             processed_image, original_shape = self.preprocess_image_for_detection(image_path)
#             if processed_image is None:
#                 return []
            
#             # Run inference with timeout check
#             print("Running YOLO inference...")
#             inference_start = time.time()
            
#             # Use faster inference settings
#             results = self.model(
#                 processed_image, 
#                 conf=self.confidence_threshold,
#                 iou=0.5,  # Higher IoU threshold to reduce overlapping detections
#                 max_det=5,  # Limit maximum detections
#                 verbose=False
#             )
            
#             inference_time = time.time() - inference_start
#             print(f"YOLO inference completed in {inference_time:.2f} seconds")
            
#             # Check timeout
#             if time.time() - start_time > timeout:
#                 print(f"Detection timeout exceeded ({timeout}s), returning original image")
#                 return []
            
#             # Load original image for cropping
#             original_image = cv2.imread(image_path)
#             if original_image is None:
#                 return []
            
#             os.makedirs(output_folder, exist_ok=True)
            
#             cropped_paths = []
#             base_filename = os.path.splitext(os.path.basename(image_path))[0]
            
#             # Process detections
#             detection_count = 0
#             for result in results:
#                 boxes = result.boxes
#                 if boxes is not None and len(boxes) > 0:
#                     print(f"Found {len(boxes)} detections")
                    
#                     for i, box in enumerate(boxes):
#                         if time.time() - start_time > timeout:
#                             print("Timeout during cropping, stopping")
#                             break
                            
#                         # Get bounding box coordinates
#                         x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
#                         confidence = box.conf[0].cpu().numpy()
                        
#                         print(f"Detection {i+1}: confidence={confidence:.2f}")
                        
#                         # Scale coordinates back to original image if resized
#                         if processed_image.shape[:2] != original_shape:
#                             scale_y = original_shape[0] / processed_image.shape[0]
#                             scale_x = original_shape[1] / processed_image.shape[1]
#                             x1, x2 = int(x1 * scale_x), int(x2 * scale_x)
#                             y1, y2 = int(y1 * scale_y), int(y2 * scale_y)
                        
#                         # Add padding and ensure within bounds
#                         h, w = original_image.shape[:2]
#                         x1 = max(0, x1 - padding)
#                         y1 = max(0, y1 - padding)
#                         x2 = min(w, x2 + padding)
#                         y2 = min(h, y2 + padding)
                        
#                         # Crop certificate
#                         cropped_cert = original_image[y1:y2, x1:x2]
                        
#                         # Save cropped certificate
#                         output_filename = f"{base_filename}_detected_{detection_count+1}.png"
#                         output_path = os.path.join(output_folder, output_filename)
                        
#                         cv2.imwrite(output_path, cropped_cert)
#                         cropped_paths.append(output_filename)
#                         detection_count += 1
                        
#                         print(f"Cropped certificate saved: {output_filename}")
            
#             total_time = time.time() - start_time
#             print(f"Object detection completed in {total_time:.2f} seconds, found {len(cropped_paths)} certificates")
            
#             return cropped_paths
        
#         except Exception as e:
#             print(f"Error during detection and cropping: {e}")
#             return []




# certificate_detection/detector.py
import cv2
import numpy as np
from PIL import Image
import os
from ultralytics import YOLO
import time

class CertificateDetector:
    def __init__(self, model_path="./certificate_detection/yolov8/best.pt", confidence_threshold=0.25):
        """
        Initialize the certificate detector with your trained model
        """
        self.confidence_threshold = confidence_threshold
        self.model_path = model_path
        self.model = None
        
        # Load the model once at startup
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            print(f"Model not found at {self.model_path}")
    
    def load_model(self):
        """Load your trained YOLO model with maximum speed optimizations"""
        try:
            self.model = YOLO(self.model_path)
            
            # Maximum speed optimizations
            self.model.overrides.update({
                'device': 'cpu',
                'half': False,
                'verbose': False,
                'agnostic_nms': True,
                'save': False,
                'save_txt': False,
                'save_conf': False,
                'save_crop': False,
                'show': False,
                'visualize': False
            })
            
            # Warmup the model with a dummy image for faster first inference
            dummy_img = np.zeros((320, 320, 3), dtype=np.uint8)
            self.model(dummy_img, verbose=False)
            
            print(f"Certificate detection model loaded and warmed up from {self.model_path}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def preprocess_image_for_detection(self, image_path, max_size=(320, 320)):
        """Ultra-fast preprocessing with minimal resizing"""
        try:
            # Use OpenCV for fastest loading
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if image is None:
                return None, None
                
            original_shape = image.shape[:2]
            
            # Aggressive resizing for maximum speed
            h, w = original_shape
            if h > max_size[0] or w > max_size[1]:
                # Quick resize with nearest neighbor (fastest)
                scale = min(max_size[0]/h, max_size[1]/w)
                new_h, new_w = int(h * scale), int(w * scale)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
            
            return image, original_shape
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None, None
    
    def detect_and_crop_certificates(self, image_path, output_folder="./processed_certificates", padding=10, timeout=10):
        """
        Ultra-fast detection and cropping with aggressive optimizations
        """
        if self.model is None:
            print("Model not loaded. Cannot perform detection.")
            return []
        
        start_time = time.time()
        
        try:
            print(f"Starting ultra-fast detection for: {os.path.basename(image_path)}")
            
            # Lightning-fast preprocessing
            processed_image, original_shape = self.preprocess_image_for_detection(image_path)
            if processed_image is None:
                return []
            
            # Ultra-fast inference with minimal settings
            inference_start = time.time()
            
            results = self.model(
                processed_image, 
                conf=self.confidence_threshold,
                iou=0.7,
                max_det=2,  # Limit to 2 detections max for speed
                imgsz=320,  # Smallest viable size
                verbose=False,
                stream=False,
                augment=False,  # Disable test-time augmentation
                classes=None,
                retina_masks=False
            )
            
            inference_time = time.time() - inference_start
            print(f"Ultra-fast inference completed in {inference_time:.3f} seconds")
            
            # Quick timeout check
            if time.time() - start_time > timeout:
                print(f"Detection timeout exceeded ({timeout}s)")
                return []
            
            # Load original image only if detections found
            detection_found = False
            for result in results:
                if result.boxes is not None and len(result.boxes) > 0:
                    detection_found = True
                    break
            
            if not detection_found:
                print("No detections found, skipping cropping")
                return []
            
            # Load original image for cropping
            original_image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if original_image is None:
                return []
            
            os.makedirs(output_folder, exist_ok=True)
            
            cropped_paths = []
            base_filename = os.path.splitext(os.path.basename(image_path))[0]
            
            detection_count = 0
            for result in results:
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    print(f"Found {len(boxes)} detections")
                    
                    for i, box in enumerate(boxes):
                        if time.time() - start_time > timeout:
                            break
                            
                        # Lightning-fast coordinate extraction
                        coords = box.xyxy[0].cpu().numpy().astype(int)
                        x1, y1, x2, y2 = coords
                        confidence = float(box.conf[0].cpu().numpy())
                        
                        print(f"Detection {i+1}: confidence={confidence:.2f}")
                        
                        # Quick coordinate scaling
                        if processed_image.shape[:2] != original_shape:
                            scale_y = original_shape[0] / processed_image.shape[0]
                            scale_x = original_shape[1] / processed_image.shape[1]
                            x1, x2 = int(x1 * scale_x), int(x2 * scale_x)
                            y1, y2 = int(y1 * scale_y), int(y2 * scale_y)
                        
                        # Fast boundary checking and padding
                        h, w = original_image.shape[:2]
                        x1 = max(0, x1 - padding)
                        y1 = max(0, y1 - padding)
                        x2 = min(w, x2 + padding)
                        y2 = min(h, y2 + padding)
                        
                        # Ultra-fast cropping
                        cropped_cert = original_image[y1:y2, x1:x2]
                        
                        # Fast saving with minimal compression
                        output_filename = f"{base_filename}_detected_{detection_count+1}.png"
                        output_path = os.path.join(output_folder, output_filename)
                        
                        # Fastest PNG write
                        cv2.imwrite(output_path, cropped_cert, [cv2.IMWRITE_PNG_COMPRESSION, 0])
                        cropped_paths.append(output_filename)
                        detection_count += 1
                        
                        print(f"Cropped certificate saved: {output_filename}")
            
            total_time = time.time() - start_time
            print(f"Ultra-fast detection completed in {total_time:.3f} seconds, found {len(cropped_paths)} certificates")
            
            return cropped_paths
        
        except Exception as e:
            print(f"Error during ultra-fast detection: {e}")
            return []