import dash
from dash import dcc, html, Input, Output

app = dash.Dash(__name__)

# Define available fruits and their default values
fruits = {
    "Apple": 5,
    "Banana": 7,
    "Orange": 3,
}

# Define the layout
app.layout = html.Div(
    [
        dcc.Dropdown(
            id="dropdown",
            options=[{"label": fruit, "value": fruit} for fruit in fruits.keys()],
            value=[],
            multi=True,
        ),
        html.Div(id="slider-container"),
        html.Div(id="output-container"),
    ]
)


@app.callback(Output("slider-container", "children"), [Input("dropdown", "value")])
def update_sliders(selected_fruits):
    slider_list = []
    for fruit in selected_fruits:
        slider_list.append(
            html.Div(
                [
                    html.Label(f"{fruit} Slider"),
                    dcc.Slider(
                        id=f"slider-{fruit.lower()}",
                        min=0,
                        max=10,
                        step=0.1,
                        value=fruits[fruit],
                    ),
                    html.Div(id=f"slider-output-{fruit.lower()}"),
                ]
            )
        )
    return slider_list


if __name__ == "__main__":
    app.run_server(debug=True)
