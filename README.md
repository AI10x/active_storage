# DigitalOcean Spaces Sync 🚀

This project is a Python-based utility to seamlessly upload and synchronize your local files—like those from Rails' Active Storage (`tmp/storage`)—directly into a **DigitalOcean Spaces** bucket. 

It provides two main functionalities:
1. **Single File Upload**: A script to manually upload individual files via CLI.
2. **Automated Directory Sync**: A script to synchronize an entire directory, paired with a systemd timer that runs automatically in the background every 5 minutes.

## 🌟 Features

- 🐍 **Python & Boto3 Integration**: Leverages the robust `boto3` library (which treats Spaces like AWS S3) for reliable and fast object uploading.
- ⚙️ **Configurable**: Dynamically parses a YAML configuration file (`active_storage.yml`) to grab your DigitalOcean credentials and bucket settings securely without hardcoding.
- ⏱️ **Zero-touch Automation**: A user-level `systemd` service and timer completely automates the background syncing process without requiring full root access.

---

## 📂 Project Walkthrough

Here are the key components of the repository:

### 1. `upload_to_spaces.py`
This script allows you to upload **a single file** to your Space. 
- **How it works:** You run it passing a file path. It reads your credentials from `active_storage.yml` (or environment variables) and uses `boto3` to push the file to the cloud.
- **Example Usage:**
  ```bash
  python3 upload_to_spaces.py --bucket your_bucket_name path/to/my_image.png
  ```

### 2. `sync_to_spaces.py`
This script synchronizes an **entire directory**.
- **How it works:** It recursively walks through all subdirectories and files in a specified localized folder (like `tmp/storage`), parsing your `active_storage.yml` to authenticate, and uploads every file it finds to your DigitalOcean Space, preserving the folder structure.
- **Example Usage:**
  ```bash
  python3 sync_to_spaces.py --directory tmp/storage
  ```

### 3. Systemd Automation Files
To ensure that your web application's files are continuously backed up to the cloud without manual intervention, two systemd configuration files were created (located in your `~/.config/systemd/user/` directory):
- **`do-storage-sync.service`**: Defines the command to execute `sync_to_spaces.py`.
- **`do-storage-sync.timer`**: Schedules the service to execute automatically every 5 minutes (`OnCalendar=*:0/5`).

### 4. `active_storage.yml` *(Ignored in Git)*
Since this file contains sensitive credentials (Access Keys and Secret Keys), it was added to the `.gitignore`. **Do not commit this file.**
It should be formatted as follows:
```yaml
development:
  service: DigitalOcean
  access_key_id: YOUR_DO_ACCESS_KEY
  secret_access_key: YOUR_DO_SECRET_KEY
  region: syd1
  bucket: your_bucket_name
  endpoint: https://syd1.digitaloceanspaces.com
```

---

## 💡 How the Workflow Operates

1. **Your App Saves Files Locally**: Your application (e.g., Rails, Django) saves user uploads into a temporary local directory like `tmp/storage`.
2. **The Timer Triggers**: Every 5 minutes, the `systemctl` timer awakens and invokes the `do-storage-sync.service`.
3. **The Sync Executes**: The service runs `sync_to_spaces.py`, picking up any new files dumped into the target local directory.
4. **Cloud Migration**: `boto3` authenticates against DigitalOcean Spaces and securely uploads the fresh payload.
5. **Logs**: Output and errors are logged directly to your system journal, accessible via `journalctl --user -u do-storage-sync.service`.

This architecture provides a scalable, set-and-forget solution for securely bridging local temporary storage with persistent cloud object storage.
