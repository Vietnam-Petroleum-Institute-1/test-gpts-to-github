from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import requests
import os
import base64
from fastapi import Header, APIRouter, HTTPException, FastAPI, UploadFile, File, Request, Form
from pydantic import BaseModel
from typing import List
from fastapi import UploadFile, HTTPException
import pandas as pd
import tempfile
from msal import PublicClientApplication  

app = FastAPI()

api_key = os.environ.get('API_KEY')

@app.get("/hello")
async def hello_world():
    return {"message": "Hello World"}

@app.get("/xinchao")
async def hello_world_vietnamese():
    return {"message": "Xin chào thế giới"}

class RepoDetails(BaseModel):
    owner: str
    repo: str
    token: str

class UpdateFileRequest(BaseModel):
    file_path: str
    repo_path: str
    message: str
    owner: str
    repo: str
    token: str

def upload_file_to_github(file_path, repo_path, message, owner, repo, token):
    with open(file_path, "rb") as file:
        content = base64.b64encode(file.read()).decode()
    
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{repo_path}'
    headers = {
        'Authorization': f'token {token}',
        'Content-Type': 'application/json'
    }
    data = {
        'message': message,
        'content': content
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 201:
        return {'status': 'success', 'message': f'Successfully uploaded {repo_path}'}
    else:
        return {'status': 'failed', 'message': f'Failed to upload {repo_path}: {response.json()}'}

def get_file_sha(owner: str, repo: str, repo_path: str, token: str) -> str:
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{repo_path}'
    headers = {
        'Authorization': f'token {token}',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('sha')
    else:
        return None

@app.post("/update_file")
async def update_file_in_github(request: UpdateFileRequest):
    try:
        with open(request.file_path, "rb") as file:
            content = base64.b64encode(file.read()).decode()

        sha = get_file_sha(request.owner, request.repo, request.repo_path, request.token)
        if sha is None:
            raise HTTPException(status_code=400, detail=f'Failed to get SHA for {request.repo_path}')

        url = f'https://api.github.com/repos/{request.owner}/{request.repo}/contents/{request.repo_path}'
        headers = {
            'Authorization': f'token {request.token}',
            'Content-Type': 'application/json'
        }
        data = {
            'message': request.message,
            'content': content,
            'sha': sha
        }
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            return {"status": "success", "message": f"Successfully updated {request.repo_path}"}
        else:
            raise HTTPException(status_code=400, detail=f'Failed to update {request.repo_path}: {response.json()}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def delete_files_from_repo(owner: str, repo: str, token: str):
    def get_file_sha(path):
        url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        headers = {
            'Authorization': f'token {token}',
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('sha')
        else:
            return None

    def delete_file(path, message):
        sha = get_file_sha(path)
        if sha is None:
            return {'status': 'failed', 'message': f'Failed to get SHA for {path}'}

        url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        headers = {
            'Authorization': f'token {token}',
            'Content-Type': 'application/json'
        }
        data = {
            'message': message,
            'sha': sha
        }
        response = requests.delete(url, headers=headers, json=data)
        if response.status_code == 200:
            return {'status': 'success', 'message': f'Successfully deleted {path}'}
        else:
            try:
                return {'status': 'failed', 'message': f'Failed to delete {path}: {response.json()}'}
            except ValueError:
                return {'status': 'failed', 'message': f'Failed to delete {path}: {response.text}'}

    def list_all_files():
        url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1'
        headers = {
            'Authorization': f'token {token}',
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tree = response.json().get('tree', [])
            return [file['path'] for file in tree if file['type'] == 'blob']
        else:
            return []

    files = list_all_files()
    if not files:
        raise HTTPException(status_code=404, detail="No files found in the repository")

    results = []
    for file in files:
        result = delete_file(file, 'Delete all files from repository')
        results.append(result)

    return results

@app.post("/delete_files")
def delete_files(details: RepoDetails):
    return delete_files_from_repo(details.owner, details.repo, details.token)

@app.post("/upload_file")
async def upload_file(details: RepoDetails, file: UploadFile = File(...), repo_path: str = Form(...), message: str = Form(...)):
    file_location = f"/tmp/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    result = upload_file_to_github(file_location, repo_path, message, details.owner, details.repo, details.token)
    os.remove(file_location)
    return result
@app.get("/token")
def get_access_token():
    username = 'api@oilgas.ai'
    password = 'Gaz59897'
    tenant_id = 'c5ec5abe-76c1-46cb-b3fe-c3b0071ffdb3'
    scope = ['https://analysis.windows.net/powerbi/api/.default']
 
    client_id = 'c3bf460c-3f80-48cb-ba7c-9597aa013552'
    client_secret ='skG8Q~~GwoqybvArHvjmV_z5u8R5qA~05RKPedA8'
    
    try:
        app = PublicClientApplication(
            client_id, authority="https://login.microsoftonline.com/"+tenant_id)
        result = app.acquire_token_by_username_password(
            username, password, scopes=scope)
            
        if "access_token" in result:
            return result['access_token']
        else:
            print(result.get("error_description"))
            return None
 
    except Exception as ex:
        print(ex)
        
    access_token = get_access_token()
    return access_token
@app.get("/tokenapi")
def get_access_token(user, password_user):
    username = user
    password = password_user
    tenant_id = 'c5ec5abe-76c1-46cb-b3fe-c3b0071ffdb3'
    scope = ['https://analysis.windows.net/powerbi/api/.default']
 
    client_id = 'c3bf460c-3f80-48cb-ba7c-9597aa013552'
    client_secret ='skG8Q~~GwoqybvArHvjmV_z5u8R5qA~05RKPedA8'
    
    try:
        app = PublicClientApplication(
            client_id, authority="https://login.microsoftonline.com/"+tenant_id)
        result = app.acquire_token_by_username_password(
            username, password, scopes=scope)
            
        if "access_token" in result:
            return result['access_token']
        else:
            print(result.get("error_description"))
            return None
 
    except Exception as ex:
        print(ex)
        
    access_token = get_access_token()
    return access_token

@app.get("/tokenapipep")
def get_access_token(user, password_user):
    username = user
    password = password_user

    tenant_id = '4de65572-91ab-476b-8d79-b83937779aa4'
    scope = ['https://analysis.windows.net/powerbi/api/.default']
 
    client_id = '40a27c84-d853-4bfe-b881-d5c8188b56a8'
    
    try:
        app = PublicClientApplication(
            client_id, authority="https://login.microsoftonline.com/"+tenant_id)
        result = app.acquire_token_by_username_password(
            username, password, scopes=scope)
            
        if "access_token" in result:
            return result['access_token']
        else:
            print(result.get("error_description"))
            return None
 
    except Exception as ex:
        print(ex)
        
    access_token = get_access_token()
    return access_token

@app.get("/khaithac")
def get_access_token(user, password_user):
    username = user
    password = password_user

    tenant_id = 'c513262f-406c-4ce9-8b69-b26baf5df3c4'
    scope = ['https://analysis.windows.net/powerbi/api/.default']
 
    client_id = 'fa21db3a-3b30-4a1f-9269-74663772993e'
    
    try:
        app = PublicClientApplication(
            client_id, authority="https://login.microsoftonline.com/"+tenant_id)
        result = app.acquire_token_by_username_password(
            username, password, scopes=scope)
            
        if "access_token" in result:
            return result['access_token']
        else:
            print(result.get("error_description"))
            return None
 
    except Exception as ex:
        print(ex)
        
    access_token = get_access_token()
    return access_token
    
# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
