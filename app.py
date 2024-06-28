# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
#Github reference project : https://github.com/Mubeen31/Covid-19-Dashboard-in-Python-by-Plotly-Dash

import dash
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import json 
import plotly.io as pio
from plotly.subplots import make_subplots
from datetime import datetime 
import pytz 



app = Dash(__name__)

#Get timestamp
UTC = pytz.utc
time_At_P = pytz.timezone('Europe/Paris') 
dt_time_P = datetime.now(time_At_P) 

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
RT_parking["percentage_occupe"] = round(RT_parking["Occupee"]  / RT_parking["total"] *100,2) 

#add the location (lat/lon)
parking_info = parking_info[["name" , "position.lon",	"position.lat"]]
RT_parking = RT_parking.merge(parking_info, how='inner' , left_on='nom_parking' , right_on = 'name')

#Filter parking open/close/data non disponible
RT_parking_ouvert = RT_parking.loc[RT_parking['etat_descriptif'] == "Ouvert"]
RT_parking_ferme = RT_parking.loc[RT_parking['etat_descriptif'] == "Fermé"]
RT_parking_not_available = RT_parking.loc[RT_parking['etat_descriptif'] == "frequentation temps reel indisponible"]


## AVG fullness
AVG_occupe = round(sum(RT_parking_ouvert["Occupee"]) / sum(RT_parking_ouvert["total"]) ,4)

## Availability data
NBR_place_libre = sum(RT_parking_ouvert["libre"])
NBR_place_occupee = sum(RT_parking_ouvert["Occupee"])
nbr_place_total  = sum(RT_parking_ouvert["total"])

###### Bar plot - Status des parkings
etat_data = RT_parking.groupby(['etat_descriptif'], as_index=False).size()
etat_data["share_size"] = round((etat_data['size'] / etat_data['size'].sum()) ,2)

status_bar = px.bar(etat_data, y='etat_descriptif',
            x='size' ,
            height=140,
            orientation='h' , 
            color = 'size' ,
            color_continuous_scale=px.colors.sequential.OrRd[::-1])
status_bar.update_layout(yaxis={'categoryorder':'total ascending'},
                  margin=dict(l=20, r=20, t=20, b=20),
                  yaxis_title='  ') 
status_bar.update_layout(coloraxis_showscale=False)



###### Bar plot - place de parking occupe
pio.templates.default = "plotly"
Sorting_order = RT_parking_ouvert.sort_values('percentage_occupe', ascending=False)['nom_parking'].to_list()

fig1 = make_subplots(shared_yaxes=True, shared_xaxes=True)
fig1.add_bar(x=RT_parking_ouvert['nom_parking'],y=RT_parking_ouvert['total'],opacity=0.6,width=0.95,name='total',hovertemplate='%{y}')
fig1.add_bar(x=RT_parking_ouvert['nom_parking'],y=RT_parking_ouvert['Occupee'],width=0.95,name='Occupee')
fig1.update_layout(barmode='overlay', 
                  title= "Occupation parking Strasbourg",
                  yaxis_title='Occupation',
                    xaxis={'categoryorder':'array', 'categoryarray':Sorting_order})




###### Map - place de parking occupe
fig2 = px.scatter_mapbox(RT_parking_ouvert, 
                        lat=RT_parking_ouvert['position.lat'],
                        lon=RT_parking_ouvert['position.lon'], 
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
                "<b>État : </b> %{customdata[1]}<br>" + 
                "<b>Parking libre: </b> %{customdata[2]}<br>" +
                "<b>Parking occupe: </b> %{customdata[3]}<br>"  +
                "<b>Pourcentage occupation: </b> %{customdata[4]}%<br>"  
                ) 
#fig2.show()



app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])


app.layout =  html.Div([
    html.Div([
        html.Div([
            html.Img(src=app.get_asset_url('strasbourg_logo.jpg'),
                     id='corona-image',
                     style={
                         "height": "60px",
                         "width": "auto",
                         "margin-bottom": "25px",
                     },
                     )
        ],
            className="one-third column",
        ),
        html.Div([
            html.Div([
                html.H3("Strasbourg parking", style={"margin-bottom": "0px", 'color': 'white'}),
                html.H5("Tracker état du stationnement", style={"margin-top": "0px", 'color': 'white'}),
            ])
        ], className="one-half column", id="title"),

        html.Div([
            html.H6('refresh à ' + dt_time_P.strftime("%Y-%m-%d %H:%M:%S"),
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
            html.H6(children='Status des parkings',
                    style={
                        'textAlign': 'left',
                        'color': 'white'}
                    ), 
                    dcc.Graph(
                            id='status_plot',
                            figure=status_bar
                    )
                    ], className="card_container columns",
        )

    ], className="row flex-display"),


    html.Div([
            html.H6(children='Occupation des places de parking',
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
            html.H6(children='Maps montrant les parkings avec un fort taux de remplissage',
                    style={
                        'textAlign': 'center',
                        'color': 'white'}
                    ),

                dcc.Graph(id='map-plot',
                            figure=fig2
                    ) ], className="card_container columns",
    ) 


    
])


if __name__ == '__main__':
    app.run(debug=True)


    