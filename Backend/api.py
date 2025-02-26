from flask import Flask
from features.PageRoute.controller import user_bp 

from core.Network import connection_checker
from core.Custom_Errors import NetworkError

app = Flask(__name__)

app.register_blueprint(user_bp, url_prefix='/api')

if __name__ == '__main__':
    
    try:
        if(connection_checker.check_network_connection()):
            raise NetworkError.Network_Error("No Internet")
            
        app.run(host='0.0.0.0', port=5000,debug=True)
    except Exception as e:
        print(e)