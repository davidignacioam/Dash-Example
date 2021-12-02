
#%% IoT Dashboard

## Libraries
# DF Manipulation
import pandas as pd
# Dash
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output
# Date
from time import process_time
import time
# Visualization
import plotly.graph_objects as go   
# Data
import pickle
import mysql.connector as mysql
# Others
import base64
from concurrent.futures import ThreadPoolExecutor

## Colors
MainColor = 'rgb(70,37,75)'
SecondColor = 'rgb(140,50,100)' # 'rgb(60,100,170)'
SidebarColor = 'rgb(70,37,75)'
BackgroundColor = 'rgb(170,160,190)'
TitleColor = 'rgb(210,210,210)'
AnomalyColor = 'rgba(250,250,0,0.9)'

## Time update
Update_Interval = 9.5 #Interval_Refresh = 10

####  Cards  ####

def Card_Graph(group,N):
    # Defining titles and groups
    Group = "Group-".join(("",str(group)))
    df = Poc_IoT_Calss[{'Nombre tags','Grupo'}].drop_duplicates()
    Title = df[df['Grupo'] == group]['Nombre tags'][0:1]
    # Creating List with figures
    Card_list = []
    for i in range(N) :
        Card_list.append(dcc.Graph(figure = Plot_List[df_group['index'][i]]))
    # Building the Card object
    Card = dbc.Card([
        dbc.CardHeader([
           dbc.Col([ 
                html.H6(Title, id=Group),
                dbc.Tooltip(Group, target=Group, placement="right")
                ],
                align="center",
                width={"size": 4, "offset": 4},
                 style = {
                    'background-color' : SecondColor,
                    'color' : TitleColor,
                    "padding": "0px",
                    'border-radius':'0px'
                    }
            )],
            style = {
                'height' : '3rem',
                'background-color' : SecondColor,
                'color' : TitleColor,
                'textAlign': 'center'
                }
            ),
        dbc.CardBody(
            Card_list,
            style = {
                'margin': '0px',
                'padding' : '0px',
                'background-color' : MainColor
                }
            )
        ],
        style = {
            'border-color': SecondColor,
            'background-color' : MainColor,
            'box-shadow': '2px 4px 4px 0px rgba(44, 44, 44, .4)'
            },
        outline=True
    )
    return Card

####  Plots  ####

def Plot_Lines_dark(df, dfA, Column, LineColor):
    
       ## Generl DF
    # Selecting column
    df0 = df.iloc[:,[1,Column]].dropna()
    # Name
    df = df0
    
    ## Anomalies
    # Current Name column name
    current_column = df.columns[1]
    # Filtering sensors
    df_time = dfA[dfA['Sensor'] == current_column]. \
        dropna(). \
        drop(columns=['TimeLabel']) \
        ['Time']
    df_A = df.loc[df['Timestamp'].isin(df_time)]
        
    ## General Visualization
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        name = df.columns[1], 
        x = df.iloc[:,0], 
        y = df.iloc[:,1],
        mode = "lines", 
        line_color = LineColor
    ))
    fig.add_trace(go.Scatter(
        name = 'Anomaly', 
        #name = 'Anomalía', # Spanish version
        x = df_A.iloc[:,0], 
        y = df_A.iloc[:,1],
        mode = "markers", 
        marker = dict(size = 8),
        line_color = 'yellow',
        hovertemplate = " "
    ))
    fig.update_xaxes(
        showticklabels = False,
        color = 'rgb(150,150,150)', 
        showline = True, linewidth = 1, linecolor = 'grey',
        showgrid = True, gridwidth = 0.1, gridcolor = 'grey',
        ticks = "outside", tickwidth = 2, tickcolor = 'grey', ticklen = 10
        )
    fig.update_yaxes(
        color = 'rgb(150,150,150)', 
        showline = True, linewidth = 1, linecolor = 'grey',
        showgrid = True, gridwidth = 0.1, gridcolor = 'grey',
        ticks = "outside", tickwidth = 2, tickcolor = 'grey', ticklen = 10
        )
    fig.update_layout(
        showlegend = False,
        hovermode = "x",
        height = 150,# 140
        plot_bgcolor = MainColor,
        paper_bgcolor = MainColor,
        title = df.columns[1], 
        title_x = 0.05,
        title_font_family = "Times New Roman", 
        title_font_color = TitleColor,
        margin = go.layout.Margin(
            l = 60, #left margin
            r = 20, #right margin
            b = 30, #bottom margin
            t = 40  #top margin
            )
        ) 
        
    return fig

