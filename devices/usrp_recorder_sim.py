import numpy as np
import threading
import queue
import time
import math


class USRPSim:
    def __init__(self):        
        # Threading and queue setup
        self.data_queue = queue.Queue(maxsize=100)  # Buffer for 10 recordings
        self.running = True
        self.recording_thread = None
                
        # Initialize USRP
        self.setup_usrp()

    def setup_usrp(self, sample_rate = 2e6, center_freq = 100e6, gain = 0):
        self.sample_rate = sample_rate # Default: 4 MHz to achieve 800000 samples in 0.2 seconds
        self.center_freq = center_freq # Default: 100 MHz
        self.gain = gain  # RF gain
        self.samples_per_buffer = int(sample_rate)  # Number of samples per recording

        try:
            # Get actual rate for verification
            self.actual_rate = self.samples_per_buffer
            print(f"Actual sample rate: {self.actual_rate/1e6:.2f} MHz")
            
        except Exception as e:
            print(f"Error setting up USRP: {e}")
    
    def receive_samples(self):
        """Thread function to continuously receive samples from USRP"""
        try:            
            # Buffer for received samples
            buffer = np.zeros(self.samples_per_buffer, dtype=np.complex64)
            
            samples_received = 0
            previous_time = 0

            while self.running:
                try:
                    # Receive samples
                    samples_received = 0
                    timestamp = time.time()
                    # timestamp = math.floor(time.time())

                    # Simulate USRP data
                    if timestamp - previous_time >= 1.0:
                        buffer = np.float32(np.random.uniform(-1, 1, self.samples_per_buffer)) + 1j * np.float32(np.random.uniform(-1, 1, self.samples_per_buffer))
                        # buffer = np.random.uniform(-1, 1, self.samples_per_buffer) + 1j * np.random.uniform(-1, 1, self.samples_per_buffer)
                        
                        # while samples_received < self.samples_per_buffer:
                        #     result = self.rx_streamer.recv(
                        #         buffer[samples_received:],
                        #         metadata,
                        #         timeout=0.1
                        #     )
                            
                        #     samples_received += result

                        # Put samples in queue
                        # timestamp = datetime.now()
                        self.data_queue.put((buffer.copy(), timestamp))
                        # time.sleep(1)
                        previous_time = timestamp
                    
                except queue.Full:
                    print("Queue full, dropping samples")
                    continue
                    
        except Exception as e:
            print(f"Error in receive_samples: {e}")
            self.running = False

    def get_next_samples(self, timeout=1.0):
        """
        Get the next available buffer of samples from the queue
        
        Args:
            timeout (float): How long to wait for samples in seconds
            
        Returns:
            tuple: (numpy.ndarray, datetime) containing samples and timestamp,
                  or (None, None) if no samples available
        """
        try:
            buffer, timestamp = self.data_queue.get(timeout=timeout)
            return buffer, timestamp
        except queue.Empty:
            return None, None
            
    def get_queue_size(self):
        """
        Get current number of sample buffers in queue
        
        Returns:
            int: Number of samples buffers in queue
        """
        return self.data_queue.qsize()
            
    def start(self):
        """Start recording thread"""
        self.recording_thread = threading.Thread(target=self.receive_samples)
        self.recording_thread.start()
        
    def stop(self):
        """Stop recording thread"""
        self.running = False
                
        # Wait for thread to finish
        if self.recording_thread:
            self.recording_thread.join()

# if __name__ == '__main__':
#     # Initialize config
#     config = ConfigManager('config.yaml')
#     app_config = config.get_app_config()

#     # Create and start data processor thread
#     data_processor = DataProcessor(config)
#     data_processor.start()
