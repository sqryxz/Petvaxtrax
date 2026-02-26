#!/usr/bin/env python3
"""
PetVaxHK - Flask Web Application Runner
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    print(f"🚀 Starting PetVaxHK on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
