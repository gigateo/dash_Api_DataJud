from dash import html, dcc, callback, Output, Input, State
import plotly.graph_objects as go
import plotly.express as px
from dash_bootstrap_templates import ThemeSwitchAIO
import pandas as pd
import datetime as dt
import warnings
warnings.filterwarnings('ignore')

#Traz os dados da classe APP
from app import *

#Themas Pre-definidos
url_theme1 = dbc.themes.FLATLY
url_theme2 = dbc.themes.VAPOR

template_theme1 = 'flatly'
template_theme2 = 'vapor'

#Obtem os dados e faz tratamento inicial
##Coloque o caminho do arquivo gerado pelo script: app_pub_datajud.py
df = pd.read_excel('../Conhec_Api_Pub_Datajud/dados/Procs_Conhecimento_tjap.xlsx')
df['anoAjuizamento'] = pd.to_numeric(df['dataAjuizamento'].apply(lambda x: x.year))

#df['dataAjuizamento'] = df['dataAjuizamento'].apply(lambda x: dt.datetime.strptime(x,'%Y-%m-%d') if type(x)==str else pd.NaT)
df['dataAjuizamento'] = pd.to_datetime(df['dataAjuizamento'], errors="coerce")

#DF que será disponibilizado para download
df_org = df.copy(deep=True)

#Inicia com as 10 maiores ocorrencias
df_Classes_Assuntos = None

#Lista de orgaos julgadores, Classes e Assuntos para DropDown
orgaos_Julgadores = [{'label': x, 'value': x} for x in df.orgaoJulgador.unique()]
classes = [{'label': x, 'value': x} for x in df.classe.unique()]
assuntos = [{'label': x, 'value': x} for x in df.assuntos.unique()]



# Layout #
#content = html.Div(id="page-content")

app.layout = dbc.Container([
    #Barra de menus e filtros
    dbc.Row([
        dbc.Col([
            html.Img(src='./assets/tjap-logo-ouro-2023.png', width='100%', style={'padding-top': '5px'}),
            html.H5('Corregedoria-Geral de Justiça', style={'padding-top': '10px'}),

            html.Hr(),
            ThemeSwitchAIO(aio_id='theme', themes=[url_theme1, url_theme2]),
            html.Hr(),

            html.H4('Filtros Aplicáveis', style={'text-align': 'center'}),

            html.H5('Orgão Julgador', style={'padding-top': '5px'}),
            dcc.Dropdown(
                id='oJ',
                value='', #[orgao['label'] for orgao in orgaos_Julgadores[:1]],
                multi=True,
                placeholder="Selecione um ou mais",
                options= orgaos_Julgadores
                ,style={'font-size' : '10px'}
            ),

            html.H5('Selecione o Periodo', style={'padding-top': '10px'}),
            html.Div([
                dcc.DatePickerRange(
                            id="calendario",
                            min_date_allowed=str(min(df["dataAjuizamento"])),
                            max_date_allowed=str(max(df["dataAjuizamento"])),
                            end_date=str(max(df["dataAjuizamento"])),
                            start_date=str(min(df["dataAjuizamento"])),
                            display_format='DD/MM/YYYY',
                            clearable=False,
                            #with_portal=True,
                            start_date_placeholder_text='Data ini',
                            end_date_placeholder_text='Data Fim',                            
                        ),
                    ], style={'font-size' : '8px'}),

            html.Div([
                        html.Button("Download em Excel", id="btn_xlsx", style={'margin-top': '25px'}),
                        dcc.Download(id="download-dataframe-xlsx"),
                    ]),
            
        ], sm=6, md=2),

        #Coluna2 com 75% da tela
        dbc.Col([

            #Linha1
            dbc.Row([
                dbc.Col([
                    html.H5('Pré-Visualização dos Processos Filtrados', style={'padding-top': '5px'}),
                    html.Div(id='df_preview', style={"maxHeight": "38vh", "overflow": "scroll", 'font-size': '12px'},),
                     
                ], md=5),

                dbc.Col([
                    dcc.Graph(id='bar_Graph_Oj') #Ajuizados por ano
                ], md=7)  
            ]),

            #Linha2
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='line_Graph_Hist_Ajuiza'),
                    ], md=4),  

                dbc.Col([
                    dcc.Loading(dcc.Graph(id='bar_Graph_Animada'), type='cube'),
                    #dcc.Graph(id='scatter_Graph_Classes'),
                    ], md=4),   

                dbc.Col([
                    dcc.Graph(id='solar_Graph_Classes', style={'align': 'left'})
                    ], md=4),     #4 /12 unidades disponiveis para essa linha          
            ]),
                
        ], sm=6, md=10),

    ])

], fluid=True,)

