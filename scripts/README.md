# Add to CartoVista dev scripts

Contains scripts for developers, as well as the setup information below

## Generating swagger python clients
Install java (it is needed for the script)

Run the script `generateApiClient.ps1` located in this folder. The script will ask for the url of your openAPI specification. 
  - for cloud: use https://cloud.cartovista.com/swagger/v2/swagger.json
  - for dev: use https://cloud-dev.cartovista.com/swagger/v2/swagger.json
  - for localhost: use http://localhost:8000/swagger/v2/swagger.json while your backend is running

Running the script again will replace the clients, allowing you to test in a different environement

The `generateApiClient.ps1` script can be run with the -Prod argument. Running it with this argument will place the resulting api client in the env_production folder instead of the git ignored env_development folder.

## Add Oauth Client to CartoVista database

For authentication to work, the database of the CartoVista environment you are using needs an entry in the cv_oauth_client table. Run the following SQL if an entry does not already exist.
```
INSERT INTO "CartoVistaWebPortal".cv_oauth_client(
	client_id, name, redirect_uris, scopes)
	VALUES ('3cba2e6269684a7f912e4cfac6a9811d', 'QGIS CartoVista Plugin', '{http://127.0.0.1/callback}', '{FULL_ACCESS}');
```


## Deploy the Plugin locally

1. Create constants.py file in the env_development directory with the following content:
```
OAUTH_CLIENT_ID = "" # client_id of the plugin's entry in the cv_oauth_client table in the database (e.g. "3cba2e6269684a7f912e4cfac6a9811d" to match insert statement above)
DEPLOYMENT_URL = "" #url of the targeted deployment. Ensure that it matches the specification used to generate the python API clients (e.g. "http://localhost:8000")
```
2. Run the build script

   - Run build.ps1 located in this directory. Add the -Prod argument if you would like the use the api_client and constants from the env_production folder instead of env_development.

3. Refresh the plugin if QGIS is open

This can be done by either:

  - closing and reopening QGIS
  
  - Plugins > Manage and Install Plugins... > uncheck then check "Add to CartoVista"
  
  - Install and use the "Plugin reloader" plugin. This will create a button in the toolbar that can reload a specified plugin in one click.
  (Seems like this is not reloading every file, restart is required for now. Will try to fix)
    - <img width="228" height="56" alt="image" src="https://github.com/user-attachments/assets/988eab61-0ed0-4a41-90c7-1693f1511cc4" />

  


## Test the Plugin

1. Load "Add to CartoVista" plugin in QGIS: Plugins → Manage and Install Plugins...

2. Upload a Layer or Map  
  a) For a layer: Right-click on a Layer → Export -> Share to CartoVista... → Upload Layer  
  b) For a map: Click on the Plugin toolbar icon → Create a Map

3. Wait for the Success message


## Debug the Plugin

1. Install First Aid plugin

2. Click on new debug button or use ctrl + F12 to open debugger

3. Open the .py files you want to debug. Files should be in C:\Users\USERNAME_HERE\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\cartovista
    or %AppData%\QGIS\QGIS3\profiles\default\python\plugins\cartovista

4. Add breakpoint

5. Use CartoVista plugin like upload map or layer.

## Zip the Plugin
Run the build_zip.ps1 script in this folder. Add the -Prod argument if you would like the use the api_client and constants from the env_production folder instead of env_development.

The resulting zip will be created in this folder.
