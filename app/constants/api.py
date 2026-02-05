"""
All external API endpoints live here
"""

#BASE API endpoint
BASE_API = "http://analytics-staging.ga4gh.org:8000"

# PyPI API endpoint
ALL_PACKAGES_API = BASE_API + "/pypi/all-packages"
TOTAL_PACKAGES_API = BASE_API + "/pypi/total-packages"
PACKAGE_VERSIONS_API = BASE_API + "/pypi/package-versions"
RELEASES_OVER_YEARS_API = BASE_API + "/pypi/releases-over-years"
PYPI_DETAILS_API = BASE_API + "/pypi/project-details"
FIRST_RELEASES_API = BASE_API + "/pypi/first-releases"