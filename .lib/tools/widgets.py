import ipywidgets as widgets
import os
from os.path import dirname as up
import json
import requests

import docx
from datetime import datetime

class GenerateReportWidget(widgets.VBox):
    def __init__(self, **kwargs):
        home_dir = os.path.join(os.environ['USERPROFILE'],'aapslab')
        report_profile_path = os.path.join(home_dir,'.profile','report_profile.json')
        model_path = os.path.join(home_dir,'.lib','models','modelo_poa.docx')
        out_path = os.path.join(home_dir,'datos','reportes')

        if os.path.exists(report_profile_path):
            with open(report_profile_path,'r') as f:
                report_profile_json = json.load(f)
        else:
            report_profile_json = {}

        report_number = widgets.BoundedIntText(
            value= report_profile_json.get('last_report_num',0) + 1,
            min=0, max=999, step=1,
            description='Número de reporte:',
            tooltip='entre 0 y 999',
            layout=widgets.Layout(width='50%',),
            style={'description_width': 'initial'},
        )

        name_text = widgets.Text(
            value = report_profile_json.get('name'),
            placeholder='Nombre del autor del documento',
            description='Nombre:',
            layout=widgets.Layout(width='50%',),
        )

        specialty_text = widgets.Text(
            value = report_profile_json.get('specialty'),
            placeholder='Especialidad del profesional',
            description='Especialidad:',
            layout=widgets.Layout(width='50%',),
        )

        qualification_type = widgets.ToggleButtons(
            value=report_profile_json.get('prof'),
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
        )

        save_profile_button = widgets.Button(
            description='Guardar Perfil',
            button_style='info',
            tooltip='Generar Reporte',
            icon='save',
        ) 

        help_html = widgets.HTML()

        prof_name_to_denom = {'Ingeniero':'Ing.', 'Económico':'Lic.',}

        now = datetime.now()
        month_names = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        month_num_to_name = {k+1:v for k,v in zip(range(12), month_names)}

        def on_generate_button_click(b):
            try:
                if os.path.exists(model_path):
                    doc = docx.Document(model_path)
                else:
                    help_html.value = '<font color="red">No se encontró el modelo base de POA.</font>'
                    return

                doc.paragraphs[3].text = f'AAPS/DER/INF/{report_number.value:03d}/2019'

                prof = qualification_type.value
                denom = prof_name_to_denom[prof]

                col = doc.tables[0].columns[2]
                col.cells[2].paragraphs[3].text = f'{denom} {name_text.value}'.title()
                col.cells[2].paragraphs[4].text = f'{prof} {specialty_text.value}'.upper()
                col.cells[5].paragraphs[0].text = f'La Paz, {now.day} de {month_num_to_name[now.month]} de {now.year}'

                if not os.path.exists(out_path):
                    os.makedirs(out_path)

                doc.save(os.path.join(out_path,f'reporte_poa_{month_num_to_name[now.month]}_{now.day}_{now.hour}_{now.minute}.docx'))

                help_html.value = 'Informe generado y guardado en la carpeta <code>datos/reportes</code>!</br>Puedes descargar los reportes desde el navegador (<a href="http://localhost:8888/tree/datos/reportes"><font color="blue">LINK</font></a>) o acceder a ellos directamente a la carpeta en tu ordenador.'
                if os.path.exists(report_profile_path):
                    with open(report_profile_path,'r') as f:
                        report_profile_json = json.load(f)

                    report_profile_json['last_report_num'] = report_number.value

                    with open(report_profile_path,'w') as f:
                        json.dump(report_profile_json,f)
            except Exception as e:
                help_html.value = f"<font color='red'>{str(e)}</font>"

        def on_save_profile_button_click(b):
            try:
                if not os.path.exists(os.path.dirname(report_profile_path)):
                    os.makedirs(os.path.dirname(report_profile_path))

                report_profile_json = dict(
                    name=name_text.value,
                    prof=qualification_type.value,
                    specialty=specialty_text.value,
                    last_report_num=report_number.value,
                )

                with open(report_profile_path,'w') as f:
                    json.dump(report_profile_json,f)

                help_html.value = 'Perfil guardado!'
            except Exception as e:
                help_html.value = f"<font color='red'>{str(e)}</font>"

        generate_button.on_click(on_generate_button_click)
        save_profile_button.on_click(on_save_profile_button_click)
        
        accordion = widgets.Accordion([widgets.VBox([name_text, qualification_type, specialty_text, report_number,])])
        accordion.set_title(0, 'Datos Generales')
        accordion.selected_index = None

        super().__init__(children=[accordion,widgets.HBox([generate_button,save_profile_button]),help_html], **kwargs)
        

