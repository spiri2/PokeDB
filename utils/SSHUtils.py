import paramiko
from paramiko.client import SSHClient
class SSHUtils:
    def __init__(self):
        self.username = "SSH_USERNAME"
        self.password = "SSH_PASSWORD"
        self.host = "HOST_IP"
        self.port = PORT_HERE

    def rdm_update(self):

        ssh = SSHClient()
        
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(self.host, port=self.port,
                    username=self.username,
                    password=self.password,
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

    
    def rdm_restart(self):
        ssh = SSHClient()

        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(self.host, port=self.port,
                    username=self.username,
                    password=self.password,
                    look_for_keys=False)

            stdin, stdout, stderr = ssh.exec_command("cd rdm && docker-compose down && docker-compose up -d")

            output = stdout.readlines()
            error = stderr.readlines()

            return [True, output]

        except Exception as e:
            return [False, [e]]
        finally:
            ssh.close()
