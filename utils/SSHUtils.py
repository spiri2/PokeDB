import paramiko
from paramiko.client import SSHClient
class SSHUtils:
    def rdm_update(self):
        username = "YOUR_SSH_USERNAME_HERE"
        password = "YOUR_SSH_PASSWORD_HERE"
        host = "YOUR_HOST_IP_HERE"
        port = YOUR_PORT_HERE

        ssh = SSHClient()
        
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(host, port=port,
                    username=username,
                    password=password,
                    look_for_keys=False)

            stdin, stdout, stderr = ssh.exec_command("cd rdm && docker-compose pull && docker-compose up -d")

            output = stdout.readlines()
            error = stderr.readlines()

            if len(error) > 0:
                return [False, error]
            else:
                return [True, output]
        except Exception as e:
            return [False, [e]]
        finally:
            ssh.close()

