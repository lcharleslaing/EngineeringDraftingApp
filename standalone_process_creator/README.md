# Django Process Creator

A comprehensive Django application for creating, managing, and documenting business processes with AI-powered analysis, image management, drag-and-drop reordering, and comprehensive reporting capabilities.

## Features

### 🎯 Core Functionality
- **Process Management**: Create, edit, and organize business processes
- **Step-by-Step Documentation**: Detailed step documentation with rich text support
- **Module Organization**: Group processes by modules for better organization
- **AI-Powered Analysis**: Generate summaries and detailed process analysis using OpenAI
- **Drag-and-Drop Interface**: Reorder steps and images with intuitive drag-and-drop
- **Auto-Expanding Textareas**: Text areas automatically resize as you type

### 📊 Rich Media Support
- **Image Management**: Upload and organize screenshots with drag-and-drop reordering
- **PDF Support**: Upload and preview PDF documents
- **CAD File Support**: Support for DWG and IDW files (with optional conversion)
- **Link Management**: Add and organize external links
- **Full-Screen Image Viewer**: Zoom and pan functionality for detailed image viewing

### 📈 Reporting & Analytics
- **PDF Export**: Generate professional PDF reports
- **Word Export**: Export processes to Word documents
- **Process Statistics**: Comprehensive analytics and metrics
- **Custom Filenames**: Timestamped filenames for easy organization

### 🔧 Technical Features
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Built with Tailwind CSS and DaisyUI
- **Real-time Updates**: Auto-save functionality for seamless editing
- **File Conversion**: Optional support for CAD file conversion
- **Windows Integration**: Support for Windows file paths and directory links

## Installation

### Quick Start

1. **Download the package** to your Django project root directory
2. **Run the installation script**:
   ```bash
   python install.py
   ```
3. **Configure your environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your settings
   ```
4. **Start the server**:
   ```bash
   python manage.py runserver
   ```
5. **Visit the application**:
   ```
   http://localhost:8000/process-creator/
   ```

### Manual Installation

1. **Copy the app** to your Django project:
   ```bash
   cp -r process_creator/ /path/to/your/django/project/
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Add to settings.py**:
   ```python
   INSTALLED_APPS = [
       # ... your existing apps ...
       'process_creator',
   ]
   
   # Required settings
   X_FRAME_OPTIONS = 'SAMEORIGIN'
   MEDIA_URL = '/media/'
   MEDIA_ROOT = BASE_DIR / 'media'
   
   # OpenAI configuration
   OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
   ```

4. **Add to urls.py**:
   ```python
   from django.urls import include, path
   from django.conf import settings
   from django.conf.urls.static import static
   
   urlpatterns = [
       # ... your existing patterns ...
       path('process-creator/', include('process_creator.urls')),
   ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```

5. **Run migrations**:
   ```bash
   python manage.py makemigrations process_creator
   python manage.py migrate
   ```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
# Required
SECRET_KEY=your-secret-key-here
DEBUG=True
OPENAI_API_KEY=your-openai-api-key-here

# Optional - File conversion tools
ODA_CONVERTER_PDF=path/to/oda-converter.exe
INVENTOR_IDW_TO_PDF=path/to/inventor-converter.exe
```

### OpenAI API Setup

1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add it to your `.env` file
3. The app will automatically use it for AI features

### File Conversion (Optional)

For DWG and IDW file support, install the conversion tools:

- **ODA File Converter**: For DWG files
- **Inventor**: For IDW files

Set the paths in your `.env` file.

## Usage

### Creating a Process

1. Click "New Process" on the main page
2. Enter a process name and select a module (optional)
3. Add steps with detailed descriptions
4. Upload images, PDFs, or other documents
5. Add external links as needed

### AI Features

1. **Generate Summary**: Click the "Summary" button to generate an AI summary
2. **Process Analysis**: Click "Analysis" for detailed process improvement suggestions
3. **Custom Prompts**: Modify the AI instructions in the settings

### Organizing Content

1. **Drag and Drop**: Reorder steps and images by dragging
2. **Modules**: Group related processes using modules
3. **Links**: Add external references and file links
4. **Images**: Upload screenshots with automatic thumbnail generation

### Exporting

1. **PDF Export**: Generate professional PDF reports
2. **Word Export**: Export to Word documents
3. **Statistics**: View detailed process analytics

## API Reference

### Models

- **Module**: Process categories
- **Process**: Main process entity
- **Step**: Individual process steps
- **StepImage**: Process screenshots
- **StepLink**: External links
- **StepFile**: Uploaded files
- **AIInteraction**: AI usage tracking

### Views

- `process_list`: List all processes
- `process_edit`: Edit a process
- `process_create`: Create new process
- `process_pdf`: Export to PDF
- `process_word`: Export to Word
- `process_stats`: Get process statistics

## Customization

### Templates

All templates are located in `process_creator/templates/process_creator/`:

- `base.html`: Base template with all dependencies
- `list.html`: Process list view
- `edit.html`: Process editing interface
- `print.html`: Print/PDF template

### Styling

The app uses Tailwind CSS and DaisyUI. You can customize the appearance by:

1. Modifying the base template
2. Adding custom CSS
3. Overriding component classes

### AI Prompts

Customize AI behavior by modifying the default prompts in the models:

- `summary_instructions`: Controls summary generation
- `analysis_instructions`: Controls analysis generation

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Ensure `OPENAI_API_KEY` is set in your `.env` file
   - Restart your Django server after adding the key

2. **Images not uploading**
   - Check `MEDIA_URL` and `MEDIA_ROOT` settings
   - Ensure the media directory is writable

3. **PDF export not working**
   - Install `xhtml2pdf`: `pip install xhtml2pdf`
   - Check file permissions

4. **Drag and drop not working**
   - Ensure JavaScript is enabled
   - Check browser console for errors

### Debug Mode

Enable debug mode in your `.env` file:
```env
DEBUG=True
```

This will show detailed error messages and enable the Django debug toolbar.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

1. Check the troubleshooting section
2. Review the Django documentation
3. Open an issue on GitHub

## Changelog

### Version 1.0.0
- Initial release
- Core process management
- AI integration
- PDF/Word export
- Image management
- Drag-and-drop interface
- Statistics and analytics

---

**Made with ❤️ for better process documentation**
