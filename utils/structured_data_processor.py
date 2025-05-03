import os
import pandas as pd
from typing import List, Dict, Any, Optional, Union
import json
from io import StringIO

class StructuredDataProcessor:
    """
    Utility class for processing structured data files (CSV and Excel)
    and splitting them into suitable chunks for vector database storage.
    """
    
    def __init__(self, max_rows_per_chunk: int = 50):
        """
        Initialize the structured data processor.
        
        Args:
            max_rows_per_chunk: Maximum number of rows per data chunk
        """
        self.max_rows_per_chunk = max_rows_per_chunk
    
    def process_file(self, file_path: str, original_filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process a CSV or Excel file and return chunks suitable for vector database storage.
        
        Args:
            file_path: Path to the CSV or Excel file
            original_filename: Original filename if different from file_path
            
        Returns:
            List of dictionaries containing text chunks and metadata
        """
        # Determine file type and load into DataFrame
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file extension: {file_ext}")
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
        
        # Use provided original filename or extract from path
        if not original_filename:
            original_filename = os.path.basename(file_path)
        
        # Create document title from filename without extension
        doc_title = os.path.splitext(original_filename)[0]
        
        # Process the DataFrame into chunks
        return self._process_dataframe(df, original_filename, doc_title)
    
    def _process_dataframe(self, df: pd.DataFrame, doc_name: str, doc_title: str) -> List[Dict[str, Any]]:
        """
        Process a DataFrame into chunks suitable for vector database storage.
        
        Args:
            df: Pandas DataFrame containing the structured data
            doc_name: Document name for metadata
            doc_title: Document title for metadata
            
        Returns:
            List of dictionaries containing text chunks and metadata
        """
        chunks = []
        total_rows = len(df)
        
        if total_rows == 0:
            return []
        
        # Generate data summary
        summary = self._generate_summary(df)
        chunks.append({
            "text": summary,
            "metadata": {
                "document_name": doc_name,
                "document_title": doc_title,
                "chunk_type": "summary",
                "chunk_idx": 0,
                "total_rows": total_rows
            }
        })
        
        # Split data into chunks
        start_row = 0
        while start_row < total_rows:
            end_row = min(start_row + self.max_rows_per_chunk, total_rows)
            chunk_df = df.iloc[start_row:end_row]
            
            # Convert chunk to text representation
            chunk_text = self._dataframe_to_text(chunk_df, start_row)
            
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "document_name": doc_name,
                    "document_title": doc_title,
                    "chunk_type": "data_chunk",
                    "chunk_idx": len(chunks),
                    "row_start": start_row,
                    "row_end": end_row - 1,
                    "total_rows": total_rows
                }
            })
            
            start_row = end_row
        
        return chunks
    
    def _generate_summary(self, df: pd.DataFrame) -> str:
        """
        Generate a summary of the DataFrame content.
        
        Args:
            df: Pandas DataFrame to summarize
            
        Returns:
            Text summary of the DataFrame
        """
        # Get basic DataFrame info
        total_rows = len(df)
        total_columns = len(df.columns)
        column_names = list(df.columns)
        
        # Get data types
        dtypes = df.dtypes.astype(str).to_dict()
        
        # Get basic statistics if numerical columns exist
        numerical_stats = {}
        numerical_cols = df.select_dtypes(include=['number']).columns
        if len(numerical_cols) > 0:
            stats_df = df[numerical_cols].describe()
            for col in numerical_cols:
                if col in stats_df:
                    numerical_stats[col] = {
                        "min": stats_df.loc['min', col],
                        "max": stats_df.loc['max', col],
                        "mean": stats_df.loc['mean', col],
                        "std": stats_df.loc['std', col]
                    }
        
        # Get value counts for categorical columns (limited to top values)
        categorical_stats = {}
        categorical_cols = df.select_dtypes(exclude=['number']).columns
        for col in categorical_cols:
            if len(df[col].dropna().unique()) < 10:  # Only for columns with fewer than 10 unique values
                value_counts = df[col].value_counts().head(5).to_dict()
                categorical_stats[col] = value_counts
        
        # Check for missing values
        missing_values = df.isnull().sum().to_dict()
        missing_values = {k: v for k, v in missing_values.items() if v > 0}
        
        # Build summary text
        summary = []
        summary.append(f"DATASET SUMMARY")
        summary.append(f"Total rows: {total_rows}")
        summary.append(f"Total columns: {total_columns}")
        summary.append(f"Columns: {', '.join(column_names)}")
        
        # Add data types
        summary.append("\nCOLUMN DATA TYPES:")
        for col, dtype in dtypes.items():
            summary.append(f"{col}: {dtype}")
        
        # Add missing values info if any
        if missing_values:
            summary.append("\nMISSING VALUES:")
            for col, count in missing_values.items():
                percent = (count / total_rows) * 100
                summary.append(f"{col}: {count} ({percent:.1f}%)")
        
        # Add numerical statistics
        if numerical_stats:
            summary.append("\nNUMERICAL COLUMNS STATISTICS:")
            for col, stats in numerical_stats.items():
                summary.append(f"{col} - Min: {stats['min']:.2f}, Max: {stats['max']:.2f}, Mean: {stats['mean']:.2f}, StdDev: {stats['std']:.2f}")
        
        # Add categorical information
        if categorical_stats:
            summary.append("\nCATEGORICAL COLUMNS VALUE COUNTS:")
            for col, counts in categorical_stats.items():
                top_values = ", ".join([f"{v} ({c})" for v, c in counts.items()])
                summary.append(f"{col} - Top values: {top_values}")
        
        # Add sample data
        summary.append("\nSAMPLE DATA (First 5 rows):")
        sample_io = StringIO()
        df.head(5).to_csv(sample_io, index=False)
        summary.append(sample_io.getvalue())
        
        return "\n".join(summary)
    
    def _dataframe_to_text(self, df: pd.DataFrame, start_row: int) -> str:
        """
        Convert a DataFrame chunk to text representation.
        
        Args:
            df: Pandas DataFrame chunk
            start_row: Starting row index of this chunk
            
        Returns:
            Text representation of the DataFrame chunk
        """
        # Create a buffer for CSV output
        output = StringIO()
        
        # Write context information
        output.write(f"DATA ROWS {start_row+1} to {start_row+len(df)}\n\n")
        
        # Write the data in CSV format
        df.to_csv(output, index=False)
        
        # Add a JSON representation for complex queries
        output.write("\nJSON FORMAT (for structured querying):\n")
        
        # Convert DataFrame to list of records (limited for large datasets)
        max_json_rows = 100  # Limit JSON size for very large chunks
        if len(df) > max_json_rows:
            records = df.head(max_json_rows).to_dict(orient='records')
            json_str = json.dumps(records, default=str, indent=2)
            output.write(json_str)
            output.write(f"\n... (showing {max_json_rows} of {len(df)} rows)")
        else:
            records = df.to_dict(orient='records')
            json_str = json.dumps(records, default=str, indent=2)
            output.write(json_str)
        
        return output.getvalue()