import pandas as pd
import logging
from typing import List, Dict
import os
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        self.upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        os.makedirs(self.upload_folder, exist_ok=True)

    def save_file(self, file) -> str:
        """Save uploaded file and return its path."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"upload_{timestamp}.csv"
        file_path = os.path.join(self.upload_folder, filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        
        return file_path

    def process_csv(self, file_path: str) -> List[Dict]:
        """Process CSV file and extract media sources."""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Try to find URL column
            url_columns = ['url', 'link', 'website', 'source', 'URL', 'Link', 'Website', 'Source']
            url_column = None
            for col in url_columns:
                if col in df.columns:
                    url_column = col
                    break
            
            if not url_column:
                raise ValueError("No URL column found in CSV file")
            
            # Process each row
            results = []
            for _, row in df.iterrows():
                try:
                    url = str(row[url_column]).strip()
                    if not url or url.lower() == 'nan':
                        continue
                        
                    # Extract domain
                    parsed = urlparse(url)
                    if not parsed.netloc:
                        continue
                        
                    # Create result dictionary
                    result = {
                        'domain': parsed.netloc,
                        'url': url,
                        'name': row.get('name', '') or row.get('title', '') or parsed.netloc,
                        'description': row.get('description', '') or row.get('desc', '') or '',
                        'category': row.get('category', '') or row.get('type', '') or '',
                        'imported_at': datetime.utcnow().isoformat()
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing row: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            raise
        finally:
            # Clean up the uploaded file
            try:
                os.remove(file_path)
            except:
                pass

file_service = FileService() 