class LoginWidget(widgets.VBox):
    
    def __init__(self, **kwargs):
        token_json_path = os.path.join(os.getcwd(), '.auth', 'token.json')
        host = '200.87.123.68'
        protocol = 'http'
        
        help_html0 = widgets.HTML()
        
        username_widget = widgets.Text(
            description='Usuario:',
            placeholder='Usuario del sistema AAPS-API',
        )
        
        password_widget = widgets.Password(
            description='Contraseña:',
            placeholder='Contraseña del usuario'
        )
        
        update_button = widgets.Button(
            description='Actualizar los datos!',
            button_style='success',
            disabled=True,
            tooltip='Actualiza los datos locales desde el sistema AAPS-API!',
            icon='download',
            layout=widgets.Layout(width='300px')
        )

        show_password_button = widgets.ToggleButton(
            value = False,
            button_style='info',
            tooltip='Mostrar Contraseña',
            disabled=True,
            icon='eye',
            layout=widgets.Layout(width='40px')
        )

        help_html = widgets.HTML()
        help_html.layout.width = '500px'
        
        l_widget = widgets.HBox([
            widgets.VBox([
                username_widget,
                widgets.HBox([password_widget,show_password_button,]),
                update_button,
            ]),
            help_html,
        ])
        l_widget.layout.display='none'

        def set_help_html(username, password, show_pass):
            user_label = 'Nombre de Usuario:' if username != '' else ''
            pass_label = 'Contraseña:' if password != '' else ''
            encoded_pass = password if show_pass else '\u2022' * len(password)
            help_html.value = f"<font color='gray'>{user_label}</font> {username} <font color='gray'>{pass_label}</font> {encoded_pass}"

        def on_username_change(change):
            set_help_html(change['new'], password_widget.value, show_password_button.value)
            if change['new'] == '':
                update_button.disabled = True
            elif password_widget.value != '':
                update_button.disabled = False

        def on_password_change(change):
            set_help_html(username_widget.value,change['new'], show_password_button.value)
            if change['new'] == '':
                show_password_button.disabled = True
                update_button.disabled = True
            else:
                show_password_button.disabled = False
                if username_widget.value != '':
                    update_button.disabled = False

        def on_show_pass_change(change):
            set_help_html(username_widget.value, password_widget.value, change['new'])

        def on_update_button_click(b):
            try:
                username = username_widget.value
                password = password_widget.value
                r = requests.post(f'{protocol}://{host}/api-token-auth/', json={'username':username, 'password':password})
                
                if 'token' in r.json().keys():
                    os.makedirs(up(token_json_path))
                    with open(token_json_path,'w') as f:
                        json.dump(r.json(),f)
                    l_widget.layout.display = 'none'
                    help_html0.value = '</br><font color="green">Las credenciales son válidas!</font></br><font color="green">Token guardado. Todo listo para cargar datos!</font>'
                else:
                    help_html.value = "<font color='red'>Las credenciales proporcionadas no son válidas.</font> Verifica tus credenciales. Si el problema persiste, trata de ingresar a través de la <a href='https://aaps-data.appspot.com/admin/'>aplicación administrativa</a>. Si no puedes ingresar a través de esa página tampoco, contacta al administrador/administradora."
            except Exception as e:
                help_html.value = str(e)
            
        username_widget.observe(on_username_change, names='value')
        password_widget.observe(on_password_change, names='value')
        show_password_button.observe(on_show_pass_change, names='value')
        update_button.on_click(on_update_button_click)

        
        
        if not os.path.exists(token_json_path):
            help_html0.value = "<font color='red'>Parece que no cuentas con un token de autorización. Por favor ingresa tus credenciales para generar uno.</font>"
            l_widget.layout.display=None
        else:
            help_html0.value = "<font color='green'>Token de autorización encontrado. Todo listo para cargar datos!</font>"
        
        super().__init__(children=[help_html0,l_widget,], **kwargs)