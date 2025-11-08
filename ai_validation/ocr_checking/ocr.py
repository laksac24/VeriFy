# # import pytesseract
# # import os
# # from PIL import Image
# # import cv2
# # import numpy as np

# # def ocr_checker(final_state):
# #     ocr_results = {}
# #     processed_folder = "./processed_certificates"

# #     for file in final_state["accepted_certi"]:
# #         if file.endswith(".png"):
# #             img_path = os.path.join(processed_folder, file)
# #             try:
# #                 # Basic pytesseract OCR
# #                 text = pytesseract.image_to_string(img_path, lang='eng')
# #                 ocr_results[file] = text.strip()
# #             except Exception as e:
# #                 print(f"OCR failed for {file}: {e}")
# #                 # Fallback with image preprocessing
# #                 try:
# #                     img = cv2.imread(img_path)
# #                     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# #                     _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
# #                     text = pytesseract.image_to_string(thresh, config='--psm 6')
# #                     ocr_results[file] = text.strip()
# #                 except:
# #                     ocr_results[file] = "OCR_EXTRACTION_FAILED"

# #     final_state["ocr_texts"] = ocr_results
# #     return final_state



# # import pytesseract
# # import os
# # from PIL import Image
# # import cv2
# # import numpy as np
# # import subprocess
# # import shutil
# # import glob

# # def comprehensive_tesseract_search():
# #     """Comprehensive search for Tesseract with detailed logging"""
# #     print("\n" + "="*60)
# #     print("COMPREHENSIVE TESSERACT SEARCH")
# #     print("="*60)
    
# #     found_paths = []
    
# #     # 1. Check shutil.which (most reliable)
# #     print("1. Checking shutil.which('tesseract')...")
# #     try:
# #         which_path = shutil.which('tesseract')
# #         if which_path:
# #             print(f"   ✓ Found via shutil.which: {which_path}")
# #             if os.path.exists(which_path):
# #                 found_paths.append(which_path)
# #             else:
# #                 print(f"   ✗ Path exists in which but file missing: {which_path}")
# #         else:
# #             print("   ✗ shutil.which returned None")
# #     except Exception as e:
# #         print(f"   ✗ shutil.which failed: {e}")
    
# #     # 2. Check common paths
# #     print("\n2. Checking common paths...")
# #     common_paths = [
# #         '/usr/bin/tesseract',
# #         '/usr/local/bin/tesseract', 
# #         '/bin/tesseract',
# #         '/opt/bin/tesseract',
# #         '/usr/share/tesseract-ocr/tesseract',
# #         'tesseract'
# #     ]
    
# #     for path in common_paths:
# #         if os.path.exists(path) or path == 'tesseract':
# #             try:
# #                 result = subprocess.run([path, '--version'], 
# #                                       capture_output=True, text=True, timeout=5)
# #                 if result.returncode == 0:
# #                     print(f"   ✓ Working: {path}")
# #                     if path not in found_paths:
# #                         found_paths.append(path)
# #                 else:
# #                     print(f"   ✗ Exists but not working: {path} (exit code: {result.returncode})")
# #             except FileNotFoundError:
# #                 print(f"   ✗ Not found: {path}")
# #             except Exception as e:
# #                 print(f"   ✗ Error testing {path}: {e}")
# #         else:
# #             print(f"   ✗ Does not exist: {path}")
    
# #     # 3. Search entire filesystem (limited scope)
# #     print("\n3. Searching filesystem for tesseract...")
# #     search_dirs = ['/usr', '/bin', '/opt', '/usr/local']
    
# #     for search_dir in search_dirs:
# #         if os.path.exists(search_dir):
# #             try:
# #                 print(f"   Searching in {search_dir}...")
# #                 result = subprocess.run(
# #                     ['find', search_dir, '-name', 'tesseract*', '-type', 'f', '-executable'],
# #                     capture_output=True, text=True, timeout=10
# #                 )
# #                 if result.stdout:
# #                     for found_file in result.stdout.strip().split('\n'):
# #                         if found_file and 'tesseract' in found_file.lower():
# #                             print(f"     Found: {found_file}")
# #                             # Test if it's the actual tesseract binary
# #                             try:
# #                                 test_result = subprocess.run([found_file, '--version'], 
# #                                                            capture_output=True, text=True, timeout=5)
# #                                 if test_result.returncode == 0 and 'tesseract' in test_result.stdout.lower():
# #                                     print(f"     ✓ Working tesseract binary: {found_file}")
# #                                     if found_file not in found_paths:
# #                                         found_paths.append(found_file)
# #                             except:
# #                                 print(f"     ✗ Not working: {found_file}")
# #             except subprocess.TimeoutExpired:
# #                 print(f"   ⚠ Search in {search_dir} timed out")
# #             except Exception as e:
# #                 print(f"   ✗ Search in {search_dir} failed: {e}")
    
# #     # 4. Check if tesseract packages are installed
# #     print("\n4. Checking installed packages...")
# #     package_commands = [
# #         ['dpkg', '-l', 'tesseract*'],
# #         ['apt', 'list', '--installed', 'tesseract*'],
# #         ['rpm', '-qa', 'tesseract*']
# #     ]
    
# #     for cmd in package_commands:
# #         try:
# #             result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
# #             if result.stdout and 'tesseract' in result.stdout.lower():
# #                 print(f"   Package info from {cmd[0]}:")
# #                 for line in result.stdout.split('\n')[:5]:  # Show first 5 lines
# #                     if line.strip():
# #                         print(f"     {line}")
# #                 break
# #         except:
# #             continue
    
