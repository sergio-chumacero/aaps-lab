import ipywidgets as widgets
import os
from os.path import join, exists, dirname
import json
import requests
from requests.exceptions import ConnectionError
import qgrid
import pandas as pd
from pandas import ExcelWriter
from datetime import datetime
import docx
import base64
from docxtpl import DocxTemplate

home_dir = join(os.environ['USERPROFILE'],'aapslab')
data_path = join(home_dir,'datos')

tpl_path = join(home_dir,'.lib','templates')
out_path = join(data_path,'reportes')

profile_path = join(home_dir,'.profile','profile.json')

coop_xl_path = join(data_path,'poas_coop.xlsx')
muni_xl_path = join(data_path,'poas_muni.xlsx')
epsas_xl_path = join(data_path,'epsas.xlsx')

coop_tpl_path = join(tpl_path,'coop_poa_tpl.docx')
muni_tpl_path = join(tpl_path,'muni_poa_tpl.docx')

server_base_url = 'http://aaps-lab.ml'
available_datasets = ['EPSAS','POAS']

class GenerateReportWidget(widgets.VBox):
    def __init__(self, **kwargs):
        def text_to_float(x):
            return float(x.replace(',',''))
        def float_to_text(x):
            return "{:,.2f}".format(x)

        if exists(profile_path):
            with open(profile_path,'r') as f:
                profile_json = json.load(f)
        else:
            profile_json = {}

        sheet_names = ['general','ingresos','gastos','inversiones']
        month_names = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        month_num_to_name = {k+1:v for k,v in zip(range(12), month_names)}
        prof_name_to_denom = {'Ingeniero':'Ing.', 'Económico':'Lic.',}
        column_name_to_verbose = dict(
            epsa='EPSA',
            year='AÑO',
            order='ÓRDEN (REPROG.)',
            in_op_ap='SERVICIOS DE AGUA POTABLE',
            in_op_alc='SERVICIOS DE ALCANTARILLADO',
            in_op_alc_pozo='SERVICIOS DE ALCANTARILLADO DE POZO',
            in_op_otros='OTROS INGRESOS OPERATIVOS',
            in_financieros='INGRESOS FINANCIEROS',
            in_no_op_otros='OTROS INGRESOS NO OPERATIVOS',
            gastos_empleados_permanentes='EMPLEADOS PERMANENTES',
            gastos_empleados_no_permanentes='EMPLEADOS NO PERMANENTES',
            gastos_prevision_social='PREVISIÓN SOCIAL',
            gastos_servicio_no_personales='SERVICIOS NO PERSONALES',
            gastos_materiales='MATERIALES Y SUMINISTROS',
            gastos_activos='ACTIVOS REALES',
            gastos_deuda_publica='SERVICIOS DE LA DEUDA PÚBLICA',
            gastos_transferencias='TRANSFERENCIAS',
            gastos_impuesto='IMPUESTOS, REGALÍAS Y TASAS',
            gastos_otros='OTROS GASTOS',
            costos_operacion='COSTOS DE OPERACIÓN',
            costos_mantenimiento='COSTOS DE MANTENIMIENTO',
            gastos_administrativos='GASTOS ADMINISTRATIVOS',
            gastos_comerciales='GASTOS COMERCIALES',
            gastos_financieros='GASTOS FINANCIEROS',
            inv_infraestructura_ap='CONSTRUCCIÓN DE INFRAESTRUCTURA SISTEMA AGUA POTABLE',
            inv_infraestructura_alc='CONSTRUCCIÓN DE INFRAESTRUCTURA SISTEMA DE ALCANTARILLADO',
            inv_equipo='ADQUISICIÓN DE MAQUINARIA Y EQUIPO',
            inv_diseno_estudio='DISEÑO Y ESTUDIOS DE PROYECTOS',
            inv_otros='OTROS',
        )

        ant_par_2_epsas = [
            'EPSAS','SAGUAPAC','COSMOL','ELAPAS','SEMAPA',
            'SELA','COATRI','CAPAG','AAPOS','COSAALT',
            'EMAPYC','COSPHUL','COSCHAL','COOPAGUAS','COSPAIL',
            'COOPLAN','EMAAB','LA GUARDIA','COOPAPPI','COSMIN',
            'EMSABAV','COSPAS','SEAPAS','COSAP','COOPLIM',
            'MANCHACO','COSEPW',
        ]

        report_number = widgets.BoundedIntText(
            value= profile_json.get('last_report_num',0) + 1,
            min=0, max=999, step=1,
            description='Número de reporte:',
            tooltip='entre 0 y 999',
            layout=widgets.Layout(width='50%',),
            style={'description_width': 'initial'},
        )
        name_text = widgets.Text(
            value = profile_json.get('name'),
            placeholder='Nombre del autor del documento',
            description='Nombre:',
            layout=widgets.Layout(width='50%',),
        )
        specialty_text = widgets.Text(
            value = profile_json.get('specialty'),
            placeholder='Especialidad del profesional',
            description='Especialidad:',
            layout=widgets.Layout(width='50%',),
        )
        qualification_type = widgets.ToggleButtons(
            value=profile_json.get('prof'),
            options=['Ingeniero', 'Económico',],
            description='Profesión:',
            button_style='info',
            tooltips=['Profesional Ingeniero', 'Profesional Económico',],
        )
        generate_button = widgets.Button(
            description='Generar Reporte',
            button_style='success',
            tooltip='Generar Reporte',
            icon='file-text',
            layout=widgets.Layout(width='300px',height='50px',font_size='20px'),
        )
        save_profile_button = widgets.Button(
            description='Guardar Perfil',
            button_style='info',
            tooltip='Generar Reporte',
            icon='save',
        )
        type_toggle = widgets.ToggleButtons(
            options=['Cooperativas', 'Municipales',],
            value = None,
            description='Tipo de EPSA:',
            disabled=False,
            button_style='info',
            tooltips=['Cooperativas', 'EPSAS Municipales',],
        )
        epsa_dropdown = widgets.Dropdown(
            options=[],
            value=None,
            description='EPSA:',
            disabled=False,
            layout = widgets.Layout(width='50%', display='none'),
        )
        year_dropdown = widgets.Dropdown(
            options=[],
            value=None,
            description='Año:',
            disabled=False,
            layout = widgets.Layout(display='none', width='50%'),
        )
        order_dropdown = widgets.Dropdown(
            options=[],
            value=None,
            description='Orden (reprog.):',
            disabled=False,
            layout = widgets.Layout(display='none', width='50%'),
            style={'description_width': '200'},
        )
        generate_random_button = widgets.Button(
            description='Generar Aleatorio',
            button_style='info',
            tooltip='Generar Reporte con datos aleatorios',
            icon='file-text',
            layout=widgets.Layout(width='300px',height='50px',font_size='20px', display='none'),
        ) 
        date_picker = widgets.DatePicker(
            value = datetime.now(),
            description='Fecha:',
            disabled=False
        )

        in_op_text = widgets.Text(
            value=None,
            description='Operativos (Bs.):',
            disabled=True,
            layout=widgets.Layout(width='300px'),
            style={'description_width': '115px'},
        )
        in_no_op_text = widgets.Text(
            value=None,
            description='No Operativos (Bs.):',
            disabled=True,
            layout=widgets.Layout(width='300px'),
            style={'description_width': '115px'},
        )
        in_op_percentage = widgets.HTML()
        in_no_op_percentage = widgets.HTML()
        serv_pers_percentage = widgets.HTML()

        in_total_text = widgets.Text(
            value=None,
            description='Totales (Bs.):',
            disabled=True,
            layout=widgets.Layout(width='300px'),
            style={'description_width': '115px'},
        ) 
        serv_pers_text = widgets.Text(
            value=None,
            description='Servicios Personales (Bs.):',
            disabled=True,
            layout=widgets.Layout(width='300px'),
            style={'description_width': '155px'},
        )
        total_gastos_text = widgets.Text(
            value=None,
            description='Gastos Totales (Bs.):',
            disabled=True,
            layout=widgets.Layout(width='300px'),
            style={'description_width': '155px'},
        )

        total_inv_text = widgets.Text(
            value=None,
            description='Total (Bs.):',
            disabled=True,
            layout=widgets.Layout(width='300px'),
            style={'description_width': '100px'},
        )

        city_dropdown = widgets.Dropdown(
            options=['La Paz', 'Santa Cruz', 'Cochabamba'],
            value=profile_json.get('city'),
            description='Ciudad:',
            disabled=False,
            style={'description_width':'initial'},
        )

        info_button = widgets.ToggleButton(
            button_style='info',
            icon='info-circle',
            tooltip='Ayuda acerca de la tabla interactiva',
            layout=widgets.Layout(width='37px',height='37px')
        )

        table_help = widgets.HTML(
            layout=widgets.Layout(width='95%')
        )
        help_html = widgets.HTML()

        help_grid = qgrid.QGridWidget(df=pd.DataFrame())
        active_tab = widgets.Text(value='general')

        out_name_text = widgets.Text(
            value=f'reporte_poa',
            description='Nombre del reporte:',
            disabled=False,
            tooltip='Nombre del archivo que será generado. Por ejemplo: reporte_poa.docx',
            layout=widgets.Layout(width='400px'),
            style={'description_width': '165px'},
        )
        out_name_help = widgets.HTML(value=f'{out_path}\\<b>{out_name_text.value}</b>.docx')

        ingresos_text_box = widgets.Textarea(
            value='',
            placeholder='Análisis de Igresos. Será incluido en el reporte generado bajo la tabla de ingresos. Puedes dejarlo vacío y llenarlo directamente en el documento generado.',
            description='Análisis:',
            disabled=False,
            layout=widgets.Layout(display='none',width='100%'),
        )
        gastos_text_box = widgets.Textarea(
            value='',
            placeholder='Análisis de Gastos. Será incluido en el reporte generado bajo la tabla de gastos. Puedes dejarlo vacío y llenarlo directamente en el documento generado.',
            description='Análisis:',
            disabled=False,
            layout=widgets.Layout(display='none',width='100%'),
        )
        inversiones_text_box = widgets.Textarea(
            value='',
            placeholder='Análisis de Inversiones. Será incluido en el reporte generado bajo la tabla de inversiones. Puedes dejarlo vacío y llenarlo directamente en el documento generado.',
            description='Análisis:',
            disabled=False,
            layout=widgets.Layout(display='none',width='100%'),
        )

        def build_intro():
            num = report_number.value
            prof = prof_name_to_denom[qualification_type.value] if qualification_type.value else ''
            name = name_text.value
            specialty = specialty_text.value
            date = date_picker.value
            city = city_dropdown.value
            return f'''<div style="background-color: #ddffff;border-left: 6px solid #2196F3; padding: 0.01em 16px">
            INFORME AAPS/DER/INF/{num:03d}/{date.year}</br>
            {prof} {name.title()}</br>
            PROFESIONAL {prof.upper()} {specialty.upper()}</br>
            {city}, {date.day} de {month_num_to_name[date.month]} de {date.year}
            </div>'''

        intro_html = widgets.HTML(value=build_intro())
        intro_help_html = widgets.HTML()
        download_tag = widgets.HTML()

        def on_type_toggle_change(change):
            if change['new'] == 'Cooperativas':
                if exists(coop_xl_path):
                    help_html.value = ''
                    help_grid.df = pd.read_excel(coop_xl_path, sheet_name='general')
                    epsa_dropdown.options = list(help_grid.df.epsa)
                    generate_button.disabled = False
                    generate_random_button.layout.display = 'none'
                else:
                    help_grid.df = pd.DataFrame()
                    epsa_dropdown.options = []
                    epsa_dropdown.layout.display = 'none'
                    year_dropdown.options = []
                    year_dropdown.layout.display = 'none'
                    order_dropdown.options = []
                    order_dropdown.layout.display = 'none'
                    for grid in grids:
                        grid.df = pd.DataFrame()
                    generate_button.disabled = True
                    generate_random_button.layout.display = None
                    help_html.value = "Parece que no tienes datos de Cooperativas. Trata de descargar estos datos desde la aplicación <a href='http://localhost:8888/apps/Actualizar%20o%20Descargar%20Datos.ipynb?appmode_scroll=0' target='_blank'>Actualizar o Descargar Datos</a>. También puedes generar un reporte con datos aleatorios."    

            if change['new'] == 'Municipales':
                if exists(muni_xl_path):
                    help_html.value = ''
                    help_grid.df = pd.read_excel(muni_xl_path, sheet_name='general')
                    epsa_dropdown.options = list(help_grid.df.epsa)
                    generate_button.disabled = False
                    generate_random_button.layout.dislpay = 'none'
                else:
                    help_grid.df = pd.DataFrame()
                    epsa_dropdown.options = []
                    epsa_dropdown.layout.display = 'none'
                    year_dropdown.options = []
                    year_dropdown.layout.display = 'none'
                    order_dropdown.options = []
                    order_dropdown.layout.display = 'none'
                    for grid in grids:
                        grid.df = pd.DataFrame()
                    generate_button.disabled = True
                    generate_random_button.layout.display = None
                    help_html.value = "<font color='red'>Parece que no tienes datos de Cooperativas. Trata de descargar estos datos desde la aplicación 'Descargar Datos'. También puedes generar un reporte con datos aleatorios.</font>"

        def on_epsa_dropdown_change(change):
            if change['new']:
                epsa_dropdown.layout.display = None
                df = help_grid.df
        #         out_name_text.value = f'reporte_poa_{change["new"]}.docx'
                year_dropdown.options = []
                year_dropdown.options = list(df[df.epsa==change['new']].year)

        def on_year_dropdown_change(change):
            if change['new']:
                year_dropdown.layout.display = None
                df = help_grid.df
                out_name_text.value = f'reporte_poa_{epsa_dropdown.value}_{change["new"]}'
                order_dropdown.options = []
                order_dropdown.options = list(df[(df.epsa==epsa_dropdown.value)&(df.year==change['new'])].order)

        def on_order_dropdown_change(change):
            if change['new']:
                order_dropdown.layout.display = None

                xl_path = coop_xl_path if type_toggle.value == 'Cooperativas' else muni_xl_path

                sheets = [pd.read_excel(xl_path,sheet_name=sn) for sn in sheet_names]
                col_lists = [list(s) for s in sheets]
                df = pd.concat(sheets,axis=1)
                fdf = df[(df.epsa==epsa_dropdown.value)&(df.year==year_dropdown.value)&(df.order==change['new'])]
                dfs = [fdf[cl] for cl in col_lists]

                in_op_cols = ['in_op_ap','in_op_alc','in_op_alc_pozo','in_op_otros']
                in_no_op_cols = ['in_financieros','in_no_op_otros']

                in_op_val = dfs[1][in_op_cols].iloc[0].sum()
                in_no_op_val = dfs[1][in_no_op_cols].iloc[0].sum()
                in_total_val = dfs[1].iloc[0].sum()
                total_gastos_val = dfs[2].iloc[0].sum()
                total_inv_val = dfs[3].iloc[0].sum()

                widget_vals = [
                    (in_op_text,in_op_val,),
                    (in_no_op_text,in_no_op_val,),
                    (in_total_text,in_total_val,),
                    (total_gastos_text,total_gastos_val,),
                    (total_inv_text,total_inv_val,),
                ]

                in_op_percentage.value = '{:.2f}'.format(in_op_val / in_total_val * 100) + '%'
                in_no_op_percentage.value = '{:.2f}'.format(in_no_op_val / in_total_val * 100) + '%'

                if type_toggle.value == 'Municipales':
                    serv_pers_text.layout.display = None
                    serv_pers_cols = ['gastos_empleados_permanentes','gastos_empleados_no_permanentes','gastos_prevision_social',]
                    serv_pers_val = dfs[2][serv_pers_cols].iloc[0].sum()
                    widget_vals.append((serv_pers_text,serv_pers_val,))
                    serv_pers_percentage.value = '{:.2f}'.format(serv_pers_val/ total_gastos_val * 100) + '%'
                if type_toggle.value == 'Cooperativas':
                    serv_pers_text.layout.display = 'none'
                    serv_pers_percentage.value = ''

                for w,val in widget_vals:
                    w.value = float_to_text(val)

                for df in dfs:
                    df.columns = [column_name_to_verbose.get(cn,cn) for cn in list(df)]

                columns = ['Descripción','Valor (Bs.)']
                dfs = [df.transpose() for df in dfs]

                for df in dfs:
                    df.reset_index(level=0, inplace=True)
                    df.columns = columns
                for df,total in zip(dfs[1:],[in_total_val,total_gastos_val,total_inv_val]):
                    df['%'] = df['Valor (Bs.)'].apply(lambda x: '{:.2f}'.format(x / total * 100))
                    df['Valor (Bs.)']= df['Valor (Bs.)'].apply(float_to_text)

                for grid,df in zip(grids,dfs):
                    grid.df = df
                    
                
                for box in [ingresos_text_box, gastos_text_box, inversiones_text_box]:
                    box.value = ''
                    box.layout.display = None

        def on_save_profile_button_click(b):
            if profile_json:
                profile_json['name'] = name_text.value
                profile_json['prof'] = qualification_type.value
                profile_json['specialty'] = specialty_text.value
                profile_json['last_report_num'] = report_number.value
                profile_json['city'] = city_dropdown.value

                with open(profile_path,'w') as f:
                    json.dump(profile_json,f)

                intro_help_html.value = 'Perfil guardado!'

        def on_generate_button_click(b,random=False):
            if not type_toggle.value:
                help_html.value = '<font color="red">Porfavor escoge el tipo de reporte (cooperativa o EPSA municipal).</font>'
                return

            if type_toggle.value == 'Cooperativas':
                if not exists(coop_tpl_path):
                    help_html.value = '<font color="red">No se encontró el modelo base de POA para cooperativas.</font>'
                    return
                tpl_path = coop_tpl_path
                is_coop, is_muni = True, False

            if type_toggle.value == 'Municipales':
                if not exists(muni_tpl_path):
                    help_html.value = '<font color="red">No se encontró el modelo base de POA para EPSAs municipales.</font>'
                    return
                tpl_path = muni_tpl_path
                is_coop, is_muni = False, True

            doc = DocxTemplate(tpl_path)

            if not random:
                income_data, expenses_data, investments_data = [grids[i+1].get_changed_df()['Valor (Bs.)'].apply(text_to_float) for i in range(3)]
                income_p_data, expenses_p_data, investments_p_data = [grids[i+1].get_changed_df()['%'].apply(text_to_float) for i in range(3)]

            # Intro
            date = date_picker.value
            prof = qualification_type.value if qualification_type.value else ''
            specialty = specialty_text.value.upper() if specialty_text.value else ''
            denom = prof_name_to_denom[prof] if prof else ''
            name = name_text.value.title() if name_text.value else ''

            
            epsa =  epsa_dropdown.value
            ant_2_par = ''
            if epsa in ant_par_2_epsas:
                ant_2_par = f'Manual de Seguimiento de cumplimiento de obligaciones compromisos y procedimientos a seguir de la EPSA {epsa}.'
            else:
                ant_2_par = 'Mediante la RAR SISAB Nº 124/2007 del 12 de junio del 2007 se aprueba la guía de solicitud de Licencias y Registros, Manual de Seguimiento de Licencias y Manual para la elaboración del Plan de Desarrollo Quinquenal para licencias.'
            
            context = dict(
                prof=prof.upper(),
                day=str(date.day),
                month=month_num_to_name[date.month],
                year=str(date.year),
                denom=denom,
                name=name,
                report_num=f'{report_number.value:03d}',
                city=city_dropdown.value,
                specialty=specialty,
                antecedente2=ant_2_par,
                antecedente3='Tercer párrafo de antecedentes.',
                antecedente4='Cuarto párrafo de antecedentes.',
                cumplimiento_paragraphs= [
                    'Primer párrafo de cumplimiento.',
                    'Segundo párrafo de cumplimiento.',
                    'Tercer párrafo de cumplimiento.'
                ],
                ingresos_paragraphs=ingresos_text_box.value.split('\n\n'),
                gastos_paragraphs=gastos_text_box.value.split('\n\n'),
                inversiones_paragraphs=inversiones_text_box.value.split('\n\n'),
            )
            
            for i,val,p_val in zip(range(6),income_data.apply(float_to_text),income_p_data.apply(float_to_text)):
                context[f'in_{i+1}'] = val
                context[f'in_{i+1}_p'] = p_val
            
            in_labels_indexes = [
                ('in_op',[0,1,2,3,],),
                ('in_op_serv',[0,1,],),
                ('in_op_otros',[2,3,],),
                ('in_no_op',[4,5,],),
                ('in_total',[0,1,2,3,4,5,],),
            ]
            
            for label,indexes in in_labels_indexes:
                context[label] = float_to_text(income_data[indexes].sum())
                context[f'{label}_p'] = float_to_text(income_p_data[indexes].sum())
            
            if is_coop:
                num_rows = 5
                out_labels_indexes = [
                    ('out_total',[0,1,2,3,4],),
                    ('costos',[0,1],),
                    ('gastos',[2,3,4],),
                ]
            if is_muni:
                num_rows = 10
                out_labels_indexes = [
                    ('gastos',[0,1,2,3,4,5,6,7,8,9,]),
                    ('serv_pers',[0,1,2,]),
                ]

            for i,val,p_val in zip(range(num_rows),expenses_data.apply(float_to_text),expenses_p_data.apply(float_to_text)):
                context[f'out_{i+1}'] = val
                context[f'out_{i+1}_p'] = p_val
            for label,indexes in out_labels_indexes:
                context[label] = float_to_text(expenses_data[indexes].sum())
                context[f'{label}_p'] = float_to_text(expenses_p_data[indexes].sum())
                
            for i,val,p_val in zip(range(5),investments_data.apply(float_to_text),investments_p_data.apply(float_to_text)):
                context[f'inv_{i+1}'] = val
                context[f'inv_{i+1}_p'] = p_val
            
            context['inversiones'] = float_to_text(investments_data.sum())
            
            # Finish
            if not exists(out_path):
                os.makedirs(out_path)

            doc.render(context)
            doc.save(join(out_path,f"{out_name_text.value}.docx"))

            with open(join(out_path,f'{out_name_text.value}.docx'),'rb') as f:
                b64 = base64.b64encode(f.read())

            help_html.value = f'''
            Informe generado y guardado en la carpeta de <font color="#ff7823"><a href="http://localhost:8888/tree/datos/reportes" target="_blank"><code>datos/reportes</code></a></font>!
            Puedes descargarlos desde ahí, acceder al archivo en tu ordenador o descargarlos haciendo click en el botón de arriba.
            '''
            download_tag.value = f'<a class="jupyter-button mod-info" style="line-height: 50px; height:50px" download="{out_name_text.value}.docx" href="data:text/csv;base64,{b64.decode()}" target="_blank"><i class="fa fa-download"></i>Descargar</a>'

            if not random:
                if exists(profile_path):
                    with open(profile_path,'r') as f:
                        profile_json = json.load(f)
                    profile_json['last_report_num'] = report_number.value
                    with open(profile_path,'w') as f:
                        json.dump(profile_json,f)

        format_help ='''<font color="red">
            El valor editado no se encuentra en un formato de número reconocible.
            Tuvimos que revertir el valor de la celda al valor antiguo para mantener la consistencia de la tabla.
            El nuevo valor puede contener dígitos, comas y tan sólo un punto para delimitar los decimales.
        </font>
        '''

        def on_cell_edited(event,grid):
            col,idx,old,new = [event[key] for key in ['column','index','old','new']]

            if col in ['%','Descripción']:
                changed_df = grid.get_changed_df()
                changed_df[col][idx] = old
                grid.df = changed_df
                return
            if active_tab.value == 'general':
                return
            try:
                text_to_float(new)
                help_html.value = ''
            except ValueError:
                changed_df = grid.get_changed_df()
                changed_df[col][idx] = old
                grid.df = changed_df
                help_html.value = format_help
                return

            in_op_idxs = [
                'SERVICIOS DE AGUA POTABLE',
                'SERVICIOS DE ALCANTARILLADO',
                'SERVICIOS DE ALCANTARILLADO DE POZO',
                'OTROS INGRESOS OPERATIVOS',
            ] 
            in_no_op_idxs = [
                'INGRESOS FINANCIEROS',
                'OTROS INGRESOS NO OPERATIVOS',
            ]
            serv_pers_idxs = [
                'EMPLEADOS PERMANENTES',
                'EMPLEADOS NO PERMANENTES',
                'PREVISIÓN SOCIAL',
            ]
            inv_idxs = [
                'CONSTRUCCIÓN DE INFRAESTRUCTURA SISTEMA AGUA POTABLE',
                'CONSTRUCCIÓN DE INFRAESTRUCTURA SISTEMA DE ALCANTARILLADO',
                'ADQUISICIÓN DE MAQUINARIA Y EQUIPO',
                'DISEÑO Y ESTUDIOS DE PROYECTOS',
                'OTROS',
            ]

            df = grid.get_changed_df()
            df_total = float_to_text(df[col].apply(text_to_float).sum())
            df['%'][idx] = float_to_text(text_to_float(df['Valor (Bs.)'][idx])/text_to_float(df_total)*100)

            idx_text_percentages = [
                (in_op_idxs,in_op_text,in_op_percentage),
                (in_no_op_idxs,in_no_op_text,in_no_op_percentage),
            ]

            if type_toggle.value == 'Municipales':
                idx_text_percentages.append((serv_pers_idxs,serv_pers_text,serv_pers_percentage,))

            for idxs,text_widget,percentage_widget in idx_text_percentages:
                if df['Descripción'][idx] in idxs:
                    new_val = df[df['Descripción'].isin(idxs)]['Valor (Bs.)'].apply(text_to_float).sum()
                    text_widget.value = float_to_text(new_val)
                    percentage_widget.value = '{:.2f}'.format(new_val / text_to_float(df_total) * 100) + '%'

            tab_names = ['ingresos','gastos','inversiones']
            total_widgets = [in_total_text,total_gastos_text,total_inv_text]

            for tab_name,total_widget in zip(tab_names, total_widgets):
                if active_tab.value == tab_name:
                    total_widget.value = df_total

            grid.df = df

        def on_generate_random_button_click(b):
            on_generate_button_click(b,random=True)

        def set_active_tab(val):
            active_tab.value = val

        def update_active_tab(val):
            return lambda event,grid: set_active_tab(val)

        def update_intro(change):
            intro_html.value = build_intro()

        def on_info_button_change(change):
            color = 'black' if change['new'] else '#fff'
            limit = -1 if change['new'] else 0

            table_help.value = f'''<ul style="color:{color};">
            <li>En la siguiente tabla puedes ver los datos, a partir de los cuales se generará el POA.</li>
            <li>Las columnas de valor pueden ser modificadas haciendo doble click sobre la celda</li> 
            <li>El valor ingresado debe ser un número con un punto separando los decimales. Las comas son ignoradas.</li>
            <li>Todo cambio realizado se verá reflejado actualizará los porcentajes y se verá en el reporte generado.</li>
            </ul> '''[:limit]
            
        def on_out_name_text_change(change):
            out_name_help.value = out_path + '\\' + f'<b>{change["new"]}</b>' + '.docx'

        type_toggle.observe(on_type_toggle_change, names='value')
        epsa_dropdown.observe(on_epsa_dropdown_change, names='value')
        year_dropdown.observe(on_year_dropdown_change, names='value')
        order_dropdown.observe(on_order_dropdown_change, names='value')
        save_profile_button.on_click(on_save_profile_button_click)
        generate_button.on_click(on_generate_button_click)
        generate_random_button.on_click(on_generate_random_button_click)
        info_button.observe(on_info_button_change,names='value')
        out_name_text.observe(on_out_name_text_change,names='value')

        for widg in [report_number,city_dropdown,qualification_type,name_text,specialty_text,date_picker]:
            widg.observe(update_intro,names='value')

        qgrid.on('cell_edited',on_cell_edited)

        tab_names = [sn.title() for sn in sheet_names]
        grids = []
        for i in range(len(tab_names)):
            grids.append(qgrid.QGridWidget(df=pd.DataFrame(),show_toolbar=False,))

        for i,val in zip(range(4),['general','ingresos','gastos','inversiones']):
            grids[i].on('selection_changed',update_active_tab(val))
            
        tab = widgets.Tab([
            grids[0],
            widgets.VBox([
                grids[1],
                widgets.HBox([in_op_text,in_op_percentage,]),
                widgets.HBox([in_no_op_text,in_no_op_percentage,]),
                in_total_text,
                ingresos_text_box,
            ]),
            widgets.VBox([
                grids[2],
                widgets.HBox([serv_pers_text,serv_pers_percentage,]),
                total_gastos_text,
                gastos_text_box,
            ]),
            widgets.VBox([
                grids[3],
                total_inv_text,
                inversiones_text_box,
            ]),
        ])

        for i,name in enumerate(tab_names):
            tab.set_title(i, name)

        accordion = widgets.Accordion([
            widgets.HBox([widgets.VBox([
                name_text,
                qualification_type,
                specialty_text,
                report_number,
                city_dropdown,
                date_picker,
                widgets.HBox([save_profile_button,intro_help_html,]),
            ]),intro_html]),
            widgets.VBox([type_toggle, epsa_dropdown, year_dropdown, order_dropdown,]),
            widgets.Button(),
        ])
        accordion.set_title(0, '1. Datos Generales / Intro')
        accordion.set_title(1, '2. Cargar Datos POA')
        accordion.set_title(2, '3. Antecedentes')
        accordion.selected_index = None


        super().__init__(children=[accordion,widgets.HBox([table_help,info_button]),tab,widgets.HBox([out_name_text,out_name_help]),widgets.HBox([generate_button,generate_random_button,download_tag]),help_html,], **kwargs)
        
