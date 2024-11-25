import numpy as np
import signal
import sys
from data_processor import DataProcessor
from data_uploader import SFTPUploader
# from devices.usrp_recorder import USRPRecorder
from devices.usrp_recorder_sim import USRPSim
from pathlib import Path
from util.config_manager import ConfigManager

# Station configuration parameters
site_name = ""
data_path = ""
log_file_name = ""
trig_lev_file_name = ""

# USRP configuration parameters
sample_rate = 0 # 2 MHz
record_time = 0 # Second
center_freq = 0 # Center frequency
gain = 0  # Increase this value to amplify signal

def signal_handler(signum, frame):
    """Handle Ctrl+C"""
    print("\nStopping recording...")
    recorder.stop()

    # Stop the data processor thread
    data_processor.stop()
    data_processor.join()  # Wait for the thread to finish

    # Stop the data uploader thread
    data_uploader.stop()
    data_uploader.join()  # Wait for the thread to finish

    # del recorder
    sys.exit(0)

def main():
    try:
        while True:
            # Check queue size
            queue_size = recorder.get_queue_size()
            # print(f"Samples in queue: {queue_size}")
            
            # Get next samples
            buffer, gps_time = recorder.get_next_samples(timeout=1.0)
            
            # No data continue to get next queue
            if buffer is None or len(buffer) == 0:
                # print("No buffer")
                continue

            # Extract seconds and microseconds
            seconds = int(gps_time)
            microseconds = int((gps_time - seconds) * 1e6 * 10) # Multiply by 10 to get a 7-digit number

            file_name = f"{site_name}{seconds}.{microseconds:07d}"
            file_path = Path(data_path, file_name)
                
            # Save data
            np.save(file_path, buffer)
            
            print(f"Saved {file_name}.npy to {data_path}")

    except KeyboardInterrupt:
        print("\nStopping recording...")
        recorder.stop()
        sys.exit(0)

if __name__ == "__main__":
    # Initialize config
    config = ConfigManager('config.yaml')
    app_config = config.get_app_config()
    usrp_config = app_config.usrp

    print(f"App Name: {app_config.app_name}")
    print(f"Site Name: {app_config.site_name}")
    print(f"Host Server: {app_config.sftp.host}")

    site_name = app_config.site_name
    data_path = app_config.data_path
    record_time = app_config.record_time
    max_data_count_per_file = sample_rate * record_time

    sample_rate = usrp_config.sampling_rate
    center_freq = usrp_config.center_freq
    gain = usrp_config.gain

    # Create output directory if it doesn't exist
    Path(data_path).mkdir(exist_ok=True)

    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start data processor thread
    data_processor = DataProcessor(config)
    data_processor.start()
    print("Data processor thread started...")

    # Create and start data uploader thread
    data_uploader = SFTPUploader(config)
    data_uploader.start()
    
    # Create and start recorder
    # recorder = USRPRecorder()
    recorder = USRPSim()
    print("Starting recording... Press Ctrl+C to stop")

    recorder.setup_usrp(
        sample_rate = sample_rate,
        center_freq = center_freq,
        gain = gain)
    recorder.start()
    
    main()