## Fim do Layout

## ======== CallBacks ============
#Exibe o grafico do total de processos por ano e ajusta o tema ao grafico
@app.callback(
    Output('bar_Graph_Oj', 'figure'),
    Input('oJ', 'value'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
    Input('calendario', 'start_date'),
    Input('calendario', 'end_date'),
)
def orgaosJulg(orgJulg, toogle, start_date, end_date): ##... parametros Na funcao
    template = template_theme1 if toogle else template_theme2
    global df_org

    if not orgJulg:
        df_org = df
    
        if not start_date and not end_date:

            fig = px.bar(df_org['anoAjuizamento'].value_counts(),  text_auto=True,
                    labels={"anoAjuizamento": "Ano de Ajuizamento", "value": "Total de processos"},
                    title="Total de processos Ajuizados por Ano", 
                    template=template).update_layout(showlegend=False)
            return fig
        
        elif start_date and end_date:
            ##Fonte: https://dash-example-index.herokuapp.com/pietabs
            df_org = df_org[df_org['dataAjuizamento'].between(start_date, end_date)]

            fig = px.bar(df_org['anoAjuizamento'].value_counts(),  text_auto=True,
                    labels={"anoAjuizamento": "Ano de Ajuizamento", "value": "Total de processos"},
                    title="Total de processos Ajuizados por Ano", 
                    template=template).update_layout(showlegend=False)
            return fig

    else:
        
        if not start_date and not end_date:
            df_filtrado = df.copy(deep=True)
            mask = df_filtrado['orgaoJulgador'].isin(orgJulg)
            df_org = df_filtrado[mask]

            fig = px.bar(df_org['anoAjuizamento'].value_counts(),  text_auto=True,
                        labels={"anoAjuizamento": "Ano de Ajuizamento", "value": "Total de processos"},
                        title="Total de processos Ajuizados por Ano", 
                        template=template).update_layout(showlegend=False)
            return fig
        
        elif start_date and end_date:
            df_filtrado = df.copy(deep=True)
            mask = df_filtrado['orgaoJulgador'].isin(orgJulg)
            df_org = df_filtrado[mask]

            ##Fonte: https://dash-example-index.herokuapp.com/pietabs
            df_org = df_org[df_org['dataAjuizamento'].between(start_date, end_date)]

            fig = px.bar(df_org['anoAjuizamento'].value_counts(),  text_auto=True,
                    labels={"anoAjuizamento": "Ano de Ajuizamento", "value": "Total de processos"},
                    title="Total de processos Ajuizados por Ano", 
                    template=template).update_layout(showlegend=False)
            return fig
    

#Exibe o grafico do Ranking das Top 5 Classes e seus assuntos
@app.callback(
    Output('solar_Graph_Classes', 'figure'),
    Input('oJ', 'value'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
    Input('calendario', 'start_date'),
    Input('calendario', 'end_date'),
)
def classseAssuntos(orgJulg, toogle, start_date, end_date):
    template = template_theme1 if toogle else template_theme2
    global df_Classes_Assuntos

    if not orgJulg:
        if not start_date and not end_date:
            #Inicia com as 10 maiores ocorrencias
            df_Classes_Assuntos = df[['orgaoJulgador', 'classe', 'assuntos']].value_counts().reset_index().rename({'count' : 'total'}, axis=1)[:20]

            df_Classes = pd.read_excel('./assets/parametrizacao-classes-todos-ramos-2023-12.xlsx', skiprows=1, sheet_name='Classes Datajud')
            df_Assuntos = pd.read_csv('./assets/assuntos_CNJ.csv')

            #Juntando com os nomes para exibir no grafico
            df_Classes_Assuntos = pd.merge(df_Classes_Assuntos, df_Assuntos, how="left", left_on='assuntos', right_on='cod')
            df_Classes_Assuntos = pd.merge(df_Classes_Assuntos, df_Classes, how="left", left_on='classe', right_on='cod')

            fig = px.sunburst(df_Classes_Assuntos, path=['classe', 'assuntos'],  
                            values='total',
                            hover_data=['desc_classe', 'desc_assunto'], 
                            template=template).update_layout(showlegend=False, margin = dict(t=10, l=10, r=10, b=10)).update_traces(hovertemplate='<br>Valor Total: %{value}<br>Classe: %{customdata[0]}<br>Assunto: %{customdata[1]}</br>')
            return fig
        
        elif start_date and end_date:
            df_filtrado = df.copy(deep=True)
            df_Classes_Assuntos = df_filtrado[df_filtrado['dataAjuizamento'].between(start_date, end_date)]
            df_Classes_Assuntos = df_Classes_Assuntos[['orgaoJulgador', 'classe', 'assuntos']].value_counts().reset_index().rename({'count' : 'total'}, axis=1)[:20]

            df_Classes = pd.read_excel('./assets/parametrizacao-classes-todos-ramos-2023-12.xlsx', skiprows=1, sheet_name='Classes Datajud')
            df_Assuntos = pd.read_csv('./assets/assuntos_CNJ.csv')

            #Juntando com os nomes para exibir no grafico
            df_Classes_Assuntos = pd.merge(df_Classes_Assuntos, df_Assuntos, how="left", left_on='assuntos', right_on='cod')
            df_Classes_Assuntos = pd.merge(df_Classes_Assuntos, df_Classes, how="left", left_on='classe', right_on='cod')

            fig = px.sunburst(df_Classes_Assuntos, path=['classe', 'assuntos'],  
                            values='total',
                            hover_data=['desc_classe', 'desc_assunto'], 
                            template=template).update_layout(showlegend=False, margin = dict(t=10, l=10, r=10, b=10)).update_traces(hovertemplate='<br>Valor Total: %{value}<br>Classe: %{customdata[0]}<br>Assunto: %{customdata[1]}</br>')
            return fig

    else:
        if not start_date and not end_date:    
            df_filtrado = df.copy(deep=True)
            
            mask = df_filtrado['orgaoJulgador'].isin(orgJulg)
            df_Classes_Assuntos = df_filtrado[mask]

            df_Classes_Assuntos = df_Classes_Assuntos[['orgaoJulgador', 'classe', 'assuntos']].value_counts().reset_index().rename({'count' : 'total'}, axis=1)[:20]
            
            df_Assuntos = pd.read_csv('./assets/assuntos_CNJ.csv')
            df_Classes = pd.read_excel('./assets/parametrizacao-classes-todos-ramos-2023-12.xlsx', skiprows=1, sheet_name='Classes Datajud')

            #Juntando com os nomes para exibir no grafico
            df_Classes_Assuntos = pd.merge(df_Classes_Assuntos, df_Assuntos, how="left", left_on='assuntos', right_on='cod')
            df_Classes_Assuntos = pd.merge(df_Classes_Assuntos, df_Classes, how="left", left_on='classe', right_on='cod')

            fig = px.sunburst(df_Classes_Assuntos, path=['classe', 'assuntos'],
                        values='total',
                        hover_data=['desc_classe', 'desc_assunto'],  
                        template=template).update_layout(showlegend=False, margin = dict(t=10, l=10, r=10, b=10)).update_traces(hovertemplate='<br>Valor Total: %{value}<br>Classe: %{customdata[0]}<br>Assunto: %{customdata[1]}</br>')
            
            return fig
        
        elif start_date and end_date:
            df_filtrado = df.copy(deep=True)
            df_filtrado = df_filtrado[df_filtrado['dataAjuizamento'].between(start_date, end_date)]

            mask = df_filtrado['orgaoJulgador'].isin(orgJulg)
            df_Classes_Assuntos = df_filtrado[mask]

            df_Classes_Assuntos = df_Classes_Assuntos[['orgaoJulgador', 'classe', 'assuntos']].value_counts().reset_index().rename({'count' : 'total'}, axis=1)[:20]
            
            df_Assuntos = pd.read_csv('./assets/assuntos_CNJ.csv')
            df_Classes = pd.read_excel('./assets/parametrizacao-classes-todos-ramos-2023-12.xlsx', skiprows=1, sheet_name='Classes Datajud')

            #Juntando com os nomes para exibir no grafico
            df_Classes_Assuntos = pd.merge(df_Classes_Assuntos, df_Assuntos, how="left", left_on='assuntos', right_on='cod')
            df_Classes_Assuntos = pd.merge(df_Classes_Assuntos, df_Classes, how="left", left_on='classe', right_on='cod')

            fig = px.sunburst(df_Classes_Assuntos, path=['classe', 'assuntos'],
                        values='total',
                        hover_data=['desc_classe', 'desc_assunto'],  
                        template=template).update_layout(showlegend=False, margin = dict(t=10, l=10, r=10, b=10)).update_traces(hovertemplate='<br>Valor Total: %{value}<br>Classe: %{customdata[0]}<br>Assunto: %{customdata[1]}</br>')
            
            return fig


### Série Histórica dos ultimos 5 anos 
@app.callback(
    Output('line_Graph_Hist_Ajuiza', 'figure'),
    Input('oJ', 'value'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
    #Input("selection", "value"),
)
def df_Hist(orgJulg, toogle):
    template = template_theme1 if toogle else template_theme2
    global df_org

    if not orgJulg:
        df_org = df
        #Pega os ultimos 5 anos gerais
        ano = df_org['anoAjuizamento'].sort_values(ascending=False).unique()[:5].tolist()
        mask = df_org['anoAjuizamento'].isin(ano)
        df_hist = df_org[mask]

        df_hist = df_hist.groupby(['anoAjuizamento', 'grau']).size().to_frame('total').reset_index()

        fig = px.line(data_frame=df_hist, x='anoAjuizamento', y='total', color='grau',        
                  title="Série Histórica de Ajuizamentos nos últimos 5 anos", markers=True,
                  template=template).update_layout(showlegend=True)
        return fig

    else:
        df_filtrado = df.copy(deep=True)
        mask = df_filtrado['orgaoJulgador'].isin(orgJulg)
        df_filtrado = df_filtrado[mask]
        
        ano = df_filtrado['anoAjuizamento'].sort_values(ascending=False).unique()[:5].tolist()
        mask = df_filtrado['anoAjuizamento'].isin(ano)
        df_hist = df_filtrado[mask]

        df_hist = df_hist.groupby(['anoAjuizamento']).size().to_frame('total').reset_index()

        fig = px.line(data_frame=df_hist, x='anoAjuizamento',  y='total',
                  title="Série Histórica de Ajuizamentos nos últimos 5 anos", markers=True,
                  template=template).update_layout(showlegend=False)
        return fig


## Altera a tabela de pre-visualizacao 
@app.callback(
    Output("df_preview", "children"),
    Input("oJ", "value"),
)
def df_Preview(orgJulg):
    if not orgJulg:
        return dbc.Table.from_dataframe(df[['numeroProcesso', 'orgaoJulgador', 'classe', 'assuntos']][:28], striped = True, bordered = True, hover = True)    
    else:
        mask = df_org['orgaoJulgador'].isin(orgJulg)
        df_Resumo = df_org[mask]
        return dbc.Table.from_dataframe(df_Resumo[['numeroProcesso', 'orgaoJulgador', 'classe', 'assuntos']][:28], striped = True, bordered = True, hover = True)


@app.callback(
    Output("bar_Graph_Animada", "figure"), 
    Input("oJ", "value"),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value')
)
def df_Anim(orgJulg, toogle):
    template = template_theme1 if toogle else template_theme2
    global df_org

    if not orgJulg:
        df_org = df
        #Pega os ultimos 5 anos gerais
        ano = df_org['anoAjuizamento'].sort_values(ascending=False).unique()[:10].tolist()
        mask = df_org['anoAjuizamento'].isin(ano)
        df_hist = df_org[mask]

        df_hist = df_hist.groupby(['anoAjuizamento', 'grau', 'orgaoJulgador']).size().to_frame('total').reset_index()

        fig = px.bar(data_frame=df_hist, x='grau', y='total', color='grau', 
                     animation_frame='anoAjuizamento', animation_group='orgaoJulgador',         
                  title="Evolução dos Ajuizamentos  nos últimos 10 anos",
                  template=template).update_layout(showlegend=True)
        return fig

    else:
        df_filtrado = df.copy(deep=True)
        mask = df_filtrado['orgaoJulgador'].isin(orgJulg)
        df_filtrado = df_filtrado[mask]
        
        ano = df_filtrado['anoAjuizamento'].sort_values(ascending=False).unique()[:10].tolist()
        mask = df_filtrado['anoAjuizamento'].isin(ano)
        df_hist = df_filtrado[mask]

        df_hist = df_hist.groupby(['anoAjuizamento', 'grau', 'orgaoJulgador']).size().to_frame('total').reset_index()

        fig = px.bar(data_frame=df_hist, x='grau', y='total', color='grau',
                     animation_frame='anoAjuizamento', animation_group='orgaoJulgador',
                  title="Evolução dos Ajuizamentos  nos últimos 10 anos", 
                  template=template).update_layout(showlegend=False)
        return fig



##Botao de Download no formato Excel
@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("btn_xlsx", "n_clicks"),
    prevent_initial_call=True,
)
def press_Download(n_clicks):
    return dcc.send_data_frame(df_org.to_excel, "OrgaosJulgadoresFiltrados.xlsx")


#Rodar o servidor
if __name__ == '__main__':
    app.run_server()