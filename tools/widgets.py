import ipywidgets as widgets
import os
from os.path import dirname as up
import json
import requests

class LoginWidget(widgets.VBox):
    
    def __init__(self):
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
        
        super().__init__(children=[help_html0,l_widget,])