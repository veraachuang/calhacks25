# calhacks25
something with spectacles

## Web App with Python Integration

A Flask-based web application with Python backend integration.

## Project Structure

```
calhacks25/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── main.js
│   │   └── images/
│   └── templates/
│       └── index.html
├── tests/
├── venv/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup Instructions

### 1. Activate Virtual Environment

```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

The app will be available at `http://127.0.0.1:5000`

### 4. Deactivate Virtual Environment

```bash
deactivate
```

## Development

- Add your Python modules in the `app/` directory
- Place HTML templates in `app/templates/`
- Add CSS files in `app/static/css/`
- Add JavaScript files in `app/static/js/`
- Add images in `app/static/images/`

## Requirements

- Python 3.7+
- Flask 3.0.0