class LoadDataWidget(widgets.VBox):   
    def __init__(self, **kwargs):
        
        def intersection(a,b):
            return list(set(a)&set(b))
        def difference(a,b):
            return list(set(a)-set(b))
        def is_contained(a,b):
            return set(a) <= set(b)

        profile_json = None

        local_datasets = []
        if exists(epsas_xl_path):
            local_datasets.append('EPSAS')
        if exists(coop_xl_path) and exists(muni_xl_path):
            local_datasets.append('POAS')

        external_datasets = difference(available_datasets,local_datasets)

        general_cols = ['epsa','year','order']
        income_cols = ['in_op_ap','in_op_alc','in_op_alc_pozo','in_op_otros','in_financieros','in_no_op_otros']
        coop_expenses_cols = [
            'costos_operacion',
            'costos_mantenimiento',
            'gastos_administrativos',
            'gastos_comerciales',
            'gastos_financieros',
        ]
        muni_expenses_cols = [
            'gastos_empleados_permanentes',
            'gastos_empleados_no_permanentes',
            'gastos_prevision_social',
            'gastos_servicio_no_personales',
            'gastos_materiales',
            'gastos_activos',
            'gastos_deuda_publica',
            'gastos_transferencias',
            'gastos_impuesto',
            'gastos_otros',
        ]
        investments_cols = [
            'inv_infraestructura_ap',
            'inv_infraestructura_alc',
            'inv_equipo',
            'inv_diseno_estudio',
            'inv_otros',
        ]

        help_html0 = widgets.HTML()

        username_widget = widgets.Text(
            description='Usuario:',
            placeholder='Usuario del sistema AAPS-API',
            layout=widgets.Layout(width='90%')
        )

        password_widget = widgets.Password(
            description='Contraseña:',
            layout=widgets.Layout(width='90%'),
        )

        generate_token_button = widgets.Button(
            description='Generar Credenciales!',
            button_style='success',
            disabled=True,
            tooltip='Actualiza los datos locales del sistema AAPS-API!',
            icon='key',
            layout=widgets.Layout(width='50%')
        )

        show_password_button = widgets.ToggleButton(
            value = False,
            button_style='info',
            tooltip='Mostrar Contraseña',
            disabled=True,
            icon='eye',
            layout=widgets.Layout(width='40px')
        )

        update_token_button = widgets.Button(
            description='Actualizar Credenciales',
            button_style='info',
            tooltip='Actualiza los credenciales de autorización',
            layout=widgets.Layout(display='none',width='250px')
        )

        update_button = widgets.Button(
            button_style='info',
            tooltip='Actualizar el paso 1.',
            icon='refresh',
            layout=widgets.Layout(width='50px'),
        )

        local_datasets_select = widgets.SelectMultiple(
            options=local_datasets,
            value=[],
            rows=len(local_datasets)+2,
            description='Conjuntos Locales:',
            disabled=False,
            layout=widgets.Layout(width='100%'),
            style={'description_width': 'initial'},
        )

        external_datasets_select = widgets.SelectMultiple(
            options=external_datasets,
            value=[],
            description='Conjuntos Externos:',
            disabled=False,
            rows=len(external_datasets)+2,
            layout=widgets.Layout(width='100%'),
            style={'description_width': 'initial'},
        )
        download_button = widgets.Button(
            description='Actualizar/Descargar Datos',
            button_style='success',
            tooltip='Generar Reporte',
            icon='download',
            disabled=True,
            layout=widgets.Layout(width='300px',height='50px',font_size='20px'),
        )

        def build_overview():
            lds = local_datasets_select.value
            eds = external_datasets_select.value

            lds_enum =  '<ol>' + ''.join([f'<li>{x}</li>' for x in lds]) + '</ol>'
            eds_enum =  '<ol>' + ''.join([f'<li>{x}</li>' for x in eds]) + '</ol>'

            update_txt = '' if lds == () else 'Estos conjuntos de datos serán actualizados:</br>'
            download_txt = '' if eds == () else 'Estos conjuntos de datos nuevos serán descargados:</br>'

            overview_html.value=f'''<div style="background-color: #ddffff;border-left: 6px solid #2196F3; padding: 0.01em 16px">
            {update_txt}
            {lds_enum}
            {download_txt}
            {eds_enum}
            </div>'''

        overview_html = widgets.HTML(layout=widgets.Layout(width='50%'))
        build_overview()

        help_html = widgets.HTML(layout=widgets.Layout(width='500px'))
        download_help = widgets.HTML()
        button_help = widgets.HTML()

        login_widget = widgets.HBox(children=[
            widgets.VBox([
                username_widget,
                widgets.HBox([password_widget,show_password_button,]),
                widgets.HBox([generate_token_button,update_button]),
            ]),
            help_html,
        ], layout=widgets.Layout(display='none'))

        download_data_widget = widgets.VBox(children=[
            widgets.HBox([local_datasets_select,external_datasets_select,]),
            overview_html,
        ], layout=widgets.Layout(display='none'))

        def set_help_html(username, password, show_pass):
            user_label = 'Nombre de Usuario:' if username != '' else ''
            pass_label = 'Contraseña:' if password != '' else ''
            encoded_pass = password if show_pass else '\u2022' * len(password)
            help_html.value = f"<font color='gray'>{user_label}</font> {username} <font color='gray'>{pass_label}</font> {encoded_pass}"

        def on_username_change(change):
            set_help_html(change['new'], password_widget.value, show_password_button.value)
            if change['new'] == '':
                generate_token_button.disabled = True
            elif password_widget.value != '':
                generate_token_button.disabled = False

        def on_password_change(change):
            set_help_html(username_widget.value,change['new'], show_password_button.value)
            if change['new'] == '':
                show_password_button.disabled = True
                generate_token_button.disabled = True
            else:
                show_password_button.disabled = False
                if username_widget.value != '':
                    generate_token_button.disabled = False

        def on_show_pass_change(change):
            set_help_html(username_widget.value, password_widget.value, change['new'])

        def on_generate_token_button_click(b):

            username = username_widget.value
            password = password_widget.value
            r = requests.post(f'{server_base_url}/api-token-auth/', json={'username':username, 'password':password})

            if 'token' in r.json().keys():
                with open(profile_path,'r') as f:
                    profile_json_h = json.load(f)

                profile_json_h['token'] = r.json()['token']

                with open(profile_path,'w') as f:
                    json.dump(profile_json_h,f)

                profile_json = profile_json_h

                login_widget.layout.display = 'none'
                help_html0.value = '<font color="green">Las credenciales son válidas!</font></br><font color="green">Token guardado. Todo listo para descargar datos.</font>'
                download_help.value = '<font color="green">Las credenciales son válidas!</font><font color="green">Token guardado. Todo listo para descargar datos.</font></br><div style="margin-bottom:20pt"><font size=3>Selecciona los conjuntos de datos que serán actualizado y/o descargados. Mantén presionado CTRL para seleccionar múltiples conjuntos.</font></div>'
                update_token_button.layout.display = None
                download_data_widget.layout.display = None
                load_data_accordion.selected_index = 1
                download_button.disabled = False

            else:
                help_html.value = "<font color='red'>Las credenciales proporcionadas no son válidas.</font> Verifica tus credenciales. Si el problema persiste, trata de ingresar a través de la <a href='https://aaps-data.appspot.com/admin/'>aplicación administrativa</a>. Si no puedes ingresar a través de esa página tampoco, contacta al administrador/administradora."


        def on_update_token_button_click(b):
            help_html0.value = 'Para actualizar tus credenciales, porfavor ingresa tu nombre de usuario y contraseña.'
            login_widget.layout.display=None
            update_token_button.layout.display='none'

        def on_update_button_click(b):
            username_widget.value=''
            password_widget.value=''
            login_widget.layout.display='none'

            if exists(profile_path):
                with open(profile_path,'r') as f:
                    profile_json = json.load(f)
            else:
                help_html0.value = '<font color="red">No se encontró el archivo de perfil de usuario.</font>'

            if not 'token' in profile_json.keys():
                help_html0.value = "Parece que no cuentas con credenciales de autorización todavía. Por favor ingresa tus credenciales para generar uno."
                login_widget.layout.display=None
            else:
                help_html0.value = "<font color='green'>Credenciales de autorización encontrados. Todo listo para descargar datos! Si no puedes descargar datos es posible que tu token este desactualizado.</font>"
                update_token_button.layout.display=None

        def on_local_dataset_select_change(change):
            build_overview()
        def on_external_dataset_select_change(change):
            build_overview()

        def on_download_button_click(b):
            with open(profile_path,'r') as f:
                token = json.load(f).get('token')
            headers = dict(Authorization=f'Token {token}')
            selected_datasets = local_datasets_select.value + external_datasets_select.value
            epsas_json, poas_json = None, None
            try:
                if 'EPSAS' in selected_datasets:
                    epsas_json = requests.get(f'{server_base_url}/api/epsas/?fields!=id,modified',headers=headers).json()
                if 'POAS' in selected_datasets:
                    poas_json = requests.get(f'{server_base_url}/api/poas/?fields!=id,modified',headers=headers).json()
                INVALID_TOKEN = None
                if isinstance(epsas_json,dict):
                    if epsas_json.get('detail') == 'Token inválido.':
                        INVALID_TOKEN = True
                if isinstance(poas_json,dict):
                    if poas_json.get('detail') == 'Token inválido.':
                        INVALID_TOKEN = True
                if INVALID_TOKEN:
                    download_help.value = '<font color="red">Credenciales inválidas. Actualiza tus credenciales en el paso 1 y trata de nuevo.</font>'
                    download_data_widget.layout.display = 'none'
                    return
            except ConnectionError:
                try:
                    requests.head('http://www.google.com', verify=False, timeout=5)
                    button_help.value = '<font color="red">No se pudo establecer conexión con el servidor de datos.</font>'
                except ConnectionError:
                    NETWORK_CONNECTED = False
                    button_help.value = '<font color="red">No se pudo establecer conexión con el servidor de datos. Verifica que tienes conexión a internet e intentalo nuevamente.</font>'
                return
            
            if isinstance(epsas_json,list):
                cols = ['code','name','state','category']
                if not exists(data_path):
                    os.makedirs(data_path)
                pd.DataFrame(epsas_json)[cols].to_excel(epsas_xl_path)
            
            if isinstance(poas_json,list):
                coop_writer = ExcelWriter(coop_xl_path)
                muni_writer = ExcelWriter(muni_xl_path)
                
                poas_clean = dict(coop=[],muni=[])
                for poa in poas_json:
                    cm_dicts = [poa.get('coop_expense'),poa.get('muni_expense')]

                    for cm_dict,cm in zip(cm_dicts,['coop','muni']):
                        if isinstance(cm_dict,dict):
                            for k,v in cm_dict.items():
                                if not k == 'modified':
                                    poa[k] = v
                            del poa['coop_expense']
                            del poa['muni_expense']
                            poas_clean[cm].append(poa)

                coop_df = pd.DataFrame(poas_clean['coop'])
                muni_df = pd.DataFrame(poas_clean['muni'])

                cols_lists = [general_cols,income_cols,None,investments_cols]
                sheet_names = ['general','ingresos','gastos','inversiones']

                for cols_list,sn in zip(cols_lists, sheet_names):
                    if sn == 'gastos':
                        coop_df[coop_expenses_cols].to_excel(coop_writer,sn,index=False)
                        muni_df[muni_expenses_cols].to_excel(muni_writer,sn,index=False)
                    else:
                        coop_df[cols_list].to_excel(coop_writer,sn,index=False)
                        muni_df[cols_list].to_excel(muni_writer,sn,index=False)

                if not exists(data_path):
                    os.makedirs(data_path)

                coop_writer.save()
                muni_writer.save()
                    
            if not selected_datasets == []: 
                button_help.value = '<font size=3>Datos Actualizados/Descargados. Los puedes encontrar en la carpeta <a href="http://localhost:8888/tree/datos/" target=_><code><font color="#fcb070">datos</font></code></a> y ahora los puedes usar en las otras aplicaciones! Por ejemplo: <a href="http://localhost:8888/apps/Generar%20Reportes%20POA.ipynb?appmode_scroll=0" target=_><font color="#fcb070">Generar Reportes POA</font></a></font>'

        username_widget.observe(on_username_change, names='value')
        password_widget.observe(on_password_change, names='value')
        show_password_button.observe(on_show_pass_change, names='value')
        generate_token_button.on_click(on_generate_token_button_click)
        update_token_button.on_click(on_update_token_button_click)
        update_button.on_click(on_update_button_click)
        local_datasets_select.observe(on_local_dataset_select_change,names='value')
        external_datasets_select.observe(on_external_dataset_select_change,names='value')
        download_button.on_click(on_download_button_click)

        load_data_accordion = widgets.Accordion(children=[
            widgets.VBox([help_html0,login_widget,update_token_button]),
            widgets.VBox([download_help,download_data_widget,]),
        ])
        load_data_accordion.set_title(0, '1. Ingreso/Autenticación')
        load_data_accordion.set_title(1, '2. Seleccionar Datos')

        if exists(profile_path):
            with open(profile_path,'r') as f:
                profile_json = json.load(f)
        else:
            help_html0.value = '<font color="red">No se encontró el archivo de perfil de usuario.</font>'

        if not 'token' in profile_json.keys():
            help_html0.value = "Parece que no cuentas con un token de autorización todavía. Por favor ingresa tus credenciales para generar uno."
            download_help.value = 'Parece que no cuentas con un token de autorización todavía. Por favor ingresa tus credenciales en el paso 1 para generar uno.'
            login_widget.layout.display = None
        else:
            help_html0.value = "<font color='green'>Tus credenciales están en orden. Todo listo para cargar datos! Si no puedes cargar datos es posible que tu token este desactualizado.</font>"
            download_help.value = '<div style="margin-bottom:20pt"><font size=3>Selecciona los conjuntos de datos que serán actualizado y/o descargados. Mantén presionado CTRL para seleccionar múltiples conjuntos.</font></div>'
            update_token_button.layout.display = None
            download_data_widget.layout.display = None
            download_button.disabled = False
            load_data_accordion.selected_index = 1
        
        super().__init__(children=[load_data_accordion,widgets.HBox([download_button,button_help,])], **kwargs)