import threading
import os
import paramiko
import pysftp
import socket
import time
from pathlib import Path, PurePosixPath
from util.config_manager import ConfigManager

class SFTPUploader(threading.Thread):
    def __init__(self, config: ConfigManager):
        """
        Initialize the SFTP uploader thread
        """
        super().__init__()
        # Get SFTP configuration from config manager
        self.app_config = config.get_app_config()
        self.sftp_config = config.get_sftp_config()

        # Site and local path configuration
        self.site_name = self.app_config.site_name
        self.segment_path = self.app_config.segment_path

        # SFTP connection parameters
        self.host = self.sftp_config.host
        self.port = self.sftp_config.port
        self.username = self.sftp_config.username
        self.password = self.sftp_config.password
        self.remote_path = self.sftp_config.remote_path
        self.running = False
        
        self.remote_path = PurePosixPath(self.remote_path, self.site_name)

    def sftp_connect(self):
            """
            Establish a connection to the SFTP server with comprehensive error handling
            
            :return: SFTP connection object or None
            """
            max_retries = 5
            retry_delay = 2

            for attempt in range(max_retries):
                try:
                    # Set socket timeout
                    socket.setdefaulttimeout(5)
                    
                    # Disable host key checking (consider more secure method in production)
                    cnopts = pysftp.CnOpts()
                    cnopts.hostkeys = None

                    # Establish connection with specific exception handling
                    sftp = pysftp.Connection(
                        host=self.host, 
                        username=self.username,
                        password=self.password,
                        default_path=f"{self.remote_path}",
                        cnopts=cnopts,
                        port=self.port
                    )
                    return sftp
                
                except paramiko.AuthenticationException:
                    print(f"Authentication failed for user {self.username}", flush=True)
                    break  # Stop retrying for authentication failures
                except paramiko.SSHException as ssh_err:
                    print(f"SSH connection failed (Attempt {attempt + 1}): {ssh_err}", flush=True)
                except socket.timeout:
                    print(f"Socket timeout connecting to {self.host} (Attempt {attempt + 1})", flush=True)
                except (pysftp.CredentialException, pysftp.ConnectionException) as e:
                    print(f"SFTP Connection Attempt {attempt + 1} Failed due to SFTP-specific error: {e}", flush=True)
                except Exception as e:
                    print(f"SFTP Connection Attempt {attempt + 1} Failed: {e}", flush=True)
                    
                # Wait before next retry
                time.sleep(retry_delay)
            
            print("Failed to establish SFTP connection after multiple attempts", flush=True)
            return None
    
    def upload_file(self, sftp: pysftp.Connection, segment_file: Path):
            """
            Upload a single file with detailed error handling
            
            :return: Boolean indicating upload success
            """
            segment_filename = segment_file.name
            
            try:
                now = time.ctime()
                print(f"[{now}]: Uploading {segment_filename}", flush=True)
                sftp.put(str(segment_file), preserve_mtime=True)
                
                # Remove segment file after successful upload
                os.remove(str(segment_file))
                return True
            except PermissionError:
                print(f"Permission denied when uploading {segment_filename}", flush=True)
            except FileNotFoundError:
                print(f"File not found: {segment_filename}")
            except paramiko.SFTPError as sftp_err:
                print(f"SFTP error during upload of {segment_filename}: {sftp_err}", flush=True)
            except IOError as io_err:
                print(f"IO error during upload of {segment_filename}: {io_err}", flush=True)
            except Exception as e:
                print(f"Unexpected error uploading {segment_filename}: {e}", flush=True)
            
            return False
    
    def run(self):
        """
        Main thread execution for uploading segment files
        """
        self.running = True
        
        while self.running:
            try:
                # Establish SFTP connection
                sftp = self.sftp_connect()
                if sftp is None:
                    continue

                # Create a directory for uploaded files to SFTP server
                # posix_remote_path = str(self.remote_path)
                # if not sftp.exists(posix_remote_path):
                #     print(f"Remote directory not found: {posix_remote_path}. Creating it...", flush=True)
                #     sftp.makedirs(posix_remote_path)
                #     sftp.chdir(posix_remote_path)
                # else:
                #     sftp.chdir(posix_remote_path)

                # Get list of files
                file_list = sorted(Path(self.segment_path).glob('*'))

                # Limit upload to 50 files
                upload_count = min(len(file_list), 50)
                files_to_upload = file_list[:upload_count]

                # Attempt to upload files
                for segment_file in files_to_upload:                 
                    # Wait for the last file to stabilize
                    if segment_file == files_to_upload[-1]:
                        time.sleep(0)

                    # Upload individual file
                    if not self.upload_file(sftp, segment_file):
                        # If upload fails, break the upload loop
                        break

            except Exception as e:
                print(f"Unexpected error in SFTP uploader: {e}", flush=True)
                time.sleep(1)
            finally:
                if sftp:
                    try:
                        sftp.close()
                        #print("SFTP connection closed", flush=True)

                        # Wait before next upload cycle
                        #time.sleep(1)
                    except Exception as e:
                        print(f"Error closing SFTP connection: {e}", flush=True)

    def stop(self):
        """
        Stop the thread
        """
        self.running = False

if __name__ == '__main__':
    # Initialize config
    config = ConfigManager('config.yaml')
    
    # Create and start SFTP uploader thread
    uploader = SFTPUploader(config)
    uploader.start()
    