# Signal Recorder Application

## Prerequisites
- Python 3.8+
- pip
- virtualenv

## Setup and Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd <repository-directory>
```

2. Make the run script executable:
```bash
chmod +x run.sh
```

3. Create a `config.yaml` file in the project root with your specific configuration. Example:
```yaml
app_name: CKJAPAN-LLTS
site_name: TestSite
sftp:
  host: sftp.example.com
  port: 22
  username: your_username
  password: your_password
  remote_path: /LLTS/Upload/
usrp:
  sampling_rate: 2e6 # 2 MHz
  center_freq: 100e6 # 100 MHz
  gain: 0
  adc_voltage_range: 1 # [-1,1] Volts peak-to-peak
data_path: /path/to/data/storage
segment_path: /path/to/data/segment
record_time: 1 # second
trigger_level: 100 # mV
```

## Running the Application

To start the signal recorder:
```bash
./run.sh
```

## Features
- Automatic virtual environment setup
- Dependency management
- Configurable signal recording
- SFTP data upload
- Graceful interrupt handling

## Notes
- Ensure you have the required hardware or simulation environment for USRP recording
- Modify `config.yaml` to match your specific recording requirements
- The script uses a simulated USRP recorder (`USRPSim`) by default
