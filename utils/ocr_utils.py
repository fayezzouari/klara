import os
import tempfile
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import easyocr
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentOCR:
    """Class to extract text from images in PDF documents using EasyOCR."""
    
    def __init__(self, languages=['en']):
        """
        Initialize the OCR engine.
        
        Args:
            languages: List of languages to use for OCR (default: ['en'])
        """
        self.languages = languages
        self._reader = None
        
    @property
    def reader(self):
        """Lazy initialization of the EasyOCR reader."""
        if self._reader is None:
            logger.info(f"Initializing EasyOCR with languages: {self.languages}")
            self._reader = easyocr.Reader(self.languages)
        return self._reader
    
    def extract_images_from_pdf(self, pdf_path):
        """
        Extract images from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of tuples containing (image_array, page_num, image_num)
        """
        images = []
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num, page in enumerate(pdf_document):
                image_list = page.get_images(full=True)
                
                # Check if page has no text content (might be a scanned page)
                text = page.get_text()
                has_text_content = len(text.strip()) > 50  # Arbitrary threshold
                
                # Process either all images or just the page as image if no text
                if not has_text_content:
                    # Convert the entire page to an image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img_array = np.array(img)
                    images.append((img_array, page_num, 0, True))  # True = full page
                
                # Process individual images in the page
                for img_idx, img_info in enumerate(image_list):
                    xref = img_info[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Only process images that are sufficiently large
                    try:
                        img = Image.open(tempfile.BytesIO(image_bytes))
                        # Skip very small images (likely icons, etc.)
                        if img.width < 100 or img.height < 100:
                            continue
                        img_array = np.array(img.convert("RGB"))
                        images.append((img_array, page_num, img_idx, False))  # False = embedded image
                    except Exception as e:
                        logger.warning(f"Error processing image: {e}")
            
            pdf_document.close()
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {e}")
            return []
    
    def perform_ocr(self, image_array):
        """
        Perform OCR on an image.
        
        Args:
            image_array: Numpy array containing the image
            
        Returns:
            String of extracted text
        """
        try:
            results = self.reader.readtext(image_array)
            text = " ".join([result[1] for result in results])
            return text
        except Exception as e:
            logger.error(f"Error performing OCR: {e}")
            return ""
    
    def process_pdf(self, pdf_path):
        """
        Extract text from images in a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary mapping (page_num, image_num) to extracted text
        """
        extracted_text = {}
        images = self.extract_images_from_pdf(pdf_path)
        
        logger.info(f"Found {len(images)} images in {pdf_path}")
        
        for img_array, page_num, img_idx, is_full_page in images:
            key = (page_num, img_idx)
            text = self.perform_ocr(img_array)
            
            # Only keep results that have meaningful text
            if len(text.strip()) > 10:  # At least some meaningful content
                extracted_text[key] = {
                    'text': text,
                    'page_num': page_num,
                    'is_full_page': is_full_page
                }
                logger.info(f"Extracted {len(text.split())} words from page {page_num+1}, image {img_idx}")
        
        return extracted_text