from flask import Flask, flash, request, redirect, render_template, url_for, session
from flask_sock import Sock
from werkzeug.utils import secure_filename
from time import sleep
import os, glob
from configparser import ConfigParser
import inx.functions
import logging, subprocess

#ciao
app = Flask(__name__)
socket = Sock(app)
app.secret_key = 'whEtr8uQoB'
log_filename = "app.log"

logging.basicConfig(filename=log_filename, level=logging.INFO)

if app.config["ENV"] == "development":
    server_type = "development"
elif app.config["ENV"] == "production":
    server_type = "production"
else:
    server_type = "Unknown"
print ("Server type: ", server_type)


@socket.route('/echo')
def echo(websocket):
    get_config(session["db"])
    # print( "session[\"db\"] ", session["db"])
    global config_dict
    # The variable "triggered" is used to detect if the process
    # of updating data has been launched at least once
    triggered = False
    
    while True:
        if triggered == False:
            triggered = True # Set the execution of this function to true
            result, conx, curs = inx.functions.connect_db(websocket, config_dict["connection_string"], config_dict['company'])
            # The connect_db returns (True, conx, curs)
            # 1st return value: True if connection successful
            # 2nd return value: the connection object to the database
            # 3rd return value: the curson object
            if result != False:
                websocket.send('Process starting')
                # Here we need to work on the files, creating a list of files
                files = glob.glob(config_dict["upload_folder"] + "/*") # Get files

                # Pass files and other essential variables to the run_process function
                inx.functions.run_process(websocket, conx, curs, files, config_dict['run_stored_procedures'])
                websocket.send("Process ended")
            else:
                websocket.send("Connection to DB failed")
              
@app.route("/")
def home():
    # Set ConfigParser and read ini file
    return render_template("home.html", server_type = server_type)

@app.route('/test')
def test():
    return render_template("test.html")

@app.route("/webhook", methods=['POST'])
def handling_webhook():
    # ciao trigger 12
    payload = request.json
    commit_name = payload["head_commit"]["message"] + " (" + payload["head_commit"]["timestamp"] + ")"
    if payload["repository"]["full_name"] == "marcozanella/inx-loader":
        try:
            script_path = "/home/sql_user/inx-loader/script_to_update_the_app.sh"
            username = "sql_user"
            #subprocess.run(["sudo", "-u", username, "/bin/bash", script_path, log_filename], check=True)
            subprocess.run(['su', '-c', f'bash {script_path}', username], check=True)
            logging.info("payload origin confirmed - deploy name " + commit_name)
            logging.info("Ran the script to upgrade the app ...")
        except subprocess.CalledProcessError as e:
            logging.error(e.output)
        # logging.info("Finished the script to upgrade the app ...")
    return "Webhook received successfully", 200
    
@app.route('/inxeu', methods=['POST', 'GET'])
def inxeu():
    # Getting the endpoint name
    # endpoint = request.url_rule.endpoint
    session["db"] = request.url_rule.endpoint
    print ( session["db"] )
    get_config(session["db"])
    clear_folders(config_dict["upload_folder"])
    if request.method == 'POST':
        if 'form_ke30' in request.files and 'form_ke24' in request.files:
            the_ke30_fileobject = request.files['form_ke30']
            the_ke24_fileobject = request.files['form_ke24']
        if the_ke30_fileobject.filename == '' and the_ke24_fileobject.filename == '':
            flash('No selected file')
            return redirect(request.url)
        location = config_dict["upload_folder"]
        check_filename_and_saves_on_server(the_ke30_fileobject, location, 'ke30')
        check_filename_and_saves_on_server(the_ke24_fileobject, location, 'ke24')
        
        # if the_ke30_fileobject.filename != '':
        #     if the_ke30_fileobject and allowed_file(the_ke30_fileobject.filename):
        #         the_ke30_filename = securify_filename(the_ke30_fileobject.filename)
        #         the_ke30_fileobject.save(os.path.join(app.config['UPLOAD_FOLDER_INXEU'], the_ke30_filename))
        # if the_ke24_fileobject.filename != '':
        #     if the_ke24_fileobject and allowed_file(the_ke24_fileobject.filename):
        #         the_ke24_filename = securify_filename(the_ke24_fileobject.filename)
        #         the_ke24_fileobject.save(os.path.join(app.config['UPLOAD_FOLDER_INXEU'], the_ke24_filename))
        return render_template('logger.html', request=request)
    elif request.method == 'GET':
        return render_template('inxeu.html', request=request)