####  Static Data  ####

global Poc_IoT_Calss
global df_Colour

Poc_IoT_Calss = pickle.load(open('Poc_IoT_Calss', 'rb')) \
    .sort_values('Maquina') \
    .reset_index(drop=True) \
    .reset_index()

Poc_IoT_Calss = Poc_IoT_Calss[(Poc_IoT_Calss['Sensores'] != 'sensor_15') &
                              (Poc_IoT_Calss['Sensores'] != 'sensor_50')]  \
    .reset_index(drop=True) \
    .reset_index() \
    .drop(columns=['index']) \
    .rename(columns={"level_0": "index"})

## Setting Df with Colors
df_Colour = pd.DataFrame({
    'Group' : Poc_IoT_Calss['GrupoColor'].unique(),
    'ColorLine' : ['rgba(0, 250, 250, 1)',
                   'rgba(240, 160, 60, 1)',
                   'rgba(200, 90, 250, 1)',
                   'rgba(100, 250, 100, 1)',
                   'rgba(250, 0, 200, 1)',
                   'rgba(255, 0, 0, 1)',
                   'rgba(255, 180, 180, 1)'] 
}).reset_index()


####  Live Data Update  ####

def get_new_data():
    
    global time_data_start
    global time_data_end
    global Poc_IoT_df
    global Poc_IoT_Anomalies
    global Plot_List
    global Group_List
    global Container_list
    global df_group
    global df_value
    global df_machine
    global name_machine
    global anomaly_message
    global anomaly_color
    global Tab_Color
    
    time_data_start = process_time() 
    
    ### SQL Conexion
    mydb = mysql.connect(
        user = "b87ea112b3fd75",
        password = "159c5141",
        database = "heroku_e1bef121251bd17",
        host = "us-cdbr-east-04.cleardb.com"
    )
    
    ## Query I
    # Setting
    mycursor = mydb.cursor(buffered = True, dictionary = True)
    mycursor.execute("""
        SELECT * 
        FROM df_sensors2 
        ORDER BY id desc 
        LIMIT 180
        """
        )
    # Creating de Object
    Poc_IoT_df_query = mycursor.fetchall()
    #Initialise empty list
    from_db = []
    # Loop over the results and append them into our list: Returns a list of tuples
    for result in Poc_IoT_df_query:
        result = result
        from_db.append(result)
    # Creating the Data Frame
    Poc_IoT_df = pd.DataFrame(from_db). \
        rename(columns={'timestamp':'Timestamp'}). \
        drop(columns=['flag2'])
    ## Sorting Columns
    colnames = Poc_IoT_Calss[['Sensores','Maquina']]. \
        sort_values('Maquina')['Sensores']. \
        tolist()
    colnames.insert(0,'Timestamp')
    colnames.insert(0,'id')
    #colnames.insert(len(colnames),'machine_status')
    Poc_IoT_df.columns = colnames
    # Defining Date type
    Poc_IoT_df['Timestamp'] = pd.to_datetime(Poc_IoT_df['Timestamp'])
    # Deleting Objects
    del Poc_IoT_df_query
    del result
    del from_db
    
    ## Query II
    # Setting
    mycursor.execute("""
        SELECT * 
        FROM anomalies 
        ORDER BY id desc 
        LIMIT 10000
        """
        ) # order by id desc LIMIT 180
    # Creating de Object
    Poc_IoT_Anomalies_query = mycursor.fetchall()
    #Initialise empty list
    from_db = []
    # Loop over the results and append them into our list: Returns a list of tuples
    for result in Poc_IoT_Anomalies_query:
        result = result
        from_db.append(result)
    # Creating the Data Frame
    Poc_IoT_Anomalies = pd.DataFrame(from_db).drop(columns=['id'])
    Poc_IoT_Anomalies['Time'] = pd.to_datetime(Poc_IoT_Anomalies['Time'])
    Poc_IoT_Anomalies['TimeLabel'] = pd.to_datetime(Poc_IoT_Anomalies['TimeLabel'])
    current_preiod = max(pd.to_datetime(Poc_IoT_Anomalies['TimeLabel']))
    Poc_IoT_Anomalies = Poc_IoT_Anomalies[Poc_IoT_Anomalies['TimeLabel'] == current_preiod]
    # Deleting Objects
    del Poc_IoT_Anomalies_query
    del current_preiod
    del result
    del from_db
    
    ## Query III
    mycursor.execute("""
        SELECT * 
        FROM status_pred 
        ORDER BY id desc 
        LIMIT 1
        """
        )
    # Creating de Object
    Poc_IoT_Prediction_query = mycursor.fetchall()
    # Clossing connection
    mycursor.close()
    mydb.close()
    #Initialise empty list
    from_db = []
    # Loop over the results and append them into our list: Returns a list of tuples
    for result in Poc_IoT_Prediction_query:
        result = result
        from_db.append(result)
    # Creating the Data Frame
    Poc_IoT_Pred = pd.DataFrame(from_db).drop(columns=['id','TimeLabel'])
    Poc_IoT_Pred['Time'] = pd.to_numeric(Poc_IoT_Pred['Time'], downcast='float')
    Poc_IoT_Pred['Accuracy'] = pd.to_numeric(Poc_IoT_Pred['Accuracy'], downcast='float').round(decimals=0)
    # Variables
    status_failure = Poc_IoT_Pred['Failure'][0]
    time_failure = Poc_IoT_Pred['Time'][0]
    accuracy_failure = Poc_IoT_Pred['Accuracy'][0]
    # Deleting Objects
    del Poc_IoT_Prediction_query
    del result
    del from_db

    
    ####  OBJECTS  

    ## Plot_List with Figures
    Plot_List = [([ 0 ]),([ 1 ])]
    for value in Poc_IoT_Calss['Maquina'].unique():
        df_value = Poc_IoT_Calss[Poc_IoT_Calss['Maquina'] == value]
        for index in df_value['index']:
            Color = df_Colour[df_Colour['Group'] == df_value['GrupoColor'][index]]
            Col = 2 + index
            Plot = Plot_Lines_dark(Poc_IoT_df, Poc_IoT_Anomalies, Col, Color['ColorLine'][int(Color['index'])])
            Plot_List.insert(Col,Plot) 

    ## Group_List with Cards

    # Defininf the original Empty List
    Group_List = [([ 0 ]),([ 1 ])]
    # General Loop
    for group in Poc_IoT_Calss['Grupo'].unique() : # [Poc_IoT_Calss['Grupo'] < 96]
        # Filtering by Group and Creating Index columns
        df_group = Poc_IoT_Calss[Poc_IoT_Calss['Grupo'] == group].reset_index(drop=True)
        # Loop for creating original number column
        for i in range(df_group.shape[0]) :
            df_group.iloc[i,0] = df_group.iloc[i,0]+2
        # Defining how many Figures are inside each Group
        N = len(df_group['Grupo'])
        Card = Card_Graph(group, N)
        Group_List.insert(group,Card)


    ####  Dashboard: STRUCTURE  ####
  
    # PREDICTIONS
    if status_failure == 'True' :
        if time_failure > 30 :
            prediction_message = f"The machine has prediction of Failiure in {time_failure} more minutes with a {accuracy_failure} percent of Accuracy." 
            prediction_color = "warning" 
        if not time_failure > 30 :
            prediction_message = f"The machine has prediction of Failiure in {time_failure} more minutes with a {accuracy_failure} percent of Accuracy." 
            prediction_color = "danger" 
    if not status_failure == 'True' :
        prediction_message = f"The machine has no prediction of Failiure." 
        prediction_color = "success"
    
    ## Loop for UI structure
    name_machine = Poc_IoT_Calss['Maquina'].unique()
    Container_list = []
    #Tab_Color = []  
    for machine in name_machine :
        df_machine = Poc_IoT_Calss[Poc_IoT_Calss['Maquina'] == machine]
        machine_sensors = df_machine['Sensores']
        Page_list = []
        for group in df_machine['Grupo'].unique() :
            # ANOMALIES
            anomaly_sensors = Poc_IoT_Anomalies.loc[
                Poc_IoT_Anomalies['Sensor'].isin(machine_sensors)
                ]['Sensor']. \
                unique()
            if not anomaly_sensors.size == 0 : 
                anomaly_message = f"The machine {machine} has anomalies in the following sensors: {anomaly_sensors}" 
                anomaly_color = "danger" # warning
                #Tab_Color.append('rgb(250,220,220)')
            if anomaly_sensors.size == 0 : 
                anomaly_message = f"The machine {machine} has no anomalies in this period of time."
                anomaly_color = "success"
                #Tab_Color.append('rgb(220,250,220)')
            # Building UI
            Page_list.append(
                html.Div([
                    html.H3('IoT - Dashboard', 
                            style={'text-align' : 'center',
                                   #'background-color' : SecondColor,
                                   "color" : TitleColor})
                    ],  style={"background-color" : SidebarColor,
                               "padding" : "1rem"})
                )
            Page_list.append(html.Br())
            Page_list.append(
                dbc.Alert(prediction_message, color=prediction_color)
                )
            Page_list.append(
                dbc.Alert(anomaly_message, color=anomaly_color)
                )
            # Page_list.append(html.Br())
            Page_list.append(
                dbc.Row([
                    dbc.Col(html.Div(Group_List[group]), width=12)
                    ], align="center")
                )
            Page_list.append(html.Br())
        Container_list.append(Page_list)
    
    # Data process Time
    time_data_end = process_time() 
    print("Data processing:", time_data_end-time_data_start) 
        

