# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import json 
import plotly.io as pio
from plotly.subplots import make_subplots



app = Dash(__name__)


############################# Pulling the data
#Parking info
Parking_info = requests.get("https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/parkings/records?limit=100&timezone=europe%2FParis") 
Dump_parking_info = json.dumps(Parking_info.json())
Loads_parking_info = json.loads(Dump_parking_info)  
parking_info = pd.json_normalize(Loads_parking_info['results'])

#Stationnement info real time
Parking_reel_tine = requests.get("https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets/occupation-parkings-temps-reel@eurometrostrasbourg/records?limit=100&timezone=europe%2FParis") 
Dump_RT_parking = json.dumps(Parking_reel_tine.json())
Loads_RT_parking = json.loads(Dump_RT_parking)  
RT_parking = pd.json_normalize(Loads_RT_parking['results'])

#Compute data
RT_parking["Occupee"] = RT_parking["total"]  - RT_parking["libre"] 
RT_parking["percentage_occupe"] = RT_parking["Occupee"]  / RT_parking["total"]  

#add the location (lat/lon)
parking_info = parking_info[["name" , "position.lon",	"position.lat"]]
RT_parking = RT_parking.merge(parking_info, how='inner' , left_on='nom_parking' , right_on = 'name')



#AVG fullness
AVG_occupe = round(sum(RT_parking["Occupee"]) / sum(RT_parking["total"]) ,4)

#Availability data
NBR_place_libre = sum(RT_parking["libre"])
NBR_place_occupee = sum(RT_parking["Occupee"])
nbr_place_total  = sum(RT_parking["total"])

## Bar plot - place de parking occupe
pio.templates.default = "plotly"

fig1 = make_subplots(shared_yaxes=True, shared_xaxes=True)
fig1.add_bar(x=RT_parking['nom_parking'],y=RT_parking['total'],opacity=0.6,width=0.95,name='total',hovertemplate='%{y}')
fig1.add_bar(x=RT_parking['nom_parking'],y=RT_parking['Occupee'],width=0.95,name='Occupee')
fig1.update_layout(barmode='overlay', 
                  title= "Occupation parking Strasbourg",
                  xaxis_title=' ', 
                  yaxis_title='Occupation')

fig1.update_layout(xaxis={'categoryorder':'total descending'})

## Map - place de parking occupe
fig2 = px.scatter_mapbox(RT_parking, 
                        lat=RT_parking['position.lat'],
                        lon=RT_parking['position.lon'], 
                        hover_name="nom_parking", 
                        size="etat" ,
                        #hover_data=["status" , "Bike available" , "Available space" ],
                        custom_data=['nom_parking', 'etat_descriptif', 'libre' , 'Occupee','percentage_occupe'] ,
                        color="percentage_occupe",
                        color_continuous_scale=px.colors.sequential.OrRd ,
                        opacity = 0.8,
                        zoom=11, 
                        height=450)
fig2.update_layout(mapbox_style="carto-positron")
fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig2.update_layout(coloraxis_showscale=False)
fig2.update_traces(
    hovertemplate = 
                "<b>%{customdata[0]}</b><br>"   +  
                "<b>Etat : </b> %{customdata[1]}<br>" + 
                "<b>Parking libre: </b> %{customdata[2]}<br>" +
                "<b>Parking occupe: </b> %{customdata[3]}<br>"  +
                "<b>Pourcentage occupation: </b> %{customdata[4]}<br>"  
                ) 
#fig2.show()



app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])


app.layout =  html.Div([
    html.Div([
        html.Div([
            html.H3("Covid - 19", style={"margin-bottom": "0px", 'color': 'black'})
        ],
            className="one-third column",
        ),
        html.Div([
            html.Div([
                html.H3("Strabourg parking", style={"margin-bottom": "0px", 'color': 'white'}),
                html.H5("Track Covid - 19 Cases", style={"margin-top": "0px", 'color': 'white'}),
            ])
        ], className="one-half column", id="title"),

        html.Div([
            html.H6('Last Updated: ' +  '  00:01 (UTC)',
                    style={'color': 'orange'}),

        ], className="one-third column", id='title1'),

    ], id="header", className="row flex-display", style={"margin-bottom": "25px"}) , 


      html.Div([
        html.Div([
            html.H6(children='Place de parking disponible',
                    style={
                        'textAlign': 'center',
                        'color': 'white',
                        'fontSize': 20}
                    ),

            html.P(NBR_place_libre,
                   style={
                       'textAlign': 'center',
                       'color': 'lime',
                       'fontSize': 40}
                   )], className="card_container two columns",
        ),

        html.Div([
            html.H6(children='nombre places occupées',
                    style={
                        'textAlign': 'center',
                        'color': 'white',
                        'fontSize': 20}
                    ),

            html.P(NBR_place_occupee,
                   style={
                       'textAlign': 'center',
                       'color': '#dd1e35',
                       'fontSize': 40}
                   )], className="card_container two columns",
        ),

        html.Div([
            html.H6(children='Moyenne places occupées',
                    style={
                        'textAlign': 'center',
                        'color': 'white'}
                    ),

            html.P(f"{round(AVG_occupe * 100,2) }"  + '%',
                   style={
                       'textAlign': 'center',
                       'color': 'gold',
                       'fontSize': 40}
                   )], className="card_container two columns",
        ),

        html.Div([
            html.H6(children='Moyenne occupation',
                    style={
                        'textAlign': 'center',
                        'color': 'white'}
                    ),

            html.P(f"{round(AVG_occupe * 100,2) }"  + '%',
                   style={
                       'textAlign': 'center',
                       'color': 'grey',
                       'fontSize': 40}
                   )], className="card_container columns",
        )

    ], className="row flex-display"),


    html.Div([
            html.H6(children='Occupation des places par parking',
                    style={
                        'textAlign': 'center',
                        'color': 'white'}
                    ),

                dcc.Graph(
                            id='bar-plot',
                            figure=fig1
                    ) ], className="card_container columns",
    ),

    html.Div([
            html.H6(children='Occupation des places par parking',
                    style={
                        'textAlign': 'center',
                        'color': 'white'}
                    ),

                dcc.Graph(id='map-plot',
                            figure=fig2
                    ) ], className="card_container columns",
    ) ,


    html.Div(children='''
        Reporting pour visualiser la gestion des parkings
    '''),
    dcc.Graph(id='example-graph2',
              figure=fig2)
])


if __name__ == '__main__':
    app.run(debug=True)


    