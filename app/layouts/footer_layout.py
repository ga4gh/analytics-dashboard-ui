# app/layouts/footer_layout.py
# Footer styled to match refcloud-ui's components/layout/Footer.tsx, using
# new_ga4gh's real icon technique (components/_buttons.scss's btn-icon mixin:
# a FontAwesomeBrands glyph on the button's .btn-text::before) rather than
# inline SVG, which dcc.Markdown's sanitizer silently strips.

from datetime import datetime
from dash import html


def _social_button(href, icon_class, label):
    return html.A(
        html.Span(label, className=f"btn-text {icon_class}"),
        className="ga4gh-btn-light",
        href=href,
        target="_blank",
        rel="noopener noreferrer",
    )


def get_footer():
    return html.Footer(
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src="/assets/logo-mark-white.svg",
                            alt="The Global Alliance for Genomics and Health",
                            className="f-logo-img",
                        ),
                        html.P(
                            [
                                "GA4GH Analytics Dashboard",
                                html.Br(),
                                "Global Alliance for Genomics and Health",
                            ],
                            className="f-logo-text",
                        ),
                        html.P(f"Copyright © {datetime.now().year}"),
                    ],
                    className="f-logo",
                ),
                html.Nav(
                    [
                        _social_button("https://www.youtube.com/c/GA4GH", "btn-icon-youtube", "YouTube"),
                        _social_button("https://linkedin.com/company/ga4gh", "btn-icon-linkedin", "LinkedIn"),
                        _social_button("https://www.facebook.com/GA4GH/", "btn-icon-facebook", "Facebook"),
                    ],
                    className="f-social",
                ),
            ],
            className="ga4gh-footer-container",
        ),
        className="footer",
    )
