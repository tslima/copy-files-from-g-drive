# COPY FILES FROM GOOGLE DRIVE

* Recursivelly goes down in folder tree to download files
* Preserves original hierarchy
* Generate a done file to permit resume of process
* Uses 10 threads to speed up process

## USAGE

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then you need to access Google OAuth Console to create a secret key for te application. Copy file and rename to `credentials.json`

Now you can run the application:

```bash
python copy_files_from_g_drive.py <root folder id>
```