import uhd
import numpy as np
import threading
import queue
import time
import sys

class USRPRecorder:
    def __init__(self):
        # Threading and queue setup
        self.data_queue = queue.Queue(maxsize=100)  # Buffer for 100 recordings
        self.running = threading.Event()  # Use Event instead of boolean for thread synchronization
        self.recording_thread = None
                
        # Initialize USRP
        self.setup_usrp()
        
    def setup_usrp(self, sample_rate = 4e6, center_freq = 100e6, gain = 0):
        """Initialize and configure USRP device

        Args:
            sample_rate: RX sample rate (Hz)
            center_freq: RX frequency (Hz)
            gain: RX gain (dB)
        """
        # Configuration parameters
        self.sample_rate = sample_rate # Default: 2 MHz
        self.center_freq = center_freq # Default: 100 MHz
        self.gain = gain  # RF gain
        self.samples_per_buffer = int(sample_rate)  # Number of samples per recording

        try:
            # Create USRP device instance
            self.usrp = uhd.usrp.MultiUSRP("num_recv_frames=1024")
            
            # Configure device settings
            self.usrp.set_rx_rate(self.sample_rate)
            self.usrp.set_rx_freq(self.center_freq)
            self.usrp.set_rx_gain(self.gain)
            
            # Setup streaming
            stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
            stream_args.channels = [0]
            self.rx_streamer = self.usrp.get_rx_stream(stream_args)
            
            # Get actual rate for verification
            self.actual_rate = self.usrp.get_rx_rate()
            print(f"Actual sample rate: {self.actual_rate/1e6:.2f} MHz")
            
        except Exception as e:
            print(f"Error setting up USRP: {e}")
            sys.exit(1)
            
    def receive_samples(self):
        """Thread function to continuously receive samples from USRP"""
        try:
            # Prepare streaming
            stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
            stream_cmd.stream_now = True
            self.rx_streamer.issue_stream_cmd(stream_cmd)
            
            # Buffer for received samples
            buffer = np.zeros(self.samples_per_buffer, dtype=np.complex64)
            metadata = uhd.types.RXMetadata()
            
            while self.running.is_set():
                try:
                    # Receive samples
                    samples_received = 0
                    timestamp = time.time()
                    
                    while samples_received < self.samples_per_buffer and self.running.is_set():
                        result = self.rx_streamer.recv(
                            buffer[samples_received:],
                            metadata,
                            timeout=0.1  # Short timeout to check running status more frequently
                        )
                        
                        if metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                            if metadata.error_code == uhd.types.RXMetadataErrorCode.timeout:
                                # Handle timeout by checking if we should continue
                                if not self.running.is_set():
                                    break
                                continue
                            print(f"Error receiving samples: {metadata.error_code}")
                            continue

                        samples_received += result
                    
                    # Only put in queue if we got a full buffer and are still running
                    if samples_received == self.samples_per_buffer and self.running.is_set():
                        try:
                            self.data_queue.put((buffer.copy(), timestamp), timeout=0.1)
                        except queue.Full:
                            print("Queue full, dropping samples")
                    
                except Exception as e:
                    if self.running.is_set():  # Only print error if we're still supposed to be running
                        print(f"Error in receive_samples loop: {e}")
                    
        except Exception as e:
            print(f"Error in receive_samples thread: {e}")
        finally:
            # Ensure streaming is stopped even if an exception occurred
            try:
                stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
                self.rx_streamer.issue_stream_cmd(stream_cmd)
            except Exception as e:
                print(f"Error stopping stream in cleanup: {e}")
            
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
        self.running.set()  # Set the event to True
        self.recording_thread = threading.Thread(target=self.receive_samples)
        self.recording_thread.start()
        
    def stop(self):
        """Stop recording thread"""
        # Clear the running event first
        self.running.clear()
        
        # Stop streaming
        try:
            stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
            self.rx_streamer.issue_stream_cmd(stream_cmd)
        except Exception as e:
            print(f"Error stopping stream: {e}")
        
        # Wait for thread to finish with timeout
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)  # Wait up to 2 seconds
            if self.recording_thread.is_alive():
                print("Warning: Recording thread did not terminate within timeout")
            
        # Clear the queue
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break