# #     # 5. Check environment variables
# #     print("\n5. Environment variables:")
# #     print(f"   PATH: {os.environ.get('PATH', 'Not set')}")
# #     print(f"   TESSDATA_PREFIX: {os.environ.get('TESSDATA_PREFIX', 'Not set')}")
    
# #     # 6. Check directory listings
# #     print("\n6. Directory listings:")
# #     check_dirs = ['/usr/bin', '/bin', '/usr/local/bin']
# #     for check_dir in check_dirs:
# #         if os.path.exists(check_dir):
# #             try:
# #                 files = [f for f in os.listdir(check_dir) if 'tesseract' in f.lower()]
# #                 if files:
# #                     print(f"   {check_dir}: {files}")
# #             except:
# #                 pass
    
# #     # 7. Summary and recommendations
# #     print(f"\n" + "="*60)
# #     print("SUMMARY")
# #     print("="*60)
# #     print(f"Found {len(found_paths)} working Tesseract installations:")
# #     for i, path in enumerate(found_paths, 1):
# #         print(f"{i}. {path}")
    
# #     if found_paths:
# #         return found_paths[0]  # Return the first working path
# #     else:
# #         print("\n❌ NO WORKING TESSERACT INSTALLATION FOUND!")
# #         print("\n🔧 TROUBLESHOOTING STEPS:")
# #         print("1. Make sure your build script actually ran:")
# #         print("   - Check Render build logs")
# #         print("   - Ensure build.sh has correct permissions")
# #         print("2. Try manual installation commands:")
# #         print("   apt-get update && apt-get install -y tesseract-ocr")
# #         print("3. Check if using correct Linux distribution")
# #         print("4. Consider switching to Docker deployment")
# #         return None

# # def ocr_checker(final_state):
# #     # Comprehensive Tesseract search
# #     tesseract_path = comprehensive_tesseract_search()
    
# #     if tesseract_path:
# #         pytesseract.pytesseract.tesseract_cmd = tesseract_path
# #         print(f"\n✅ Tesseract configured successfully: {tesseract_path}")
# #     else:
# #         print("\n❌ Tesseract not available - OCR will fail")
    
# #     ocr_results = {}
# #     processed_folder = "./processed_certificates"

# #     for file in final_state["accepted_certi"]:
# #         if file.endswith(".png"):
# #             img_path = os.path.join(processed_folder, file)
            
# #             if not tesseract_path:
# #                 print(f"OCR failed for {file}: Tesseract not available")
# #                 ocr_results[file] = "TESSERACT_NOT_FOUND"
# #                 continue
                
# #             try:
# #                 # Basic pytesseract OCR
# #                 text = pytesseract.image_to_string(img_path, lang='eng')
# #                 ocr_results[file] = text.strip()
# #                 print(f"✓ OCR successful for {file}: {len(text.strip())} characters extracted")
# #             except Exception as e:
# #                 print(f"OCR failed for {file}: {e}")
# #                 # Fallback with image preprocessing
# #                 try:
# #                     img = cv2.imread(img_path)
# #                     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# #                     _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
# #                     text = pytesseract.image_to_string(thresh, config='--psm 6')
# #                     ocr_results[file] = text.strip()
# #                     print(f"✓ OCR successful with preprocessing for {file}")
# #                 except Exception as e2:
# #                     print(f"All OCR methods failed for {file}: {e2}")
# #                     ocr_results[file] = "OCR_EXTRACTION_FAILED"

# #     final_state["ocr_texts"] = ocr_results
# #     return final_state



# import pytesseract
# import os
# from PIL import Image
# import cv2
# import numpy as np

# def ocr_checker(final_state):
#     # Set tesseract path for Docker (it will be in /usr/bin/tesseract)
#     pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    
#     ocr_results = {}
#     processed_folder = "./processed_certificates"

#     for file in final_state["accepted_certi"]:
#         if file.endswith(".png"):
#             img_path = os.path.join(processed_folder, file)
#             try:
#                 # Basic pytesseract OCR
#                 text = pytesseract.image_to_string(img_path, lang='eng')
#                 ocr_results[file] = text.strip()
#                 print(f"✓ OCR success for {file}: {len(text.strip())} chars")
#             except Exception as e:
#                 print(f"OCR failed for {file}: {e}")
#                 # Fallback with image preprocessing
#                 try:
#                     img = cv2.imread(img_path)
#                     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#                     _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#                     text = pytesseract.image_to_string(thresh, config='--psm 6')
#                     ocr_results[file] = text.strip()
#                     print(f"✓ OCR success with preprocessing for {file}")
#                 except:
#                     ocr_results[file] = "OCR_EXTRACTION_FAILED"
#                     print(f"❌ All OCR methods failed for {file}")

#     final_state["ocr_texts"] = ocr_results
#     return final_state



import easyocr
import os
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context


def ocr_checker(final_state):
    reader = easyocr.Reader(['en'])  # add more languages if needed
    ocr_results = {}
    processed_folder = "./processed_certificates"

    for file in final_state["accepted_certi"]:
        if file.endswith(".png"):
            img_path = os.path.join(processed_folder, file)
            result = reader.readtext(img_path, detail=0)  # get only text
            ocr_results[file] = " ".join(result)

    final_state["ocr_texts"] = ocr_results
    return final_state