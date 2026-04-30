from app.layouts.pypi_layout import get_pypi_layout
from app.services.pypi_client import get_pypi_details, get_total_packages

layout = get_pypi_layout(get_pypi_details(), get_total_packages())
