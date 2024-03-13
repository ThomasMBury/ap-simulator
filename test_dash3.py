from dash import Dash, dcc, html, Input, Output, ALL, Patch, callback

app = Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div(
    [
        dcc.Dropdown(
            id="dropdown_plot_vars",
            options=["a", "b", "c", "d"],
            value=["a", "b"],
            multi=True,
            maxHeight=400,
            optionHeight=20,
            style=dict(fontSize=12),
        ),
        html.Div(id="tabs-container-div", children=[]),
        html.Div(id="tabs-container-output-div"),
    ]
)


@callback(
    Output("tabs-container-div", "children"), Input("dropdown_plot_vars", "value")
)
def display_tabs(plot_vars):

    list_tabs = []
    for var in plot_vars:
        list_tabs.append(dcc.Tab(value="tab-{}".format(var), label=var))

    children = (
        dcc.Tabs(
            id="tabs-example-graph",
            value="tab-1-example-graph",
            children=list_tabs,
        ),
    )

    return children


@callback(
    Output("tabs-container-output-div", "children"),
    Input("tabs-example-graph", "value"),
)
def render_content(tab):
    if tab == "tab-a":
        return html.Div(
            [
                html.H3("Tab content 1"),
                dcc.Graph(
                    figure=dict(data=[dict(x=[1, 2, 3], y=[3, 1, 2], type="bar")])
                ),
            ]
        )
    elif tab == "tab-b":
        return html.Div(
            [
                html.H3("Tab content 2"),
                dcc.Graph(
                    figure=dict(data=[dict(x=[1, 2, 3], y=[5, 10, 6], type="bar")])
                ),
            ]
        )
    elif tab == "tab-c":
        return html.Div(
            [
                html.H3("Tab content 3"),
                dcc.Graph(
                    figure=dict(data=[dict(x=[1, 2, 3], y=[10, 10, 6], type="bar")])
                ),
            ]
        )
    elif tab == "tab-d":
        return html.Div(
            [
                html.H3("Tab content 4"),
                dcc.Graph(
                    figure=dict(data=[dict(x=[1, 2, 3], y=[20, 10, 6], type="bar")])
                ),
            ]
        )


# @callback(
#     Output("dropdown-container-div", "children"), Input("add-filter-btn", "n_clicks")
# )
# def display_dropdowns(n_clicks):
#     patched_children = Patch()
#     new_dropdown = dcc.Dropdown(
#         ["NYC", "MTL", "LA", "TOKYO"],
#         id={"type": "city-filter-dropdown", "index": n_clicks},
#     )
#     patched_children.append(new_dropdown)
#     return patched_children


# @callback(
#     Output("tabs-container-output-div", "children"),
#     Input({"type": "city-filter-dropdown", "index": ALL}, "value"),
# )
# def display_output(values):
#     return html.Div(
#         [html.Div(f"Dropdown {i + 1} = {value}") for (i, value) in enumerate(values)]
#     )


# @callback(
#     Output("dropdown-container-output-div", "children"),
#     Input({"type": "city-filter-dropdown", "index": ALL}, "value"),
# )
# def display_output(values):
#     return html.Div(
#         [html.Div(f"Dropdown {i + 1} = {value}") for (i, value) in enumerate(values)]
#     )


if __name__ == "__main__":
    app.run(debug=True)
