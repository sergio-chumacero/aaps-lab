import ipywidgets as widgets
import os
from os.path import join, exists, dirname
import json
import requests
import qgrid
import pandas as pd
from datetime import datetime
import docx

# Paths

home_dir = join(os.environ['USERPROFILE'],'aapslab')
data_path = join(home_dir,'datos')
models_path = join(home_dir,'.lib','models')
out_path = join(data_path,'reportes')

profile_path = join(home_dir,'.profile','profile.json')

coop_xl_path = join(data_path,'poas_coop.xlsx')
muni_xl_path = join(data_path,'poas_muni.xlsx')

coop_doc_path = join(models_path,'modelo_poa_coop.docx')
muni_doc_path = join(models_path,'modelo_poa_muni.docx')

server_base_url = 'http://localhost:8000'

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
            gastos_servicios_no_personales='SERVICIOS NO PERSONALES',
            gastos_materiales='MATERIALES Y SUMINISTROS',
            gastos_activos='ACTIVOS REALES',
            gastos_deuda_publica='SERVICIOS DE LA DEUDA PÚBLICA',
            gastos_transferencias='TRANSFERENCIAS',
            gastos_impuesto='IMPUESTOS, REGALÍAS Y TASAS',
            gastos_otros='OTROS GASTOS',
            inv_infraestructura_ap='CONSTRUCCIÓN DE INFRAESTRUCTURA SISTEMA AGUA POTABLE',
            inv_infraestructura_alc='CONSTRUCCIÓN DE INFRAESTRUCTURA SISTEMA DE ALCANTARILLADO',
            inv_equipo='ADQUISICIÓN DE MAQUINARIA Y EQUIPO',
            inv_diseno_estudio='DISEÑO Y ESTUDIOS DE PROYECTOS',
            inv_otros='OTROS',
        )

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
            layout= widgets.Layout(display='none')
        ) 
        date_picker = widgets.DatePicker(
            value = datetime.now(),
            description='Fecha:',
            disabled=False
        )

        in_op_text = widgets.Text(
            value=None,
            description='Ingresos Operativos (Bs.):',
            disabled=True,
            layout=widgets.Layout(display='none',width='400px'),
            style={'description_width': '185px'},
        )
        in_no_op_text = widgets.Text(
            value=None,
            description='Ingresos No Operativos (Bs.):',
            disabled=True,
            layout=widgets.Layout(display='none',width='400px'),
            style={'description_width': '185px'},
        )
        in_total_text = widgets.Text(
            value=None,
            description='Ingresos Totales (Bs.):',
            disabled=True,
            layout=widgets.Layout(display='none',width='400px'),
            style={'description_width': '185px'},
        ) 
        serv_pers_text = widgets.Text(
            value=None,
            description='Servicios Personales (Bs.):',
            disabled=True,
            layout=widgets.Layout(display='none',width='400px'),
            style={'description_width': '185px'},
        )
        total_gastos_text = widgets.Text(
            value=None,
            description='Gastos Totales (Bs.):',
            disabled=True,
            layout=widgets.Layout(display='none',width='400px'),
            style={'description_width': '185px'},
        )

        total_inv_text = widgets.Text(
            value=None,
            description='Total Inversiones (Bs.):',
            disabled=True,
            layout=widgets.Layout(display='none',width='400px'),
            style={'description_width': '165px'},
        ) 


        help_html = widgets.HTML()

        help_grid = qgrid.QGridWidget(df=pd.DataFrame())

        def build_intro():
            num = report_number.value
            prof = qualification_type.value
            name = name_text.value
            specialty = specialty_text.value
            date = date_picker.value
            return f'''<div style="background-color: #ddffff;border-left: 6px solid #2196F3; padding: 0.01em 16px">
            INFORME AAPS/DER/INF/{num:03d}/{date.year}</br>
            {prof_name_to_denom[prof]} {name.title()}</br>
            PROFESIONAL {prof.upper()} {specialty.upper()}</br>
            La Paz, {date.day} de {month_num_to_name[date.month]} de {date.year}
            </div>'''

        intro_html = widgets.HTML(value=build_intro())
        intro_help_html = widgets.HTML()

        def on_type_toggle_change(change):
            if change['new'] == 'Cooperativas':
                if exists(coop_xl_path):
                    help_html.value = ''
                    help_grid.df = pd.read_excel(coop_xl_path, sheet_name='general')
                    epsa_dropdown.options = list(help_grid.df.epsa)
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
                    help_html.value = "<font color='red'>Parece que no tienes datos de Cooperativas. Trata de descargar estos datos desde la aplicación 'Descargar Datos'. También puedes generar un reporte con datos aleatorios.</font>"

            if change['new'] == 'Municipales':
                if exists(muni_xl_path):
                    help_html.value = ''
                    help_grid.df = pd.read_excel(muni_xl_path, sheet_name='general')
                    epsa_dropdown.options = list(help_grid.df.epsa)
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
                    help_html.value = "<font color='red'>Parece que no tienes datos de Cooperativas. Trata de descargar estos datos desde la aplicación 'Descargar Datos'. También puedes generar un reporte con datos aleatorios.</font>"

        def on_epsa_dropdown_change(change):
            if change['new']:
                epsa_dropdown.layout.display = None
                df = help_grid.df
                year_dropdown.options = list(df[df.epsa==change['new']].year)

        def on_year_dropdown_change(change):
            if change['new']:
                year_dropdown.layout.display = None
                df = help_grid.df
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
                serv_pers_cols = ['gastos_empleados_permanentes','gastos_empleados_no_permanentes','gastos_prevision_social',]

                text_widgets = [in_op_text,in_no_op_text,in_total_text,serv_pers_text,total_gastos_text,total_inv_text]
                values = [
                    dfs[1][in_op_cols].iloc[0].sum(),
                    dfs[1][in_no_op_cols].iloc[0].sum(),
                    dfs[1].iloc[0].sum(),
                    dfs[2][serv_pers_cols].iloc[0].sum(),
                    dfs[2].iloc[0].sum(),
                    dfs[3].iloc[0].sum(),
                ]

                for w,val in zip(text_widgets,values):
                    w.value = float_to_text(val)
                    w.layout.display = None

                for df in dfs:
                    df.columns = [column_name_to_verbose.get(cn,cn) for cn in list(df)]

                dfs = [df.transpose() for df in dfs]
                for df in dfs:
                    df.columns = ['Valor (Bs.)']
                for df in dfs[1:]:
                    df['Valor (Bs.)']= df['Valor (Bs.)'].apply(lambda x:"{:,.2f}".format(x))

                for grid,df in zip(grids,dfs):
                    grid.df = df

        def on_report_number_change(change):
            intro_html.value = build_intro()
        def on_qualification_type_change(change):
            intro_html.value = build_intro()
        def on_name_text_change(change):
            intro_html.value = build_intro()
        def on_specialty_text_change(change):
            intro_html.value = build_intro()
        def on_date_picker_change(change):
            intro_html.value = build_intro()

        def on_save_profile_button_click(b):
            if profile_json:
                profile_json['name'] = name_text.value
                profile_json['prof'] = qualification_type.value
                profile_json['specialty'] = specialty_text.value
                profile_json['last_report_num'] = report_number.value

                with open(profile_path,'w') as f:
                    json.dump(profile_json,f)

                intro_help_html.value = 'Perfil guardado!'

        def on_generate_button_click(b):
            if not type_toggle.value:
                help_html.value = '<font color="red">Porfavor escoge el tipo de reporte (cooperativa o EPSA municipal).</font>'
                return

            is_muni, is_coop = None, None
            if type_toggle.value == 'Cooperativas':
                if not exists(coop_doc_path):
                    help_html.value = '<font color="red">No se encontró el modelo base de POA para cooperativas.</font>'
                doc_path = coop_doc_path
                is_coop = True

            if type_toggle.value == 'Municipales':
                if not exists(coop_doc_path):
                    help_html.value = '<font color="red">No se encontró el modelo base de POA para EPSAs municipales.</font>'
                doc_path = muni_doc_path
                is_muni = True

            doc = docx.Document(doc_path)
            income_data, expenses_data, investments_data = [list(grids[i+1].get_changed_df()['Valor (Bs.)'].apply(text_to_float)) for i in range(3)]

            # Intro
            prof = qualification_type.value
            date = date_picker.value
            denom = prof_name_to_denom[prof]

            doc.paragraphs[3].text = f'AAPS/DER/INF/{report_number.value:03d}/{date.year}'
            col = doc.tables[0].columns[2]
            col.cells[2].paragraphs[3].text = f'{denom} {name_text.value}'.title()
            col.cells[2].paragraphs[4].text = f'{prof} {specialty_text.value}'.upper()
            col.cells[5].paragraphs[0].text = f'La Paz, {date.day} de {month_num_to_name[date.month]} de {date.year}'

            # Ingresos

            for i,val in zip([3,4,6,7,9,10],income_data):
                doc.tables[4].columns[1].cells[i].text = float_to_text(val)

            doc.tables[4].columns[1].cells[2].text = float_to_text(income_data[0] + income_data[1])
            doc.tables[4].columns[1].cells[5].text = float_to_text(income_data[2] + income_data[3])
            doc.tables[4].columns[1].cells[8].text = float_to_text(income_data[4] + income_data[5])
            doc.tables[4].columns[1].cells[1].text = float_to_text(sum([income_data[i] for i in range(4)]))
            doc.tables[4].columns[1].cells[0].text = float_to_text(sum(income_data))

            # Gastos
            if is_coop:
                for i,val in zip([2,3,5,6,7],expenses_data):
                    doc.tables[5].columns[1].cells[i].text = float_to_text(val)

                doc.tables[5].columns[1].cells[1].text = float_to_text(expenses_data[0] + expenses_data[1])
                doc.tables[5].columns[1].cells[4].text = float_to_text(expenses_data[2] + expenses_data[3] + expenses_data[4])
                doc.tables[5].columns[1].cells[0].text = float_to_text(sum(expenses_data))

            if is_muni:
                for i,val in zip([j+2 for j in range(10)],expenses_data):
                    doc.tables[5].columns[1].cells[i].text = float_to_text(val) 

                doc.tables[5].columns[1].cells[1].text = float_to_text(expenses_data[0] + expenses_data[1] + expenses_data[2])
                doc.tables[5].columns[1].cells[0].text = float_to_text(sum(expenses_data))

            # Inversiones

            for i,val in zip([1,2,3,4,5],investments_data):
                doc.tables[6].columns[1].cells[i].text = float_to_text(val)

            doc.tables[6].columns[1].cells[0].text = float_to_text(sum(investments_data)) 

            # Finish
            if not exists(out_path):
                os.makedirs(out_path)

            doc.save(join(out_path,f'reporte_poa.docx'))

            help_html.value = '''
            Informe generado y guardado en la carpeta <a href="http://localhost:8888/tree/datos/reportes"><code>datos/reportes</code></a>!
            Puedes descargar los reportes desde el navegador (<a href="http://localhost:8888/tree/datos/reportes"><font color="blue">LINK</font></a>)
            o acceder a ellos directamente a la carpeta en tu ordenador.'
            '''

            if profile_json:
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
            try:
                new_val = float(new.replace(',',''))
                help_html.value = ''
            except ValueError:
                changed_df = grid.get_changed_df()
                changed_df[event['column']][event['index']] = event['old']
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

            idxs_list = [in_op_idxs,in_no_op_idxs,serv_pers_idxs]
            text_widgets = [in_op_text, in_no_op_text,serv_pers_text]

            total_idxs_list = [in_op_idxs + in_no_op_idxs,serv_pers_idxs,inv_idxs]
            total_widgets = [in_total_text,total_gastos_text,total_inv_text]

            for idxs, text_widget in zip(idxs_list,text_widgets):
                if idx in idxs:
                    text_widget.value = float_to_text(df[col][idxs].apply(text_to_float).sum())

            for idxs, text_widget in zip(total_idxs_list,total_widgets):
                if idx in idxs:
                    text_widget.value = df_total


        type_toggle.observe(on_type_toggle_change, names='value')
        epsa_dropdown.observe(on_epsa_dropdown_change, names='value')
        year_dropdown.observe(on_year_dropdown_change, names='value')
        order_dropdown.observe(on_order_dropdown_change, names='value')
        report_number.observe(on_report_number_change, names='value')
        qualification_type.observe(on_qualification_type_change,names='value')
        name_text.observe(on_name_text_change,names='value')
        specialty_text.observe(on_specialty_text_change,names='value')
        date_picker.observe(on_date_picker_change,names='value')
        save_profile_button.on_click(on_save_profile_button_click)
        generate_button.on_click(on_generate_button_click)

        qgrid.on('cell_edited',on_cell_edited)

        tab_names = [sn.title() for sn in sheet_names]
        grids = []
        for i in range(len(tab_names)):
            grids.append(qgrid.QGridWidget(df=pd.DataFrame()))

        tab = widgets.Tab([
            grids[0],
            widgets.VBox([grids[1],in_op_text,in_no_op_text,in_total_text]),
            widgets.VBox([grids[2],serv_pers_text,total_gastos_text]),
            widgets.VBox([grids[3],total_inv_text]),
        ])

        for i,name in enumerate(tab_names):
            tab.set_title(i, name) 

        table_instructions ='''<h4>En la siguiente tabla puedes ver los datos, a partir de los cuales se generará el POA.
        Los valores de las celdas pueden ser modificados haciendo doble click sobre una celda.
        Todo cambio realizado se verá reflejado en el reporte generado.</h4>
        '''

        accordion = widgets.Accordion([
            widgets.HBox([widgets.VBox([name_text, qualification_type, specialty_text, report_number,date_picker,widgets.HBox([save_profile_button,intro_help_html,]),]),intro_html]),
            widgets.VBox([type_toggle, epsa_dropdown, year_dropdown, order_dropdown, generate_random_button]),
            widgets.HTML(value=table_instructions),
        ])
        accordion.set_title(0, '1. Datos Generales')
        accordion.set_title(1, '2. Datos POA')
        accordion.set_title(2, '3. Vista Previa / Editar Datos')
        accordion.selected_index = None
        
        super().__init__(children=[accordion,tab,generate_button,help_html,], **kwargs)
        