@app.route('/inxd', methods=['POST', 'GET'])
def inxd():
    # Getting the endpoint name
    # endpoint = request.url_rule.endpoint
    session["db"] = request.url_rule.endpoint
    print ( session["db"] )
    get_config(session["db"])
    clear_folders(config_dict["upload_folder"])
    if request.method == 'POST':
        if 'form_ke30' in request.files and 'form_ke24' in request.files:
            the_ke30_fileobject = request.files['form_ke30']
            the_ke24_fileobject = request.files['form_ke24']
            the_zaq_fileobject = request.files['form_zaq']
            the_oo_fileobject = request.files['form_oo']
            the_oh_fileobject = request.files['form_oh']
            the_oit_fileoject = request.files['form_oit']
            the_arr_fileoject = request.files['form_arr']
            the_prl_fileoject = request.files['form_prl']
        if the_ke30_fileobject.filename == '' and the_ke24_fileobject.filename == '' and the_zaq_fileobject.filename == '' and the_oo_fileobject.filename == '' and the_oh_fileobject.filename == '' and the_oit_fileoject.filename == '' and the_arr_fileoject.filename == '' and the_prl_fileoject.filename == '':
            flash('No selected file')
            return redirect(request.url)
        location = config_dict["upload_folder"]
        check_filename_and_saves_on_server(the_ke30_fileobject, location, 'ke30')
        check_filename_and_saves_on_server(the_ke24_fileobject, location, 'ke24')
        check_filename_and_saves_on_server(the_zaq_fileobject, location, 'zaq')
        check_filename_and_saves_on_server(the_oo_fileobject, location, 'oo')
        check_filename_and_saves_on_server(the_oh_fileobject, location, 'oh')
        check_filename_and_saves_on_server(the_oit_fileoject, location, 'oit')
        check_filename_and_saves_on_server(the_arr_fileoject, location, 'arr')
        check_filename_and_saves_on_server(the_prl_fileoject, location, 'prl')
        # return redirect(url_for("logger"))
        return render_template('logger.html', request=request)
    if request.method == 'GET':
        # return render_template('base.html', request=request)
        return render_template('inxd.html', request=request)

@app.route("/local", methods=["POST", "GET"])
def loc():
    # Getting the endpoint name
    # endpoint = request.url_rule.endpoint
    session["db"] = request.url_rule.endpoint
    print ( session["db"] )
    get_config(session["db"])
    clear_folders(config_dict["upload_folder"])
    if request.method == 'POST':
        if 'form_ke30' in request.files and 'form_ke24' in request.files:
            the_ke30_fileobject = request.files['form_ke30']
            the_ke24_fileobject = request.files['form_ke24']
            the_zaq_fileobject = request.files['form_zaq']
            # the_oo_fileobject = request.files['form_oo']
            # the_oh_fileobject = request.files['form_oh']
            # the_oit_fileoject = request.files['form_oit']
            # the_arr_fileoject = request.files['form_arr']
            # the_prl_fileoject = request.files['form_prl']
        if the_ke30_fileobject.filename == '' and the_ke24_fileobject.filename == '' and the_zaq_fileobject == '':
        # if the_ke30_fileobject.filename == '' and the_ke24_fileobject.filename == '' and the_zaq_fileobject.filename == '' and the_oo_fileobject.filename == '' and the_oh_fileobject.filename == '' and the_oit_fileoject.filename == '' and the_arr_fileoject.filename == '' and the_prl_fileoject.filename == '':
            flash('No selected file')
            return redirect(request.url)
        location = config_dict["upload_folder"]
        check_filename_and_saves_on_server(the_ke30_fileobject, location, 'ke30')
        check_filename_and_saves_on_server(the_ke24_fileobject, location, 'ke24')
        check_filename_and_saves_on_server(the_zaq_fileobject, location, 'zaq')
        # check_filename_and_saves_on_server(the_oo_fileobject, location, 'oo')
        # check_filename_and_saves_on_server(the_oh_fileobject, location, 'oh')
        # check_filename_and_saves_on_server(the_oit_fileoject, location, 'oit')
        # check_filename_and_saves_on_server(the_arr_fileoject, location, 'arr')
        # check_filename_and_saves_on_server(the_prl_fileoject, location, 'prl')

        return render_template('logger.html', request=request)
    if request.method == 'GET':
        # return render_template('base.html', request=request)
        return render_template('local.html', request=request)
    pass

