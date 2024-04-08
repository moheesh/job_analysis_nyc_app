import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objs as go
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64

# Assuming 'df' is your DataFrame containing the data
path = 'Jobs_NYC_Postings.csv'
df = pd.read_csv(path)

# Remove columns
df.drop(['Full-Time/Part-Time indicator', 'Minimum Qual Requirements', 'Work Location 1', 'Recruitment Contact'], axis=1, inplace=True)

# Replace missing values
df['Preferred Skills'].fillna('Not specified', inplace=True)
df['Additional Information'].fillna('None', inplace=True)
df['To Apply'].fillna('Not specified', inplace=True)
df['Hours/Shift'].fillna('Not specified', inplace=True)

# Calculate 1 month after the post date when 'Post Until' is NaN
post_date = pd.to_datetime(df['Posting Date'])
post_until = df['Post Until'].copy()
post_until[pd.isna(post_until)] = post_date[pd.isna(post_until)] + pd.DateOffset(months=1)
df['Post Until'] = post_until

# Convert 'Posting Date' column to datetime
df['Posting Date'] = pd.to_datetime(df['Posting Date'])

# Extract unique years and months from 'Posting Date'
unique_years = df['Posting Date'].dt.year.unique()
unique_months = df['Posting Date'].dt.month_name().unique()

# Define the order of months
month_order = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

# Convert month names to categorical data type with specified order
df['Posting Month'] = pd.Categorical(df['Posting Date'].dt.month_name(), categories=month_order, ordered=True)

# Initialize Dash app
app = dash.Dash(__name__)

server = app.server

# Define the layout of the Dash app
app.layout = html.Div([
    html.H1("Number of Jobs Posted by Month"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': str(year), 'value': year} for year in unique_years],
        value=unique_years[0]  # Set the default value to the first year
    ),
    html.Div(id='graphs-container')
])


# Define callback to update the graphs based on selected year
@app.callback(
    Output('graphs-container', 'children'),
    [Input('year-dropdown', 'value')]
)
def update_graph(selected_year):
    # Filter DataFrame based on selected year
    filtered_df = df[df['Posting Date'].dt.year == selected_year]

    # Group by 'Posting Month' and count the number of jobs
    jobs_by_month = filtered_df.groupby('Posting Month').size().reset_index(name='Number of Jobs')

    # Create figure for the bar chart
    bar_figure = {
        'data': [
            {'x': jobs_by_month['Posting Month'], 'y': jobs_by_month['Number of Jobs'], 'type': 'bar',
             'name': 'Number of Jobs'}
        ],
        'layout': {
            'title': f'Number of Jobs Posted in {selected_year}',
            'xaxis': {'title': 'Month'},
            'yaxis': {'title': 'Number of Jobs'}
        }
    }

    # Group by 'Career Level' and count the number of jobs
    jobs_by_career_level = filtered_df.groupby('Career Level').size().reset_index(name='Number of Jobs')

    # Create figure for the pie chart
    pie_figure = {
        'data': [
            go.Pie(labels=jobs_by_career_level['Career Level'], values=jobs_by_career_level['Number of Jobs'])
        ],
        'layout': {
            'title': f'Distribution of Career Levels in {selected_year}'
        }
    }

    # Filter DataFrame where salary frequency is 'annual'
    annual_salary_df = filtered_df[filtered_df['Salary Frequency'] == 'Annual']

    # Create strip plot for the average annual salary distribution
    plt.figure(figsize=(10, 6))
    sns.stripplot(data=annual_salary_df, y='Salary Range From', x='Career Level', hue='Career Level')
    plt.title(f'Average Annual Salary Distribution by Career Level in {selected_year}')
    plt.xlabel('Career Level')
    plt.ylabel('Average Annual Salary')
    plt.legend(title='Career Level', bbox_to_anchor=(1.05, 1), loc='upper left')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    stripplot_image = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    # Display the strip plot as an image
    stripplot_container = html.Div([
        html.Img(src='data:image/png;base64,{}'.format(stripplot_image))
    ])

    # Create histogram for the average annual salary distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(data=annual_salary_df, x='Salary Range From', bins=20, kde=True, color='orange')
    plt.title(f'Average Annual Salary Distribution Histogram in {selected_year}')
    plt.xlabel('Average Annual Salary')
    plt.ylabel('Density')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    hist_image = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    # Display the histogram as an image
    histogram_container = html.Div([
        html.Img(src='data:image/png;base64,{}'.format(hist_image))
    ])

    # Create line plot for the number of jobs over time
    jobs_over_time = filtered_df.groupby('Posting Date').size().reset_index(name='Number of Jobs')
    line_figure = {
        'data': [
            go.Scatter(x=jobs_over_time['Posting Date'], y=jobs_over_time['Number of Jobs'], mode='lines',
                       name='Number of Jobs')
        ],
        'layout': {
            'title': f'Number of Jobs Posted Over Time in {selected_year}',
            'xaxis': {'title': 'Posting Date'},
            'yaxis': {'title': 'Number of Jobs'}
        }
    }

    return [
        html.Div([
            dcc.Graph(figure=bar_figure, style={'width': '50%', 'display': 'inline-block'}),
            dcc.Graph(figure=pie_figure, style={'width': '50%', 'display': 'inline-block'})
        ]),
        html.Div([
            stripplot_container,
            histogram_container
        ]),
        dcc.Graph(figure=line_figure)
    ]


# Run the Dash app on localhost
if __name__ == '__main__':
    app.run_server(debug=True)
