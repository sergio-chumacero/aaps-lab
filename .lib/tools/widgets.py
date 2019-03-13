import ipywidgets as widgets
import os
from os.path import join, exists, dirname
import json
import requests
import pyexcel as pe
import pandas as pd

import docx
from datetime import datetime

# Paths

home_dir = join(os.environ['USERPROFILE'],'aapslab')
profile_path = join(home_dir,'.profile','profile.json')
data_path = join(home_dir,'datos')
models_path = join(home_dir,'.lib','models')
out_path = join(data_path,'reportes')

# Server Info

server_base_url = 'http://localhost:8000'
# server_base_url = 'http://200.87.123.68/'

# Widgets

class GenerateReportWidget(widgets.VBox):
    def __init__(self, **kwargs):

        if exists(profile_path):
            with open(profile_path,'r') as f:
                profile_json = json.load(f)
        else:
            profile_json = {}

        coop_path = join(data_path,'poas_coop.xlsx')
        muni_path = join(data_path,'poas_muni.xlsx')
        
        if exists(coop_path):
            coop_book = pe.get_book(file_name=coop_path)
            coop_df = pd.concat([pd.read_excel(coop_path, sheet_name=sn) for sn in ['general','ingresos','gastos','inversiones']], axis=1)

        if exists(muni_path):
            muni_book = pe.get_book(file_name=muni_path)
            muni_df = pd.concat([pd.read_excel(muni_path, sheet_name=sn) for sn in ['general','ingresos','gastos','inversiones']], axis=1)

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
#             disabled=True,
        )

        save_profile_button = widgets.Button(
            description='Guardar Perfil',
            button_style='info',
            tooltip='Generar Reporte',
            icon='save',
        ) 
        
        epsa_toggle = widgets.ToggleButtons(
            options=['Cooperativas', 'Municipales',],
            value = None,
            description='Tipo de EPSA:',
            disabled=False,
            button_style='info', # 'success', 'info', 'warning', 'danger' or ''
            tooltips=['Cooperativas', 'EPSAS Municipales',],
        #     icons=['check'] * 3
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
            style={'description_width': 'initial'},
        )

        help_html = widgets.HTML()

        prof_name_to_denom = {'Ingeniero':'Ing.', 'Económico':'Lic.',}

        now = datetime.now()
        month_names = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        month_num_to_name = {k+1:v for k,v in zip(range(12), month_names)}

        def on_generate_button_click(b):
            
            epsa = epsa_dropdown.value
            year = year_dropdown.value
            order = order_dropdown.value

            if not epsa_toggle.value:
                help_html.value = '<font color="red">Porfavor escoge entre Cooperativas o EPSAs municipales.</font>'
                return

            if epsa_toggle.value == 'Cooperativas':
                if exists(join(models_path,'modelo_poa_coop.docx')):
                    doc = docx.Document(join(models_path,'modelo_poa_coop.docx'))
                    df = coop_df
                    book = coop_book
                else:
                    help_html.value = '<font color="red">No se encontró el modelo base de POA de cooperativas.</font>'
                    return
                if exists(join(data_path,'poas_coop.xlsx')):
                    xlsx_path = join(data_path,'poas_coop.xlsx')
                else:
                    help_html.value = '<font color="red">No se encontraron los datos de POAs de cooperativas.</font>'
                    return


            if epsa_toggle.value == 'Municipales':
                if exists(join(models_path,'modelo_poa_muni.docx')):
                    doc = docx.Document(join(models_path,'modelo_poa_muni.docx'))
                    df = muni_df
                    book = muni_book
                else:
                    help_html.value = '<font color="red">No se encontró el modelo base de POA de EPSAs municipales.</font>'
                    return
                if exists(join(data_path,'poas_muni.xlsx')):
                    xlsx_path = join(data_path,'poas_muni.xlsx')
                else:
                    help_html.value = '<font color="red">No se encontraron los datos de POAs de EPSAs municipales.</font>'
                    return

            doc.paragraphs[3].text = f'AAPS/DER/INF/{report_number.value:03d}/2019'

            prof = qualification_type.value
            denom = prof_name_to_denom[prof]

            # General Info

            col = doc.tables[0].columns[2]
            col.cells[2].paragraphs[3].text = f'{denom} {name_text.value}'.title()
            col.cells[2].paragraphs[4].text = f'{prof} {specialty_text.value}'.upper()
            col.cells[5].paragraphs[0].text = f'La Paz, {now.day} de {month_num_to_name[now.month]} de {now.year}'

            # Ingresos
            income_cols = list(pd.read_excel(xlsx_path, sheet_name='ingresos'))
            income_data = [df[(df.epsa==epsa)&(df.year==year)&(df.order==order)][col].iloc[0] for col in income_cols]

            for i,val in zip([3,4,6,7,9,10],income_data):
                doc.tables[4].columns[1].cells[i].text = "{:,.2f}".format(val) 

            doc.tables[4].columns[1].cells[2].text = "{:,.2f}".format(income_data[0] + income_data[1])
            doc.tables[4].columns[1].cells[5].text = "{:,.2f}".format(income_data[2] + income_data[3])
            doc.tables[4].columns[1].cells[8].text = "{:,.2f}".format(income_data[4] + income_data[5])
            doc.tables[4].columns[1].cells[1].text = "{:,.2f}".format(sum([income_data[i] for i in range(4)]))
            doc.tables[4].columns[1].cells[0].text = "{:,.2f}".format(sum(income_data))

            # Gastos

            expenses_cols = list(pd.read_excel(xlsx_path, sheet_name='gastos'))
            expenses_data = [df[(df.epsa==epsa)&(df.year==year)&(df.order==order)][col].iloc[0] for col in expenses_cols]

            if epsa_toggle.value == 'Cooperativas':
                for i,val in zip([2,3,5,6,7],expenses_data):
                    doc.tables[5].columns[1].cells[i].text = "{:,.2f}".format(val) 

                doc.tables[5].columns[1].cells[1].text = "{:,.2f}".format(expenses_data[0] + expenses_data[1])
                doc.tables[5].columns[1].cells[4].text = "{:,.2f}".format(expenses_data[2] + expenses_data[3] + expenses_data[4])
                doc.tables[5].columns[1].cells[0].text = "{:,.2f}".format(sum(expenses_data))

            if epsa_toggle.value == 'Municipales':
                for i,val in zip([j+2 for j in range(10)],expenses_data):
                    doc.tables[5].columns[1].cells[i].text = "{:,.2f}".format(val) 

                doc.tables[5].columns[1].cells[1].text = "{:,.2f}".format(expenses_data[0] + expenses_data[1] + expenses_data[2])
                doc.tables[5].columns[1].cells[0].text = "{:,.2f}".format(sum(expenses_data))

            # Inversiones

            investments_cols = list(pd.read_excel(xlsx_path, sheet_name='inversiones'))
            investments_data = [df[(df.epsa==epsa)&(df.year==year)&(df.order==order)][col].iloc[0] for col in investments_cols]

            for i,val in zip([1,2,3,4,5],investments_data):
                doc.tables[6].columns[1].cells[i].text = "{:,.2f}".format(val) 

            doc.tables[6].columns[1].cells[0].text = "{:,.2f}".format(sum(investments_data)) 

            if not exists(out_path):
                os.makedirs(out_path)

            doc.save(join(out_path,f'reporte_poa_{epsa}_{year}_{order}_{now.hour}_{now.minute}.docx'))

            help_html.value = 'Informe generado y guardado en la carpeta <code>datos/reportes</code>!</br>Puedes descargar los reportes desde el navegador (<a href="http://localhost:8888/tree/datos/reportes"><font color="blue">LINK</font></a>) o acceder a ellos directamente a la carpeta en tu ordenador.'

            if os.path.exists(profile_path):
                with open(report_profile_path,'r') as f:
                    profile_json = json.load(f)

                profile_json['last_report_num'] = report_number.value

                with open(profile_path,'w') as f:
                    json.dump(report_profile_json,f)

        def on_save_profile_button_click(b):
            try:
                with open(profile_path, 'r') as f:
                    profile_json = json.load(f)
                    
                profile_json['name'] = name_text.value
                profile_json['prof'] = qualification_type.value
                profile_json['specialty'] = specialty_text.value
                profile_json['last_report_num'] = report_number.value

                with open(profile_path,'w') as f:
                    json.dump(profile_json,f)

                help_html.value = 'Perfil guardado!'
            except Exception as e:
                help_html.value = f"<font color='red'>{str(e)}</font>"

        def on_epsa_dropdown_change(change):
            if epsa_toggle.value == 'Cooperativas':
                df = coop_df
            if epsa_toggle.value == 'Municipales':
                df = muni_df
            try:
                years = list(df[df.epsa == change['new']].year)
                year_dropdown.options = years
                year_dropdown.value = years[0]
                year_dropdown.layout.display = None
            except Exception as e:
                help_html.value = f"<font color='red'>{str(e)}</font>"

        def on_year_dropdown_change(change):
            if epsa_toggle.value == 'Cooperativas':
                df = coop_df
            if epsa_toggle.value == 'Municipales':
                df = muni_df
            try:
                orders = list(df[(df.epsa == epsa_dropdown.value) & (df.year == change['new'])].order)
                order_dropdown.options = orders
                order_dropdown.value = orders[0] if orders else None
                order_dropdown.layout.display = None
            except Exception as e:
                help_html.value = f"<font color='red'>{str(e)}</font>"

        def on_epsa_toggle_change(change):
            if change['new'] == 'Cooperativas':
                if exists(coop_path):
                    book = coop_book
                    df = coop_df
                else:
                    help_html.value = "<font color='red'>Parece que no tienes datos de Cooperativas. Trata de descargar estos datos desde la aplicación 'Descargar Datos'.</font>"
                    return1
            
            if change['new'] == 'Municipales':
                if exists(muni_path):
                    book = muni_book
                    df = muni_df
                else:
                    help_html.value = "<font color='red'>Parece que no tienes datos de EPSAS Municipales. Trata de descargar estos datos desde la aplicación 'Descargar Datos'.</font>"
                    return
                
            epsa_dropdown.options = list(df.epsa) 
            epsa_dropdown.layout.display = None
                
        generate_button.on_click(on_generate_button_click)
        save_profile_button.on_click(on_save_profile_button_click)
        epsa_dropdown.observe(on_epsa_dropdown_change, names='value')
        year_dropdown.observe(on_year_dropdown_change, names='value')
        epsa_toggle.observe(on_epsa_toggle_change, names='value')
        
        accordion = widgets.Accordion([
            widgets.VBox([name_text, qualification_type, specialty_text, report_number,save_profile_button]),
            widgets.VBox([epsa_toggle, epsa_dropdown, year_dropdown, order_dropdown]),
        ])
        accordion.set_title(0, 'Datos Generales')
        accordion.set_title(1,'Datos POA')
        accordion.selected_index = None

        super().__init__(children=[accordion,widgets.HBox([generate_button,]),help_html], **kwargs)
        

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
        load_data_accordion.set_title(0, '0. Ingreso/Autenticación')
        load_data_accordion.set_title(1, '1. Cargar Datos')

        with open(profile_path,'r') as f:
            profile_json = json.load(f)

        if not 'token' in profile_json.keys():
            help_html0.value = "Parece que no cuentas con un token de autorización todavía. Por favor ingresa tus credenciales para generar uno."
            login_widget.layout.display=None
        else:
            help_html0.value = "<font color='green'>Tus credenciales estan en orden. Todo listo para cargar datos! Si no puedes cargar datos es posible que tu token este desactualizado.</font>"
            update_token_button.layout.display=None
        
        super().__init__(children=[load_data_accordion], **kwargs)