@app.route("/logger")
def logger():
    return render_template("logger.html")

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    config = ConfigParser()
    config.read('config.ini')

    if request.method == 'POST':
        config.set('DEFAULT', 'sql_driver_ver', request.form['sql-driver'])
        config.set('DEFAULT', 'max_content_length', request.form['max-cont-len'])
        config.set('DEFAULT', 'allowed_extensions', request.form['allowed-ext'])
        run_stored_procs = bool(request.form.get('run_sp'))
        debug_table = bool(request.form.get('one-col-time'))
        xl_df = bool(request.form.get('export-excel'))
        config.set('DEFAULT', 'run_stored_procedures', str(run_stored_procs))
        config.set('DEFAULT', 'one_column_at_a_time', str(debug_table))
        config.set('DEFAULT', 'export_excel_dataframe', str(xl_df))
        config.set('INXD_SERVER_CONFIG', 'inxd_db_host', request.form['inxd-db-host'])
        config.set('INXD_SERVER_CONFIG', 'inxd_db_name', request.form['inxd-db-name'])
        config.set('INXD_SERVER_CONFIG', 'inxd_db_username', request.form['inxd-db-username'])
        config.set('INXD_SERVER_CONFIG', 'inxd_db_password', request.form['inxd-db-password'])
        config.set('INXD_SERVER_CONFIG', 'inxd_upload_folder', request.form['inxd-upload-folder'])

        config.set('INXEU_SERVER_CONFIG', 'inxeu_db_host', request.form['inxeu-db-host'])
        config.set('INXEU_SERVER_CONFIG', 'inxeu_db_name', request.form['inxeu-db-name'])
        config.set('INXEU_SERVER_CONFIG', 'inxeu_db_username', request.form['inxeu-db-username'])
        config.set('INXEU_SERVER_CONFIG', 'inxeu_db_password', request.form['inxeu-db-password'])
        config.set('INXEU_SERVER_CONFIG', 'inxeu_upload_folder', request.form['inxeu-upload-folder'])
        
        config.set('LOCAL_SERVER_CONFIG', 'local_db_host', request.form['local-db-host'])
        config.set('LOCAL_SERVER_CONFIG', 'local_db_name', request.form['local-db-name'])
        config.set('LOCAL_SERVER_CONFIG', 'local_db_username', request.form['local-db-username'])
        config.set('LOCAL_SERVER_CONFIG', 'local_db_password', request.form['local-db-password'])
        config.set('LOCAL_SERVER_CONFIG', 'local_upload_folder', request.form['local-upload-folder'])

        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        return redirect(url_for('settings'))

    sql_driver_ver = config.get('DEFAULT', 'sql_driver_ver')
    max_content_length = config.get('DEFAULT', 'max_content_length')
    allowed_extensions = config.get('DEFAULT', 'allowed_extensions')
    run_stored_procedures = config.getboolean('DEFAULT', 'run_stored_procedures')
    one_column_at_a_time = config.getboolean('DEFAULT', 'one_column_at_a_time')
    export_excel = config.getboolean('DEFAULT', 'export_excel_dataframe')
    inxd_db_host = config.get('INXD_SERVER_CONFIG', 'inxd_db_host')
    inxd_db_name = config.get('INXD_SERVER_CONFIG', 'inxd_db_name')
    inxd_db_username = config.get('INXD_SERVER_CONFIG', 'inxd_db_username')
    inxd_db_password = config.get('INXD_SERVER_CONFIG', 'inxd_db_password')
    inxd_upload_folder = config.get('INXD_SERVER_CONFIG', 'inxd_upload_folder')
    inxeu_db_host = config.get('INXEU_SERVER_CONFIG', 'inxeu_db_host')
    inxeu_db_name = config.get('INXEU_SERVER_CONFIG', 'inxeu_db_name')
    inxeu_db_username = config.get('INXEU_SERVER_CONFIG', 'inxeu_db_username')
    inxeu_db_password = config.get('INXEU_SERVER_CONFIG', 'inxeu_db_password')
    inxeu_upload_folder = config.get('INXEU_SERVER_CONFIG', 'inxeu_upload_folder')
    local_db_host = config.get('LOCAL_SERVER_CONFIG', 'local_db_host')
    local_db_name = config.get('LOCAL_SERVER_CONFIG', 'local_db_name')
    local_db_username = config.get('LOCAL_SERVER_CONFIG', 'local_db_username')
    local_db_password = config.get('LOCAL_SERVER_CONFIG', 'local_db_password')
    local_upload_folder = config.get('LOCAL_SERVER_CONFIG', 'local_upload_folder')
    

    return render_template('settings.html', sql_driver=sql_driver_ver, max_cont_length=max_content_length, allow_ext=allowed_extensions, run_sp=run_stored_procedures, debug_table=one_column_at_a_time, export_excel=export_excel, inxd_dbhost=inxd_db_host, inxd_dbname=inxd_db_name, inxd_dbusername=inxd_db_username, inxd_dbpassword=inxd_db_password, inxd_uploadfolder=inxd_upload_folder, inxeu_dbhost=inxeu_db_host, inxeu_dbname=inxeu_db_name, inxeu_dbusername=inxeu_db_username, inxeu_dbpassword=inxeu_db_password, inxeu_uploadfolder=inxeu_upload_folder, local_dbhost=local_db_host, local_dbname=local_db_name, local_dbusername=local_db_username, local_dbpassword=local_db_password, local_uploadfolder=local_upload_folder)
 