def get_new_data_every(period = Update_Interval):
    while True:
        get_new_data()
        print("Data Updated")
        time.sleep(period)
        

########  SERVER  ########

## Setting Dash App
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.css.config.serve_locally = False
for css in [dbc.themes.BOOTSTRAP,
            './assets/mycss.css',
            'https://use.fontawesome.com/releases/v5.8.1/css/all.css']:
   app.css.append_css({"external_url": css})
app.title = "IoT PoC Dashboard"

# get initial data                                                                                                                                                            
get_new_data()


####  Live Pages Updates  ####

global page_1
global page_2
global page_3
global page_4
global page_5
global page_6
global page_7
    
@app.callback(Output('live-update-page1', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    page_1 =  dbc.Container(Container_list[0],fluid=True)
    return page_1

@app.callback(Output('live-update-page2', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    page_2 =  dbc.Container(Container_list[1],fluid=True)
    return page_2

@app.callback(Output('live-update-page3', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    page_3 =  dbc.Container(Container_list[2],fluid=True)
    return page_3

@app.callback(Output('live-update-page4', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    page_4 =  dbc.Container(Container_list[3],fluid=True)
    return page_4

@app.callback(Output('live-update-page5', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    page_5 =  dbc.Container(Container_list[4],fluid=True)
    return page_5

@app.callback(Output('live-update-page6', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    page_6 =  dbc.Container(Container_list[5],fluid=True)
    return page_6

@app.callback(Output('live-update-page7', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    page_7 =  dbc.Container(Container_list[6],fluid=True)
    return page_7

####  Sidebar  ####

@app.callback(
    Output("page-content", "children"), 
    [Input("url", "pathname")]
    )
def render_page_content(pathname):
    if pathname == "/":
        return html.Div(id='live-update-page1')
    elif pathname == "/page-1":
        return html.Div(id='live-update-page1')
    elif pathname == "/page-2":
        return html.Div(id='live-update-page2')
    elif pathname == "/page-3":
        return html.Div(id='live-update-page3')
    elif pathname == "/page-4":
        return html.Div(id='live-update-page4')
    elif pathname == "/page-5":
        return html.Div(id='live-update-page5')
    elif pathname == "/page-6":
        return html.Div(id='live-update-page6')
    elif pathname == "/page-7":
        return html.Div(id='live-update-page7')
    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron([
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P("The pathname {pathname} was not recognised..."),
            html.Br()
            ])


####  Sidebar  ####
image_filename = '/Users/usuario/Documents/Python/Evalueserve/PoC/IoT/assets/logo.png' 
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

sidebar = html.Div([
        dbc.Nav([
            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),
                     style={'height':'100%', 'width':'100%'}),
            html.Br(),
            html.Br(),
            # Page 1
            dbc.NavLink([html.I(className="fas fa-cogs")," "],
                        id="NavLink-1",
                        href="/page-1", 
                        active="exact",
                        style = {'color':TitleColor}), # Tab_Color[0]
            dbc.Tooltip(name_machine[0],
                        target="NavLink-1",
                        placement="right"),
            # Page 2
            dbc.NavLink([html.I(className="fas fa-hdd")," "],
                        id="NavLink-2",
                        href="/page-2", 
                        active="exact",
                        style = {'color':TitleColor}),
            dbc.Tooltip(name_machine[1],
                        target="NavLink-2",
                        placement="right"),
            # Page 3
            dbc.NavLink([html.I(className="fas fa-hdd")," "],
                        id="NavLink-3",
                        href="/page-3", 
                        active="exact",
                        style = {'color':TitleColor}),
            dbc.Tooltip(name_machine[2],
                        target="NavLink-3",
                        placement="right"),
            # Page 4
            dbc.NavLink([html.I(className="fas fa-hdd")," "],
                        id="NavLink-4",
                        href="/page-4", 
                        active="exact",
                        style = {'color':TitleColor}),
            dbc.Tooltip(name_machine[3],
                        target="NavLink-4",
                        placement="right"),
            # Page 5
            dbc.NavLink([html.I(className="fas fa-dolly-flatbed")," "],
                        id="NavLink-5",
                        href="/page-5", 
                        active="exact",
                        style = {'color':TitleColor}),
            dbc.Tooltip(name_machine[4],
                        target="NavLink-5",
                        placement="right"),
            # Page 6
            dbc.NavLink([html.I(className="fas fa-dolly-flatbed")," "],
                        id="NavLink-6",
                        href="/page-6", 
                        active="exact",
                        style = {'color':TitleColor}),
            dbc.Tooltip(name_machine[5],
                        target="NavLink-6",
                        placement="right"),
            # Page 7
            dbc.NavLink([html.I(className="fas fa-server")," "],
                        id="NavLink-7",
                        href="/page-7", 
                        active="exact",
                        style = {'color':TitleColor}),
            dbc.Tooltip(name_machine[6],
                        target="NavLink-7",
                        placement="right")
            ],
            vertical = True, pills = True, justified=True
            )
        ],
    style = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "7rem",
        "padding": "1rem 1rem",
        "background-color": SidebarColor,
        "color": TitleColor
        }
    )

content = html.Div(
    id = "page-content", 
    style = {
        "margin-left": "7rem",
        "margin-right": "0rem",
        "padding": "1rem 1rem",
        'background-color' : BackgroundColor
        }
    )

## Layout Function
def make_layout():
    update_layout = html.Div([
        dcc.Interval(
            id = 'interval-component',
            interval = 1000*Update_Interval, # in milliseconds
            n_intervals = 0
        ),
        dcc.Location(id="url"), 
        sidebar, 
        content], style={'background-color': BackgroundColor,
                         'min-height':'1000px'}) 
    return update_layout
        
        
app.layout = make_layout

# Run the function in another thread
executor = ThreadPoolExecutor(max_workers=1)
executor.submit(get_new_data_every)

if __name__ == '__main__': app.run_server(debug=False, use_reloader=False)

# %%
