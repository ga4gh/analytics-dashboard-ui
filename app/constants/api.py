"""
All external API endpoints live here
"""

#BASE API endpoint
BASE_API = "http://AnalyticsDashboardAlbBalancer-1386294349.us-east-2.elb.amazonaws.com:8000"
#BASE_API = "http://0.0.0.0:8000" # local test url

# PyPI API endpoint
ALL_PACKAGES_API = BASE_API + "/pypi/all-packages"
TOTAL_PACKAGES_API = BASE_API + "/pypi/total-packages"
PACKAGE_VERSIONS_API = BASE_API + "/pypi/package-versions"
RELEASES_OVER_YEARS_API = BASE_API + "/pypi/releases-over-years"
PYPI_DETAILS_API = BASE_API + "/pypi/project-details"
FIRST_RELEASES_API = BASE_API + "/pypi/first-releases"

# GitHub API endpoint
GITHUB_REPOS_API = BASE_API + "/github/all"
GITHUB_REPO_DETAILS_API = BASE_API + "/github/repo-details"
REPO_ENDPOINT = f"{BASE_API}/github/name/" # fetches repo based on repo name parameter provided by user after name/
REPO_OWNER_ENPOINT = f"{BASE_API}/github/owner/" # fetches repos based on repo owner parameter provided user after owner/

# PubMed Endpoints
PM_KEYWORD = f"{BASE_API}/pubmed/articles/GA4GH"

# EPMC API endpoint
BASE_API_LOCAL = "http://0.0.0.0:8000" # local test url
EPMC_ALL_LATEST_ENTRIES = BASE_API + "/epmc/all-latest-entries"
EPMC_AFFILIATION_COUNTRIES_COUNT = BASE_API + "/epmc/affiliation-countries-count"
EPMC_ALL_PMC_AUTHORS = BASE_API + "/epmc/all-pmc-authors"
EPMC_UNIQUE_CITATIONS = BASE_API + "/epmc/unique-citations"
EPMC_UNIQUE_AUTHOR_COUNT = BASE_API + "/epmc/unique-authors-count"
EPMC_TOP_AUTHORS = BASE_API + "/epmc/top-authors"
EPMC_ALL_ARTICLES = BASE_API + "/epmc/all-articles"
