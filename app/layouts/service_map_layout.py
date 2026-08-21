"""Map of registered GA4GH services"""

import numpy as np
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import dcc, html

from app.utils.ga4gh_theme import COLORS, chart_expand_button

LATITUDE=0
LONGITUDE=1

HOVERTEMPLATE = \
'<b>Name:</b> %{customdata[0]}<br>' + \
'<b>Implementation ID: </b>%{customdata[1]}<br>' + \
'<b>Implementation Type: </b>%{customdata[2]}<br>' + \
'<b>API Type: </b>%{customdata[3]}<br>' + \
'<b>API Version: </b>%{customdata[4]}<br>' + \
'<b>URL: </b>%{customdata[5]}<br>' + \
'<b>Organisation: </b>%{customdata[6]}<br>' + \
'<b>City: </b>%{customdata[7]}<br>' + \
'<b>Country: </b>%{customdata[8]}<br>' + \
'<b># of DRS Objects: </b>%{customdata[9]}<br>' + \
'<b>Storage Footprint (GB): </b>%{customdata[10]}<br>'

def apply_jitter(city, value, coordinate=LATITUDE):
    jitters = {
        LATITUDE: {
            "US-IL": (-1.0, 0.0),
            "US-VA": (-0.25, 0.25),
            "US-MA": (-0.25, 0.25),
        },
        LONGITUDE: {
            "US-IL": (-1.0, 0.0),
            "US-VA": (-0.25, 0.25),
            "US-MA": (-0.5, 0.0),
        }
    }

    jitter = jitters.get(coordinate, {}).get(city, None)
    if jitter:
        return value + np.random.uniform(jitter[0], jitter[1])
    return value

def _make_service_map_figure(st_df, s_df, d_df):

    api_types = {}

    for row in st_df.itertuples():
        for version in row.versions:
            api_types[version["id"]] = [row.abbreviation, version["version"]]

    sdf_trimmed = pd.DataFrame()
    # basic info
    sdf_trimmed["name"] = s_df["name"]
    sdf_trimmed["implementationId"] = s_df["implementationId"]
    sdf_trimmed["implementationType"] = s_df["implementationType"]
    sdf_trimmed["url"] = s_df["url"]
    sdf_trimmed["organisation"] = s_df["organisation"].str.get("name")
    # geolocation
    sdf_trimmed["lat"] = s_df["geolocation"].str.get("latitude")
    sdf_trimmed["lon"] = s_df["geolocation"].str.get("longitude")
    sdf_trimmed["city"] = s_df["geolocation"].str.get("city")
    sdf_trimmed["country"] = s_df["geolocation"].str.get("country")
    # api type
    sdf_trimmed["standardVersionId"] = s_df["standardVersion"].str.get("id")
    sdf_trimmed["apiType"] = sdf_trimmed.apply(lambda row: api_types.get(row["standardVersionId"], ["Unknown", "Unknown"])[0], axis=1)
    sdf_trimmed["apiVersion"] = sdf_trimmed.apply(lambda row: api_types.get(row["standardVersionId"], ["Unknown", "Unknown"])[1], axis=1)
    # DRS-specific metrics
    sdf_trimmed["drsObjects"] = s_df["implData"].str.get("drs").str.get("objectsCount")
    sdf_trimmed["storageFootprintGb"] = s_df["implData"].str.get("drs").str.get("storageFootprintGb")

    # Apply region-specific jitter to lat/lon to prevent marker overlap (if multiple implementations share the same location)
    sdf_trimmed['lat'] = sdf_trimmed.apply(lambda row: apply_jitter(row['city'], row['lat'], coordinate=LATITUDE), axis=1)
    sdf_trimmed['lon'] = sdf_trimmed.apply(lambda row: apply_jitter(row['city'], row['lon'], coordinate=LONGITUDE), axis=1)

    fig = px.scatter_geo(
        sdf_trimmed,
        lat="lat",
        lon="lon",
        custom_data=[
            "name",
            "implementationId",
            "implementationType",
            "apiType",
            "apiVersion",
            "url",
            "organisation",
            "city",
            "country",
            "drsObjects",
            "storageFootprintGb"
        ],
        projection="natural earth"
    )

    fig.update_layout(
        autosize=True,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )

    # Matches new_ga4gh's services-map.js D3 map exactly — can't reference the
    # CSS custom properties (--grey/--lightgrey/--faint-lightblue) directly
    # from a Plotly figure, same limitation their own JS comment notes for its
    # SCSS variables.
    fig.update_geos(
        showland = True, landcolor=COLORS["lightgrey"],
        showocean=True, oceancolor="rgba(79, 174, 220, 0.31)",
        showlakes=True, lakecolor="rgba(79, 174, 220, 0.31)",
        showcountries=True, countrycolor=COLORS["grey"],
    )

    # Matches new_ga4gh's .tooltip (layout/_services-map.scss): rgba($dark, .92)
    # background with white text, instead of Plotly's default (which mirrors
    # the marker's own blue).
    fig.update_traces(
        marker=dict(color=COLORS["darkblue"], size=12.5, opacity=1.0),
        hovertemplate=HOVERTEMPLATE,
        hoverlabel=dict(bgcolor='rgba(54, 54, 54, 0.92)', font_color='white', font_size=13),
    )

    return fig

def get_service_map_layout(standards_df, services_df, deployments_df):
    st_df = standards_df.copy() if standards_df is not None else pd.DataFrame()
    s_df = services_df.copy() if services_df is not None else pd.DataFrame()
    d_df = deployments_df.copy() if deployments_df is not None else pd.DataFrame()

    fig = _make_service_map_figure(st_df, s_df, d_df)

    return dbc.Card(
        dbc.CardBody([
            html.H5("Map of Registered GA4GH Services"),
            html.Figure([
                chart_expand_button("service_map"),
                dcc.Graph(id="service_map", figure=fig),
                dcc.Store(id="service_map-zoom-clamp-dummy"),
                html.Figcaption("Interactive map of registered services implementing GA4GH API specifications.")
            ])
        ]),
        className="mb-4 shadow-sm",
        style={"borderRadius": "12px"},
    )
