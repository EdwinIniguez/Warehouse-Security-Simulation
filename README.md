Para crear un ambiente virtual nuevo muevete a la carpeta donde vaz a trabajar y pon en la terminal:
python -m venv .venv

If it shows the python binary at .venv/bin/python, inside of your project then it worked.


Para activar el ambiente virtual en Windows:
.venv\Scripts\Activate.ps1

Y deberia de aparecer algo así:
(.venv) PS C:\Users\Moy\OneDrive\Documentos\MultiAgentes-Computacionales\Proyecto_Final_1> 

Checa si el ambiente virtual esta activado con:
Get-Command python

Upgrade pip
If you are using pip to install packages (it comes by default with Python), you should upgrade it to the latest version.
Make sure the virtual environment is active (with the command above) and then run:
python -m pip install --upgrade pip

Add .gitignore
If you are using Git (you should), add a .gitignore file to exclude everything in your .venv from Git.
echo "*" > .venv/.gitignore

If you have a requirements.txt, you can now use it to install its packages. ej:
pip install -r requirements.txt

O instalalos directamente:
pip install "fastapi[standard]"
