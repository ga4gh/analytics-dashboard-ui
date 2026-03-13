import dash
from app.layouts.github_layout import get_github_layout
from app.services.github_client import prepare_github_data
from app.callbacks.github_callbacks import register_github_callbacks


# ---- Prepare Data Once for Layout ----
(
    gh_df,
    gh_activity_df,
    gh_activity_counts,
    gh_interest_df,
    total_repositories,
) = prepare_github_data()

layout = get_github_layout(gh_df, total_repositories)