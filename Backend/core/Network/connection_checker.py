import psutil
import socket  

def check_network_connection():

    interfaces = psutil.net_if_addrs()
    
    for interface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:  
                if addr.address != "127.0.0.1": 
                    return False
                
    return True
    

if __name__=="__main__":
    print(check_network_connection())