import paramiko
from paramiko.client import SSHClient
class SSHUtils:
    def rdm_update(self):
        username = "YOUR_SSH_USERNAME_HERE"
        password = "YOUR_SSH_PASSWORD_HERE"
        host = "YOUR_HOST_IP_HERE"
        port = YOUR_PORT_HERE

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
