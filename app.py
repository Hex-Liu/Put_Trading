import numpy as np
import pickle
import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import plotly.figure_factory as ff

### - Initialization Data
Project_Dir = '/Users/macbook/Documents/Columbia/Columbia MSOR/Fall 18/4573 Finc Models/Put_Trading'
Processed_Data_Dir = Project_Dir + r"/Processed_Data"

dt_optn = pickle.load(open(Processed_Data_Dir + '/Dash_Sim_Result.p', "rb"))
dt_ni = pickle.load(open(Processed_Data_Dir + '/Dash_Sim_Ni.p', "rb"))
dt_optn.index.name = 'idx'
dt_optn = dt_optn.reset_index()
### -Dash APP
external_stylesheets = ["https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

col_ds_tbl = ['idx', 'Strike', 'Ask_p', 'Mean_Ret', 'Pr_Neg', 'VaR_5Pct']

app.config['suppress_callback_exceptions'] = True
dt_d2m_matr = dt_optn.loc[:, ['Fig', 'Maturity', 'D2M']]
dt_d2m_matr.drop_duplicates(inplace=True)
dt_d2m_matr['str_4ratio'] = (
        dt_d2m_matr['D2M'].dt.days.astype(str) + ' Days, ' + dt_d2m_matr['Maturity'].dt.date.astype(str))
dict_optn_tbl_round = {'Strike': 1, 'Ask_p': 2, 'Mean_Ret': 3, 'Pr_Neg': 3, 'VaR_5Pct': 2}


def serve_layout():
    return html.Div([
        dcc.Tabs(id="tabs", value='tab-1', children=[
            dcc.Tab(label='Customization', value='tab-1'),
            dcc.Tab(label='Recommendation', value='tab-2'),
        ]),
        html.Div(id='tabs-content')
    ])


app.layout = serve_layout


# -Call back
@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])
def render_content(tab):
    ls_fig = dt_optn.Fig.unique()
    init_fig = ls_fig[0]
    init_optn = dt_optn.loc[dt_optn.Fig == init_fig, :]
    init_ls_d2m = init_optn['D2M'].dt.days.unique()
    dt = init_optn.loc[init_optn.D2M == pd.Timedelta(init_ls_d2m[0], 'D'), col_ds_tbl]
    dt = dt.round(dict_optn_tbl_round)
    if tab == 'tab-1':
        return html.Div([
            dcc.Dropdown(
                id='fig_dropdown',
                options=[{'label': k, 'value': k} for k in ls_fig],
                value=init_fig
            ),

            html.Hr(),

            dcc.RadioItems(
                id='D2M_RadioItems',
                options=[{'label': dt_d2m_matr.loc[idx, 'str_4ratio'], 'value': dt_d2m_matr.loc[idx, 'D2M'].days}
                         for idx in dt_d2m_matr.loc[dt_d2m_matr.Fig == init_fig].index]
            ),

            html.Hr(),

            dash_table.DataTable(
                id='Option_table',
                columns=[{'name': i, 'id': i, 'deletable': False} for i in dt.columns],
                data=dt.to_dict("rows"),
                editable=False,
                filtering=False,
                sorting=True,
                sorting_type="multi",
                row_selectable="multi",
                row_deletable=False,
                selected_rows=[],
            ),
            html.Div(id='test'),
            html.Div(id='dist_plot')
        ])
    elif tab == 'tab-2':
        return html.Div([
            html.Div([
                dash_table.DataTable(
                    id='Recmd_table',
                    columns=[{'name': i, 'id': i, 'deletable': False} for i in dt.columns],
                    data=dt_optn.sort_values('Mean_Ret', ascending=False).head(20) \
                        .round(dict_optn_tbl_round).to_dict("rows"),
                    editable=False,
                    filtering=False,
                    sorting=True,
                    sorting_type="multi",
                    row_selectable="multi",
                    row_deletable=False,
                    selected_rows=list(range(5)),
                ),
                html.Div(id='dist_plot_rec')
            ])
        ])


@app.callback(
    Output('D2M_RadioItems', 'options'),
    [Input('fig_dropdown', 'value')])
def set_cities_options(fig):
    return [{'label': dt_d2m_matr.loc[idx, 'str_4ratio'], 'value': dt_d2m_matr.loc[idx, 'D2M'].days}
            for idx in dt_d2m_matr.loc[dt_d2m_matr.Fig == fig].index]


@app.callback(
    Output('D2M_RadioItems', 'value'),
    [Input('D2M_RadioItems', 'options')])
def set_cities_options(options):
    return options[0]['value']


@app.callback(
    Output('Option_table', 'data'),
    [Input('fig_dropdown', 'value'),
     Input('D2M_RadioItems', 'value')])
def set_cities_options(fig, d2m):
    dt = dt_optn.loc[(dt_optn.D2M == pd.Timedelta(d2m, 'D')) & (dt_optn.Fig == fig), col_ds_tbl]
    dt = dt.round(dict_optn_tbl_round)
    return dt.to_dict("rows")


@app.callback(
    Output('Option_table', 'selected_rows'),
    [Input('Option_table', 'data')])
def set_tbl_selected(data):
    data = pd.DataFrame(data)
    return [data.Mean_Ret.values.argmax()]


@app.callback(
    Output('dist_plot', 'children'),
    [Input('Option_table', 'selected_rows'),
     Input('Option_table', 'data'),
     Input('Option_table', 'columns')])
def set_display_children(slct_row, data, columns):
    dt_tmp = pd.DataFrame(data, columns=[c['id'] for c in columns])
    idx = dt_tmp.iloc[list(slct_row)]['idx']
    # sim_series=dt_ni[idx]

    fig = ff.create_distplot([dt_ni[i] for i in idx], [str(i) for i in idx], bin_size=.5, show_rug=False,
                             show_curve=False)
    return dcc.Graph(
        figure=fig,
        id='my-graph'
    )

@app.callback(
    Output('dist_plot_rec', 'children'),
    [Input('Recmd_table', 'selected_rows'),
     Input('Recmd_table', 'data'),
     Input('Recmd_table', 'columns')])
def set_display_children(slct_row, data, columns):
    dt_tmp = pd.DataFrame(data, columns=[c['id'] for c in columns])
    idx = dt_tmp.iloc[list(slct_row)]['idx']
    # sim_series=dt_ni[idx]

    fig = ff.create_distplot([dt_ni[i] for i in idx], [str(i) for i in idx], bin_size=.5, show_rug=False,
                             show_curve=False)
    return dcc.Graph(
        figure=fig,
        id='my-graph_rec'
    )

if __name__ == '__main__':
    app.run_server(debug=True)
