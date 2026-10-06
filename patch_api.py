import os

file_path = "/Users/adarsh/AI_Business_Tycoon_FE/UnityProject/Assets/Scripts/Game/Services/TycoonAPIService.cs"
with open(file_path, "r") as f:
    content = f.read()

# Replace the generic error handler in PostRequest<TRequest, TResponse>
old_str = """                else
                {
                    string errorMsg = $"Request failed: {request.error} (Code: {request.responseCode})";
                    Debug.LogError($"[TycoonAPIService] {errorMsg}");
                    onError?.Invoke(errorMsg);
                }"""

new_str = """                else
                {
                    string body = request.downloadHandler != null ? request.downloadHandler.text : "";
                    string errorMsg = $"Request failed: {request.error} (Code: {request.responseCode})\\nBody: {body}";
                    Debug.LogError($"[TycoonAPIService] {errorMsg}");
                    onError?.Invo                    onError?.Invo                    onError?.Invo   ce (which is PostRequest<TRequest, TResponse>)
if old_str in content:
    content = content.replace(old_str, new_str, 1)
    with open(file_path, "w") as f:
        f.write(content)
    print("TycoonAPIService.cs patched successfully for detailed logging.")
else:
    print("Could not find the target string to replace. It might already be patched.")