@app.route("/pbi")
def powerbi():
    return render_template("powerbi.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config_dict["allowed_extensions"]

def securify_filename(filename):
    return secure_filename(filename)

def check_filename_and_saves_on_server(fileobject, location_to_save, filetype):
    if fileobject.filename != '':
        if fileobject and allowed_file(fileobject.filename):
            filename = securify_filename(fileobject.filename)
            # fileobject.save(url_for('uploads', filename=fileobject.filename))
            fileobject.save(os.path.join(location_to_save, filetype + "__" + filename))

def clear_folders(folder):
    folder += '/'
    list_dir = os.listdir(folder)
    for item in list_dir:
        extension = os.path.splitext(item)[1][1:]
        if extension in config_dict["allowed_extensions"]:
            os.remove(os.path.join(folder, item))
            
    # for path, subdirs, files in os.walk(folder):
    #     for name in files:
    #         if os.path.isfile(os.path.join(path,name)):
    #             os.remove(os.path.join(path,name))

def process_file(sock, data):
    sleep(1)
    sock.send("from process_file" + data)

def get_config(company):
    # print('get_config is called', company)
    # Get these setting from settings.ini
    config = ConfigParser()
    config.read('config.ini')
    global config_dict
    # config_dict = {
    #     "sql_driver_ver": config["DEFAULT"]["sql_driver_ver"],
    #     "max_content_length": config["DEFAULT"]["max_content_length"],
    #     "allowed_extensions": config["DEFAULT"]["allowed_extensions"],
    #     "run_stored_procedures": config["DEFAULT"]["run_stored_procedures"],
    #     "one_column_at_a_time": config["DEFAULT"]["one_column_at_a_time"],
    #     "export_excel_dataframe": config["DEFAULT"]["export_excel_dataframe"]
    # }
    config_dict = {
        "sql_driver_ver": config.get('DEFAULT', 'sql_driver_ver'),
        "max_content_length": config.get("DEFAULT", "max_content_length"),
        "allowed_extensions": config.get("DEFAULT", "allowed_extensions"),
        "run_stored_procedures": config.getboolean("DEFAULT", "run_stored_procedures"),
        "one_column_at_a_time": config.getboolean("DEFAULT", "one_column_at_a_time"),
        "export_excel_dataframe": config.getboolean("DEFAULT", "export_excel_dataframe"),
        "company": company
    }
    match company:
        case "inxd":
            config_dict["db_server"] = config.get("INXD_SERVER_CONFIG", "inxd_db_host")
            config_dict["db_name"] = config.get("INXD_SERVER_CONFIG", "inxd_db_name")
            config_dict["db_username"] = config.get("INXD_SERVER_CONFIG", "inxd_db_username")
            config_dict["db_password"] = config.get("INXD_SERVER_CONFIG", "inxd_db_password")
            config_dict["upload_folder"] = config.get("INXD_SERVER_CONFIG", "inxd_upload_folder")
            pass
        case "inxeu":
            config_dict["db_server"] = config.get ("INXEU_SERVER_CONFIG", "inxeu_db_host")
            config_dict["db_name"] = config.get ("INXEU_SERVER_CONFIG", "inxeu_db_name")
            config_dict["db_username"] = config.get ("INXEU_SERVER_CONFIG", "inxeu_db_username")
            config_dict["db_password"] = config.get ("INXEU_SERVER_CONFIG", "inxeu_db_password")
            config_dict["upload_folder"] = config.get ("INXEU_SERVER_CONFIG", "inxeu_upload_folder")
            pass
        case "loc":
            config_dict["db_server"] = config.get("LOCAL_SERVER_CONFIG", "local_db_host")
            config_dict["db_name"] = config.get("LOCAL_SERVER_CONFIG", "local_db_name")
            config_dict["db_username"] = config.get("LOCAL_SERVER_CONFIG", "local_db_username")
            config_dict["db_password"] = config.get("LOCAL_SERVER_CONFIG", "local_db_password")
            config_dict["upload_folder"] = config.get("LOCAL_SERVER_CONFIG", "local_upload_folder")
            pass
    '''
    if company == "inxd":
        config_dict["db_server"] = config["INXD_SERVER_CONFIG"]["inxd_db_host"]
        config_dict["db_name"] = config["INXD_SERVER_CONFIG"]["inxd_db_name"]
        config_dict["db_username"] = config["INXD_SERVER_CONFIG"]["inxd_db_username"]
        config_dict["db_password"] = config["INXD_SERVER_CONFIG"]["inxd_db_password"]
        config_dict["upload_folder"] = config["INXD_SERVER_CONFIG"]["inxd_upload_folder"]
    else:
        config_dict["db_server"] = config["INXEU_SERVER_CONFIG"]["inxeu_db_host"]
        config_dict["db_name"] = config["INXEU_SERVER_CONFIG"]["inxeu_db_name"]
        config_dict["db_username"] = config["INXEU_SERVER_CONFIG"]["inxeu_db_username"]
        config_dict["db_password"] = config["INXEU_SERVER_CONFIG"]["inxeu_db_password"]
        config_dict["upload_folder"] = config["INXEU_SERVER_CONFIG"]["inxeu_upload_folder"]
        '''
    connection_string = "DRIVER={ODBC Driver " + config_dict["sql_driver_ver"] + " for SQL Server};SERVER=" + config_dict["db_server"] + ";DATABASE=" + config_dict["db_name"] + ";UID=" + config_dict["db_username"] + ";PWD=" + config_dict["db_password"] + ";Encrypt=yes;"
    if company == "loc":
        connection_string = connection_string + "TrustServerCertificate=yes;Connection Timeout=30;"
    else:
        connection_string = connection_string + "TrustServerCertificate=no;Connection Timeout=30;"
    
    config_dict["connection_string"] = connection_string
    config_dict["allowed_extensions"] = config_dict["allowed_extensions"].split(" ")
    

if __name__ == "__main__":
    app.run()

