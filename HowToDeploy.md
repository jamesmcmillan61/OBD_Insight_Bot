
# How to Deploy

## Deployment Overview

This project was deployed on a **Windows Virtual Machine (VM)** with the following specifications:

- Operating System: **Windows**
- GPU: **None required**
- Storage: **64 GB**
- Web Server: **IIS**
- Framework: **ASP.NET Core**
- AI API: **Python (FastAPI + Uvicorn)**

---

## Front-End Deployment (IIS)

### Enable IIS on Windows

1. Open **Run** (`Win + R`)
2. Type:
   ```
   appwiz.cpl
   ```
3. Select **Turn Windows features on or off**

---

### Install Web Server (IIS)

- Select **Role-based or feature-based installation**
- Enable **Web Server (IIS)** and ensure **Include management tools** is selected
- Enable **IIS Hostable Web Core**
- Under Role Services, ensure **IIS Management Scripts and Tools** are selected
- Install and restart the VM

Verify installation by navigating to `http://localhost` in a browser on the VM.

---

### Install ASP.NET Core Hosting Bundle

Download and install the hosting bundle from Microsoft, then run:

```
iisreset
```

---

### Publish the Web Application

1. Open the project in **Visual Studio**
2. Right-click the project → **Publish**
3. Choose **Folder** and keep default settings
4. Click **Publish**

---

### Deploy to IIS

1. Copy published files
2. Paste into:
   ```
   C:\inetpub\wwwroot
   ```
3. Open the VM IP address in a browser to confirm

---

## AI Deployment

### Setup Python Environment

```powershell
cd "C:\Users\725231\source\repos\2526 - IBM OBD InsightBot\AI\obd-insightbot-api"
python -m venv myenv
.\myenv\Scripts\Activate
```
### Install requirments and start up pipeline

```powershell

pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Deployment Complete

The application is now fully deployed with IIS hosting the front end and FastAPI serving the AI backend.
