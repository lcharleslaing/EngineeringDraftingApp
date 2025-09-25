"""
File conversion service for converting Office and CAD files to PDF
"""
import os
import tempfile
import subprocess
import win32com.client as win32
from django.conf import settings
from django.core.files import File
import logging

logger = logging.getLogger(__name__)


class FileConversionError(Exception):
    """Custom exception for file conversion errors"""
    pass


def convert_office_to_pdf(input_path, output_path):
    """
    Convert Office files (Word, Excel) to PDF using LibreOffice
    """
    try:
        # Use LibreOffice headless mode
        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', os.path.dirname(output_path),
            input_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            raise FileConversionError(f"LibreOffice conversion failed: {result.stderr}")
        
        # LibreOffice creates PDF with same name as input
        expected_pdf = os.path.splitext(input_path)[0] + '.pdf'
        if os.path.exists(expected_pdf):
            os.rename(expected_pdf, output_path)
            return True
        else:
            raise FileConversionError("PDF output not found after conversion")
            
    except subprocess.TimeoutExpired:
        raise FileConversionError("LibreOffice conversion timed out")
    except Exception as e:
        raise FileConversionError(f"Office conversion failed: {str(e)}")


def convert_idw_to_pdf(input_path, output_path):
    """
    Convert Inventor IDW files to PDF using Inventor COM
    Handles multi-sheet drawings
    """
    try:
        # Create Inventor application
        inv = win32.Dispatch("Inventor.Application")
        inv.Visible = False
        
        # Open the IDW file
        doc = inv.Documents.Open(input_path)
        
        # Get PDF AddIn
        pdf_addin = inv.ApplicationAddIns.ItemById("{0AC6FD96-2F4D-42CE-8BE0-8AEA580399E4}")
        if not pdf_addin:
            raise FileConversionError("PDF AddIn not found in Inventor")
        
        # Create export context
        ctx = inv.TransientObjects.CreateNameValueMap()
        
        # Export options for multi-sheet
        ctx.Value("All_Color_AS_Black", False)
        ctx.Value("Remove_Line_Weights", False)
        ctx.Value("Vector_Resolution", 400)
        ctx.Value("Sheet_Range", 2)  # 2 = All sheets
        ctx.Value("AllSheets", True)
        ctx.Value("Fit_to_Page", True)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export to PDF
        pdf_addin.SaveCopyAs(doc, ctx, output_path)
        
        # Close document
        doc.Close(True)
        
        return True
        
    except Exception as e:
        logger.error(f"IDW conversion failed: {str(e)}")
        raise FileConversionError(f"IDW conversion failed: {str(e)}")


def convert_dwg_to_pdf(input_path, output_path):
    """
    Convert DWG files to PDF using AutoCAD Core Console
    Handles multiple layouts
    """
    try:
        # Create temporary script file
        script_content = f'''
-PLOT
Model
DWG To PDF.pc3
ANSI_A
Inches
Landscape
No
Plot
{output_path}
Y
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scr', delete=False) as script_file:
            script_file.write(script_content)
            script_path = script_file.name
        
        try:
            # AutoCAD Core Console paths (try common versions)
            autocad_paths = [
                r"C:\Program Files\Autodesk\AutoCAD 2025\accoreconsole.exe",
                r"C:\Program Files\Autodesk\AutoCAD 2024\accoreconsole.exe",
                r"C:\Program Files\Autodesk\AutoCAD 2023\accoreconsole.exe",
            ]
            
            autocad_exe = None
            for path in autocad_paths:
                if os.path.exists(path):
                    autocad_exe = path
                    break
            
            if not autocad_exe:
                raise FileConversionError("AutoCAD Core Console not found")
            
            # Run AutoCAD Core Console
            cmd = [autocad_exe, '/i', input_path, '/s', script_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise FileConversionError(f"AutoCAD conversion failed: {result.stderr}")
            
            return True
            
        finally:
            # Clean up script file
            if os.path.exists(script_path):
                os.unlink(script_path)
                
    except subprocess.TimeoutExpired:
        raise FileConversionError("AutoCAD conversion timed out")
    except Exception as e:
        logger.error(f"DWG conversion failed: {str(e)}")
        raise FileConversionError(f"DWG conversion failed: {str(e)}")


def convert_file_to_pdf(file_path, file_extension):
    """
    Convert various file types to PDF
    Returns the path to the converted PDF file
    """
    file_extension = file_extension.lower()
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        output_path = temp_file.name
    
    try:
        if file_extension in ['docx', 'doc', 'xlsx', 'xls']:
            convert_office_to_pdf(file_path, output_path)
        elif file_extension == 'idw':
            convert_idw_to_pdf(file_path, output_path)
        elif file_extension == 'dwg':
            convert_dwg_to_pdf(file_path, output_path)
        else:
            raise FileConversionError(f"Unsupported file type: {file_extension}")
        
        return output_path
        
    except Exception as e:
        # Clean up on failure
        if os.path.exists(output_path):
            os.unlink(output_path)
        raise e


def get_file_icon(file_extension):
    """
    Get appropriate icon for file type
    """
    icons = {
        'docx': '📄',
        'doc': '📄',
        'xlsx': '📊',
        'xls': '📊',
        'dwg': '📐',
        'idw': '📐',
        'pdf': '📕',
    }
    return icons.get(file_extension.lower(), '📎')


def format_file_size(size_bytes):
    """
    Format file size in human readable format
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
