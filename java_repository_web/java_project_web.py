from streamlit_ace import st_ace
import streamlit as st
import requests
import base64

# ----- CONFIG -----
GITHUB_USER = "wpzvqrs8"  # Replace with your GitHub username
GITHUB_REPO = "java_pro"  # Replace with your repo name
BRANCH = "main"  # Usually 'main' or 'master'

# Get the GitHub token securely from Streamlit secrets
TOKEN = st.secrets["github_token"]
headers = {"Authorization": f"token {TOKEN}"}


# ---- FUNCTIONS ----
def get_java_files():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/git/trees/{BRANCH}?recursive=1"
    response = requests.get(url, headers=headers)

    # Handle API response and check for errors
    if response.status_code != 200:
        st.error(f"GitHub API error {response.status_code}: {response.text}")
        return []

    data = response.json()
    if 'tree' not in data:
        st.error(f"Unexpected API response: 'tree' key not found.\nResponse: {data}")
        return []

    # Filter out Java files
    java_files = [item['path'] for item in data['tree'] if item['path'].endswith(".java")]
    return java_files


def get_file_content(file_path):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{file_path}?ref={BRANCH}"
    response = requests.get(url, headers=headers)

    # Handle API response and check for errors
    if response.status_code != 200:
        st.error(f"Failed to fetch {file_path}: {response.status_code} {response.text}")
        return "", None

    data = response.json()
    content = base64.b64decode(data['content']).decode('utf-8')
    sha = data['sha']
    return content, sha


def update_file(file_path, new_content, sha, message="Update via Streamlit"):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{file_path}"
    encoded_content = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
    payload = {
        "message": message,
        "content": encoded_content,
        "sha": sha,
        "branch": BRANCH
    }
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code not in [200, 201]:
        st.error(f"Failed to update file: {response.status_code} {response.text}")
        return response.status_code, response.json()

    return response.status_code, response.json()


# ---- STREAMLIT UI ----
st.title("📝 Java Repo Editor")

# Fetch the list of Java files from GitHub repo
files = get_java_files()
if not files:
    st.warning("No Java files found.")
else:
    # Allow the user to select a Java file to edit
    selected_file = st.sidebar.selectbox("Select a Java file to edit", files)

    # Fetch the content of the selected file
    content, sha = get_file_content(selected_file)
    if content:
        # Use the Streamlit Ace editor to edit the content
        edited_content = st_ace(value=content, language='java', theme='monokai', height=500)

        # Input for commit message
        commit_message = st.text_input("Commit message", value="Update via Streamlit")

        if st.button("Save changes to GitHub"):
            status, result = update_file(selected_file, edited_content, sha, commit_message)
            if status in [200, 201]:
                st.success("✅ File updated successfully on GitHub!")
            else:
                st.error(f"❌ Failed to update file: {result}")



