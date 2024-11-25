import threading
import os
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
        Establish a connection to the SFTP server with retry mechanism
        
        :return: SFTP connection object
        """
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Set socket timeout
                socket.setdefaulttimeout(5)
                
                # Disable host key checking (consider more secure method in production)
                self.cnopts = pysftp.CnOpts()
                self.cnopts.hostkeys = None

                # Establish connection
                sftp = pysftp.Connection(
                    host=self.host, 
                    username=self.username,
                    password=self.password,
                    default_path=f"{self.remote_path}",
                    cnopts=self.cnopts
                )
                return sftp
                # return pysftp.Connection(self.host, username=self.username, password=self.password, default_path=str(self.remote_path))
            except Exception as e:
                print(f"SFTP Connection Attempt {attempt + 1} Failed: {e}")
                time.sleep(retry_delay)
        
        print("Failed to establish SFTP connection after multiple attempts")
        return None
            
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
                #     print(f"Remote directory not found: {posix_remote_path}. Creating it...")
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
                    segment_filename = segment_file.name
                    
                    # Wait for the last file to stabilize
                    if segment_file == files_to_upload[-1]:
                        time.sleep(5)

                    try:
                        print(f"Uploading {segment_filename}")
                        sftp.put(str(segment_file), preserve_mtime=True)
                        # sftp.close()

                        # Remove segment file
                        os.remove(str(segment_file))
                    except Exception as e:
                        print(f"Upload failed for {segment_filename}: {e}")
                        break

            except Exception as e:
                print(f"Unexpected error in SFTP uploader: {e}")
                time.sleep(1)
            finally:
                if sftp:
                    try:
                        sftp.close()
                        print("SFTP connection closed")

                        # Wait before next upload cycle
                        time.sleep(1)
                    except Exception as e:
                        print(f"Error closing SFTP connection: {e}")

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
    