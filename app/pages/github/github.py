from app.layouts.github_layout import get_github_layout
from app.services.github_client import prepare_github_data


# ---- Prepare Data Once for Layout ----
(
    gh_df,
    gh_activity_df,
    gh_activity_counts,
    gh_interest_df,
    total_repositories,
    workstreams
) = prepare_github_data()

layout = get_github_layout(gh_df, total_repositories, workstreams)