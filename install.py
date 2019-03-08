import os
import json
from menuinst import install
from jupyterthemes import install_theme
from git import Git
import requests

install_theme(
    theme='grade3',
    monofont=None,
    tcfontsize=12,
    dffontsize=95,
    cellwidth='88%',
    altprompt=True,
    toolbar=True,
    nbname=True,
    kernellogo=True
)

base_path = os.environ['USERPROFILE']
json_path = os.path.join(base_path,'AAPS-LAB','Menu','notebook.json')
home_directory = os.path.join(base_path,'aapslab')

if not os.path.exists(home_directory):
    try:
        requests.head('http://www.google.com', verify=False, timeout=5)
        Git(os.path.dirname(home_directory)).clone('https://github.com/sergio-chumacero/aapslab.git')
        if os.path.exists(os.path.join(home_directory,'.gitignore')):
            os.remove(os.path.join(home_directory,'.gitignore'))
    except ConnectionError as e:
        os.mkdir(home_directory)
        
        

if os.path.exists(json_path):
    install(json_path, remove=True)
    
    with open(json_path,'r') as f:
        notebook_json = json.load(f)     
        
    notebook_json['menu_items'][0]['name'] = 'AAPS-LAB'
    notebook_json['menu_items'][0]['pyscript'] = '${PYTHON_SCRIPTS}/jupyter-notebook-script.py ' + f'"{home_directory}"'
    
    with open(json_path,'w') as f:
        json.dump(notebook_json, f)
    
    install(json_path)