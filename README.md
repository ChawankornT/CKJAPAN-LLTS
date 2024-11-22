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
chmod +x run_signal_recorder.sh
```

3. Create a `config.yaml` file in the project root with your specific configuration. Example:
```yaml
app:
  app_name: SignalRecorder
  site_name: TestSite
  data_path: /path/to/data/storage
  record_time: 60  # seconds
  
  sftp:
    host: sftp.example.com
    username: your_username
    password: your_password

usrp:
  sampling_rate: 2000000  # 2 MHz
  center_freq: 100000000  # 100 MHz
  gain: 10
```

## Running the Application

To start the signal recorder:
```bash
./run_signal_recorder.sh
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
