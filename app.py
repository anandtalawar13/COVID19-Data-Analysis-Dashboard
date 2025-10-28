from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# Load dataset
url = "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv"
df = pd.read_csv(url)
# df = pd.read_excel('COVID-19 cases dataset.xlsx')

# Initialize Dash app
app = Dash(__name__)
app.title = "COVID-19 Data Analysis Dashboard"

# Layout
app.layout = html.Div([
    html.H1("COVID-19 Data Analysis Dashboard", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Select Country"),
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': c, 'value': c} for c in sorted(df['country'].unique())],
            value=['India'],
            multi=True
        ),
        html.Label("Select Date Range"),
        dcc.DatePickerRange(
            id='date-picker',
            start_date=df['date'].min(),
            end_date=df['date'].max()
        ),
        html.Label("Case Type"),
        dcc.RadioItems(
            id='cases-type',
            options=[
                {'label': 'Daily', 'value': 'daily'},
                {'label': 'Cumulative', 'value': 'cumulative'}
            ],
            value='daily',
            inline=True
        ),
        html.Label("Y-axis Scale"),
        dcc.Checklist(
            id='log-scale',
            options=[{'label': 'Log Scale', 'value': 'log'}],
            value=[]
        )
    ], style={'width': '50%', 'margin': 'auto'}),

    html.Br(),

    dcc.Graph(id='daily-cases'),
    dcc.Graph(id='daily-deaths'),
    dcc.Graph(id='vaccination-progress'),
    dcc.Graph(id='cases-vs-deaths')
])

# Callback
@app.callback(
    [Output('daily-cases', 'figure'),
     Output('daily-deaths', 'figure'),
     Output('vaccination-progress', 'figure'),
     Output('cases-vs-deaths', 'figure')],
    [Input('country-dropdown', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('log-scale', 'value'),
     Input('cases-type', 'value')]
)
def update_charts(selected_countries, start_date, end_date, log_scale, cases_type):
    filtered = df[df['country'].isin(selected_countries)]
    filtered = filtered[(filtered['date'] >= start_date) & (filtered['date'] <= end_date)]

    if cases_type == 'cumulative':
        filtered['new_cases'] = filtered.groupby('country')['new_cases'].cumsum()
        filtered['new_deaths'] = filtered.groupby('country')['new_deaths'].cumsum()

    yaxis_type = "log" if 'log' in log_scale else "linear"

    fig_cases = px.line(
        filtered, x='date', y='new_cases', color='country',
        title=f"{cases_type.title()} COVID-19 Cases",
        labels={'new_cases': 'Cases'}
    )
    fig_cases.update_yaxes(type=yaxis_type)

    fig_deaths = px.line(
        filtered, x='date', y='new_deaths', color='country',
        title=f"{cases_type.title()} COVID-19 Deaths",
        labels={'new_deaths': 'Deaths'}
    )
    fig_deaths.update_yaxes(type=yaxis_type)

    fig_vaccine = px.line(
        filtered, x='date', y='people_fully_vaccinated_per_hundred', color='country',
        title='Vaccination Coverage (% Fully Vaccinated)',
        labels={'people_fully_vaccinated_per_hundred': '% Fully Vaccinated'},
        hover_data=['gdp_per_capita', 'median_age', 'population_density']
    )

    latest = filtered.groupby('country').apply(lambda x: x.loc[x['date'].idxmax()]).reset_index(drop=True)
    fig_cases_vs_deaths = px.scatter(
        latest, x='total_cases_per_million', y='total_deaths_per_million',
        size='population', color='country',
        title='Total Cases vs Deaths per Million (Bubble size = Population)',
        hover_data=['gdp_per_capita', 'median_age', 'population_density', 'people_fully_vaccinated_per_hundred']
    )

    return fig_cases, fig_deaths, fig_vaccine, fig_cases_vs_deaths

# Run server
if __name__ == '__main__':
    app.run(debug=True)