class LoadDataWidget(widgets.VBox):   
    def __init__(self, **kwargs):
        
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
            description='Generar Token!',
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
            description='Actualizar Token',
        #     button_style='info',
            tooltip='Actualiza el token de autorización',
            layout=widgets.Layout(display='none')
        )

        update_button = widgets.Button(
            button_style='info',
            tooltip='Actualiza el paso 0',
            icon='refresh',
            layout=widgets.Layout(width='50px')
        )

        help_html = widgets.HTML()
        help_html.layout.width = '500px'

        login_widget = widgets.HBox([
            widgets.VBox([
                username_widget,
                widgets.HBox([password_widget,show_password_button,]),
                widgets.HBox([generate_token_button,update_button]),
            ]),
            help_html,
        ])
        login_widget.layout.display='none'

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
            try:
                username = username_widget.value
                password = password_widget.value
                r = requests.post(f'{server_base_url}/api-token-auth/', json={'username':username, 'password':password})

                if 'token' in r.json().keys():
                    with open(profile_path,'r') as f:
                        profile_json = json.load(f)
                    
                    profile_json['token'] = r.json()['token']
                    
                    with open(profile_path,'w') as f:
                        json.dump(profile_json,f)
                    
                    login_widget.layout.display = 'none'
                    help_html0.value = '</br><font color="green">Las credenciales son válidas!</font></br><font color="green">Token guardado. Todo listo para cargar datos.</font>'
                else:
                    help_html.value = "<font color='red'>Las credenciales proporcionadas no son válidas.</font> Verifica tus credenciales. Si el problema persiste, trata de ingresar a través de la <a href='https://aaps-data.appspot.com/admin/'>aplicación administrativa</a>. Si no puedes ingresar a través de esa página tampoco, contacta al administrador/administradora."
            except Exception as e:
                help_html.value = str(e)
                
        def on_update_token_button_click(b):
            help_html0.value = ''
            login_widget.layout.display=None
            update_token_button.layout.display='none'

        def on_update_button_click(b):
            username_widget.value=''
            password_widget.value=''
            login_widget.layout.display='none'
            
            with open(profile_path,'r') as f:
                profile_json = json.load(f)

            if not 'token' in profile_json.keys():
                help_html0.value = "Parece que no cuentas con un token de autorización todavía. Por favor ingresa tus credenciales para generar uno."
                login_widget.layout.display=None
            else:
                help_html0.value = "<font color='green'>Token de autorización encontrado. Todo listo para cargar datos! Si no puedes cargar datos es posible que tu token este desactualizado.</font>"
                update_token_button.layout.display=None
            
        username_widget.observe(on_username_change, names='value')
        password_widget.observe(on_password_change, names='value')
        show_password_button.observe(on_show_pass_change, names='value')
        generate_token_button.on_click(on_generate_token_button_click)
        update_token_button.on_click(on_update_token_button_click)
        update_button.on_click(on_update_button_click)

        load_data_accordion = widgets.Accordion(children=[widgets.VBox([help_html0,login_widget,update_token_button]),widgets.Button()])
        load_data_accordion.set_title(0, '1. Ingreso/Autenticación')
        load_data_accordion.set_title(1, '0. Cargar Datos')

        with open(profile_path,'r') as f:
            profile_json = json.load(f)

        if not 'token' in profile_json.keys():
            help_html0.value = "Parece que no cuentas con un token de autorización todavía. Por favor ingresa tus credenciales para generar uno."
            login_widget.layout.display=None
        else:
            help_html0.value = "<font color='green'>Tus credenciales estan en orden. Todo listo para cargar datos! Si no puedes cargar datos es posible que tu token este desactualizado.</font>"
            update_token_button.layout.display=None
        
        super().__init__(children=[load_data_accordion], **kwargs)