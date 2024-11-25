import json
import threading
import time
import numpy as np
import shutil
import os
from pathlib import Path, PurePath
from util.config_manager import ConfigManager
    
class DataProcessor(threading.Thread):
    def __init__(self, config: ConfigManager):
        """Initialize the data processor thread"""
        super().__init__()
        # Initialize config
        self.config = config
        self.app_config = self.config.get_app_config()
        self.usrp_config = self.config.get_usrp_config()

        self.site_name = self.app_config.site_name
        self.data_path = self.app_config.data_path
        self.segment_path = self.app_config.segment_path
        self.record_time = self.app_config.record_time
        self.trigger_level = self.app_config.trigger_level
        self.running = False

        # USRP specifications
        self.adc_voltage_range = self.usrp_config.adc_voltage_range # [-1,1] Volts peak-to-peak
        self.sample_rate = self.usrp_config.sampling_rate
        self.gain = self.usrp_config.gain

    def run(self):
        """Main thread execution"""
        self.running = True
        while self.running:
            try:
                # Create a path object
                data_path = Path(self.data_path)

                # Looking for segment file .npy only
                fileList = sorted(data_path.glob("*.npy"))
                fileCount = len(fileList)

                if fileCount <= 1:
                    time.sleep(5)
                    continue
                    
                # Process each file
                for file in fileList:
                    try:
                        file_name = file.name
                        file_name_without_ext = file.stem
                        
                        # Check file extension
                        file_ext = file_name.split(".")[-1].lower()

                        if len(file_name_without_ext) != 22 or file_ext == "over":
                            continue

                        file_sec = int(file_name_without_ext[4:14])
                        file_microsec = int(file_name_without_ext[15:22])

                        # Read and process file
                        complex_array = self._read_complex_data(file)
                        if complex_array is None:
                            continue

                        # Process data segments
                        self._process_segments(complex_array, file_sec, file_microsec)
                        
                        # Move processed file to folder processed_data
                        # shutil.move(file, str(PurePath(self.processed_path, file_name)))

                        # Remove file
                        os.remove(str(file))
                    
                    except Exception as e:
                        print(f"Error processing file {file}: {str(e)}")
                time.sleep(5)
            except Exception as e:
                print(f"Error in data processor thread: {str(e)}")
                time.sleep(1)  # Wait before retrying

    def _read_complex_data(self, file_path: Path) -> np.ndarray:
        """Read complex IQ data from saved file"""
        try:
            # Load complex IQ samples
            complex_data = np.load(file_path)
            # print(f"Loaded {len(complex_data)} samples from {file_path}")
            return complex_data
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return None

    def _digital_to_voltage(self, complex_data: np.ndarray):
        """
        Convert digital IQ samples to millivolts(mV).
        """
        # Extract real part and convert to millivolts (UHD data is already normalized to [-1,1])
        voltage_mv = np.real(complex_data) * self.adc_voltage_range * 1000
        
        # print(f"Voltage range: {voltage_mv.min():.2f} to {voltage_mv.max():.2f} mV")
        return voltage_mv

    def _find_peak_values(self, voltage: np.ndarray[float]):
        """
        Find the peak value within 1 millisecond windows of the voltage data
        """
        sample_window = int(self.sample_rate * 0.001)  # 1 millisecond window
        peak_values = []
        peak_times = []

        for i in range(0, len(voltage), sample_window):
            window_data = voltage[i:i+sample_window]

            # Find peak value and its index
            peak_idx = np.argmax(np.abs(window_data))
            peak_value = round(float(window_data[peak_idx]), 2)

            if abs(peak_value) >= self.trigger_level:
                # Calculate time of peak in microseconds
                peak_time = int((i + peak_idx) / self.sample_rate * 1e6 * 10) # Multiply by 10 to get a 7-digit number

                peak_values.append(peak_value)  # Convert to mV
                peak_times.append(peak_time)

        return peak_values, peak_times

    def _process_segments(self, complex_array: np.ndarray, file_sec: int, file_microsec: int):
        """Process and write data segments"""
        # Convert to voltage
        voltage = self._digital_to_voltage(complex_array)

        # Find peak values and times
        peak_values, peak_times = self._find_peak_values(voltage)

        # Calculate timestamp in second
        peak_times_sec = [
            f"{file_sec}.{str(file_microsec + time).zfill(7)}"
            if file_microsec + time < 10000000
            else f"{file_sec + 1}.{str(file_microsec + time - 10000000).zfill(7)}"
            for time in peak_times
        ]

        # Write to json format
        # self._write_to_json(peak_values, peak_times_sec, file_sec, file_microsec)

        # Write to file
        self._write_to_file(peak_values, peak_times_sec)

    def _write_to_json(self, peak_values: list, peak_times: list, file_sec: int, file_microsec: int):
        """Save peak values and times of the peak to a JSON file."""
        # Create list of peak dictionaries
        data = {
            "data": [
                {
                    "time_sec": time,
                    "value_mv": value
                }
                for time, value in zip(peak_times, peak_values)
            ]
        }

        # Create json file path
        json_file_name = f"{self.site_name}{file_sec}.{str(file_microsec).zfill(7)}.json"
        json_file_path = PurePath(self.segment_path, json_file_name)

        # Save to JSON file
        try:
            with open(json_file_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Saved data to: {json_file_path}")
            return str(json_file_path)
        except Exception as e:
            print(f"Error saving JSON file {json_file_path}: {str(e)}")
            return None
        
    def _write_to_file(self, peak_values: list, peak_times: list):
        """Save peak values and times of the peak to a file."""
        try:
            # Group by integer part
            grouped_data = {}
            for time, value in list(zip(peak_times, peak_values)):
                time_sec = int(float(time))
                time_decimal = int(str(time).split('.')[1])
                if time_sec not in grouped_data:
                    grouped_data[time_sec] = []
                grouped_data[time_sec].append(f"{time_decimal}={value}")

            # Write the grouped data to existing files (append mode)
            for group, entries in grouped_data.items():
                file_name = f"{self.site_name}{group}"
                file_path = PurePath(self.segment_path, file_name)

                with open(file_path, 'a') as f:  # Open in append mode ('a')
                    for entry in entries:
                        f.write(entry + "\n")

                print(f"Saved data to: {file_path}")
            return str(file_path)
        except Exception as e:
            print(f"Error saving file {file_path}: {str(e)}")
            return None
        
    def stop(self):
        """Stop the thread"""
        self.running = False

if __name__ == '__main__':
    # Initialize config
    config = ConfigManager('config.yaml')
    app_config = config.get_app_config()

    # Create and start data processor thread
    data_processor = DataProcessor(config)
    data_processor.start()
