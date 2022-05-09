import plotly.express as px
from dash import dcc, html, dash
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output
from assets.data_validation import DataValidation

#---------------------------------------------
# File: API_Dash_graphs.py
# Author: Wouter Abels (wouter.abels@rws.nl)
# Created: 21/02/22
# Last modified: 04/04/22
# Python ver: 3.9.7
#---------------------------------------------

# Load data
total_plot_data, macev_taxongroup_colours, unique_measurementobject, historic_and_data= DataValidation().plotly_data()

# Build App
app = dash.Dash(__name__, title='MACEV Grafieken')
app.layout =html.Div([
        html.H1('Macroevertebraten Abundantie'),
        html.H2('Perceel A t/m C, 2015-2021 '),
        dcc.RadioItems(id='abundance_radio', options= [{'label': 'Totale Abundantie', 'value':'Totale Abundantie'},{'label': 'Relatieve Abundantie', 'value': 'Relatieve Abundantie',}], value= 'Totale Abundantie', labelStyle={'display': 'inline-block'}, style=dict(display='flex', justifyContent='center')),
        dcc.Graph(id= 'abundance_graph'),
        html.P('Meetobject'),
        dcc.Dropdown(id= 'object_dropdown', options=[{'label': i, 'value': i} for i in unique_measurementobject], value= unique_measurementobject[0]),
        dcc.Graph(id= 'object_graph')
        ])

@app.callback(
    Output('abundance_graph', 'figure'),
    Input('abundance_radio', 'value'),
    )

def graph_total_update(dropdown_value):
    fig = px.bar(total_plot_data, color_discrete_map=macev_taxongroup_colours, title='Totale Abundantie', template='simple_white', orientation='h', labels={'value': 'Totale Abundantie (n)', 'index': 'Jaar', 'Taxongroup': 'Taxongroep'})
    fig1 = px.bar(total_plot_data.apply(lambda x: x*100/sum(x),axis=1), color_discrete_map=macev_taxongroup_colours, title='Relatieve Abundantie', template='simple_white', orientation='h', labels={'value': 'Relatieve Abundantie (%)', 'index': 'Jaar', 'Taxongroup': 'Taxongroep'})
    if dropdown_value == 'Totale Abundantie':
        return fig
    elif dropdown_value == 'Relatieve Abundantie':
        return fig1

@app.callback(
    Output('object_graph', 'figure'),
    Input('object_dropdown', 'value'),
    Input('abundance_radio', 'value'),
    )

def graph_object_update(dropdown_object, dropdown_value):
    for object in unique_measurementobject:
        if dropdown_value =='Totale Abundantie':
            if object == dropdown_object:
                object_plot_data = DataValidation().relative_data_location_per_year(historic_and_data, dropdown_object)
                fig2 = px.bar(object_plot_data, color_discrete_map=macev_taxongroup_colours, title='Totale Abundantie meetobject: '+ str(dropdown_object), template='simple_white', orientation='h', labels={'value': 'Totale Abundantie (n)', 'index': 'Jaar', 'Taxongroup': 'Taxongroep'})
                return fig2
        if dropdown_value == 'Relatieve Abundantie':
            if object == dropdown_object:
                object_plot_data = DataValidation().relative_data_location_per_year(historic_and_data, dropdown_object)
                fig3 = px.bar(object_plot_data.apply(lambda x: x*100/sum(x),axis=1), color_discrete_map=macev_taxongroup_colours, title='Relatieve Abundantie meetobject: '+ str(dropdown_object), template='simple_white', orientation='h', labels={'value': 'Relatieve Abundantie (%)', 'index': 'Jaar', 'Taxongroup': 'Taxongroep'})
                return fig3

# Run app
if __name__ == '__main__':
    app.run_server(debug=True)