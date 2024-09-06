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
import json

app = FastAPI()
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

class RepoInfo(BaseModel):
    owner: str
    repo: str
    token: str

class FileData(BaseModel):
    file_name: str
    file_content: str

class ActionAPIInput(BaseModel):
    domain: str
    method: str
    path: str
    operation: str
    operation_hash: str
    is_consequential: bool
    params: dict

def upload_file_to_github(file_content, repo_path, message, owner, repo, token):
    content = base64.b64encode(file_content).decode('utf-8')

    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{repo_path}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha') if response.status_code == 200 else None

    data = {
        'message': message,
        'content': content,
    }
    if sha:
        data['sha'] = sha

    response = requests.put(url, headers=headers, json=data)

    if response.status_code in [200, 201]:
        return f'Tải lên thành công {repo_path}'
    else:
        raise HTTPException(status_code=400, detail=f'Không thể tải lên {repo_path}: {response.text}')

#@app.post("/upload_file")
@app.post("/action_upload_file") 
async def upload_files(
    repo_info: str = Form(...),
    files: List[UploadFile] = File(...)
):
    try:
        repo_info_dict = json.loads(repo_info)
        repo_info_obj = RepoInfo(**repo_info_dict)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON for repo_info")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid data for RepoInfo")

    results = []
    for file in files:
        file_content = await file.read()
        repo_path = file.filename
        message = f'Tải lên {file.filename} từ API'
        try:
            result = upload_file_to_github(
                file_content, 
                repo_path, 
                message, 
                repo_info_obj.owner, 
                repo_info_obj.repo, 
                repo_info_obj.token
            )
            results.append(result)
        except HTTPException as e:
            results.append(str(e.detail))
    
    return {"results": results}

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

@app.get("/token")
def get_access_token():
    username = ''
    password = ''
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
    
@app.post("/upload_file")
async def action_upload_files(input_data: ActionAPIInput):
    logger.debug(f"Received input data: {input_data}")
    try:
        results = []
        for file_data in input_data.params.files:
            file_content = base64.b64decode(file_data.file_content).decode()
            repo_path = file_data.file_name
            message = f'Tải lên {repo_path} từ Action API'
            try:
                result = upload_file_to_github(
                    file_content,
                    repo_path,
                    message,
                    input_data.params.repo_info.owner,
                    input_data.params.repo_info.repo,
                    input_data.params.repo_info.token
                )
                results.append(result)
            except HTTPException as e:
                results.append(str(e.detail))
        
        return {"results": results}
    except Exception as e:
        logger.exception("An error occurred: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
