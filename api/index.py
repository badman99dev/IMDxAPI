"""Vercel serverless entry point for the IMDxAPI FastAPI app."""

import os
import sys

# Ensure the project root is importable on Vercel's serverless runtime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangum import Mangum
from app.main import app

handler = Mangum(app)