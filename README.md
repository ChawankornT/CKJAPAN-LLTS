# Signal Recorder Application

## Prerequisites
- Python 3.6+
- pip
- virtualenv
- UHD library* ([Ettus Research](https://files.ettus.com/manual/))

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/ChawankornT/CKJAPAN-LLTS.git
cd <repository-directory>
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Make the run script executable:
```bash
chmod +x run_llts.sh
```

4. Add Script Directory to PATH: Add the directory containing the script to your PATH environment variable:
```bash
echo 'export PATH=$PATH:/<path-to>/CKJAPAN-LLTS' >> ~/.bashrc
source ~/.bashrc
```

5. Create a `config.yaml` file in the project root with your specific configuration. Example:
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

## UHD (USRP Hardware Driver) Installation:

1. Update the Package Lists:
```bash
sudo apt update
```

2. Install UHD: 
```bash
sudo apt install uhd-host
```

3. Verify the Installation: After installation, verify that UHD is properly installed and can detect USRP devices.
Find connected devices:
```bash
uhd_find_devices
```
Probe a specific USRP device:
```bash
uhd_usrp_probe
```
If a device is detected, it will output detailed information about the USRP hardware.

4. Optional: Install UHD Python bindings: If you're using Python with UHD:
```bash
sudo apt install python3-uhd
```

5. More [Installation Instructions](https://files.ettus.com/manual/page_install.html), follow their [Ettus Research GitHub Repository](https://github.com/EttusResearch/uhd)

## Running the Application

To start the signal recorder:
```bash
./run_llts.sh
```
Or, if not added to your PATH, execute the script directly:
```bash
/path/to/CKJAPAN-LLTS/run_llts.sh
```

## Features
- Automatic virtual environment setup
- Dependency management
- Configurable signal recording
- SFTP data upload
- Graceful interrupt handling

## Notes
- Ensure you have the required hardware or UHD for USRP recording
- Modify `config.yaml` to match your specific recording requirements
