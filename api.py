from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import requests
import os

app = FastAPI()

api_key = os.environ.get('API_KEY')

@app.get("/helloworld")
async def hello_world():
    return {"message": "Hello World"}
    
@app.get("/xinchao")
async def hello_world():
    return {"message": "Xin chào thế giới"}
class RepoDetails(BaseModel):
    owner: str
    repo: str
    token: str

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

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
