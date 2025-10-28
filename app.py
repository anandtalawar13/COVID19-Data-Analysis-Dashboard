from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px

#  Load and Prepare Dataset
url = "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv"
df = pd.read_csv(url)

columns = [
    "country", "date",
    "total_cases", "new_cases", "total_deaths", "new_deaths",
    "total_cases_per_million", "total_deaths_per_million",
    "total_vaccinations", "people_fully_vaccinated",
    "people_fully_vaccinated_per_hundred",
    "new_vaccinations", "total_tests_per_thousand",
    "stringency_index",
    "population", "gdp_per_capita",
    "population_density", "median_age"
]
df = df[columns]

countries = ['India', 'United States', 'Russia', 'Brazil', 'South Africa', 'France', 'United Kingdom']
df = df[df['country'].isin(countries)]

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['country', 'date'])

num_cols = df.select_dtypes(include='number').columns
df[num_cols] = df.groupby('country')[num_cols].ffill()
df = df.fillna(0).infer_objects(copy=False)

# Initialize App
app = Dash(__name__)
app.title = "COVID-19 Interactive Dashboard"

# Layout
app.layout = html.Div([
    html.H1("COVID-19 Interactive Dashboard", style={'textAlign': 'center'}),
    
    # Input Controls
    html.Div([
        html.Div([
            html.Label("Select Countries:"),
            dcc.Dropdown(
                id='country-dropdown',
                options=[{'label': c, 'value': c} for c in countries],
                value=['India', 'United States'],
                multi=True
            ),
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label("Select Date Range:"),
            dcc.DatePickerRange(
                id='date-picker',
                start_date=df['date'].min(),
                end_date=df['date'].max(),
                display_format='YYYY-MM-DD'
            ),
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
        
    ], style={'display': 'flex', 'justify-content': 'space-around'}),
    
    html.Div([
        html.Div([
            html.Label("Y-axis Scale:"),
            dcc.Checklist(
                id='log-scale',
                options=[{'label': 'Use Log Scale', 'value': 'log'}],
                value=[],
                inline=True
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label("Cases/Deaths Type:"),
            dcc.RadioItems(
                id='cases-type',
                options=[
                    {'label': 'Daily', 'value': 'daily'},
                    {'label': 'Cumulative', 'value': 'cumulative'}
                ],
                value='daily',
                labelStyle={'display': 'inline-block', 'margin-right': '10px'}
            )
        ], style={'width': '60%', 'display': 'inline-block', 'padding': '10px'})
    ], style={'display': 'flex', 'justify-content': 'space-around'}),
    
    # Graphs
    dcc.Graph(id='daily-cases'),
    dcc.Graph(id='daily-deaths'),
    dcc.Graph(id='vaccination-progress'),
    dcc.Graph(id='cases-vs-deaths'),

    html.H2("Additional Insights", style={'textAlign': 'center', 'marginTop': 30}),
    dcc.Graph(id='stringency-trend'),
    dcc.Graph(id='gdp-vs-vaccine'),
    dcc.Graph(id='density-vs-cases'),
    dcc.Graph(id='animated-trend')
])

# Callbacks
@app.callback(
    [Output('daily-cases', 'figure'),
     Output('daily-deaths', 'figure'),
     Output('vaccination-progress', 'figure'),
     Output('cases-vs-deaths', 'figure'),
     Output('stringency-trend', 'figure'),
     Output('gdp-vs-vaccine', 'figure'),
     Output('density-vs-cases', 'figure'),
     Output('animated-trend', 'figure')],
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
    
    # Graph 1: Cases
    fig_cases = px.line(
        filtered, x='date', y='new_cases', color='country',
        title=f"{cases_type.title()} COVID-19 Cases"
    )
    fig_cases.update_yaxes(type=yaxis_type)
    
    # Graph 2: Deaths
    fig_deaths = px.line(
        filtered, x='date', y='new_deaths', color='country',
        title=f"{cases_type.title()} COVID-19 Deaths"
    )
    fig_deaths.update_yaxes(type=yaxis_type)
    
    # Graph 3: Vaccination Progress
    fig_vaccine = px.line(
        filtered, x='date', y='people_fully_vaccinated_per_hundred', color='country',
        title='Vaccination Coverage (% Fully Vaccinated)'
    )
    
    # Graph 4: Cases vs Deaths
    latest = filtered.groupby('country').apply(lambda x: x.loc[x['date'].idxmax()]).reset_index(drop=True)
    fig_cases_vs_deaths = px.scatter(
        latest, x='total_cases_per_million', y='total_deaths_per_million',
        size='population', color='country',
        title='Total Cases vs Deaths per Million (Bubble size = Population)'
    )
    
    # Graph 5: Stringency Index Trend
    fig_stringency = px.line(
        filtered, x='date', y='stringency_index', color='country',
        title='Government Stringency Index Over Time'
    )
    
    # Graph 6: GDP vs Vaccination
    fig_gdp_vaccine = px.scatter(
        latest, x='gdp_per_capita', y='people_fully_vaccinated_per_hundred',
        size='population', color='country',
        title='GDP per Capita vs Vaccination Rate',
        trendline='ols'
    )
    
    # Graph 7: Population Density vs Cases
    fig_density = px.scatter(
        latest, x='population_density', y='total_cases_per_million',
        color='country', size='population',
        title='Population Density vs Cases per Million',
        trendline='ols'
    )
    
    # Graph 8: Animated Global Trend
    fig_animated = px.scatter(
        filtered, x='total_cases_per_million', y='total_deaths_per_million',
        animation_frame='date', color='country',
        size='population', title='COVID-19 Progression Over Time (Animated)',
        log_x=True, log_y=True, range_x=[10, 1e6], range_y=[1, 1e5]
    )
    
    return (fig_cases, fig_deaths, fig_vaccine, fig_cases_vs_deaths,
            fig_stringency, fig_gdp_vaccine, fig_density, fig_animated)

# Run
if __name__ == '__main__':
    app.run(debug=True)
